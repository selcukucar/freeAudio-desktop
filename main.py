"""freeAudio Desktop: standalone, native Windows application."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import threading
import traceback
import wx
import wx.lib.scrolledpanel
from desktop.storage import Settings, data_directory
from desktop.host import install, SettingsDialog
from desktop.version import VERSION

ROOT = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else ROOT


class DesktopFrame(wx.Frame):
    def prePopup(self):
        pass

    def postPopup(self):
        pass

    def _popupSettingsDialog(self, dialogClass=None, panelClass=None):
        if panelClass is None:
            from freeAudio.settingsPanel import freeAudioSettingsPanel
            panelClass = freeAudioSettingsPanel
        with SettingsDialog(self, panelClass, self.settings, self.translate) as dialog:
            dialog.ShowModal()

    def build(self, plugin, settings, translate, notifications):
        from desktop.shortcuts import Shortcuts
        self.plugin, self.settings, self.translate = plugin, settings, translate
        self.notifications = notifications
        self._closing = False
        self._update_check_running = False
        self._save_error_reported = False
        self._pending_update = None
        _ = translate
        self.SetTitle('freeAudio Desktop ' + VERSION)
        self.SetSize((700, 440))
        self.shortcuts = Shortcuts(self, plugin, settings, notifications.message)
        panel = wx.lib.scrolledpanel.ScrolledPanel(self, style=wx.TAB_TRAVERSAL)
        notifications.control.Reparent(panel)
        outer = wx.BoxSizer(wx.VERTICAL)
        heading = wx.StaticText(panel, label=_('Radio, podcasts, audio books and local music'))
        outer.Add(heading, 0, wx.ALL, 16)
        browser = wx.Button(panel, label=_('&Open library'))
        self._playback_status = wx.StaticText(panel, label=_('Playback stopped'))
        outer.Add(self._playback_status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self._stop_button = wx.Button(panel, label=_('&Stop playback (F8)'))
        pause = wx.Button(panel, label=_('&Pause / resume playback'))
        settings_button = wx.Button(panel, label=_('&Settings'))
        commands = wx.Button(panel, label=_('&Commands and shortcuts'))
        messages = wx.Button(panel, label=_('&Notification history'))
        language = wx.Button(panel, label=_('&Language / Dil'))
        updates = wx.Button(panel, label=_('Check for &updates'))
        help_button = wx.Button(panel, label=_('&Help'))
        backup_button = wx.Button(panel, label=_('Profile &backup and restore'))
        exit_button = wx.Button(panel, label=_('E&xit'))
        for button in (self._stop_button, pause, browser, settings_button, commands, messages, language, updates, backup_button, help_button, exit_button):
            outer.Add(button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        outer.Add(notifications.control, 0, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(outer)
        panel.SetupScrolling(scroll_x=False)
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(frame_sizer)
        self.SetMinSize((640, 460))
        self.SetSize((760, 620))
        self._stop_button.Bind(wx.EVT_BUTTON, lambda event: self.stop_playback())
        pause.Bind(wx.EVT_BUTTON, lambda event: self.pause_playback())
        browser.Bind(wx.EVT_BUTTON, lambda event: plugin._open_dialog())
        settings_button.Bind(wx.EVT_BUTTON, lambda event: self._popupSettingsDialog())
        commands.Bind(wx.EVT_BUTTON, lambda event: self.shortcuts.show(self, _))
        messages.Bind(wx.EVT_BUTTON, self.history)
        language.Bind(wx.EVT_BUTTON, self.change_language)
        updates.Bind(wx.EVT_BUTTON, lambda event: self.check_updates())
        help_button.Bind(wx.EVT_BUTTON, self.help)
        backup_button.Bind(wx.EVT_BUTTON, self.backup_profile)
        exit_button.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        self.Bind(wx.EVT_CLOSE, self.exit)
        if settings['freeAudio'].get('resume_on_start') and settings['freeAudio'].get('last_station_url'):
            self._stop_button.SetFocus()
        else:
            browser.SetFocus()
        self.Bind(wx.EVT_CHAR_HOOK, self.playback_key)
        self._playback_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.refresh_playback_status, self._playback_timer)
        self._playback_timer.Start(500)
        if self.shortcuts.failures:
            wx.CallAfter(notifications.message, _('Some shortcuts are unavailable. Open Commands and shortcuts for details.'))
        self._autosave = wx.Timer(self)
        def autosave(event):
            self.persist_settings()
            self.shortcuts.refresh_catalog()
        self.Bind(wx.EVT_TIMER, autosave, self._autosave)
        self._autosave.Start(10000)

    def playback_key(self, event):
        if event.GetKeyCode() == wx.WXK_F8:
            self.stop_playback()
        else:
            event.Skip()

    def refresh_playback_status(self, event=None):
        if self._closing:
            return
        player = self.plugin._player
        if player.has_media():
            label = self.translate('Current media: %s') % player.get_current_name()
        else:
            label = self.translate('Playback stopped')
        if self._playback_status.GetLabel() != label:
            self._playback_status.SetLabel(label)

    def stop_playback(self):
        if self._closing:
            return
        token = self._playback_gate.cancel()
        timer = getattr(self.plugin, '_pause_resume_timer', None)
        if timer:
            timer.Stop()
            self.plugin._pause_resume_timer = None
        self.notifications.message(self.translate('Stopping playback...'))
        def finish(error):
            if self._closing or token != self._playback_gate.current:
                return
            self.refresh_playback_status()
            self.notifications.message(self.translate('Could not stop playback. Please try again.') if error else
                                       self.translate('Playback stopped. Recordings continue independently.'))
        def work():
            error = None
            try:
                def stop():
                    self.plugin._player.stop()
                    self.plugin._stations = []
                    self.plugin._current_index = -1
                self._playback_gate.run(token, stop)
            except Exception as exc:
                logging.exception('Could not stop playback')
                error = exc
            wx.CallAfter(finish, error)
        threading.Thread(target=work, daemon=True, name='desktop-stop-playback').start()

    def pause_playback(self):
        if not self.plugin._player.has_media():
            self.notifications.message(self.translate('No media is playing. Open the library to choose media.'))
            return
        from desktop.host import invoke
        from types import SimpleNamespace
        invoke(self.plugin.script_pauseResume, SimpleNamespace(send=lambda: None))

    def history(self, event):
        _ = self.translate
        with wx.Dialog(self, title=_('Notification history'), size=(700, 450),
                       style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER) as dialog:
            outer = wx.BoxSizer(wx.VERTICAL)
            text = wx.TextCtrl(dialog, value='\n'.join(self.notifications.history),
                               style=wx.TE_MULTILINE | wx.TE_READONLY)
            text.SetName(_('Notifications'))
            outer.Add(text, 1, wx.EXPAND | wx.ALL, 10)
            outer.Add(dialog.CreateButtonSizer(wx.CLOSE), 0, wx.ALL, 10)
            dialog.SetSizer(outer)
            text.SetFocus()
            dialog.ShowModal()

    def change_language(self, event):
        _ = self.translate
        with wx.SingleChoiceDialog(self, _('Choose language. Restart the application to apply.'),
                                   'Language / Dil', ['Türkçe', 'English']) as dialog:
            dialog.SetSelection(0 if self.settings['desktop'].get('language') == 'tr' else 1)
            if dialog.ShowModal() == wx.ID_OK:
                self.settings['desktop']['language'] = ['tr', 'en'][dialog.GetSelection()]
                self.settings.save()
                self.notifications.message(_('Language saved. Restart the application.'))

    def help(self, event):
        path = ROOT / 'docs' / ('tr' if self.settings['desktop'].get('language') == 'tr' else '') / 'desktop.html'
        os.startfile(str(path))

    def check_updates(self, silent=False):
        # The desktop has its own release channel. Never install an NVDA add-on.
        from desktop.updates import check_release
        _ = self.translate
        repository = self.settings['desktop'].get('update_repository', '')
        if not repository:
            if not silent:
                self.notifications.message(_('The update channel has not been published yet.'))
            return
        if self._update_check_running:
            return
        self._update_check_running = True
        def finish(result, error):
            if getattr(self, '_closing', False) or not self:
                return
            self._update_check_running = False
            if error is not None:
                if not silent:
                    self.notifications.message(_('The update check could not be completed. Please try again later.'))
                return
            if result is None:
                if not silent:
                    self.notifications.message(_('No newer release was found.'))
            else:
                version, url = result
                self.offer_update(version, url)
        def work():
            try:
                result = check_release(repository, VERSION)
                wx.CallAfter(finish, result, None)
            except Exception as error:
                logging.exception('Update check failed')
                wx.CallAfter(finish, None, str(error))
        threading.Thread(target=work, daemon=True).start()

    def offer_update(self, version, url):
        _ = self.translate
        portable = (APP_DIR / 'portable.flag').exists()
        installed = bool(getattr(sys, 'frozen', False) and not portable)
        first = _('Download and install update (application restarts)') if installed else _('Download portable update ZIP')
        choices = [first, _('Download only'), _('Open release page')]
        with wx.SingleChoiceDialog(self, _('A new version is available: %s') % version,
                                   _('Application update'), choices) as choice:
            if choice.ShowModal() != wx.ID_OK:
                return
            selection = choice.GetSelection()
        if selection == 2:
            import webbrowser
            webbrowser.open(url)
            return
        from desktop.update_dialog import UpdateDownloadDialog
        repository = self.settings['desktop']['update_repository']
        with UpdateDownloadDialog(self, repository, version, portable or not installed,
                                  self.settings.directory / 'updates', _) as dialog:
            if dialog.ShowModal() != wx.ID_OK or dialog.result is None:
                return
            asset, path = dialog.result
        if installed and selection == 0:
            if not self.persist_settings():
                return
            self._pending_update = (asset, path)
            self.Close()
        else:
            wx.MessageBox(_('The verified update was saved to: %s') % str(path) + '\n\n' +
                          (_('For portable updates, close the application and preserve your data folder when extracting the new ZIP.') if asset.portable else ''),
                          _('Application update'), wx.OK | wx.ICON_INFORMATION, self)
            os.startfile(str(path.parent))

    def backup_profile(self, event):
        from desktop.backup import export_profile, prepare_restore
        _ = self.translate
        with wx.SingleChoiceDialog(self, _('Choose a profile action.'),
                                   _('Profile backup and restore'),
                                   [_('Create a backup'), _('Restore a backup at next startup')]) as choice:
            if choice.ShowModal() != wx.ID_OK:
                return
            restore = choice.GetSelection() == 1
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST if restore else wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        with wx.FileDialog(self, _('Profile backup'), wildcard='freeAudio Desktop (*.zip)|*.zip',
                           defaultFile='freeAudio-profile.zip', style=style) as picker:
            if picker.ShowModal() != wx.ID_OK:
                return
            path = picker.GetPath()
        try:
            if restore:
                if wx.MessageBox(_('Restore settings and libraries from this backup at the next startup? Your current profile will be backed up first.'),
                                 _('Restore profile'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) != wx.YES:
                    return
                prepare_restore(self.settings.directory, path)
                self.notifications.message(_('Backup checked. Restart the application to restore it.'))
            else:
                self.settings.save()
                export_profile(self.settings.directory, path, VERSION)
                self.notifications.message(_('Profile backup saved. Recordings, downloads and account credentials are not included.'))
        except Exception as error:
            logging.exception('Profile operation failed')
            wx.MessageBox(_('The profile operation could not be completed.') + '\n' + str(error),
                          _('Error'), wx.OK | wx.ICON_ERROR, self)

    def persist_settings(self):
        try:
            self.settings.save()
            self._save_error_reported = False
            return True
        except Exception:
            logging.exception('Could not save the application profile')
            if not self._save_error_reported:
                self._save_error_reported = True
                self.notifications.message(self.translate('Settings could not be saved. Check that the profile folder is writable.'))
            return False

    def exit(self, event):
        if self._closing:
            return
        recorder = self.plugin._recorder
        if event.CanVeto() and (recorder.is_recording() or recorder.get_active_scheduled()):
            if wx.MessageBox(self.translate('A recording is in progress. Stop recording and exit?'),
                             'freeAudio Desktop', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) != wx.YES:
                self._pending_update = None
                event.Veto()
                return
        pending_update = getattr(self, '_pending_update', None)
        if pending_update is not None:
            try:
                from desktop.updates import verify_download
                verify_download(*pending_update)
                if not self.persist_settings():
                    self._pending_update = None
                    if event.CanVeto():
                        event.Veto()
                    return
            except Exception:
                logging.exception('Update changed before installation')
                self._pending_update = None
                wx.MessageBox(self.translate('The update could not be verified. Installation was cancelled.'),
                              self.translate('Error'), wx.OK | wx.ICON_ERROR, self)
                if event.CanVeto():
                    event.Veto()
                return
        self._closing = True
        if hasattr(self, '_playback_gate'):
            self._playback_gate.cancel()
        if hasattr(self, '_playback_timer'):
            self._playback_timer.Stop()
        self._autosave.Stop()
        self.shortcuts.close()
        try:
            self.plugin.terminate()
        finally:
            try:
                saved = self.persist_settings()
                if pending_update is not None and saved:
                    try:
                        from desktop.updates import launch_installer
                        launch_installer(*pending_update, APP_DIR, self.settings['desktop'].get('language', 'tr'))
                    except Exception:
                        logging.exception('Could not start the downloaded installer')
                        wx.MessageBox(self.translate('The installer could not be started. The verified download is kept in your profile updates folder.'),
                                      self.translate('Error'), wx.OK | wx.ICON_ERROR, self)
            finally:
                self.Destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version='freeAudio Desktop ' + VERSION)
    parser.add_argument('--portable', action='store_true')
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--language', choices=['tr', 'en'])
    parser.add_argument('--smoke-test', action='store_true')
    args = parser.parse_args()
    app = wx.App(False)
    directory = args.data_dir or data_directory(APP_DIR, args.portable)
    directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(handlers=[RotatingFileHandler(directory / 'desktop.log',
                        maxBytes=1024 * 1024, backupCount=3, encoding='utf-8')],
                        level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    frame = None
    try:
        import hashlib
        app._instance = wx.SingleInstanceChecker('freeAudioDesktop-' + hashlib.sha256(str(directory.resolve()).encode()).hexdigest()[:16])
        if app._instance.IsAnotherRunning():
            wx.MessageBox('freeAudio Desktop is already running. / Uygulama zaten çalışıyor.', 'freeAudio Desktop')
            return 1
        from desktop.backup import apply_pending_restore, export_profile
        try:
            apply_pending_restore(directory, VERSION)
        except Exception:
            logging.exception('Profile restore failed; continuing with existing settings')
            pending = directory / 'restore-pending.zip'
            if pending.exists():
                os.replace(pending, directory / 'restore-rejected.zip')
            wx.MessageBox('Profile restore failed. Existing settings were kept. / Yedek geri yüklenemedi. Mevcut ayarlar korundu.', 'freeAudio Desktop')
        settings = Settings(directory)
        from desktop.updates import read_channel
        published_repository = read_channel(ROOT / 'release-channel.json')
        if not settings['desktop'].get('update_repository') and published_repository:
            settings['desktop']['update_repository'] = published_repository
        backup_warning = False
        if settings['desktop'].get('last_version') != VERSION and settings.path.exists():
            try:
                export_profile(directory, directory / ('backups/profile-before-' + VERSION + '.zip'), VERSION)
            except Exception:
                logging.exception('Automatic pre-upgrade profile backup failed')
                backup_warning = True
        settings['desktop']['last_version'] = VERSION
        language = args.language or settings['desktop'].get('language', 'tr')
        settings['desktop']['language'] = language
        settings['freeAudio']['legacy_migrated'] = True
        if not settings['desktop'].get('update_repository'):
            settings['freeAudio']['auto_check_updates'] = False
        frame = DesktopFrame(None, title='freeAudio Desktop')
        translate, notifications = install(ROOT, settings, frame, language)
        sys.path.insert(0, str(ROOT / 'vendor'))
        import freeAudio
        from freeAudio.radioDialog import RadioDialog
        RadioDialog._open_help = lambda self: frame.help(None)
        import globalPluginHandler
        # Replace host-specific actions; playback/content modules remain upstream.
        freeAudio.GlobalPlugin._build_tools_menu = lambda self: None
        freeAudio.GlobalPlugin._check_for_updates = lambda self, silent=False: frame.check_updates(silent)
        freeAudio._cleanup_orphaned_timeshift_buffers = lambda: None
        from desktop.playback import PlaybackGate, install_playback_gate
        frame._playback_gate = PlaybackGate()
        install_playback_gate(freeAudio.GlobalPlugin, frame._playback_gate)
        freeAudio.GlobalPlugin._stop_from_dialog = lambda self: frame.stop_playback()
        original_stop = freeAudio.GlobalPlugin.script_stop
        def desktop_stop(self, gesture):
            frame.stop_playback()
        desktop_stop.__dict__.update(original_stop.__dict__)
        desktop_stop.__doc__ = original_stop.__doc__
        freeAudio.GlobalPlugin.script_stop = desktop_stop
        plugin = freeAudio.GlobalPlugin()
        globalPluginHandler.runningPlugins.append(plugin)
        frame.build(plugin, settings, translate, notifications)
        if backup_warning:
            wx.CallAfter(notifications.message, translate('The automatic backup could not be created. Your existing profile was not changed.'))
        app.SetTopWindow(frame)
        frame.Show()
        if settings['freeAudio'].get('resume_on_start') and settings['freeAudio'].get('last_station_url'):
            wx.CallAfter(frame._stop_button.SetFocus)
        exit_code = 0
        if args.smoke_test:
            def smoke_checks():
                if frame._stop_button.GetLabel() != translate('&Stop playback (F8)'):
                    raise RuntimeError('Main stop button label regression')
                plugin._open_dialog()
                if plugin._dialog._stop_btn.GetLabel() != translate('&Stop playback (F8)'):
                    raise RuntimeError('Library stop button label regression')
                from freeAudio.settingsPanel import freeAudioSettingsPanel
                settings_dialog = SettingsDialog(frame, freeAudioSettingsPanel, settings, translate)
                panel = settings_dialog.panel
                if panel._resume.GetLabel() != translate('&Resume last media when the application starts'):
                    raise RuntimeError('Desktop resume label regression')
                if panel._track_change_voice.GetString(0) != translate('Screen reader'):
                    raise RuntimeError('Desktop voice label regression')
                if plugin.script_openDialog.__doc__ != plugin.script_openDialog.description:
                    raise RuntimeError('Localized command descriptions must be preserved')
                if not settings['desktop'].get('update_repository') and panel._auto_check_updates.IsShown():
                    raise RuntimeError('Unconfigured update controls must be hidden')
                resume_label = panel._resume.GetLabel()
                braille_label = panel._braille_messages.GetLabel()
                settings_dialog.Destroy()
                import wave
                import time
                wave_path = directory / 'smoke-silence.wav'
                with wave.open(str(wave_path), 'wb') as sound:
                    sound.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                    sound.writeframes(b'\0\0' * 16000 * 5)
                audio_ok = None  # CI runners may have no audio output device.
                if os.environ.get('FREEAUDIO_SKIP_AUDIO_DEVICE_TEST') != '1':
                    engine = freeAudio.radioPlayer._BassEngine(str(Path(freeAudio.__file__).parent))
                    try:
                        if not engine.load():
                            raise RuntimeError('Packaged BASS host failed: ' + str(engine.get_stderr_tail()))
                        if not engine.play(str(wave_path.resolve()), volume_0_1=0, seekable=True):
                            raise RuntimeError('Packaged audio playback failed')
                        time.sleep(.1)
                        audio_ok, position, length = engine.timeshift_seek(2)
                        if not audio_ok or length < 4.9:
                            raise RuntimeError('Packaged audio seek failed')
                    finally:
                        engine.unload()
                (directory / 'smoke-test.json').write_text(json.dumps({
                    'version': VERSION, 'language': language,
                    'tabs': plugin._dialog._notebook.GetPageCount(),
                    'commands': len(frame.shortcuts.commands),
                    'shortcut_failures': frame.shortcuts.failures,
                    'audio_devices': plugin._player.get_audio_devices(),
                    'engine_module_path': freeAudio.__file__,
                    'local_audio_play_and_seek': audio_ok,
                    'screen_reader_bridges': [type(item).__name__ for item in notifications.outputs],
                    'resume_label': resume_label,
                    'braille_label': braille_label,
                }, ensure_ascii=False, indent=2), encoding='utf-8')
                frame.Close()
            def smoke():
                nonlocal exit_code
                try:
                    smoke_checks()
                except Exception:
                    exit_code = 1
                    details = traceback.format_exc()
                    (directory / 'smoke-error.txt').write_text(details, encoding='utf-8')
                    print(details, file=sys.stderr)
                    frame.Close()
            wx.CallLater(1000, smoke)
        app.MainLoop()
        return exit_code
    except Exception:
        details = traceback.format_exc()
        logging.exception('Application startup failed')
        (directory / 'startup-error.txt').write_text(details, encoding='utf-8')
        if args.smoke_test:
            print(details, file=sys.stderr)
        else:
            wx.MessageBox('freeAudio Desktop\n' + details, 'Startup error / Başlatma hatası', wx.OK | wx.ICON_ERROR)
        if frame:
            frame.Destroy()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
