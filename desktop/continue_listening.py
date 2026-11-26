"""Build a recent, unfinished media list using the existing position store."""
from pathlib import Path
import math


def time_label(seconds):
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes}:{seconds:02}'


def continuation_items(history, player, downloads, libraries=None):
    if libraries is None:
        from freeAudio import getem, librivox, gutenberg_audiobooks
        libraries = []
        for kind in (getem.GetemLibrary, librivox.LibrivoxLibrary, gutenberg_audiobooks.GutenbergLibrary):
            try:
                libraries.append(kind())
            except Exception:
                pass
    downloaded = {item['url']: item for item in downloads.snapshot() if item['state'] == 'completed'}
    result, seen = [], set()
    for item in history.snapshot():
        station = dict(item['station'])
        kind = station.get('media_kind')
        if kind not in ('podcast', 'audiobook'):
            continue
        key = station.get('podcast_resume_key') or station.get('url')
        available = True
        identity = station.get('getem_detail_url') or key
        if not identity or identity in seen:
            continue
        seen.add(identity)
        if kind == 'audiobook':
            book = None
            for library in libraries:
                try:
                    book = library.get_book_by_key(identity)
                except Exception:
                    continue
                if book:
                    break
            if book and book.chapters:
                try: index = min(max(0, int(book.last_chapter_index)), len(book.chapters)-1)
                except (ValueError, TypeError): index = 0
                chapter = book.chapters[index]
                key = chapter.get('url', '')
                station['getem_chapter_index'] = index
                station['name'] = book.title + ' — ' + (chapter.get('title') or str(index+1))
            else:
                available = False
        entry = downloaded.get(key)
        if entry and entry.get('listened'):
            continue
        position = player.get_podcast_position(key) if key else 0
        if not isinstance(position, (int, float)) or not math.isfinite(position):
            position = 0
        if position < 0:
            if entry and entry.get('listened_override') is False:
                position = 0
            else:
                continue
        if entry and downloads.resolve_path(entry).is_file():
            from .media_dialogs import playback_station
            station = playback_station(entry, downloads)
        elif station.get('url') and not station['url'].lower().startswith(('http://','https://')):
            available = Path(station['url']).is_file()
        result.append({'station':station, 'position':position, 'available':available})
    return result
