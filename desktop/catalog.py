"""Atomic, bounded metadata stores for downloads and listening history."""
import json
import os
from pathlib import Path
import tempfile
import threading
import time


def read_items(path):
    path = Path(path).resolve()
    if not path.exists():
        return []
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Library metadata is too large')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema') != 1 or not isinstance(data.get('items'), list):
        raise ValueError('Invalid library metadata')
    return data['items']


def write_items(path, items):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            name = stream.name
            json.dump({'schema': 1, 'items': items}, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        name = None
    finally:
        if name:
            Path(name).unlink(missing_ok=True)


class ListeningHistory:
    """Keep replay metadata, never temporary GETEM proxy URLs or account data."""
    FIELDS = ('name', 'url', 'stationuuid', 'tags', 'media_kind', 'podcast_feed_url',
              'podcast_resume_key', 'getem_detail_url', 'getem_chapter_index',
              'jukebox_folder_path', 'jukebox_track_index')

    def __init__(self, directory):
        self.path = Path(directory).resolve() / 'freeAudio_listening_history.json'
        self.lock = threading.RLock()
        self.items = read_items(self.path)
        if not all(isinstance(x, dict) and isinstance(x.get('station'), dict) for x in self.items):
            raise ValueError('Invalid listening history')
        self.last_key = None

    def observe(self, station):
        if not station or not station.get('url'):
            return
        saved = {key: station[key] for key in self.FIELDS if key in station
                 and isinstance(station[key], (str, int, float))}
        if saved.get('getem_detail_url'):
            saved['url'] = ''  # A fresh authenticated proxy must be rebuilt.
            saved.pop('podcast_resume_key', None)
        key = (saved.get('getem_detail_url') or saved.get('url'), saved.get('getem_chapter_index', 0))
        with self.lock:
            if key == self.last_key:
                return
            entry = {'station': saved, 'played': time.time()}
            items = [entry] + [item for item in self.items if (
                item['station'].get('getem_detail_url') or item['station'].get('url'),
                item['station'].get('getem_chapter_index', 0)) != key]
            write_items(self.path, items[:200])
            self.items = items[:200]
            self.last_key = key

    def clear(self):
        with self.lock:
            write_items(self.path, [])
            self.items = []

    def snapshot(self):
        with self.lock:
            return [{'station': dict(x['station']), 'played': x['played']} for x in self.items]
