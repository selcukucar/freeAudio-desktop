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
        cls.release_stall = threading.Event()
        cls.messages = []
        package._notify = cls.messages.append
        sys.modules['ui'] = types.SimpleNamespace(message=cls.messages.append)
        sys.modules['config'] = types.SimpleNamespace(conf={'freeAudio': {}})
        sys.modules['scriptHandler'] = types.SimpleNamespace(
            script=lambda **kwargs: lambda fn: fn, getLastScriptRepeatCount=lambda: 0)
        cls.recording_mixin = importlib.import_module(package.__name__ + '.recordingMixin')
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                if self.path in ('/empty', '/truncated', '/html'):
                    body = b'<html>Not audio</html>' if self.path == '/html' else b'abc' if self.path == '/truncated' else b''
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html' if self.path == '/html' else 'audio/mpeg')
                    self.send_header('Content-Length', '100' if self.path == '/truncated' else str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if self.path == '/denied':
                    self.send_error(403)
                    return
                if self.path == '/stall':
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.send_header('Content-Length', str(len(cls.payload) * 100))
                    self.end_headers()
                    try:
                        self.wfile.write(cls.payload[:8192])
                        self.wfile.flush()
                        cls.release_stall.wait(8)
                    except OSError:
                        pass
                    return
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
        cls.release_stall.set()
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

    def test_podcast_download_matches_http_audio_and_leaves_no_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'episode.mp3')
            self.podcast.download_episode_file(self.base + '/radio.mp3', str(target))
            self.assertEqual(target.read_bytes(), self.payload)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_podcast_failed_downloads_leave_no_completed_or_partial_file(self):
        for route in ('/denied', '/empty', '/truncated', '/html'):
            with self.subTest(route=route), tempfile.TemporaryDirectory() as directory:
                target = Path(directory, 'episode.mp3')
                with self.assertRaises(Exception):
                    self.podcast.download_episode_file(self.base + route, str(target))
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_selected_recording_folder_is_used_for_real_capture_and_podcast_without_fallback(self):
        work = ROOT.parents[1] / 'work'
        with tempfile.TemporaryDirectory(dir=work if work.is_dir() else None) as directory:
            selected = Path(directory, 'Seçilen kayıt klasörü').resolve()
            config = sys.modules['config'].conf['freeAudio']
            with patch.dict(config, recordings_dir='"' + str(selected) + '"'), patch.object(self.recorder, '_default_recordings_dir', side_effect=AssertionError('Unwanted default destination')):
                self.assertEqual(Path(self.recorder._recordings_dir()), selected)
                target, name = self.podcast.episode_download_target('Bölüm', self.base + '/radio.mp3')
                self.podcast.download_episode_file(self.base + '/radio.mp3', target)
                self.assertEqual(Path(target).parent, selected)
                self.assertEqual(Path(target).read_bytes(), self.payload)
                recording = self.recorder.Recorder(dll_dir=str(ROOT / 'vendor/freeAudio'))
                try:
                    recording.start(types.SimpleNamespace(_current_url=self.base + '/radio.mp3', _current_url_resolved=None), 'Radio')
                    self.assertTrue(wait_for(lambda: recording._writer.is_connected()))
                    self.assertTrue(wait_for(lambda: list(selected.glob('Radio*.mp3'))))
                    saved = Path(recording.stop())
                    self.assertEqual(saved.parent, selected)
                    self.assertGreater(saved.stat().st_size, 0)
                    folder, reason = self.recorder._resolve_output_folder(None)
                    self.assertEqual(Path(folder), selected)
                    self.assertIsNone(reason)
                finally:
                    recording.terminate()

    def test_invalid_or_unavailable_recording_folder_never_uses_the_default(self):
        config = sys.modules['config'].conf['freeAudio']
        with patch.object(self.recorder, '_default_recordings_dir', side_effect=AssertionError('Unwanted fallback')):
            with patch.dict(config, recordings_dir='relative-folder'):
                with self.assertRaises(ValueError):
                    self.recorder._recordings_dir()
            with tempfile.TemporaryDirectory() as directory:
                unavailable = Path(directory, 'existing-file');unavailable.write_bytes(b'keep')
                with patch.dict(config, recordings_dir=str(unavailable)):
                    with self.assertRaises(OSError):
                        self.recorder._recordings_dir()
                with self.assertRaises(OSError):
                    self.recorder._resolve_output_folder(str(unavailable))
                self.assertEqual(unavailable.read_bytes(), b'keep')

    def test_scheduled_unavailable_destination_reports_error_without_fallback(self):
        import datetime
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'not-a-folder');target.write_bytes(b'keep')
            recorder=self.recorder.Recorder()
            messages=[]
            recorder._notify_folder_error=messages.append
            rec=self.recorder.ScheduledRecording({'name':'Radio','url':self.base+'/radio.mp3'},datetime.datetime.now(),1,output_folder=str(target))
            try:
                with patch.object(self.recorder,'_default_recordings_dir',side_effect=AssertionError('Unwanted fallback')),patch.object(self.recorder,'_StreamWriter') as writer:
                    recorder._run_scheduled(rec)
                writer.assert_not_called()
                self.assertTrue(messages)
                self.assertIsNone(rec.output_path)
                self.assertEqual(rec.occurrences_done,1)
                self.assertEqual(target.read_bytes(),b'keep')
            finally:
                recorder.terminate()

    def test_podcast_progress_and_cancellation_clean_the_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'episode.mp3')
            cancel = threading.Event()
            updates = []
            def progress(received, total):
                updates.append((received, total))
                cancel.set()
            with self.assertRaises(self.podcast.DownloadCancelled):
                self.podcast.download_episode_file(self.base + '/radio.mp3', str(target), progress=progress, cancel=cancel)
            self.assertTrue(updates)
            self.assertEqual(updates[0][1], len(self.payload))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_podcast_manager_completes_real_http_audio_and_persists_it(self):
        from desktop.downloads import DownloadManager
        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadManager(directory, self.podcast.download_episode_file)
            try:
                target = Path(directory, 'episode.mp3')
                manager.enqueue('Episode', self.base + '/radio.mp3', target)
                self.assertTrue(wait_for(lambda: manager.snapshot()[0]['state'] == 'completed'))
                self.assertEqual(target.read_bytes(), self.payload)
                self.assertEqual(manager.snapshot()[0]['received'], len(self.payload))
            finally:
                manager.close()
                for worker in manager.workers:
                    worker.join(2)

    def test_podcast_existing_download_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'episode.mp3')
            target.write_bytes(b'previous download')
            with self.assertRaises(FileExistsError):
                self.podcast.download_episode_file(self.base + '/radio.mp3', str(target))
            self.assertEqual(target.read_bytes(), b'previous download')

    def test_podcast_target_disambiguates_titles_and_limits_extension(self):
        with patch.object(self.recorder, '_recordings_dir', return_value=self.directory.name):
            first = self.podcast.episode_download_target('Same title', self.base + '/one.mp3')[0]
            second = self.podcast.episode_download_target('Same title', self.base + '/two.mp3')[0]
            self.assertNotEqual(first, second)
            self.assertEqual(first, self.podcast.episode_download_target('Same title', self.base + '/one.mp3')[0])
            self.assertTrue(self.podcast.episode_download_target('...', self.base + '/file.exe')[1].startswith('episode-'))
            self.assertTrue(self.podcast.episode_download_target('...', self.base + '/file.exe')[1].endswith('.mp3'))

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

    def test_stalled_stream_stop_closes_writer_before_finalization(self):
        player = types.SimpleNamespace(_current_url=self.base + '/stall')
        recorder = self.recorder.Recorder()
        with tempfile.TemporaryDirectory() as directory:
            try:
                with patch.object(self.recorder, '_recordings_dir', return_value=directory):
                    recorder.start(player, 'Stalled radio')
                self.assertTrue(recorder.wait_started(2))
                writer = recorder._writer
                started = time.monotonic()
                saved = recorder.stop()
                self.assertLess(time.monotonic() - started, 4)
                self.assertFalse(writer._thread.is_alive())
                self.assertEqual(Path(saved).read_bytes(), self.payload[:8192])
            finally:
                recorder.terminate()

    def test_failed_connection_does_not_claim_audio_or_save_an_empty_file(self):
        recorder = self.recorder.Recorder()
        with tempfile.TemporaryDirectory() as directory:
            try:
                with patch.object(self.recorder, '_recordings_dir', return_value=directory):
                    recorder.start(types.SimpleNamespace(_current_url=self.base + '/denied'), 'Denied')
                self.assertFalse(recorder.wait_started(2))
                self.assertIsNone(recorder.stop())
                self.assertEqual(list(Path(directory).iterdir()), [])
            finally:
                recorder.terminate()

    def test_repeated_recordings_do_not_append_to_a_previous_file(self):
        recorder = self.recorder.Recorder()
        with tempfile.TemporaryDirectory() as directory:
            try:
                saved = []
                for _ in range(2):
                    with patch.object(self.recorder, '_recordings_dir', return_value=directory):
                        recorder.start(types.SimpleNamespace(_current_url=self.base + '/radio.mp3'), 'Same radio')
                    self.assertTrue(recorder.wait_started(2))
                    saved.append(Path(recorder.stop()))
                self.assertNotEqual(*saved)
                self.assertTrue(all(p.read_bytes().startswith(self.payload[:100]) for p in saved))
            finally:
                recorder.terminate()

    def test_menu_controller_is_nonblocking_freezes_url_and_stops_after_playback_changes(self):
        from unittest.mock import Mock
        class Controller(self.recording_mixin.RecordingMixin):
            pass
        controller = Controller()
        controller._recorder = self.recorder.Recorder()
        player = Mock()
        player._current_url = self.base + '/radio.mp3'
        player._current_url_resolved = None
        player.get_current_station.return_value = {'name': 'Listening radio'}
        player.get_current_name.return_value = 'Listening radio'
        player.has_media.return_value = True
        controller._player = player
        entered, release = threading.Event(), threading.Event()
        original = self.recorder._resolve_url
        def delayed(url):
            entered.set()
            release.wait(3)
            return original(url)
        with tempfile.TemporaryDirectory() as directory, patch.object(
                self.recording_mixin.wx, 'CallAfter', side_effect=lambda fn, *args: fn(*args)), patch.object(
                self.recorder, '_recordings_dir', return_value=directory), patch.object(
                self.recorder, '_resolve_url', side_effect=delayed):
            try:
                self.messages.clear()
                started = time.monotonic()
                controller._toggle_instant_recording()
                self.assertLess(time.monotonic() - started, .5)
                self.assertTrue(entered.wait(1))
                player._current_url = self.base + '/denied'
                controller._toggle_instant_recording()  # duplicate click is ignored
                release.set()
                self.assertTrue(wait_for(lambda: not controller._instant_record_busy))
                self.assertEqual(controller._recorder._writer.original_url, self.base + '/radio.mp3')
                self.assertIn('Recording started: Listening radio', self.messages)
                player.get_current_station.return_value = {'media_kind': 'podcast'}
                controller._toggle_instant_recording()
                self.assertTrue(wait_for(lambda: not controller._instant_record_busy))
                self.assertFalse(controller._recorder.is_recording())
                self.assertTrue(any(m.startswith('Recording saved: ') for m in self.messages))
                self.assertTrue(list(Path(directory).glob('*.mp3')))
                player.stop.assert_not_called()
                player.play.assert_not_called()
            finally:
                release.set()
                controller._recorder.terminate()

    def test_shutdown_during_connection_resolution_cannot_restart_recording(self):
        recorder = self.recorder.Recorder()
        original = self.recorder._resolve_url
        def terminate_during_resolution(url):
            recorder.terminate()
            return original(url)
        with tempfile.TemporaryDirectory() as directory, patch.object(self.recorder, '_recordings_dir', return_value=directory), patch.object(self.recorder, '_resolve_url', side_effect=terminate_during_resolution):
            with self.assertRaises(RuntimeError):
                recorder.start(types.SimpleNamespace(_current_url=self.base + '/radio.mp3'), 'Shutdown')
            self.assertFalse(recorder.is_recording())

    def test_unwritable_recording_destination_does_not_report_success(self):
        recorder = self.recorder.Recorder()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'missing/recording.mp3'
            try:
                with patch.object(self.recorder, '_make_output_path', return_value=str(target)):
                    recorder.start(types.SimpleNamespace(_current_url=self.base + '/radio.mp3'), 'Unavailable folder')
                self.assertFalse(recorder.wait_started(2))
                self.assertIsNone(recorder.stop())
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
