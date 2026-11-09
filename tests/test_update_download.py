import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.updates import (UpdateAsset, DownloadCancelled, ReleaseRedirect,
                             find_asset, download_update, launch_installer, verify_download)


class Response(io.BytesIO):
    def geturl(self):
        return 'https://release-assets.githubusercontent.com/release/test'


class UpdateDownloadTests(unittest.TestCase):
    def asset(self, payload=b'installer bytes', portable=False):
        filename = 'freeAudio-Desktop-1.0.2-win64-' + ('portable.zip' if portable else 'setup.exe')
        return UpdateAsset('1.0.2', filename, 'https://github.com/owner/app/releases/download/v1.0.2/' + filename,
                           len(payload), hashlib.sha256(payload).hexdigest(), portable)

    def test_exact_release_metadata_selects_the_expected_asset_and_ignores_remote_url(self):
        asset = self.asset()
        raw = {'tag_name': 'v1.0.2', 'assets': [{'name': asset.filename, 'size': asset.size,
               'digest': 'sha256:' + asset.sha256, 'browser_download_url': 'https://evil.example/malware'}]}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(raw).encode())):
            found = find_asset('owner/app', '1.0.2')
        self.assertEqual(found.url, asset.url)

    def test_missing_hash_or_changed_release_is_rejected(self):
        for raw in [{'tag_name': 'v1.0.1'}, {'tag_name': 'v1.0.2', 'assets': [
                    {'name': self.asset().filename, 'size': 100}]}]:
            with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(raw).encode())):
                with self.assertRaises(ValueError):
                    find_asset('owner/app', '1.0.2')

    def test_verified_download_is_atomic_and_reuses_only_verified_cached_files(self):
        payload = b'installer bytes'
        asset = self.asset(payload)
        with tempfile.TemporaryDirectory() as directory:
            progress = []
            opener = Mock()
            opener.open.return_value = Response(payload)
            path = download_update(asset, directory, progress=lambda done, total: progress.append((done, total)), opener=opener)
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(progress[-1], (len(payload), len(payload)))
            self.assertEqual(list(Path(directory).glob('*.part')), [])
            download_update(asset, directory, opener=opener)
            self.assertEqual(opener.open.call_count, 1)

    def test_corrupt_and_truncated_files_never_replace_a_previously_downloaded_file(self):
        asset = self.asset()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / asset.filename
            target.write_bytes(b'previous download')
            for payload in (b'bad', b'x' * asset.size, b'x' * (asset.size + 1)):
                opener = Mock()
                opener.open.return_value = Response(payload)
                with self.assertRaises(ValueError):
                    download_update(asset, directory, opener=opener)
                self.assertEqual(target.read_bytes(), b'previous download')
                self.assertEqual(list(Path(directory).glob('*.part')), [])

    def test_cancellation_cleans_partial_download_and_does_not_execute_anything(self):
        payload = b'x' * 100000
        asset = self.asset(payload)
        cancel = threading.Event()
        opener = Mock()
        opener.open.return_value = Response(payload)
        with tempfile.TemporaryDirectory() as directory, patch('subprocess.Popen') as launch:
            with self.assertRaises(DownloadCancelled):
                download_update(asset, directory, cancel, lambda *args: cancel.set(), opener)
            self.assertEqual(list(Path(directory).iterdir()), [])
            launch.assert_not_called()

    def test_untrusted_redirect_is_rejected_before_following_it(self):
        for url in ('http://github.com/file', 'https://evil.example/file', 'https://github.com.evil.example/file'):
            with self.assertRaises(ValueError):
                ReleaseRedirect().redirect_request(None, None, 302, '', {}, url)

    def test_installer_is_reverified_before_execution_and_uses_no_shell(self):
        asset = self.asset()
        with tempfile.TemporaryDirectory() as directory, patch('subprocess.Popen') as launch:
            path = Path(directory) / asset.filename
            path.write_bytes(b'installer bytes')
            launch_installer(asset, path, directory, 'tr')
            args = launch.call_args
            self.assertFalse(args.kwargs['shell'])
            self.assertIn('/RESTARTAPP=1', args.args[0])
            self.assertIn('/VERYSILENT', args.args[0])
            launch.reset_mock()
            path.write_bytes(b'changed bytes')
            with self.assertRaises(ValueError):
                launch_installer(asset, path, directory)
            launch.assert_not_called()

    def test_portable_zip_cannot_be_launched_as_an_executable(self):
        with patch('subprocess.Popen') as launch, self.assertRaises(ValueError):
            launch_installer(self.asset(portable=True), 'anything', 'anywhere')
        launch.assert_not_called()
