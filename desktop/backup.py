"""Portable profile snapshots; media files and account credentials stay untouched."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile
from .storage import validate_settings

MAX_BYTES = 128 * 1024 * 1024
MAX_FILES = 10000


def profile_file(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '\\' in name or ':' in name or '..' in path.parts:
        return False
    if len(path.parts) == 1:
        return name in {'settings.json', 'podcast_positions.json', 'jukebox_folder_positions.json'} or (
            name.startswith('freeAudio_') and name.endswith('.json'))
    return len(path.parts) == 2 and path.parts[0] == 'freeAudio_bookmark_audio' and path.suffix.lower() == '.wav'


def export_profile(directory, destination, version):
    directory, destination = Path(directory), Path(destination)
    if destination.suffix.lower() != '.zip':
        raise ValueError('A profile backup must use the .zip extension.')
    files = [file for file in directory.rglob('*') if file.is_file() and
             profile_file(file.relative_to(directory).as_posix()) and
             file.resolve().is_relative_to(directory.resolve())]
    if len(files) > MAX_FILES or sum(file.stat().st_size for file in files) > MAX_BYTES:
        raise ValueError('Profile backup exceeds the supported size.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + '.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            hashes = {}
            for file in files:
                name = file.relative_to(directory).as_posix()
                data = file.read_bytes()
                hashes[name] = hashlib.sha256(data).hexdigest()
                archive.writestr(name, data)
            archive.writestr('profile-manifest.json', json.dumps(
                {'format': 1, 'application': 'freeAudioDesktop', 'version': version, 'files': hashes}))
        read_profile(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return len(files)


def read_profile(source):
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES + 1 or sum(item.file_size for item in entries) > MAX_BYTES:
            raise ValueError('Profile backup exceeds the supported size.')
        names = [item.filename for item in entries]
        if len(set(names)) != len(names):
            raise ValueError('Duplicate entries in profile backup.')
        manifest = json.loads(archive.read('profile-manifest.json'))
        if not isinstance(manifest, dict) or manifest.get('format') != 1 or manifest.get('application') != 'freeAudioDesktop':
            raise ValueError('This is not a supported freeAudio Desktop backup.')
        hashes = manifest.get('files')
        if not isinstance(hashes, dict) or set(names) != set(hashes) | {'profile-manifest.json'}:
            raise ValueError('Invalid profile backup manifest.')
        result = {}
        for name, expected in hashes.items():
            if not profile_file(name):
                raise ValueError('Unsupported profile entry: ' + name)
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Profile checksum mismatch: ' + name)
            if name.endswith('.json'):
                parsed = json.loads(data)
                if name == 'freeAudio_favorites.json':
                    if not isinstance(parsed, list) or not all(isinstance(item, dict) for item in parsed):
                        raise ValueError('Invalid favourites in profile backup.')
                    for item in parsed:
                        if not all(isinstance(item.get(key, ''), str) for key in ('name', 'stationuuid')):
                            raise ValueError('Invalid favourite station identity in profile backup.')
                if name in ('podcast_positions.json', 'jukebox_folder_positions.json'):
                    if not isinstance(parsed, dict) or not all(isinstance(item, dict) for item in parsed.values()):
                        raise ValueError('Invalid playback positions in profile backup.')
                if name == 'settings.json':
                    if not isinstance(parsed, dict) or parsed.get('schema_version') != 1 or not isinstance(parsed.get('settings'), dict):
                        raise ValueError('Unsupported settings in profile backup.')
                    if not all(isinstance(value, dict) for value in parsed['settings'].values()):
                        raise ValueError('Invalid settings sections in profile backup.')
                    validate_settings(parsed)
            result[name] = data
        return result


def prepare_restore(directory, source):
    read_profile(source)
    directory = Path(directory)
    temporary = directory / 'restore-pending.tmp'
    try:
        shutil.copyfile(source, temporary)
        read_profile(temporary)
        os.replace(temporary, directory / 'restore-pending.zip')
    finally:
        temporary.unlink(missing_ok=True)


def apply_pending_restore(directory, version):
    directory = Path(directory)
    pending = directory / 'restore-pending.zip'
    if not pending.exists():
        return False
    data = read_profile(pending)
    for name in data:
        if not (directory / name).resolve().is_relative_to(directory.resolve()):
            raise ValueError('Profile destination is outside the data directory.')
    backup = directory / 'backups/profile-before-restore.zip'
    export_profile(directory, backup, version)
    previous = {}
    with tempfile.TemporaryDirectory(prefix='restore-', dir=directory) as staging:
        staging = Path(staging)
        for name, content in data.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        try:
            for name in data:
                destination = directory / name
                previous[name] = destination.read_bytes() if destination.exists() else None
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staging / name, destination)
        except Exception:
            for name, content in previous.items():
                destination = directory / name
                if content is None:
                    destination.unlink(missing_ok=True)
                else:
                    destination.write_bytes(content)
            raise
    pending.unlink()
    return True
