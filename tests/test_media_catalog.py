import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from desktop.catalog import ListeningHistory, write_items
from desktop.downloads import DownloadManager
from desktop.media_dialogs import playback_station


def wait_for(predicate):
    end = time.monotonic() + 4
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(.01)
    return False


class DownloadQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.managers = []

    def tearDown(self):
        for manager in self.managers:
            manager.close()
            for worker in manager.workers:
                worker.join(3)
                self.assertFalse(worker.is_alive())
        self.temp.cleanup()

    def manager(self, downloader):
        manager = DownloadManager(self.root, downloader)
        self.managers.append(manager)
        return manager

    def test_queue_limits_workers_cancels_queued_and_active_then_retries(self):
        started, lock = [], threading.Lock()
        def downloader(url, path, progress, cancel):
            with lock:
                started.append(url)
            progress(42, 100)
            cancel.wait(3)
            if cancel.is_set():
                raise RuntimeError('cancelled')
            Path(path).write_bytes(b'audio')
        manager = self.manager(downloader)
        a = manager.enqueue('A', 'https://example.org/a', self.root / 'a.mp3')
        b = manager.enqueue('B', 'https://example.org/b', self.root / 'b.mp3')
        c = manager.enqueue('C', 'https://example.org/c', self.root / 'c.mp3')
        self.assertTrue(wait_for(lambda: len(started) == 2))
        self.assertEqual(set(started), {'https://example.org/a', 'https://example.org/b'})
        self.assertEqual(manager.enqueue('A', a['url'], self.root / 'a.mp3')['id'], a['id'])
        self.assertEqual(len(manager.snapshot()), 3)
        manager.cancel(c['id'])
        manager.cancel(a['id'])
        self.assertTrue(wait_for(lambda: next(x for x in manager.snapshot() if x['id'] == a['id'])['state'] == 'cancelled'))
        self.assertNotIn(c['url'], started)
        manager.downloader = lambda url,path,**kwargs: Path(path).write_bytes(b'audio')
        manager.retry(a['id'])
        self.assertTrue(wait_for(lambda: next(x for x in manager.snapshot() if x['id'] == a['id'])['state'] == 'completed'))

    def test_persistent_offline_playback_uses_original_resume_key_and_relative_path(self):
        manager = self.manager(lambda url,path,**kwargs: Path(path).write_bytes(b'audio'))
        item = manager.enqueue('Episode', 'https://example.org/episode.mp3', self.root / 'episode.mp3')
        self.assertTrue(wait_for(lambda: manager.snapshot()[0]['state'] == 'completed'))
        item = manager.snapshot()[0]
        self.assertEqual(item['path'], 'episode.mp3')
        station = playback_station(item, manager)
        self.assertEqual(station['podcast_resume_key'], item['url'])
        self.assertEqual(station['media_kind'], 'podcast')
        self.assertEqual(Path(station['url']).read_bytes(), b'audio')
        manager.close()
        for worker in manager.workers:
            worker.join(2)
        reopened = self.manager(lambda *args,**kwargs: self.fail('completed download restarted'))
        self.assertEqual(reopened.snapshot()[0]['state'], 'completed')
        manager.remove(item['id'])
        self.assertTrue((self.root / 'episode.mp3').is_file())

    def test_restart_marks_interrupted_downloads_for_explicit_retry(self):
        write_items(self.root / 'freeAudio_downloads.json', [dict(id='test',title='Episode',url='https://example.org/audio',path='episode.mp3',state='downloading')])
        manager = self.manager(lambda *args,**kwargs: self.fail('automatic retry'))
        self.assertEqual(manager.snapshot()[0]['state'], 'cancelled')

    def test_existing_files_are_adopted_and_changed_files_are_not_deleted(self):
        target = self.root / 'episode.mp3';target.write_bytes(b'audio')
        manager = self.manager(lambda *args,**kwargs: self.fail('existing file overwritten'))
        item = manager.enqueue('Episode','https://example.org/audio',target)
        self.assertEqual(item['state'], 'completed')
        target.write_bytes(b'changed audio')
        with self.assertRaises(ValueError):
            manager.remove(item['id'], delete_file=True)
        self.assertTrue(target.exists())
        with self.assertRaises(ValueError):
            playback_station(dict(item,state='failed'),manager)

    def test_retry_uses_the_current_user_destination(self):
        manager=self.manager(lambda *args,**kwargs: (_ for _ in ()).throw(OSError('offline')))
        item=manager.enqueue('Episode','https://example.org/audio',self.root/'old.mp3')
        self.assertTrue(wait_for(lambda: manager.snapshot()[0]['state']=='failed'))
        manager.destination=lambda title,url:self.root/'new.mp3'
        manager.downloader=lambda url,path,**kwargs:Path(path).write_bytes(b'audio')
        manager.retry(item['id'])
        self.assertTrue(wait_for(lambda: manager.snapshot()[0]['state']=='completed'))
        self.assertEqual(manager.resolve_path(manager.snapshot()[0]),self.root/'new.mp3')
        self.assertFalse((self.root/'old.mp3').exists())

    def test_failed_save_does_not_start_an_untracked_download(self):
        manager = self.manager(lambda *args,**kwargs: self.fail('untracked download'))
        with patch('desktop.downloads.write_items', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                manager.enqueue('Episode','https://example.org/audio',self.root/'episode.mp3')
        self.assertEqual(manager.snapshot(), [])


class HistoryTests(unittest.TestCase):
    def test_deduplication_reordering_limit_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            history = ListeningHistory(directory)
            history.observe({'url':'https://example.org/a','name':'A','password':'secret'})
            history.observe({'url':'https://example.org/a','name':'A'})
            self.assertEqual(len(history.snapshot()),1)
            history.observe({'url':'https://example.org/b','name':'B'})
            history.observe({'url':'https://example.org/a','name':'A'})
            self.assertEqual(history.snapshot()[0]['station']['name'],'A')
            self.assertNotIn('password',history.path.read_text())
            with patch('desktop.catalog.write_items'):
                for i in range(210):
                    history.observe({'url':f'https://example.org/{i}','name':str(i)})
            self.assertEqual(len(history.snapshot()),200)
            self.assertEqual(len(ListeningHistory(directory).snapshot()),2)
            history.clear()
            self.assertEqual(ListeningHistory(directory).snapshot(),[])

    def test_getem_keeps_book_reference_without_ephemeral_proxy_or_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            history = ListeningHistory(directory)
            history.observe({'name':'Book','url':'http://127.0.0.1:1000/private-token',
                'media_kind':'audiobook','getem_detail_url':'https://getem.boun.edu.tr/book/1',
                'getem_chapter_index':2,'podcast_resume_key':'private-key','cookie':'secret'})
            text = history.path.read_text()
            self.assertNotIn('private-token',text)
            self.assertNotIn('private-key',text)
            self.assertNotIn('secret',text)
            self.assertEqual(history.snapshot()[0]['station']['getem_chapter_index'],2)
