import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
from desktop.navigation import adjacent_media
from desktop.shortcuts import Shortcuts
from desktop.updates import release_notes
from desktop.playback import PlaybackGate
from main import DesktopFrame


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.feed=types.SimpleNamespace(url='https://example.org/feed',title='Podcast',author='Author',audio_profile=None)
        self.feed.episodes=[types.SimpleNamespace(url='https://example.org/'+str(i),title=str(i),
            to_dict=lambda i=i:{'url':'https://example.org/'+str(i),'media_kind':'podcast'}) for i in range(3)]
        self.plugin=Mock();self.plugin._nav_dialog.return_value=None
        self.plugin._nav_podcast_manager.return_value.get_feed_by_url.return_value=self.feed
        self.modules=patch.dict(sys.modules,{'freeAudio':types.SimpleNamespace(podcast=Mock())})
        self.modules.start();self.addCleanup(self.modules.stop)

    def test_podcast_moves_within_same_feed_and_reports_boundaries(self):
        station={'url':self.feed.episodes[1].url,'media_kind':'podcast','podcast_feed_url':self.feed.url}
        for direction,index in ((-1,0),(1,2)):
            result,commit=adjacent_media(self.plugin,station,direction,Mock())
            self.assertEqual(result['url'],self.feed.episodes[index].url)
            self.assertEqual(result['podcast_feed_url'],self.feed.url)
            self.assertIsNone(commit)
        station['url']=self.feed.episodes[0].url
        with self.assertRaisesRegex(ValueError,'first episode'):
            adjacent_media(self.plugin,station,-1,Mock())
        station['url']=self.feed.episodes[-1].url
        with self.assertRaisesRegex(ValueError,'last episode'):
            adjacent_media(self.plugin,station,1,Mock())

    def test_offline_podcasts_never_fetch_and_keep_resume_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            paths=[Path(directory,str(i)+'.mp3') for i in range(2)]
            for path in paths:path.write_bytes(b'audio')
            items=[dict(url='https://example.org/'+str(i),path=str(path),state='completed',title=str(i)) for i,path in enumerate(paths)]
            manager=types.SimpleNamespace(snapshot=lambda:items,resolve_path=lambda item:Path(item['path']))
            target,_=adjacent_media(self.plugin,{'url':str(paths[0]),'media_kind':'podcast','podcast_resume_key':items[0]['url']},1,manager)
            self.assertEqual(target['url'],str(paths[1]));self.assertEqual(target['podcast_resume_key'],items[1]['url'])
            self.plugin._nav_podcast_manager.assert_not_called()

    def test_all_book_sources_move_chapters_without_changing_book_or_early_progress(self):
        for source in ('getem','librivox','gutenberg_audiobooks'):
            with self.subTest(source=source):
                library=Mock();book=types.SimpleNamespace(detail_url='book-1',title='Book',audio_profile=None,
                    chapters=[{'url':'chapter-'+str(i),'title':str(i)} for i in range(3)],
                    to_dict=lambda:{'media_kind':'audiobook','getem_detail_url':'book-1'})
                providers={}
                for name,cls in [('getem','GetemLibrary'),('librivox','LibrivoxLibrary'),('gutenberg_audiobooks','GutenbergLibrary')]:
                    current=library if name==source else Mock()
                    current.get_book_by_key.return_value=book if name==source else None
                    providers[name]=types.SimpleNamespace(**{cls:lambda current=current:current},get_stream_url=lambda url,**kwargs:'https://example.org/'+url)
                with patch.dict(sys.modules,{'freeAudio':types.SimpleNamespace(**providers)}):
                    target,commit=adjacent_media(self.plugin,{'media_kind':'audiobook','getem_detail_url':'book-1','getem_chapter_index':1},1,Mock())
                    self.assertEqual(target['getem_detail_url'],'book-1');self.assertEqual(target['getem_chapter_index'],2)
                    self.assertEqual(target['podcast_resume_key'],'chapter-2')
                    library.mark_progress.assert_not_called();commit();library.mark_progress.assert_called_once_with(book,2)
                    with self.assertRaisesRegex(ValueError,'first part'):
                        adjacent_media(self.plugin,{'media_kind':'audiobook','getem_detail_url':'book-1','getem_chapter_index':0},-1,Mock())

    def test_late_navigation_cannot_play_or_change_progress_after_stop(self):
        gate=PlaybackGate();token=gate.request();gate.cancel()
        frame=types.SimpleNamespace(_closing=False,_playback_gate=gate,plugin=Mock(),notifications=Mock())
        commit=Mock()
        DesktopFrame.navigation_done(frame,token,{'url':'new'},commit,None)
        commit.assert_not_called();frame.plugin._play_station.assert_not_called()

    def test_book_navigation_syncs_library_auto_advance_after_committing_progress(self):
        gate=PlaybackGate();token=gate.request()
        frame=types.SimpleNamespace(_closing=False,_playback_gate=gate,plugin=Mock(),notifications=Mock(),translate=lambda s:s)
        order=[];commit=lambda:order.append('progress')
        frame.plugin._play_station.side_effect=lambda target:order.append('play')
        frame.plugin._nav_sync_dialog_audiobook.side_effect=lambda key:order.append('sync')
        DesktopFrame.navigation_done(frame,token,{'media_kind':'audiobook','getem_detail_url':'book-1'},commit,None)
        self.assertEqual(order,['progress','play','sync'])
        frame.plugin._nav_sync_dialog_audiobook.assert_called_once_with('book-1')

    def test_library_commands_are_separate_without_removing_saved_shortcuts(self):
        shortcuts=Shortcuts.__new__(Shortcuts)
        shortcuts.commands={'toggleRecord':('Record',Mock()),'playFavoriteStation_abc':('Station playback shortcut',Mock()),
                            'playAudiobook_def':('Book playback shortcut',Mock())}
        self.assertEqual(shortcuts.command_names(),['toggleRecord'])
        self.assertEqual(shortcuts.command_names(True),['playFavoriteStation_abc','playAudiobook_def'])

    def test_release_notes_must_match_exact_stable_version(self):
        with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps({'tag_name':'v2.1.0','body':'New controls'}).encode())):
            self.assertEqual(release_notes('owner/repo','2.1.0'),'New controls')
        for data in ({'tag_name':'v2.0.0','body':'wrong'},{'tag_name':'v2.1.0','draft':True}):
            with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(data).encode())),self.assertRaises(ValueError):
                release_notes('owner/repo','2.1.0')
