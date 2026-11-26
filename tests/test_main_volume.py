import sys,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from main import DesktopFrame
import wx

class MainVolumeTests(unittest.TestCase):
    def frame(self):
        player=Mock();player.get_volume.return_value=40
        player.set_volume.side_effect=lambda v:setattr(player.get_volume,'return_value',v)
        control=Mock();control.GetValue.return_value=40
        frame=types.SimpleNamespace(_closing=False,_syncing_volume=False,_volume_control=control,
            plugin=types.SimpleNamespace(_player=player,_sync_dialog_volume=Mock(),_open_dialog=Mock()),
            settings={'freeAudio':{}},notifications=Mock(),translate=lambda s:s)
        for name in ('set_main_volume','adjust_volume','sync_main_volume','on_volume_input'):
            setattr(frame,name,types.MethodType(getattr(DesktopFrame,name),frame))
        return frame

    def test_main_volume_changes_audio_preferences_and_library_without_opening_it(self):
        frame=self.frame()
        with patch('main.wx.Window.FindFocus',return_value=None):frame.set_main_volume(55)
        frame.plugin._player.set_volume.assert_called_once_with(55)
        frame.plugin._sync_dialog_volume.assert_called_once_with(55)
        frame._volume_control.SetValue.assert_called_once_with(55)
        self.assertEqual(frame.settings['freeAudio']['volume'],55)
        frame.notifications.message.assert_called_once_with('Volume 55')
        frame.plugin._open_dialog.assert_not_called()
        frame._volume_control.SetFocus.assert_not_called()

    def test_volume_bounds_keep_existing_amplification_and_preference_rules(self):
        for requested,actual,saved in ((-20,0,0),(220,200,100),(75,75,75)):
            frame=self.frame()
            with patch('main.wx.Window.FindFocus',return_value=None):frame.set_main_volume(requested)
            frame.plugin._player.set_volume.assert_called_once_with(actual)
            self.assertEqual(frame.settings['freeAudio']['volume'],saved)

    def test_f5_f6_work_from_main_window_and_modified_keys_are_preserved(self):
        for key,delta in ((wx.WXK_F5,-5),(wx.WXK_F6,5)):
            frame=types.SimpleNamespace(adjust_volume=Mock())
            event=Mock();event.GetKeyCode.return_value=key;event.HasAnyModifiers.return_value=False
            DesktopFrame.playback_key(frame,event)
            frame.adjust_volume.assert_called_once_with(delta)
            event.Skip.assert_not_called()
            event.HasAnyModifiers.return_value=True
            frame.adjust_volume.reset_mock()
            DesktopFrame.playback_key(frame,event)
            frame.adjust_volume.assert_not_called()
            event.Skip.assert_called_once()

    def test_sync_reads_engine_changes_without_overwriting_current_edit_or_announcing(self):
        frame=self.frame();frame.plugin._player.get_volume.return_value=80
        focus=object();frame._volume_control.IsDescendant.return_value=True
        with patch('main.wx.Window.FindFocus',return_value=focus):frame.sync_main_volume()
        frame._volume_control.SetValue.assert_not_called()
        with patch('main.wx.Window.FindFocus',return_value=None):frame.sync_main_volume()
        frame._volume_control.SetValue.assert_called_once_with(80)
        frame.notifications.message.assert_not_called()
        self.assertFalse(frame._syncing_volume)

    def test_enter_and_focus_loss_commit_only_a_changed_value(self):
        frame=self.frame();frame._volume_control.GetValue.return_value=65
        frame.set_main_volume=Mock();event=Mock()
        frame.on_volume_input(event)
        frame.set_main_volume.assert_called_once_with(65)
        event.Skip.assert_called_once()
        frame.set_main_volume.reset_mock();frame._volume_control.GetValue.return_value=40
        frame.on_volume_input(Mock())
        frame.set_main_volume.assert_not_called()

    def test_invalid_or_closed_volume_action_does_not_change_audio(self):
        frame=self.frame()
        frame.set_main_volume('invalid')
        frame.plugin._player.set_volume.assert_not_called()
        frame.notifications.message.assert_called_once()
        frame._closing=True;frame.adjust_volume(5);frame.set_main_volume(20)
        frame.plugin._player.set_volume.assert_not_called()

class NativeMainViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owns_app=wx.GetApp() is None
        cls.app=wx.GetApp() or wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if cls.owns_app:cls.app.Destroy()

    def build_frame(self,language):
        import gettext,tempfile
        from desktop.host import Notifications
        from desktop.storage import Settings
        directory=tempfile.TemporaryDirectory()
        settings=Settings(directory.name)
        settings['freeAudio'].update(volume=35,resume_on_start=False,auto_check_updates=False)
        settings['desktop']['language']=language
        frame=DesktopFrame(None)
        notifications=Notifications(frame);notifications.outputs=[];notifications.message=Mock()
        player=Mock();player.get_volume.return_value=35;player.has_media.return_value=False
        plugin=types.SimpleNamespace(_player=player,_dialog=None,_sync_dialog_volume=Mock(),_play_station=Mock())
        translation=gettext.translation('nvda',str(Path(__file__).resolve().parents[1]/'locale'),languages=[language],fallback=True).gettext
        frame.build(plugin,settings,translation,notifications)
        self.app.Yield()
        return frame,directory,translation

    def cleanup(self,frame,directory):
        frame.downloads.close()
        for worker in frame.downloads.workers: worker.join(2)
        frame._closing=True
        frame._playback_timer.Stop();frame._autosave.Stop();frame.shortcuts.close()
        frame.Destroy();self.app.Yield();directory.cleanup()

    def test_navigation_order_and_native_volume_name_in_both_languages(self):
        for language in ('tr','en'):
            with self.subTest(language=language):
                frame,directory,translate=self.build_frame(language)
                try:
                    view=frame._main_view
                    playback=[w for w in view.stop.GetParent().GetChildren() if isinstance(w,(wx.Button,wx.SpinCtrl))]
                    self.assertEqual(playback,[view.stop,view.pause,view.previous,view.following,view.record,view.volume_down,view.volume,view.volume_up])
                    tools=[w for w in view.browser.GetParent().GetChildren() if isinstance(w,wx.Button)]
                    self.assertEqual(tools,[view.browser,view.continue_listening,view.sleep,view.downloads,view.listening,view.settings,view.commands,view.messages,view.language,view.updates,view.backup,view.help,view.about,view.exit])
                    self.assertEqual(view.volume.GetName(),translate('Volume (%)'))
                    self.assertIsInstance(view.volume.GetPrevSibling(),wx.StaticText)
                    self.assertEqual(view.volume.GetPrevSibling().GetLabel(),translate('Volume (%)'))
                    self.assertEqual((view.volume.GetMin(),view.volume.GetMax()),(0,200))
                    self.assertTrue(all(control.GetHandle() for control in playback+tools))
                finally:self.cleanup(frame,directory)

    def test_download_and_history_windows_keep_selection_names_and_playback_keys(self):
        from desktop.media_dialogs import DownloadsDialog, HistoryDialog
        from unittest.mock import patch
        frame,directory,translate=self.build_frame('tr')
        downloads=history=None
        try:
            path=Path(directory.name)/'episode.mp3';path.write_bytes(b'audio')
            item=frame.downloads.enqueue('Episode','https://example.org/audio',path)
            downloads=DownloadsDialog(frame)
            self.assertEqual(downloads.list.GetName(),'Podcast indirmeleri')
            self.assertEqual(downloads.details.GetPrevSibling().GetLabel(),'İndirme ayrıntıları')
            self.assertEqual(downloads.progress.GetPrevSibling().GetLabel(),'İndirme ilerlemesi')
            self.assertTrue(downloads.buttons['play'].IsEnabled())
            self.assertFalse(downloads.buttons['cancel'].IsEnabled())
            downloads.list.SetFocus();before=wx.Window.FindFocus()
            downloads.refresh()
            self.assertEqual(before,wx.Window.FindFocus())
            downloads.action('play')
            frame.plugin._play_station.assert_called_once()
            self.assertEqual(frame.plugin._play_station.call_args.args[0]['podcast_resume_key'],item['url'])
            frame.listening_history.observe({'url':'https://example.org/radio','name':'Radio'})
            history=HistoryDialog(frame)
            self.assertEqual(history.list.GetName(),'Son dinlenenler')
            self.assertEqual(history.list.GetCount(),1)
            frame.listening_history.observe({'url':'https://example.org/podcast','name':'Episode','media_kind':'podcast'})
            history.refresh()
            self.assertIn('Radio',history.list.GetStringSelection())
            with patch('desktop.media_dialogs.wx.MessageBox',return_value=wx.YES):
                history.on_clear(None)
            self.assertEqual(history.list.GetCount(),0)
            self.assertTrue(path.exists())
        finally:
            if downloads: downloads.Close()
            if history: history.Close()
            self.cleanup(frame,directory)

    def test_record_button_tracks_recording_after_playback_stops_and_shows_custom_shortcut(self):
        frame,directory,translate=self.build_frame('tr')
        try:
            frame.plugin._recorder=Mock();frame.plugin._recorder.is_recording.return_value=True
            frame.plugin._toggle_instant_recording=Mock()
            frame.shortcuts.effective['toggleRecord']='control+alt+e'
            frame.refresh_main_media_controls()
            self.assertEqual(frame._main_view.record.GetLabel(),'Radyo kaydını durdur (Ctrl+Alt+E)')
            self.assertIn('Ctrl+Alt+E',frame._main_view.record_hint.GetLabel())
            before=wx.Window.FindFocus()
            event=wx.CommandEvent(wx.EVT_BUTTON.typeId,frame._main_view.record.GetId())
            frame._main_view.record.GetEventHandler().ProcessEvent(event)
            frame.plugin._toggle_instant_recording.assert_called_once()
            frame.plugin._recorder.is_recording.return_value=False
            frame.refresh_main_media_controls()
            self.assertEqual(frame._main_view.record.GetLabel(),'Radyo kaydını başlat (Ctrl+Alt+E)')
            self.assertEqual(before,wx.Window.FindFocus())
            frame.shortcuts.failures=['toggleRecord: unavailable']
            frame.refresh_main_media_controls()
            self.assertNotIn('Ctrl+Alt+E',frame._main_view.record.GetLabel())
            self.assertIn('kullanılamıyor',frame._main_view.record_hint.GetLabel())
        finally:self.cleanup(frame,directory)

    def test_release_notes_load_into_native_field_and_failure_keeps_actions_available(self):
        import time
        from desktop.update_dialog import UpdateOptionsDialog
        frame,directory,translate=self.build_frame('tr')
        try:
            for fail in (False,True):
                with patch('desktop.updates.release_notes',side_effect=OSError('offline') if fail else None,return_value='New recording controls'):
                    dialog=UpdateOptionsDialog(frame,'owner/repo','2.1.0',['Download','Open page'],translate)
                    try:
                        deadline=time.monotonic()+2
                        while dialog.notes.GetValue()==translate('Loading release notes...') and time.monotonic()<deadline:
                            self.app.ProcessPendingEvents();time.sleep(.01)
                        self.assertNotEqual(dialog.notes.GetValue(),translate('Loading release notes...'))
                        self.assertEqual(dialog.notes.GetPrevSibling().GetLabel(),'Bu sürümdeki yenilikler')
                        self.assertTrue(dialog.actions.IsEnabled())
                        if fail:self.assertIn('yüklenemedi',dialog.notes.GetValue())
                        else:self.assertEqual(dialog.notes.GetValue(),'New recording controls')
                    finally:dialog.Destroy();self.app.ProcessPendingEvents()
        finally:self.cleanup(frame,directory)

    def test_compact_window_keeps_content_inside_horizontal_viewport(self):
        frame,directory,translate=self.build_frame('tr')
        try:
            frame.SetSize((640,440));self.app.Yield();frame._main_view.relayout()
            panel=frame._main_view.panel
            self.assertLessEqual(panel.GetSizer().GetMinSize().width,panel.GetClientSize().width)
            self.assertGreaterEqual(panel.GetVirtualSize().height,panel.GetClientSize().height)
        finally:self.cleanup(frame,directory)
    def test_update_notice_remains_visible_in_the_new_layout_without_moving_focus(self):
        frame,directory,translate=self.build_frame('tr')
        try:
            before=wx.Window.FindFocus()
            frame.show_update_notice('9.9.9','trusted URL',announce=False)
            self.assertTrue(frame._update_status.IsShown())
            self.assertIn('9.9.9',frame._update_status.GetLabel())
            self.assertIn('9.9.9',frame._updates_button.GetLabel())
            self.assertEqual(before,wx.Window.FindFocus())
            frame.clear_update_notice()
            self.assertFalse(frame._update_status.IsShown())
        finally:self.cleanup(frame,directory)

    def test_sleep_and_continue_windows_have_native_labels_safe_defaults_and_keyboard_access(self):
        from desktop.listening_dialogs import SleepDialog, ContinueDialog
        frame,directory,translate=self.build_frame('tr')
        sleep=continuation=None
        try:
            frame.plugin._player.get_current_station.return_value={}
            sleep=SleepDialog(frame)
            self.assertEqual(sleep.action.GetSelection(),0)
            self.assertEqual(sleep.minutes.GetPrevSibling().GetLabel(),'Dakika (1–480)')
            self.assertEqual(sleep.status.GetPrevSibling().GetLabel(),'Zamanlayıcı durumu')
            self.assertFalse(sleep.cancel.IsEnabled())
            sleep.arm(None)
            self.assertEqual(frame.sleep_timer.action,'stop')
            self.assertTrue(sleep.cancel.IsEnabled())
            frame.cancel_sleep();sleep.refresh()
            self.assertFalse(sleep.cancel.IsEnabled())
            sleep.mode.SetSelection(1);sleep.arm(None)
            self.assertIsNone(frame.sleep_timer.mode)
            with patch('desktop.listening_dialogs.continuation_items',return_value=[]):
                continuation=ContinueDialog(frame)
            self.assertEqual(continuation.list.GetPrevSibling().GetLabel(),'Yarım kalan podcastler ve sesli kitaplar')
            self.assertFalse(continuation.play.IsEnabled())
            frame.refresh_local_shortcut_labels()
            self.assertIn('Ctrl+Shift+T',frame._main_view.sleep.GetLabel())
            before=frame._main_view.sleep.GetLabel()
            frame.sleep_tick();frame.refresh_local_shortcut_labels()
            self.assertEqual(frame._main_view.sleep.GetLabel(),before)
        finally:
            if sleep:sleep.Close()
            if continuation:continuation.Close()
            self.cleanup(frame,directory)
