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
    def playback_frame(self, last_url='https://example.com/radio', has_media=False):
        player = Mock()
        player.has_media.return_value = has_media
        return types.SimpleNamespace(
            _closing=False, plugin=types.SimpleNamespace(
                _player=player, _resume_last_station=Mock(), script_pauseResume=Mock()),
            settings={'freeAudio': {'last_station_url': last_url}},
            notifications=Mock(), translate=lambda text: text)

    def test_play_button_restarts_last_station_after_full_stop(self):
        frame = self.playback_frame()
        DesktopFrame.pause_playback(frame)
        frame.plugin._resume_last_station.assert_called_once_with()
        frame.plugin.script_pauseResume.assert_not_called()
        frame.notifications.message.assert_not_called()

    def test_play_button_without_saved_media_explains_how_to_choose_media(self):
        for url in ('', '   '):
            with self.subTest(url=url):
                frame = self.playback_frame(last_url=url)
                DesktopFrame.pause_playback(frame)
                frame.plugin._resume_last_station.assert_not_called()
                frame.notifications.message.assert_called_once_with(
                    'No media is playing. Open the library to choose media.')

    def test_play_button_pauses_loaded_media(self):
        frame = self.playback_frame(has_media=True)
        frame.plugin._player.is_playing.return_value = True
        DesktopFrame.pause_playback(frame)
        frame.plugin._player.pause.assert_called_once_with()
        frame.plugin._player.resume.assert_not_called()
        frame.plugin.script_pauseResume.assert_not_called()
        frame.plugin._resume_last_station.assert_not_called()

    def test_rapid_button_activations_resume_without_hotkey_repeat_actions(self):
        frame = self.playback_frame(has_media=True)
        frame.plugin._player.is_playing.side_effect = [True, False, True, False]
        for _ in range(4):
            DesktopFrame.pause_playback(frame)
        self.assertEqual(frame.plugin._player.pause.call_count, 2)
        self.assertEqual(frame.plugin._player.resume.call_count, 2)
        frame.plugin.script_pauseResume.assert_not_called()
        frame.plugin._resume_last_station.assert_not_called()

    def test_play_button_does_nothing_while_closing(self):
        frame = self.playback_frame()
        frame._closing = True
        DesktopFrame.pause_playback(frame)
        frame.plugin._resume_last_station.assert_not_called()
        frame.notifications.message.assert_not_called()

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

    def test_main_window_f8_toggles_playback(self):
        import wx
        frame = types.SimpleNamespace(toggle_playback=Mock())
        event = Mock()
        event.GetKeyCode.return_value = wx.WXK_F8
        event.HasAnyModifiers.return_value = False
        event.IsAutoRepeat.return_value = False
        DesktopFrame.playback_key(frame, event)
        frame.toggle_playback.assert_called_once()
        event.Skip.assert_not_called()

    def test_modified_f8_is_not_taken_from_other_shortcuts(self):
        import wx
        frame = types.SimpleNamespace(toggle_playback=Mock())
        event = Mock()
        event.GetKeyCode.return_value = wx.WXK_F8
        event.HasAnyModifiers.return_value = True
        DesktopFrame.playback_key(frame, event)
        frame.toggle_playback.assert_not_called()
        event.Skip.assert_called_once()

    def test_holding_f8_does_not_toggle_repeatedly(self):
        import wx
        frame = types.SimpleNamespace(toggle_playback=Mock())
        event = Mock()
        event.GetKeyCode.return_value = wx.WXK_F8
        event.HasAnyModifiers.return_value = False
        event.IsAutoRepeat.return_value = True
        DesktopFrame.playback_key(frame, event)
        frame.toggle_playback.assert_not_called()

    def test_primary_control_stops_loaded_media_and_replays_empty_player(self):
        frame = self.playback_frame(has_media=True)
        frame.stop_playback, frame.pause_playback = Mock(), Mock()
        DesktopFrame.toggle_playback(frame)
        frame.stop_playback.assert_called_once()
        frame.plugin._player.has_media.return_value = False
        DesktopFrame.toggle_playback(frame)
        frame.pause_playback.assert_called_once()

    def test_labels_update_without_moving_focus_in_either_window(self):
        frame = self.playback_frame(has_media=True)
        frame._stop_button, frame._playback_status = Mock(), Mock()
        library_button = Mock()
        frame.plugin._dialog = types.SimpleNamespace(_stop_btn=library_button)
        frame.plugin._player.get_current_name.return_value = 'Station'
        frame.plugin._player.is_playing.return_value = True
        DesktopFrame.refresh_playback_status(frame)
        frame._stop_button.SetLabel.assert_called_with('&Stop playback (F8)')
        frame.plugin._player.has_media.return_value = False
        DesktopFrame.refresh_playback_status(frame)
        for button in (frame._stop_button, library_button):
            button.SetLabel.assert_called_with('&Play last media (F8)')
            button.SetFocus.assert_not_called()
        frame._stop_button.Disable.assert_not_called()

    def test_second_press_during_slow_stop_queues_replay_and_third_cancels_it(self):
        frame = self.playback_frame()
        frame._playback_gate = PlaybackGate()
        frame._stop_pending = None
        frame._resume_after_stop = False
        frame.refresh_playback_status = Mock()
        frame.pause_playback = Mock()
        started, release = threading.Event(), threading.Event()
        def slow_stop():
            started.set()
            release.wait(2)
        frame.plugin._player.stop.side_effect = slow_stop
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                callbacks=[]
                started.clear(); release.clear()
                frame.pause_playback.reset_mock()
                with patch('main.wx.CallAfter', side_effect=lambda fn,*args: callbacks.append((fn,args))):
                    DesktopFrame.stop_playback(frame)
                    self.assertTrue(started.wait(1))
                    DesktopFrame.toggle_playback(frame)
                    self.assertTrue(frame._resume_after_stop)
                    if cancel:
                        DesktopFrame.toggle_playback(frame)
                        self.assertFalse(frame._resume_after_stop)
                    release.set()
                    end=time.monotonic()+2
                    while not callbacks and time.monotonic()<end:
                        time.sleep(.005)
                    self.assertTrue(callbacks)
                    callbacks[0][0](*callbacks[0][1])
                self.assertEqual(frame.pause_playback.call_count, 0 if cancel else 1)
                self.assertIsNone(frame._stop_pending)

    def test_toggle_cancels_connection_before_any_media_is_loaded(self):
        frame=self.playback_frame(has_media=False)
        frame._playback_gate=PlaybackGate()
        frame._playback_gate.request()
        frame.stop_playback,frame.pause_playback=Mock(),Mock()
        DesktopFrame.toggle_playback(frame)
        frame.stop_playback.assert_called_once()
        frame.pause_playback.assert_not_called()

    def test_failed_resume_resolution_clears_pending_connection(self):
        finished=threading.Event()
        class Plugin:
            _play_station=Mock()
            _start_playing=Mock()
            def _resume_last_station(self):
                finished.set()
        gate=PlaybackGate()
        install_playback_gate(Plugin,gate)
        Plugin()._resume_last_station()
        self.assertTrue(finished.wait(1))
        end=time.monotonic()+1
        while gate.pending is not None and time.monotonic()<end:
            time.sleep(.001)
        self.assertIsNone(gate.pending)

    def test_late_stop_completion_cannot_leave_controls_stuck_after_another_command(self):
        frame=self.playback_frame()
        frame._playback_gate=PlaybackGate()
        frame.refresh_playback_status=Mock()
        frame.pause_playback=Mock()
        callbacks=[]
        with patch('main.wx.CallAfter',side_effect=lambda fn,*args:callbacks.append((fn,args))):
            DesktopFrame.stop_playback(frame)
            end=time.monotonic()+1
            while not callbacks and time.monotonic()<end:
                time.sleep(.005)
            self.assertTrue(callbacks)
            frame._playback_gate.request()  # e.g. a global play command
            callbacks[0][0](*callbacks[0][1])
        self.assertIsNone(frame._stop_pending)
        self.assertFalse(frame._resume_after_stop)
        frame.pause_playback.assert_not_called()
