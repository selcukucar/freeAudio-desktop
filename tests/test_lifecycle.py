import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import DesktopFrame
from desktop.storage import Settings
from desktop.backup import export_profile, prepare_restore
import wx


class LifecycleTests(unittest.TestCase):
    def frame(self, recording=False):
        return types.SimpleNamespace(
            _closing=False, _save_error_reported=False, _autosave=Mock(),
            shortcuts=Mock(), settings=Mock(), notifications=Mock(),
            plugin=types.SimpleNamespace(_recorder=Mock(), terminate=Mock()),
            translate=lambda text: text, Destroy=Mock(), persist_settings=Mock(return_value=True))

    def test_recording_close_can_be_cancelled_without_stopping_anything(self):
        frame = self.frame()
        frame.plugin._recorder.is_recording.return_value = True
        event = Mock()
        event.CanVeto.return_value = True
        with patch('main.wx.MessageBox', return_value=wx.NO):
            DesktopFrame.exit(frame, event)
        event.Veto.assert_called_once()
        frame.plugin.terminate.assert_not_called()
        frame.Destroy.assert_not_called()

    def test_shutdown_closes_window_even_if_final_save_raises(self):
        frame = self.frame()
        frame.plugin._recorder.is_recording.return_value = False
        frame.plugin._recorder.get_active_scheduled.return_value = []
        frame.persist_settings.side_effect = OSError('write failed')
        event = Mock()
        event.CanVeto.return_value = True
        with self.assertRaises(OSError):
            DesktopFrame.exit(frame, event)
        frame.Destroy.assert_called_once()
        DesktopFrame.exit(frame, event)
        frame.plugin.terminate.assert_called_once()

    def test_save_failure_notifies_once_until_next_success(self):
        frame = self.frame()
        frame.settings.save.side_effect = [OSError('disk full'), OSError('disk full'), None, OSError('disk full')]
        self.assertFalse(DesktopFrame.persist_settings(frame))
        self.assertFalse(DesktopFrame.persist_settings(frame))
        self.assertEqual(frame.notifications.message.call_count, 1)
        self.assertTrue(DesktopFrame.persist_settings(frame))
        self.assertFalse(DesktopFrame.persist_settings(frame))
        self.assertEqual(frame.notifications.message.call_count, 2)

    def test_update_result_is_ignored_after_window_closes_and_checks_are_coalesced(self):
        frame = self.frame()
        frame._update_check_running = False
        frame.settings = {'desktop': {'update_repository': 'owner/desktop'}}
        started, release = threading.Event(), threading.Event()
        queued = []
        def fetch(*args):
            started.set()
            release.wait(timeout=3)
            return ('1.0.0', 'https://github.com/owner/desktop/releases/tag/v1.0.0')
        with patch('desktop.updates.check_release', side_effect=fetch) as check, patch(
                'main.wx.CallAfter', side_effect=lambda callback, *args: queued.append((callback, args))):
            DesktopFrame.check_updates(frame)
            self.assertTrue(started.wait(timeout=2))
            DesktopFrame.check_updates(frame)
            self.assertEqual(check.call_count, 1)
            frame._closing = True
            release.set()
            for _ in range(100):
                if queued:
                    break
                threading.Event().wait(.01)
        self.assertEqual(len(queued), 1)
        with patch('main.wx.MessageBox') as dialog:
            queued[0][0](*queued[0][1])
            dialog.assert_not_called()


class RestoreValidationTests(unittest.TestCase):
    def test_source_archive_excludes_its_own_outputs_and_local_profiles(self):
        from build import source_files
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'source'
            for name in ['main.py', 'desktop/example.py', '.venv/private.txt',
                         '.test-profile/settings.json', 'custom-build/app.exe',
                         'custom-output/source.zip', 'old-release.zip']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
            files = list(source_files(root, root / 'custom-build', root / 'custom-output'))
            self.assertEqual({file.relative_to(root).as_posix() for file in files},
                             {'main.py', 'desktop/example.py'})
            # The task's normal output directory is a parent of the source tree.
            files = list(source_files(root, root / 'custom-build', root.parent))
            self.assertIn(root / 'main.py', files)

    def test_malformed_favourite_list_does_not_replace_existing_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / 'profile'
            settings = Settings(profile)
            settings.save()
            archive = root / 'profile.zip'
            export_profile(profile, archive, '0.1.0')
            original = archive.read_bytes()
            (profile / 'freeAudio_favorites.json').write_text('["not-a-station"]')
            with self.assertRaises(ValueError):
                export_profile(profile, archive, '0.1.0')
            self.assertEqual(archive.read_bytes(), original)

    def test_semantically_invalid_settings_cannot_be_exported_over_previous_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / 'profile'
            settings = Settings(profile)
            settings['freeAudio']['volume'] = 30
            settings.save()
            archive = root / 'valid.zip'
            export_profile(profile, archive, '0.1.0')
            original = archive.read_bytes()
            payload = {'schema_version': 1, 'settings': {'freeAudio': {'volume': 'invalid'}}}
            settings.path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                export_profile(profile, archive, '0.1.0')
            self.assertEqual(archive.read_bytes(), original)
            self.assertFalse((root / 'valid.zip.tmp').exists())

    def test_invalid_hotkey_settings_are_rejected_without_overwriting_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            raw = '{"schema_version":1,"settings":{"desktop":{"shortcuts":[]}}}'
            path.write_text(raw)
            with self.assertRaises(ValueError):
                Settings(directory)
            self.assertEqual(path.read_text(), raw)
