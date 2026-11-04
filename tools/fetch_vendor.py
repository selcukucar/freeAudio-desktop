"""Restore pinned upstream binary dependencies for a Git checkout.

Release source ZIPs already contain these files. No executable is downloaded
from an unpinned release, and every restored file is verified before replacement.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'f1ade61be7e5badd43dd9b58cba80ae26959148b'
URL = 'https://codeload.github.com/Surveyor123/freeAudio/zip/' + COMMIT


def restore(archive, manifest, root=ROOT):
    root = Path(root).resolve()
    for relative, expected in manifest.items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root / 'vendor/freeAudio'):
            raise ValueError('Invalid vendor dependency path')
        member = 'freeAudio-' + COMMIT + '/addon/globalPlugins/freeAudio/' + relative.removeprefix('vendor/freeAudio/')
        data = archive.read(member)
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Vendor checksum mismatch: ' + relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + '.download')
        try:
            temporary.write_bytes(data)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    manifest = json.loads((ROOT / 'vendor-files.json').read_text(encoding='utf-8'))
    missing = {path: digest for path, digest in manifest.items()
               if not (ROOT / path).is_file() or hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest}
    if not missing:
        print('Pinned vendor dependencies: OK')
        return
    with tempfile.TemporaryFile() as temporary:
        with urllib.request.urlopen(URL, timeout=60) as response:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 160 * 1024 * 1024:
                    raise ValueError('Unexpectedly large upstream source archive')
                temporary.write(chunk)
        temporary.seek(0)
        with zipfile.ZipFile(temporary) as archive:
            restore(archive, missing)
    print('Verified and restored', len(missing), 'pinned vendor files')


if __name__ == '__main__':
    main()
