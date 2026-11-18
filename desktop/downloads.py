"""Persistent podcast queue. Two workers; UI callbacks never run under its lock."""
import hashlib
import logging
from pathlib import Path
import threading
import time
from .catalog import read_items, write_items


class DownloadManager:
    ACTIVE = ('queued', 'downloading')

    def __init__(self, directory, downloader, notify=lambda item: None, destination=None):
        self.path = Path(directory).resolve() / 'freeAudio_downloads.json'
        self.directory = Path(directory).resolve()
        self.downloader, self.notify = downloader, notify
        self.destination = destination
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.closed = False
        self.events = {}
        self.items = read_items(self.path)
        for item in self.items:
            if (not isinstance(item, dict) or not all(isinstance(item.get(k), str)
                    for k in ('id', 'url', 'title', 'path', 'state'))):
                raise ValueError('Invalid download metadata')
            if item['state'] in self.ACTIVE:
                item['state'] = 'cancelled'  # Explicit retry after a restart.
        self.workers = [threading.Thread(target=self._work, daemon=True, name='podcast-download') for _ in range(2)]
        for worker in self.workers:
            worker.start()

    def _save(self):
        write_items(self.path, self.items)

    def resolve_path(self, item):
        path = Path(item['path'])
        return self.directory / path if not path.is_absolute() else path

    def enqueue(self, title, url, destination):
        destination = Path(destination).resolve()
        key = hashlib.sha256(url.encode('utf-8')).hexdigest()
        with self.condition:
            if self.closed:
                raise RuntimeError('Download manager is closed')
            previous = next((x for x in self.items if x['id'] == key), None)
            if previous and previous['state'] in self.ACTIVE:
                return dict(previous)
            if previous and previous['state'] == 'completed' and self.resolve_path(previous).is_file():
                return dict(previous)
            if len(self.items) >= 1000 and previous is None:
                raise ValueError('The download list is full. Remove old entries first.')
            # Store paths relative to a portable profile whenever possible.
            stored_path = str(destination.relative_to(self.directory)) if destination.is_relative_to(self.directory) else str(destination)
            item = dict(id=key, title=title, url=url, path=stored_path,
                        state='queued', received=0, total=None, error='', added=time.time())
            if previous:
                self.items.remove(previous)
            if destination.is_file() and destination.stat().st_size > 0:
                item.update(state='completed', received=destination.stat().st_size, modified=destination.stat().st_mtime_ns)
            self.items.insert(0, item)
            self.events[key] = threading.Event()
            try:
                self._save()
            except Exception:
                self.items.remove(item)
                self.events.pop(key, None)
                if previous:
                    self.items.append(previous)
                raise
            self.condition.notify_all()
            return dict(item)

    def retry(self, key):
        with self.lock:
            item = next(x for x in self.items if x['id'] == key)
            target = self.destination(item['title'], item['url']) if self.destination else self.resolve_path(item)
            return self.enqueue(item['title'], item['url'], target)

    def snapshot(self):
        with self.lock:
            return [dict(x) for x in self.items]

    def cancel(self, key):
        with self.condition:
            item = next(x for x in self.items if x['id'] == key)
            if item['state'] not in self.ACTIVE:
                return
            self.events[key].set()
            if item['state'] == 'queued':
                item['state'] = 'cancelled'
                self._save()
            self.condition.notify_all()

    def remove(self, key, delete_file=False):
        with self.lock:
            item = next(x for x in self.items if x['id'] == key)
            if item['state'] in self.ACTIVE:
                raise ValueError('Cancel the download before removing it')
            if delete_file:
                target = self.resolve_path(item)
                if item['state'] != 'completed' or not target.is_file():
                    raise ValueError('The downloaded file is not available')
                # Never delete a file which has been replaced since this download.
                if (target.stat().st_size != item.get('received') or target.stat().st_mtime_ns != item.get('modified')):
                    raise ValueError('The file has changed; remove it manually')
                target.unlink()
            self.items.remove(item)
            self.events.pop(key, None)
            self._save()

    def _work(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or any(x['state'] == 'queued' for x in self.items))
                if self.closed:
                    return
                item = next(x for x in reversed(self.items) if x['state'] == 'queued')
                item['state'] = 'downloading'
                event = self.events[item['id']]
                target = self.resolve_path(item)
            try:
                def progress(received, total):
                    with self.lock:
                        item['received'], item['total'] = received, total
                self.downloader(item['url'], str(target), progress=progress, cancel=event)
                state, error = 'completed', ''
                stat = target.stat()
                size, modified = stat.st_size, stat.st_mtime_ns
            except Exception as exc:
                state, error = ('cancelled', '') if event.is_set() else ('failed', str(exc))
                size = None
            with self.lock:
                item['state'], item['error'] = state, error
                if size is not None:
                    item['received'] = size
                    item['modified'] = modified
                try:
                    self._save()
                except Exception:
                    logging.exception('Could not save the podcast download list')
                result = dict(item)
            try:
                self.notify(result)
            except Exception:
                logging.exception('Could not announce podcast download result')

    def close(self):
        with self.condition:
            self.closed = True
            for event in self.events.values():
                event.set()
            for item in self.items:
                if item['state'] == 'queued':
                    item['state'] = 'cancelled'
            self.condition.notify_all()
            try:
                self._save()
            except Exception:
                logging.exception('Could not save download state during shutdown')
