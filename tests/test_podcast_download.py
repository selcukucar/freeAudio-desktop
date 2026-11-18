"""Exercise the actual dialog handlers without loading the entire NVDA UI."""
import ast
from pathlib import Path
import threading
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]

class PodcastMenuTests(unittest.TestCase):
    def setUp(self):
        wanted = {'_show_podcast_preview_context_menu', '_on_podcast_preview_download',
                  '_on_episode_download', '_download_podcast_episode', '_on_podcast_download_done'}
        tree = ast.parse((ROOT / 'vendor/freeAudio/radioDialog.py').read_text(encoding='utf-8-sig'))
        methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in wanted]
        self.assertEqual(len(methods), len(wanted))
        cls = ast.ClassDef(name='Controller', bases=[], keywords=[], body=methods, decorator_list=[])
        self.messages, self.callbacks, self.jobs = [], [], []
        self.menu = Mock()
        self.menu.Append.side_effect = lambda *args: Mock()
        wx = types.SimpleNamespace(NOT_FOUND=-1, ID_ANY=-1, EVT_MENU='menu',
             Menu=lambda: self.menu, CallAfter=lambda fn,*args: self.callbacks.append((fn,args)))
        self.podcast = types.SimpleNamespace(episode_download_target=Mock(return_value=('C:/audio/episode.mp3','episode.mp3')),
                                            download_episode_file=Mock())
        def thread(**kwargs):
            self.jobs.append(kwargs['target'])
            return types.SimpleNamespace(start=lambda: None)
        namespace = {'wx':wx, '_':lambda s:s, 'podcast':self.podcast,
                     'ui':types.SimpleNamespace(message=self.messages.append),
                     'os':types.SimpleNamespace(path=types.SimpleNamespace(exists=lambda p:False)),
                     'threading':types.SimpleNamespace(Thread=thread)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])), '<dialog-handlers>', 'exec'),namespace)
        self.controller = c = namespace['Controller']()
        self.ep = types.SimpleNamespace(title='Selected episode',url='https://example.org/episode.mp3')
        c._plugin=None
        c._podcast_preview_episodes=[self.ep]
        c._podcast_preview_list=Mock()
        c._podcast_preview_list.GetSelection.return_value=0
        c._podcast_preview_list.GetScreenPosition.return_value=0
        c.GetScreenPosition=Mock(return_value=0)
        c._is_previewing=Mock(return_value=False)
        c._on_podcast_preview_toggle=Mock()
        c.Bind=Mock();c.PopupMenu=Mock()
        c._episode_download_btn=Mock()
        c._episode_list=Mock();c._episode_list.GetSelection.return_value=-1
        c._episode_filtered=[]

    def finish(self):
        self.jobs.pop(0)()
        fn,args=self.callbacks.pop(0);fn(*args)

    def test_preview_menu_includes_download_and_binds_correct_handler(self):
        self.controller._show_podcast_preview_context_menu()
        self.assertEqual([call.args[1] for call in self.menu.Append.call_args_list],['&Preview','&Download Episode'])
        self.assertEqual(self.controller.Bind.call_args_list[-1].args[1],self.controller._on_podcast_preview_download)
        self.menu.Destroy.assert_called_once()

    def test_preview_download_without_subscription_freezes_selection_and_reports_path(self):
        self.controller._on_podcast_preview_download(None)
        self.ep.url='https://example.org/changed.mp3'
        self.controller._podcast_preview_episodes=[]
        self.finish()
        self.podcast.download_episode_file.assert_called_once_with('https://example.org/episode.mp3','C:/audio/episode.mp3')
        self.assertEqual(self.messages[-1],'Download complete: C:/audio/episode.mp3')
        self.controller._episode_download_btn.Enable.assert_called_with(False)

    def test_duplicate_download_is_blocked_and_failure_can_be_retried(self):
        c=self.controller
        c._on_podcast_preview_download(None);c._on_podcast_preview_download(None)
        self.assertEqual(len(self.jobs),1)
        self.assertIn('Already downloading:',self.messages[-1])
        self.podcast.download_episode_file.side_effect=OSError('connection lost')
        self.finish()
        self.assertIn('Download failed:',self.messages[-1])
        c._on_podcast_preview_download(None)
        self.assertEqual(len(self.jobs),1)

    def test_destroyed_dialog_is_not_touched_by_completion(self):
        c=self.controller
        c._on_podcast_preview_download(None)
        type(c).__bool__=lambda self:False
        self.finish()
        c._episode_download_btn.Enable.assert_not_called()
        self.assertEqual(c._podcast_downloads,set())

    def test_subscribed_episode_uses_the_same_downloader(self):
        c=self.controller;c._episode_list.GetSelection.return_value=0;c._episode_filtered=[self.ep]
        c._on_episode_download(None);self.finish()
        self.podcast.download_episode_file.assert_called_once()
        c._episode_download_btn.Enable.assert_called_with(True)

    def test_no_selection_does_not_download(self):
        self.controller._podcast_preview_list.GetSelection.return_value=-1
        self.controller._on_podcast_preview_download(None)
        self.assertEqual(self.jobs,[])

if __name__=='__main__':
    unittest.main()
