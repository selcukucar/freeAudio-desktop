"""Release discovery for a separately owned desktop repository."""
import json
import re
import urllib.request
import urllib.error
import hashlib
import os
import tempfile
import threading
import subprocess
from dataclasses import dataclass
from urllib.parse import quote, urlsplit
from pathlib import Path
from packaging.version import Version


def read_channel(path):
    path = Path(path)
    if not path.exists():
        return ''
    channel = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(channel, dict):
        raise ValueError('Invalid desktop release channel')
    repository = channel.get('repository', '')
    if channel.get('schema') != 1 or not isinstance(repository, str) or (repository and not valid_repository(repository)):
        raise ValueError('Invalid desktop release channel')
    return repository


def valid_repository(repository):
    return isinstance(repository, str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', repository))


def check_release(repository, current):
    if not valid_repository(repository):
        raise ValueError('Invalid GitHub update repository')
    request = urllib.request.Request('https://api.github.com/repos/' + repository + '/releases/latest',
                                     headers={'User-Agent': 'freeAudio-Desktop/' + current})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read(1024 * 1024))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    tag = data['tag_name'].removeprefix('v')
    if data.get('draft') or data.get('prerelease') or Version(tag).is_prerelease or Version(tag) <= Version(current):
        return None
    # Build the trusted URL ourselves rather than opening response-supplied URLs.
    from urllib.parse import quote
    return tag, 'https://github.com/' + repository + '/releases/tag/' + quote(data['tag_name'], safe='')


class DownloadCancelled(Exception):
    pass


@dataclass(frozen=True)
class UpdateAsset:
    version: str
    filename: str
    url: str
    size: int
    sha256: str
    portable: bool


def trusted_download_url(url):
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.hostname in (
        'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com')
        and parsed.port in (None, 443) and not parsed.username and not parsed.password)


class ReleaseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        if not trusted_download_url(newurl):
            raise ValueError('Untrusted update redirect')
        return super().redirect_request(request, fp, code, message, headers, newurl)


def find_asset(repository, version, portable=False):
    """Resolve the exact requested release, never an arbitrary response URL."""
    if not valid_repository(repository) or Version(version).is_prerelease:
        raise ValueError('Invalid release')
    request = urllib.request.Request(
        'https://api.github.com/repos/' + repository + '/releases/tags/v' + quote(version, safe=''),
        headers={'User-Agent': 'freeAudio-Desktop-updater'})
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('Oversized release metadata')
    data = json.loads(raw)
    if data.get('draft') or data.get('prerelease') or data.get('tag_name') != 'v' + version:
        raise ValueError('Release changed or is not stable')
    suffix = '-win64-portable.zip' if portable else '-win64-setup.exe'
    filename = 'freeAudio-Desktop-' + version + suffix
    candidates = [asset for asset in data.get('assets', []) if asset.get('name') == filename]
    if len(candidates) != 1:
        raise ValueError('Expected Windows package is unavailable')
    asset = candidates[0]
    digest, size = asset.get('digest', ''), asset.get('size')
    if (not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest)
            or type(size) is not int or not 0 < size <= 512 * 1024 * 1024):
        raise ValueError('Release package lacks a valid SHA-256 digest or size')
    return UpdateAsset(version, filename,
                       'https://github.com/' + repository + '/releases/download/v' +
                       quote(version, safe='') + '/' + quote(filename, safe=''),
                       size, digest[7:].lower(), portable)


def verify_download(asset, path):
    path = Path(path)
    if path.name != asset.filename or path.stat().st_size != asset.size:
        raise ValueError('Update file size or name does not match')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != asset.sha256:
        raise ValueError('Update SHA-256 verification failed')
    return path


def download_update(asset, directory, cancel=None, progress=None, opener=None):
    cancel = cancel or threading.Event()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / asset.filename
    if destination.exists():
        try:
            if cancel.is_set():
                raise DownloadCancelled()
            return verify_download(asset, destination)
        except (ValueError, OSError):
            pass
    if not trusted_download_url(asset.url):
        raise ValueError('Untrusted update URL')
    opener = opener or urllib.request.build_opener(ReleaseRedirect())
    temporary = None
    try:
        if cancel.is_set():
            raise DownloadCancelled()
        request = urllib.request.Request(asset.url, headers={'User-Agent': 'freeAudio-Desktop-updater'})
        with opener.open(request, timeout=10) as response:
            if not trusted_download_url(response.geturl()):
                raise ValueError('Untrusted update response')
            with tempfile.NamedTemporaryFile(dir=directory, suffix='.part', delete=False) as stream:
                temporary = Path(stream.name)
                received = 0
                digest = hashlib.sha256()
                while True:
                    if cancel.is_set():
                        raise DownloadCancelled()
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > asset.size:
                        raise ValueError('Update exceeds published size')
                    stream.write(chunk)
                    digest.update(chunk)
                    if progress:
                        progress(received, asset.size)
                stream.flush()
                os.fsync(stream.fileno())
        if cancel.is_set():
            raise DownloadCancelled()
        if received != asset.size or digest.hexdigest() != asset.sha256:
            raise ValueError('Update download failed SHA-256 or size verification')
        os.replace(temporary, destination)
        temporary = None
        return verify_download(asset, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def launch_installer(asset, path, app_directory, language='tr'):
    if asset.portable:
        raise ValueError('A portable ZIP cannot be executed as an installer')
    path = verify_download(asset, path)
    args = [str(path), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
            '/CLOSEAPPLICATIONS', '/RESTARTAPP=1', '/DIR=' + str(Path(app_directory).resolve()),
            '/LANG=' + ('turkish' if language == 'tr' else 'english'),
            '/LOG=' + str(path.parent / ('install-' + asset.version + '.log'))]
    return subprocess.Popen(args, shell=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
