"""Optional public-service checks. No GETEM account or user data is used."""
import concurrent.futures
import importlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def run_checks():
    def initTranslation():
        caller = inspect.currentframe().f_back.f_globals
        caller['_'] = lambda message: message
        caller['ngettext'] = lambda singular, plural, number: singular if number == 1 else plural
    package = types.ModuleType('desktop_live_checks')
    package.__path__ = [str(ROOT / 'vendor/freeAudio')]
    sys.modules[package.__name__] = package
    sys.modules['addonHandler'] = types.SimpleNamespace(initTranslation=initTranslation)
    with tempfile.TemporaryDirectory() as directory:
        sys.modules['globalVars'] = types.SimpleNamespace(appArgs=types.SimpleNamespace(configPath=directory))
        modules = {name: importlib.import_module(package.__name__ + '.' + name)
                   for name in ('librivox', 'gutenberg_audiobooks')}
        def check(name):
            started = time.monotonic()
            module = modules[name]
            module.SEARCH_TIMEOUT = 8
            module.REQUEST_TIMEOUT = 8
            search = module.search_librivox if name == 'librivox' else module.search_gutenberg_audiobooks
            try:
                books, error = search('Pride and Prejudice', limit=2)
                if error:
                    return {'source': name, 'status': 'unavailable', 'detail': error}
                if not books:
                    return {'source': name, 'status': 'no_results'}
                book, error = module.resolve_media(books[0])
                probe_bytes = 0
                if not error and book.chapters:
                    url = book.chapters[0]['url']
                    request = urllib.request.Request(url, headers={
                        'User-Agent': 'freeAudio-Desktop-Check', 'Range': 'bytes=0-4095'})
                    with urllib.request.urlopen(request, timeout=8) as response:
                        probe_bytes = len(response.read(4096))
                return {'source': name, 'status': 'ok' if not error and book.chapters else 'resolution_failed',
                        'search_results': len(books), 'chapters': len(book.chapters),
                        'audio_probe_bytes': probe_bytes,
                        'detail': error, 'seconds': round(time.monotonic() - started, 2)}
            except Exception as error:
                return {'source': name, 'status': 'unavailable', 'detail': str(error)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(check, modules))


if __name__ == '__main__':
    print(json.dumps(run_checks(), ensure_ascii=False, indent=2))
