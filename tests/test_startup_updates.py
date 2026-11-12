"""Startup discovery must notify accessibly without taking focus or stopping media."""
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import DesktopFrame


class StartupUpdateTests(unittest.TestCase):
    def frame(self):
        frame = types.SimpleNamespace(
            _closing=False, _update_check_running=False, _update_manual_requested=False,
            _startup_update_timer=None, _available_update=None, _announced_update=None,
            settings={'desktop': {'update_repository': 'owner/app'}, 'freeAudio': {'auto_check_updates': True}},
            notifications=Mock(), _update_status=Mock(), _updates_button=Mock(),
            translate=lambda message: message, offer_update=Mock(), plugin=Mock())
        for name in ('check_updates', 'schedule_startup_update', 'show_update_notice',
                     'clear_update_notice', 'open_update_options'):
            setattr(frame, name, types.MethodType(getattr(DesktopFrame, name), frame))
        return frame

    def check(self, frame, result=None, error=None, silent=True):
        queued=[]
        with patch('desktop.updates.check_release', return_value=result, side_effect=error), patch(
                'main.wx.CallAfter', side_effect=lambda fn,*args: queued.append((fn,args))):
            frame.check_updates(silent=silent)
            end=time.monotonic()+2
            while not queued and time.monotonic()<end:
                time.sleep(.005)
            self.assertTrue(queued)
            queued[0][0](*queued[0][1])

    def test_startup_schedules_once_after_five_seconds(self):
        frame=self.frame()
        with patch('main.wx.CallLater') as timer:
            frame.schedule_startup_update()
            frame.schedule_startup_update()
        timer.assert_called_once()
        self.assertEqual(timer.call_args.args[0],5000)
        frame.check_updates=Mock()
        timer.call_args.args[1]()
        frame.check_updates.assert_called_once_with(silent=True)

    def test_disabled_unconfigured_or_closed_does_not_schedule(self):
        for state in ('disabled','unconfigured','closed'):
            with self.subTest(state=state):
                frame=self.frame()
                if state=='disabled':frame.settings['freeAudio']['auto_check_updates']=False
                if state=='unconfigured':frame.settings['desktop']['update_repository']=''
                if state=='closed':frame._closing=True
                with patch('main.wx.CallLater') as timer:
                    frame.schedule_startup_update()
                timer.assert_not_called()

    def test_timer_rechecks_preference_and_lifetime_before_network_access(self):
        for state in ('disabled','closed'):
            frame=self.frame()
            with patch('main.wx.CallLater') as timer:frame.schedule_startup_update()
            if state=='disabled':frame.settings['freeAudio']['auto_check_updates']=False
            else:frame._closing=True
            frame.check_updates=Mock()
            timer.call_args.args[1]()
            frame.check_updates.assert_not_called()

    def test_new_release_announces_once_and_leaves_playback_and_focus_alone(self):
        frame=self.frame()
        release=('9.0.0','https://github.com/owner/app/releases/tag/v9.0.0')
        self.check(frame,release)
        self.check(frame,release)
        frame.notifications.message.assert_called_once_with(
            'Version 9.0.0 is available. Use the update button to download it.')
        self.assertEqual(frame._available_update,release)
        frame.offer_update.assert_not_called()
        frame._updates_button.SetLabel.assert_called_with('Download &update 9.0.0...')
        frame._updates_button.SetFocus.assert_not_called()
        frame._update_status.SetFocus.assert_not_called()
        frame.plugin._player.stop.assert_not_called()
        frame.open_update_options()
        frame.offer_update.assert_called_once_with(*release)

    def test_up_to_date_and_offline_startups_do_not_interrupt(self):
        for error in (None,OSError('offline')):
            frame=self.frame()
            self.check(frame,error=error)
            frame.notifications.message.assert_not_called()
            frame.offer_update.assert_not_called()

    def test_manual_check_still_opens_options(self):
        frame=self.frame();release=('9.0.0','trusted URL')
        self.check(frame,release,silent=False)
        frame.offer_update.assert_called_once_with(*release)
        frame.notifications.message.assert_not_called()

    def test_manual_request_during_automatic_check_is_not_lost(self):
        frame=self.frame(); entered=threading.Event();release=threading.Event();queued=[]
        def fetch(*args):
            entered.set();release.wait(2)
            return ('9.0.0','trusted URL')
        with patch('desktop.updates.check_release',side_effect=fetch) as check, patch(
                'main.wx.CallAfter',side_effect=lambda fn,*args:queued.append((fn,args))):
            frame.check_updates(silent=True)
            self.assertTrue(entered.wait(1))
            frame.check_updates(silent=False)
            release.set()
            end=time.monotonic()+2
            while not queued and time.monotonic()<end:time.sleep(.005)
            self.assertTrue(queued)
            queued[0][0](*queued[0][1])
            check.assert_called_once()
        frame.offer_update.assert_called_once_with('9.0.0','trusted URL')
        self.assertFalse(frame._update_manual_requested)

    def test_closed_frame_does_not_start_a_worker(self):
        frame=self.frame();frame._closing=True
        with patch('desktop.updates.check_release') as fetch:
            frame.check_updates()
        fetch.assert_not_called()

    def test_background_requests_are_marshalled_to_main_thread(self):
        frame=self.frame()
        with patch('main.wx.IsMainThread',return_value=False), patch('main.wx.CallAfter') as queue, patch(
                'desktop.updates.check_release') as fetch:
            frame.check_updates(silent=True)
        queue.assert_called_once_with(frame.check_updates,True)
        fetch.assert_not_called()
