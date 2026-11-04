import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.backup import export_profile, prepare_restore, apply_pending_restore, read_profile
from desktop.storage import Settings
from desktop.updates import read_channel, valid_repository


class ProfileTests(unittest.TestCase):
    def test_backup_restore_preserves_previous_profile_and_ignores_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile'
            profile.mkdir()
            settings = Settings(profile)
            settings['desktop']['language'] = 'tr'
            settings['freeAudio']['resume_on_start'] = True
            settings.save()
            library = profile / 'freeAudio_favorites.json'
            library.write_text('[{"name":"Radyo"}]', encoding='utf-8')
            progress = profile / 'podcast_positions.json'
            progress.write_text('{"episode":{"position":42.5}}')
            folders = profile / 'jukebox_folder_positions.json'
            folders.write_text('{"folder":{"track_index":2}}')
            credentials = profile / 'freeAudio_getem_credentials.bin'
            credentials.write_bytes(b'private-account-data')
            backup = root / 'profile.zip'
            self.assertEqual(export_profile(profile, backup, '0.1.0'), 4)
            self.assertNotIn(credentials.name, read_profile(backup))
            settings['desktop']['language'] = 'en'
            settings.save()
            library.write_text('[]', encoding='utf-8')
            progress.write_text('{}')
            folders.write_text('{}')
            prepare_restore(profile, backup)
            self.assertEqual(Settings(profile)['desktop']['language'], 'en')
            self.assertTrue(apply_pending_restore(profile, '0.2.0'))
            self.assertEqual(Settings(profile)['desktop']['language'], 'tr')
            self.assertEqual(json.loads(library.read_text())[0]['name'], 'Radyo')
            self.assertEqual(json.loads(progress.read_text())['episode']['position'], 42.5)
            self.assertEqual(json.loads(folders.read_text())['folder']['track_index'], 2)
            previous = read_profile(profile / 'backups/profile-before-restore.zip')
            self.assertEqual(json.loads(previous['settings.json'])['settings']['desktop']['language'], 'en')
            self.assertEqual(credentials.read_bytes(), b'private-account-data')
            self.assertFalse(apply_pending_restore(profile, '0.2.0'))

    def test_rejects_path_traversal_and_unknown_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / 'bad.zip'
            for name in ['../settings.json', 'C:/settings.json', 'freeAudio_bad.exe']:
                with self.subTest(name=name):
                    content = b'{}'
                    with zipfile.ZipFile(archive_path, 'w') as archive:
                        archive.writestr(name, content)
                        archive.writestr('profile-manifest.json', json.dumps({
                            'format': 1, 'application': 'freeAudioDesktop',
                            'files': {name: hashlib.sha256(content).hexdigest()}}))
                    with self.assertRaises(ValueError):
                        read_profile(archive_path)

    def test_rejects_corrupt_checksum_before_changing_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / 'bad.zip'
            with zipfile.ZipFile(archive_path, 'w') as archive:
                archive.writestr('freeAudio_favorites.json', b'[]')
                archive.writestr('profile-manifest.json', json.dumps({
                    'format': 1, 'application': 'freeAudioDesktop',
                    'files': {'freeAudio_favorites.json': '0' * 64}}))
            with self.assertRaises(ValueError):
                prepare_restore(root, archive_path)
            self.assertFalse((root / 'restore-pending.zip').exists())

    def test_restore_rolls_back_if_file_replacement_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile'
            settings = Settings(profile)
            settings['desktop']['language'] = 'tr'
            settings.save()
            (profile / 'freeAudio_favorites.json').write_text('[{"name":"original"}]')
            export_profile(profile, root / 'backup.zip', '0.1.0')
            settings['desktop']['language'] = 'en'
            settings.save()
            (profile / 'freeAudio_favorites.json').write_text('[{"name":"current"}]')
            prepare_restore(profile, root / 'backup.zip')
            import os
            original_replace = os.replace
            counter = 0
            def failing_replace(source, destination):
                nonlocal counter
                # Only fail a staged profile-file replacement, not snapshot creation.
                if 'restore-' in str(source) and str(source).endswith('.json'):
                    counter += 1
                    if counter == 2:
                        raise OSError('simulated write failure')
                return original_replace(source, destination)
            with patch('desktop.backup.os.replace', side_effect=failing_replace):
                with self.assertRaises(OSError):
                    apply_pending_restore(profile, '0.2.0')
            self.assertEqual(Settings(profile)['desktop']['language'], 'en')
            self.assertEqual((profile / 'freeAudio_favorites.json').read_text(), '[{"name":"current"}]')

    def test_legacy_voice_setting_migrates_without_losing_preferences(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'settings.json'
            path.write_text(json.dumps({'schema_version': 1, 'settings': {'freeAudio': {
                'track_change_voice': 'nvda', 'resume_on_start': True, 'braille_messages': True}}}))
            settings = Settings(temporary)
            self.assertEqual(settings['freeAudio']['track_change_voice'], 'screen_reader')
            self.assertTrue(settings['freeAudio']['resume_on_start'])
            self.assertTrue(settings['freeAudio']['braille_messages'])

    def test_settings_reject_invalid_section_types(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'settings.json'
            path.write_text('{"schema_version":1,"settings":{"desktop":[]}}')
            with self.assertRaises(ValueError):
                Settings(temporary)

    def test_channel_placeholder_and_configured_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'channel.json'
            self.assertEqual(read_channel(path), '')
            path.write_text('{"schema":1,"repository":""}')
            self.assertEqual(read_channel(path), '')
            path.write_text('{"schema":1,"repository":"owner/desktop"}')
            self.assertEqual(read_channel(path), 'owner/desktop')
            for repository in ['owner/..', '../repo', 'https://github.com/owner/repo']:
                self.assertFalse(valid_repository(repository))
