import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.playback import PlaybackGate, install_playback_gate
from main import DesktopFrame


class PlaybackControlTests(unittest.TestCase):
    def test_stop_before_startup_callback_prevents_automatic_resume_but_not_manual_resume(self):
        resumed = threading.Event()
        class Plugin:
            _play_station = Mock()
            _start_playing = Mock()
            def _resume_last_station(self):
                resumed.set()
        gate = PlaybackGate()
        install_playback_gate(Plugin, gate)
        plugin = Plugin()
        gate.cancel()
        plugin._resume_last_station(startup=True)
        self.assertFalse(resumed.is_set())
        plugin._resume_last_station()
        self.assertTrue(resumed.wait(1))

    def test_stop_cancels_a_profile_worker_that_has_not_started_playback(self):
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        played = Mock()
        class Plugin:
            def _play_station(self, station, announce=True):
                entered.set()
                release.wait(2)
                self._start_playing('radio', 'Station', station=station)
                finished.set()
            def _start_playing(self, *args):
                played(*args)
            def _resume_last_station(self):
                self._play_station({'name': 'Station'})
        gate = PlaybackGate()
        install_playback_gate(Plugin, gate)
        plugin = Plugin()
        plugin._play_station({'name': 'Station'})
        self.assertTrue(entered.wait(1))
        gate.cancel()
        release.set()
        self.assertTrue(finished.wait(1))
        played.assert_not_called()

    def test_stop_during_startup_resolution_cannot_resume_later(self):
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        played = Mock()
        class Plugin:
            def _play_station(self, station):
                self._start_playing('radio', 'Station', station=station)
            def _start_playing(self, *args):
                played(*args)
            def _resume_last_station(self):
                entered.set()
                release.wait(2)
                self._play_station({'name': 'Station'})
                finished.set()
        gate = PlaybackGate()
        install_playback_gate(Plugin, gate)
        plugin = Plugin()
        started = time.monotonic()
        plugin._resume_last_station()
        self.assertLess(time.monotonic() - started, .2)
        self.assertTrue(entered.wait(1))
        gate.cancel()
        release.set()
        self.assertTrue(finished.wait(1))
        played.assert_not_called()

    def test_stopped_request_does_not_prevent_a_later_explicit_play(self):
        gate = PlaybackGate()
        old = gate.request()
        gate.cancel()
        action = Mock()
        self.assertFalse(gate.run(old, action))
        self.assertTrue(gate.run(gate.request(), action))
        action.assert_called_once()

    def test_stop_button_keeps_recordings_running_and_returns_without_waiting_for_ipc(self):
        done, audio_started, audio_release = threading.Event(), threading.Event(), threading.Event()
        gate = PlaybackGate()
        token = gate.request()
        def blocked_launch():
            audio_started.set()
            audio_release.wait(2)
        launch = threading.Thread(target=lambda: gate.run(token, blocked_launch))
        launch.start()
        self.assertTrue(audio_started.wait(1))
        recorder, player = Mock(), Mock()
        frame = types.SimpleNamespace(_closing=False, _playback_gate=gate,
            plugin=types.SimpleNamespace(_player=player, _recorder=recorder, _pause_resume_timer=Mock()),
            notifications=Mock(), translate=lambda text: text,
            refresh_playback_status=lambda: done.set())
        with patch('main.wx.CallAfter', side_effect=lambda fn, *args: fn(*args)):
            started = time.monotonic()
            DesktopFrame.stop_playback(frame)
            self.assertLess(time.monotonic() - started, .2)
            audio_release.set()
            self.assertTrue(done.wait(2))
        launch.join(1)
        player.stop.assert_called_once()
        recorder.stop.assert_not_called()
        self.assertIsNone(frame.plugin._pause_resume_timer)

    def test_main_window_f8_always_requests_stop(self):
        import wx
        frame = types.SimpleNamespace(stop_playback=Mock())
        event = Mock()
        event.GetKeyCode.return_value = wx.WXK_F8
        DesktopFrame.playback_key(frame, event)
        frame.stop_playback.assert_called_once()
        event.Skip.assert_not_called()
