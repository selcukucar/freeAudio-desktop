"""Release discovery for a separately owned desktop repository."""
import json
import re
import urllib.request
import urllib.error
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
