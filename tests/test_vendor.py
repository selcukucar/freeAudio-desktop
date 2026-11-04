import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fetch_vendor', ROOT / 'tools/fetch_vendor.py')
vendor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vendor)


class VendorRestoreTests(unittest.TestCase):
    def archive(self, data):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('freeAudio-' + vendor.COMMIT + '/addon/globalPlugins/freeAudio/bass/bass.dll', data)
        stream.seek(0)
        return zipfile.ZipFile(stream)

    def test_verified_pinned_dependency_is_restored(self):
        data = b'known upstream bytes'
        relative = 'vendor/freeAudio/bass/bass.dll'
        with tempfile.TemporaryDirectory() as directory, self.archive(data) as archive:
            vendor.restore(archive, {relative: hashlib.sha256(data).hexdigest()}, directory)
            self.assertEqual((Path(directory) / relative).read_bytes(), data)

    def test_corrupt_download_cannot_replace_existing_dependency(self):
        relative = 'vendor/freeAudio/bass/bass.dll'
        with tempfile.TemporaryDirectory() as directory, self.archive(b'corrupt') as archive:
            target = Path(directory) / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(b'existing')
            with self.assertRaises(ValueError):
                vendor.restore(archive, {relative: hashlib.sha256(b'expected').hexdigest()}, directory)
            self.assertEqual(target.read_bytes(), b'existing')

    def test_dependency_manifest_cannot_escape_vendor_directory(self):
        with tempfile.TemporaryDirectory() as directory, self.archive(b'data') as archive:
            with self.assertRaises(ValueError):
                vendor.restore(archive, {'../outside.dll': '0' * 64}, directory)
