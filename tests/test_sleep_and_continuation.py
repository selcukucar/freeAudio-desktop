import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from desktop.sleep_timer import SleepTimer, media_identity, request_windows_shutdown
from desktop.continue_listening import continuation_items
from desktop.catalog import ListeningHistory, load_catalog, write_items
from desktop.downloads import DownloadManager
from desktop.playback import PlaybackGate
from main import DesktopFrame


class SleepModelTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.timer = SleepTimer(lambda:self.now)

    def test_duration_fires_once_and_cancel_or_rearm_removes_previous_action(self):
        self.timer.arm(15)
        self.now = 899
        self.assertIsNone(self.timer.poll())
        self.assertEqual(self.timer.remaining(),1)
        self.now = 900
        self.assertEqual(self.timer.poll(),'stop')
        self.assertIsNone(self.timer.poll())
        self.timer.arm(1,action='shutdown');self.timer.cancel()
        self.now += 1000
        self.assertIsNone(self.timer.poll())
        self.timer.arm(1,action='shutdown');self.timer.arm(30)
        self.assertEqual(self.timer.action,'stop')

    def test_shutdown_always_allows_full_warning_even_after_suspend(self):
        self.timer.arm(15,action='shutdown')
        self.now = 2000
        self.assertEqual(self.timer.poll(),'warning')
        self.assertEqual(self.timer.remaining(),60)
        self.assertIsNone(self.timer.poll())
        self.now += 59
        self.assertIsNone(self.timer.poll())
        self.now += 1
        self.assertEqual(self.timer.poll(),'shutdown')

    def test_end_of_episode_matches_identity_and_shutdown_countdown_starts_after_finish(self):
        identity = media_identity({'media_kind':'audiobook','getem_detail_url':'book','getem_chapter_index':2})
        self.timer.arm(target=identity)
        self.assertIsNone(self.timer.finished(('book','other',2)))
        self.assertFalse(self.timer.changed_media(None))
        self.assertEqual(self.timer.finished(identity),'stop')
        self.assertIsNone(self.timer.finished(identity))
        self.timer.arm(target=identity,action='shutdown')
        self.assertEqual(self.timer.finished(identity),'countdown')
        self.assertEqual(self.timer.poll(),'warning')
        self.now += 60
        self.assertEqual(self.timer.poll(),'shutdown')
        self.timer.arm(target=identity)
        self.assertTrue(self.timer.changed_media(('book','book',3)))
        self.assertIsNone(self.timer.mode)

    def test_invalid_inputs_cannot_replace_an_existing_timer(self):
        self.timer.arm(30)
        for minutes in (0,-1,481,1.5,True):
            with self.assertRaises(ValueError):self.timer.arm(minutes)
            self.assertEqual(self.timer.remaining(),1800)
        with self.assertRaises(ValueError):self.timer.arm()
        with self.assertRaises(ValueError):self.timer.arm(5,action='force')

    def test_shutdown_adapter_never_forces_apps_and_test_mode_never_invokes_windows(self):
        # subprocess is mocked for every invocation. Never shut down the host.
        with patch('subprocess.run') as run:
            with self.assertRaises(RuntimeError):request_windows_shutdown(test_mode=True)
            run.assert_not_called()
            request_windows_shutdown()
        args,kwargs = run.call_args
        self.assertEqual(args[0],[str(Path(os.environ['SystemRoot'])/'System32'/'shutdown.exe'),'/s','/t','0'])
        self.assertNotIn('/f',args[0])
        self.assertTrue(kwargs['check'])


class SleepIntegrationTests(unittest.TestCase):
    def frame(self):
        player=Mock();player.get_current_station.return_value=None;player.has_media.return_value=False
        frame=types.SimpleNamespace(_closing=False,_power_launching=False,_power_pending_since=None,
            _sleep_window=None,_main_view=None,_stop_pending=None,_resume_after_stop=False,
            _last_stop_succeeded=None,_playback_gate=PlaybackGate(),sleep_timer=SleepTimer(lambda:1000),
            plugin=types.SimpleNamespace(_player=player),notifications=Mock(),translate=lambda s:s,
            has_background_jobs=Mock(return_value=False),persist_settings=Mock(return_value=True),
            show_sleep=Mock(),shutdown_result=Mock(),_no_power_actions=True)
        for name in ('sleep_tick','cancel_sleep','handle_media_finished'):
            setattr(frame,name,types.MethodType(getattr(DesktopFrame,name),frame))
        def stop():
            frame._stop_pending=frame._playback_gate.cancel()
            frame._last_stop_succeeded=None
        frame.stop_playback=Mock(side_effect=stop)
        frame.downloads=Mock()
        return frame

    def expired_shutdown(self,frame):
        frame.sleep_timer.arm(1,action='shutdown')
        frame.sleep_timer.deadline=999;frame.sleep_timer.warned=True
        frame.sleep_tick()

    def test_active_work_cancels_shutdown_but_not_plain_sleep(self):
        frame=self.frame();frame.has_background_jobs.return_value=True
        frame.sleep_timer.arm(1,action='shutdown');frame.sleep_tick()
        self.assertIsNone(frame.sleep_timer.mode);frame.stop_playback.assert_not_called()
        frame.sleep_timer.arm(1);frame.sleep_timer.deadline=999;frame.sleep_tick()
        frame.stop_playback.assert_called_once()

    def test_cancel_while_stopping_prevents_power_request(self):
        frame=self.frame();self.expired_shutdown(frame)
        self.assertIsNotNone(frame._power_pending_since)
        frame.cancel_sleep();frame._stop_pending=None
        with patch('main.threading.Thread') as thread:frame.sleep_tick()
        thread.assert_not_called()

    def test_stop_failure_replay_and_new_play_request_each_cancel_power(self):
        for change in ('failure','replay','new_request','still_playing'):
            with self.subTest(change=change):
                frame=self.frame();self.expired_shutdown(frame)
                if change=='failure':frame._stop_pending=None
                if change=='replay':frame._resume_after_stop=True
                if change=='new_request':frame._playback_gate.request()
                if change=='still_playing':
                    frame._stop_pending=None;frame._last_stop_succeeded=frame._power_stop_token
                    frame.plugin._player.has_media.return_value=True
                with patch('main.threading.Thread') as thread:frame.sleep_tick()
                thread.assert_not_called();self.assertIsNone(frame._power_pending_since)

    def test_successful_stop_still_requires_settings_saved_and_no_active_work(self):
        for save,active,expected in ((True,False,True),(False,False,False),(True,True,False)):
            frame=self.frame();self.expired_shutdown(frame)
            frame._stop_pending=None;frame._last_stop_succeeded=frame._power_stop_token
            frame.persist_settings.return_value=save;frame.has_background_jobs.return_value=active
            with patch('main.threading.Thread') as thread:frame.sleep_tick()
            self.assertEqual(thread.called,expected)

    def test_end_timer_prevents_auto_advance_and_marks_finished_offline_episode(self):
        frame=self.frame();station={'url':'local.mp3','podcast_resume_key':'https://example.org/e','media_kind':'podcast'}
        frame.sleep_timer.arm(target=media_identity(station))
        self.assertTrue(frame.handle_media_finished(station))
        frame.downloads.mark_finished.assert_called_once_with('https://example.org/e')
        frame.stop_playback.assert_called_once()

    def test_late_finish_cannot_stop_a_new_media_request(self):
        frame=self.frame();station={'url':'old','media_kind':'podcast'}
        frame.sleep_timer.arm(target=media_identity(station))
        frame._playback_gate.request()
        self.assertTrue(frame.handle_media_finished(station))
        frame.stop_playback.assert_not_called()
        frame._playback_gate.cancel()
        frame.plugin._player.get_current_station.return_value={'url':'new','media_kind':'podcast'}
        self.assertTrue(frame.handle_media_finished(station))
        frame.stop_playback.assert_not_called()
        self.assertIsNone(frame.sleep_timer.mode)


class ContinuationTests(unittest.TestCase):
    def test_ignores_radio_finished_media_and_duplicates_uses_download_resume_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory,'audio.mp3');path.write_bytes(b'audio')
            stations=[dict(url='radio',media_kind='radio'),dict(url='done',media_kind='podcast'),
                      dict(url='remote',media_kind='podcast',name='Episode'),dict(url='remote',media_kind='podcast')]
            history=Mock();history.snapshot.return_value=[{'station':s} for s in stations]
            player=Mock();player.get_podcast_position.side_effect=lambda key:-1 if key=='done' else 120
            downloads=Mock();downloads.snapshot.return_value=[dict(url='remote',title='Episode',path=str(path),state='completed')]
            downloads.resolve_path.side_effect=lambda item:Path(item['path'])
            rows=continuation_items(history,player,downloads,[])
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['position'],120)
            self.assertEqual(rows[0]['station']['url'],str(path))
            self.assertEqual(rows[0]['station']['podcast_resume_key'],'remote')
            self.assertTrue(rows[0]['available'])

    def test_book_resume_uses_latest_library_chapter_without_persisting_proxy(self):
        history=Mock();history.snapshot.return_value=[{'station':dict(url='',name='Old chapter',media_kind='audiobook',getem_detail_url='book',getem_chapter_index=0)}]
        book=types.SimpleNamespace(title='Book',last_chapter_index=1,chapters=[{'url':'a'},{'url':'b','title':'Second'}])
        library=Mock();library.get_book_by_key.return_value=book
        downloads=Mock();downloads.snapshot.return_value=[]
        player=Mock();player.get_podcast_position.return_value=21
        rows=continuation_items(history,player,downloads,[library])
        self.assertEqual(rows[0]['station']['getem_chapter_index'],1)
        self.assertEqual(rows[0]['station']['url'],'')
        player.get_podcast_position.assert_called_once_with('b')
        library.get_book_by_key.return_value=None
        self.assertFalse(continuation_items(history,player,downloads,[library])[0]['available'])

    def test_listened_mark_hides_episode_and_unlistened_mark_restores_finished_episode(self):
        history=Mock();history.snapshot.return_value=[{'station':dict(url='https://example.org/e',media_kind='podcast')}]
        player=Mock();player.get_podcast_position.return_value=-1
        entry=dict(url='https://example.org/e',state='completed',listened=True)
        downloads=Mock();downloads.snapshot.side_effect=lambda:[entry];downloads.resolve_path.return_value=Path('missing.mp3')
        self.assertEqual(continuation_items(history,player,downloads,[]),[])
        entry['listened']=False
        self.assertEqual(continuation_items(history,player,downloads,[]),[])
        entry['listened_override']=False
        self.assertEqual(continuation_items(history,player,downloads,[])[0]['position'],0)


class RecoveryTests(unittest.TestCase):
    def test_corrupt_json_is_preserved_before_repair_and_future_schema_is_readonly(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory,'library.json');original=b'{broken'
            path.write_bytes(original)
            items,backup,readonly=load_catalog(path,lambda x:True)
            self.assertEqual(items,[]);self.assertFalse(readonly)
            self.assertEqual(Path(backup).read_bytes(),original)
            path.write_text('{"schema": 999, "items": []}')
            original=path.read_bytes()
            items,backup,readonly=load_catalog(path,lambda x:True)
            self.assertTrue(readonly);self.assertEqual(path.read_bytes(),original)

    def test_bad_rows_are_backed_up_without_discarding_valid_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory,'freeAudio_listening_history.json')
            valid={'played':123,'station':{'url':'https://example.org/a','name':'A'}}
            write_items(path,[valid,{'played':'bad','station':{}},None])
            history=ListeningHistory(directory)
            self.assertEqual(history.snapshot(),[valid]);self.assertTrue(Path(history.recovery).is_file())
            history.observe({'url':'https://example.org/new'})
            history.clear();history.observe({'url':'https://example.org/new'})
            self.assertEqual(len(history.snapshot()),1)

    def test_disk_failure_during_recovery_keeps_original_readonly(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory,'broken.json');path.write_text('{broken')
            with patch('desktop.catalog.write_items',side_effect=OSError('disk full')):
                items,backup,readonly=load_catalog(path,lambda x:True)
            self.assertTrue(readonly);self.assertEqual(path.read_text(),'{broken')


if __name__=='__main__':unittest.main()
