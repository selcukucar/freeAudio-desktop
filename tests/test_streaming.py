"""End-to-end HTTP capture tests, independent of external radio services."""
import importlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]


def wait_for(predicate, seconds=4):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(.02)
    return False


class StreamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.module_patch = patch.dict(sys.modules)
        cls.module_patch.start()
        package = types.ModuleType('desktop_streaming_test')
        package.__path__ = [str(ROOT / 'vendor/freeAudio')]
        sys.modules[package.__name__] = package
        def initTranslation():
            inspect.currentframe().f_back.f_globals['_'] = lambda message: message
        sys.modules['addonHandler'] = types.SimpleNamespace(initTranslation=initTranslation)
        sys.modules['globalVars'] = types.SimpleNamespace(appArgs=types.SimpleNamespace(configPath=cls.directory.name))
        cls.recorder = importlib.import_module(package.__name__ + '.recorder')
        cls.timeshift = importlib.import_module(package.__name__ + '.timeshift')
        cls.podcast = importlib.import_module(package.__name__ + '.podcast')
        cls.payload = (ROOT / 'vendor/freeAudio/tuner.mp3').read_bytes() * 4
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                if self.path == '/feed.xml':
                    payload = ('<rss version="2.0"><channel><title>Local Podcast</title><item>'
                               '<title>Local Episode</title><guid>local-1</guid><enclosure '
                               'url="http://127.0.0.1:%s/radio.mp3" type="audio/mpeg"/>'
                               '</item></channel></rss>' % self.server.server_port).encode()
                    mime = 'application/rss+xml'
                else:
                    payload, mime = cls.payload, 'audio/mpeg'
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                try:
                    for offset in range(0, len(payload), 4096):
                        self.wfile.write(payload[offset:offset+4096])
                        self.wfile.flush()
                        time.sleep(.002)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.module_patch.stop()
        cls.directory.cleanup()

    def test_podcast_subscribes_to_real_http_feed_and_reloads(self):
        manager = self.podcast.PodcastManager()
        feed, error = manager.add_feed(self.base + '/feed.xml')
        self.assertIsNone(error)
        self.assertEqual(feed.episodes[0].title, 'Local Episode')
        self.assertEqual(self.podcast.PodcastManager().get_feed_by_url(feed.url).title, 'Local Podcast')

    def test_instant_recording_saves_audio_without_controlling_player(self):
        player = types.SimpleNamespace(_current_url=self.base + '/radio.mp3', _current_url_resolved=None)
        recorder = self.recorder.Recorder(dll_dir=str(ROOT / 'vendor/freeAudio'))
        destination = Path(self.directory.name) / 'recording.mp3'
        try:
            with patch.object(self.recorder, '_make_output_path', return_value=str(destination)):
                recorder.start(player, 'Local test radio')
            self.assertTrue(wait_for(lambda: recorder._writer.is_connected()))
            self.assertTrue(wait_for(lambda: destination.exists() and destination.stat().st_size >= 8192))
            saved = Path(recorder.stop())
            self.assertTrue(saved.read_bytes().startswith(self.payload[:8192]))
            self.assertFalse(recorder.is_recording())
            self.assertEqual(player._current_url, self.base + '/radio.mp3')
        finally:
            recorder.terminate()

    def test_time_shift_captures_audio_and_cleans_up_its_buffer(self):
        buffer = self.timeshift.TimeShiftBuffer(tmp_dir=self.directory.name)
        try:
            buffer.start(self.base + '/radio.mp3')
            path = Path(buffer.get_file_path())
            self.assertTrue(wait_for(lambda: buffer._bytes_written >= 8192))
            self.assertTrue(buffer.is_active())
            self.assertTrue(path.read_bytes().startswith(self.payload[:8192]))
            buffer.stop()
            self.assertFalse(path.exists())
            self.assertFalse(buffer.is_active())
        finally:
            buffer.stop()


if __name__ == '__main__':
    unittest.main()
