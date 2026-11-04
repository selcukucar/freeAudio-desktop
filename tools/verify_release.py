"""Verify release checksums and ZIP integrity without executing a downloaded program."""
import argparse
import hashlib
from pathlib import Path
import zipfile


def verify(directory):
    directory = Path(directory)
    for line in (directory / 'SHA256SUMS.txt').read_text(encoding='ascii').splitlines():
        expected, filename = line.split('  ', 1)
        if Path(filename).name != filename:
            raise ValueError('Unexpected filename in release checksum list')
        file = directory / filename
        with file.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('Checksum mismatch: ' + filename)
        if file.suffix == '.zip':
            with zipfile.ZipFile(file) as archive:
                if archive.testzip() is not None:
                    raise ValueError('Corrupt archive: ' + filename)
        print(filename + ': OK')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    verify(parser.parse_args().directory)
