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
        _ = translate
        self.SetTitle('freeAudio Desktop ' + VERSION)
        self.SetSize((700, 440))
        self.shortcuts = Shortcuts(self, plugin, settings, notifications.message)
        panel = wx.Panel(self, style=wx.TAB_TRAVERSAL)
        notifications.control.Reparent(panel)
        outer = wx.BoxSizer(wx.VERTICAL)
        heading = wx.StaticText(panel, label=_('Radio, podcasts, audio books and local music'))
        outer.Add(heading, 0, wx.ALL, 16)
        browser = wx.Button(panel, label=_('&Open library'))
        settings_button = wx.Button(panel, label=_('&Settings'))
        commands = wx.Button(panel, label=_('&Commands and shortcuts'))
        messages = wx.Button(panel, label=_('&Notification history'))
        language = wx.Button(panel, label=_('&Language / Dil'))
        updates = wx.Button(panel, label=_('Check for &updates'))
        help_button = wx.Button(panel, label=_('&Help'))
        backup_button = wx.Button(panel, label=_('Profile &backup and restore'))
        exit_button = wx.Button(panel, label=_('E&xit'))
        for button in (browser, settings_button, commands, messages, language, updates, backup_button, help_button, exit_button):
            outer.Add(button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        outer.Add(notifications.control, 0, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(outer)
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(frame_sizer)
        self.SetMinSize((640, 460))
        self.SetSize((760, 500))
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
        browser.SetFocus()
        if self.shortcuts.failures:
            wx.CallAfter(notifications.message, _('Some shortcuts are unavailable. Open Commands and shortcuts for details.'))
        self._autosave = wx.Timer(self)
        def autosave(event):
            self.persist_settings()
            self.shortcuts.refresh_catalog()
        self.Bind(wx.EVT_TIMER, autosave, self._autosave)
        self._autosave.Start(10000)

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
                if wx.MessageBox(_('A new version is available. Open the download page?') + '\n' + version,
                                 'freeAudio Desktop', wx.YES_NO | wx.ICON_INFORMATION, self) == wx.YES:
                    import webbrowser
                    webbrowser.open(url)
        def work():
            try:
                result = check_release(repository, VERSION)
                wx.CallAfter(finish, result, None)
            except Exception as error:
                logging.exception('Update check failed')
                wx.CallAfter(finish, None, str(error))
        threading.Thread(target=work, daemon=True).start()

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
                event.Veto()
                return
        self._closing = True
        self._autosave.Stop()
        self.shortcuts.close()
        try:
            self.plugin.terminate()
        finally:
            try:
                self.persist_settings()
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
        plugin = freeAudio.GlobalPlugin()
        globalPluginHandler.runningPlugins.append(plugin)
        frame.build(plugin, settings, translate, notifications)
        if backup_warning:
            wx.CallAfter(notifications.message, translate('The automatic backup could not be created. Your existing profile was not changed.'))
        app.SetTopWindow(frame)
        frame.Show()
        exit_code = 0
        if args.smoke_test:
            def smoke_checks():
                plugin._open_dialog()
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
