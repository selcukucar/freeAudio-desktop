import importlib
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import wave
from email.message import Message

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop.storage import Settings, data_directory
from desktop.shortcuts import parse_hotkey, desktop_defaults, Shortcuts
from desktop.updates import check_release
from desktop.host import AccessibleCheckListBox, install, SettingsDialog
import wx


class StorageTests(unittest.TestCase):
    def test_atomic_unicode_round_trip_and_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(directory)
            settings.spec['freeAudio'] = {'volume': 'integer(default=100, min=0, max=100)'}
            self.assertEqual(settings['freeAudio']['volume'], 100)
            settings['desktop']['language'] = 'tr'
            settings['desktop']['label'] = 'Türkçe, şarkı'
            settings.save()
            restored = Settings(directory)
            self.assertEqual(restored['desktop']['label'], 'Türkçe, şarkı')
            self.assertFalse(Path(directory, 'settings.tmp').exists())

    def test_unknown_schema_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'settings.json')
            original = '{"schema_version": 2, "settings": {"important": "keep"}}'
            path.write_text(original, encoding='utf-8')
            with self.assertRaises(ValueError):
                Settings(directory)
            self.assertEqual(path.read_text(encoding='utf-8'), original)

    def test_invalid_json_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'settings.json')
            path.write_text('{unfinished', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError):
                Settings(directory)
            self.assertEqual(path.read_text(encoding='utf-8'), '{unfinished')

    def test_portable_and_installed_locations_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {'APPDATA': str(root / 'roaming')}):
                self.assertEqual(data_directory(root), root / 'roaming/freeAudioDesktop')
                (root / 'portable.flag').touch()
                self.assertEqual(data_directory(root), root / 'data')


class ShortcutTests(unittest.TestCase):
    def test_desktop_bindings_avoid_reserved_keys_and_preserve_explicit_overrides(self):
        from unittest.mock import Mock
        class Plugin:
            __gestures = {'kb:control+windows+rightArrow': 'nextStation',
                          'kb:control+windows+f12': 'addBookmark'}
            def script_nextStation(self, gesture):
                pass
            def script_addBookmark(self, gesture):
                pass
        frame = Mock()
        settings = {'desktop': {'shortcuts': {'nextStation': 'control+alt+n', 'addBookmark': ''}}}
        shortcuts = Shortcuts(frame, Plugin(), settings, Mock())
        self.assertEqual(shortcuts.effective['nextStation'], 'control+alt+n')
        self.assertEqual(shortcuts.effective['addBookmark'], '')
        self.assertEqual(len(shortcuts.registered), 1)
        self.assertEqual(shortcuts.defaults['addBookmark'], 'control+alt+shift+b')
        self.assertEqual(shortcuts.defaults['nextStation'], 'control+alt+shift+rightArrow')
        shortcuts.close()
        frame.UnregisterHotKey.assert_called_once()

    def test_all_upstream_defaults_have_distinct_desktop_bindings(self):
        import ast
        defaults = {}
        for file in (ROOT / 'vendor/freeAudio').glob('*.py'):
            for node in ast.walk(ast.parse(file.read_text(encoding='utf-8-sig'))):
                if isinstance(node, ast.keyword) and node.arg == 'gesture':
                    defaults[ast.literal_eval(node.value)] = ''
        # Use the actual canonical mapping, including non-decorated mixins.
        tree = ast.parse((ROOT / 'vendor/freeAudio/__init__.py').read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__gestures' for t in node.targets):
                defaults.update(ast.literal_eval(node.value))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('script_'):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        for keyword in decorator.keywords:
                            if keyword.arg == 'gesture':
                                defaults[ast.literal_eval(keyword.value)] = node.name[7:]
        bindings = desktop_defaults({name: gesture for gesture, name in defaults.items() if name})
        parsed = [parse_hotkey(value) for value in bindings.values()]
        self.assertEqual(len(parsed), len(set(parsed)))
        self.assertGreaterEqual(len(parsed), 30)
        self.assertTrue(all(not modifiers & wx.MOD_WIN for modifiers, key in parsed))

    def test_virtual_keys_for_arrows_and_function_keys(self):
        self.assertEqual(parse_hotkey('control+windows+leftArrow'), (10, 0x25))
        self.assertEqual(parse_hotkey('kb:control+windows+f11'), (10, 0x7A))
        self.assertEqual(parse_hotkey('ctrl+alt+r'), (3, ord('R')))

    def test_invalid_shortcuts_are_rejected(self):
        for value in ['r', 'invalid+r', 'ctrl+f25', 'ctrl+', 'ctrl+ş', 'ctrl+f12']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_hotkey(value)


class UpdateTests(unittest.TestCase):
    def test_invalid_repository_does_not_make_a_request(self):
        with patch('urllib.request.urlopen') as request:
            with self.assertRaises(ValueError):
                check_release('https://example.com/other', '0.1.0')
            request.assert_not_called()

    def test_release_url_is_rebuilt_from_trusted_repository(self):
        raw = {'tag_name': 'v0.2.0', 'html_url': 'https://evil.example/run.exe'}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(raw).encode())):
            self.assertEqual(check_release('owner/desktop', '0.1.0'),
                             ('0.2.0', 'https://github.com/owner/desktop/releases/tag/v0.2.0'))

    def test_older_and_prerelease_versions_are_ignored(self):
        for data in [{'tag_name': 'v0.0.9'}, {'tag_name': 'v0.2.0a1', 'prerelease': True}]:
            with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(data).encode())):
                self.assertIsNone(check_release('owner/desktop', '0.1.0'))


class AccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.App(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.Destroy()

    def test_checklist_names_roles_and_checked_states(self):
        frame = wx.Frame(None)
        try:
            control = AccessibleCheckListBox(frame, choices=['Radyo', 'Podcast'])
            accessible = control.GetAccessible()
            self.assertEqual(accessible.GetName(2), (wx.ACC_OK, 'Podcast'))
            self.assertEqual(accessible.GetRole(1), (wx.ACC_OK, wx.ROLE_SYSTEM_CHECKBUTTON))
            self.assertFalse(accessible.GetState(1)[1] & wx.ACC_STATE_SYSTEM_CHECKED)
            self.assertEqual(accessible.DoDefaultAction(1), wx.ACC_OK)
            self.assertTrue(accessible.GetState(1)[1] & wx.ACC_STATE_SYSTEM_CHECKED)
            control.Disable()
            self.assertTrue(accessible.GetState(1)[1] & wx.ACC_STATE_SYSTEM_UNAVAILABLE)
        finally:
            frame.Destroy()
            self.app.ProcessPendingEvents()

    def test_quick_settings_save_preserves_voice_and_device_while_loading(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules):
            settings = Settings(directory)
            settings['freeAudio'].update({'audio_device': 2, 'audio_device_name': 'Saved device',
                                          'sapi5_voice_name': 'Saved voice', 'legacy_migrated': True})
            frame = wx.Frame(None)
            dialog = None
            try:
                translate, notifications = install(ROOT, settings, frame, 'en')
                with patch.object(sys, 'path', [str(ROOT / 'vendor')] + sys.path):
                    package = importlib.import_module('freeAudio')
                    panel_module = importlib.import_module('freeAudio.settingsPanel')
                    with patch.object(panel_module, '_list_sapi5_voices', return_value=[]):
                        dialog = SettingsDialog(frame, panel_module.freeAudioSettingsPanel, settings, translate)
                        self.assertIn('application starts', dialog.panel._resume.GetLabel())
                        self.assertEqual(dialog.panel._track_change_voice.GetString(0), 'Screen reader')
                        self.assertFalse(dialog.panel._auto_check_updates.IsShown())
                        dialog.panel.onSave()
                        self.assertEqual(settings['freeAudio']['audio_device'], 2)
                        self.assertEqual(settings['freeAudio']['audio_device_name'], 'Saved device')
                        self.assertEqual(settings['freeAudio']['sapi5_voice_name'], 'Saved voice')
                        self.app.ProcessPendingEvents()
            finally:
                if dialog:
                    dialog.Destroy()
                frame.Destroy()
                self.app.ProcessPendingEvents()


class EngineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.module_patch = patch.dict(sys.modules)
        cls.module_patch.start()
        package = types.ModuleType('desktop_engine_test')
        package.__path__ = [str(ROOT / 'vendor/freeAudio')]
        sys.modules[package.__name__] = package
        def initTranslation():
            inspect.currentframe().f_back.f_globals['_'] = lambda message: message
        sys.modules['addonHandler'] = types.SimpleNamespace(initTranslation=initTranslation)
        sys.modules['globalVars'] = types.SimpleNamespace(appArgs=types.SimpleNamespace(configPath=cls.directory.name))
        cls.podcast = importlib.import_module(package.__name__ + '.podcast')
        cls.bookmarks = importlib.import_module(package.__name__ + '.bookmarks')
        cls.player = importlib.import_module(package.__name__ + '.radioPlayer')

    @classmethod
    def tearDownClass(cls):
        cls.module_patch.stop()
        cls.directory.cleanup()

    def test_podcast_subscription_is_parsed_and_persisted(self):
        rss = b'''<rss version="2.0"><channel><title>Test Podcast</title><item>
            <title>Episode One</title><guid>one</guid>
            <enclosure url="https://example.invalid/audio.mp3" type="audio/mpeg"/>
            </item></channel></rss>'''
        manager = self.podcast.PodcastManager()
        response = io.BytesIO(rss)
        response.status = 200
        response.headers = Message()
        with patch.object(self.podcast.urllib.request, 'urlopen', return_value=response):
            feed, error = manager.add_feed('https://example.invalid/feed.xml')
        self.assertIsNone(error)
        self.assertEqual(feed.episodes[0].title, 'Episode One')
        restored = self.podcast.PodcastManager()
        self.assertEqual(restored.get_feed_by_url(feed.url).title, 'Test Podcast')

    def test_bookmark_position_and_note_survive_restart(self):
        manager = self.bookmarks.BookmarkManager()
        bookmark = manager.add('episode-one', 42.5)
        bookmark.text = 'Önemli bölüm'
        manager._save()
        restored = self.bookmarks.BookmarkManager()
        self.assertEqual(restored.get('episode-one')[0].position, 42.5)
        self.assertEqual(restored.get('episode-one')[0].text, 'Önemli bölüm')

    @unittest.skipUnless(sys.platform == 'win32', 'BASS host requires Windows')
    @unittest.skipIf(os.environ.get('FREEAUDIO_SKIP_AUDIO_DEVICE_TEST') == '1', 'Requires a real audio output device')
    def test_bass_subprocess_plays_and_seeks_local_audio_at_zero_volume(self):
        path = Path(self.directory.name) / 'test.wav'
        with wave.open(str(path), 'wb') as file:
            file.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            file.writeframes(b'\0\0' * 16000 * 10)
        engine = self.player._BassEngine(str(ROOT / 'vendor/freeAudio'))
        try:
            self.assertTrue(engine.load(), engine.get_stderr_tail())
            self.assertTrue(engine.play(str(path), volume_0_1=0, seekable=True))
            time.sleep(.2)
            ok, position, length = engine.timeshift_seek(3)
            self.assertTrue(ok)
            self.assertGreaterEqual(position, 3)
            self.assertAlmostEqual(length, 10, delta=.1)
            rate_ok, rate, reason = engine.set_playback_rate(1.25)
            self.assertTrue(rate_ok, reason)
            self.assertAlmostEqual(rate, 1.25, delta=.01)
            pitch_ok, pitch, reason = engine.set_transpose(2)
            self.assertTrue(pitch_ok, reason)
            self.assertAlmostEqual(pitch, 2, delta=.01)
            engine.pause()
            engine.resume()
            engine.stop()
        finally:
            engine.unload()


if __name__ == '__main__':
    unittest.main()
