"""Native, cancellable download UI; worker threads never access controls."""
import logging
import queue
import threading
import wx
from .updates import find_asset, download_update, DownloadCancelled


class UpdateOptionsDialog(wx.Dialog):
    def __init__(self, parent, repository, version, choices, translate):
        super().__init__(parent,title=translate('Application update'),size=(720,600),style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.translate = translate
        outer=wx.BoxSizer(wx.VERTICAL)
        outer.Add(wx.StaticText(self,label=translate('A new version is available: %s') % version),0,wx.ALL,12)
        outer.Add(wx.StaticText(self,label=translate('Release notes')),0,wx.LEFT|wx.RIGHT,12)
        self.notes=wx.TextCtrl(self,value=translate('Loading release notes...'),style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.notes.SetName(translate('Release notes'))
        outer.Add(self.notes,1,wx.EXPAND|wx.ALL,12)
        outer.Add(wx.StaticText(self,label=translate('Update action')),0,wx.LEFT|wx.RIGHT,12)
        self.actions=wx.Choice(self,choices=choices)
        self.actions.SetName(translate('Update action'));self.actions.SetSelection(0)
        outer.Add(self.actions,0,wx.EXPAND|wx.ALL,12)
        outer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL),0,wx.ALIGN_RIGHT|wx.ALL,12)
        self.SetSizer(outer)
        self.FindWindowById(wx.ID_CANCEL).SetLabel(translate('&Cancel'))
        self.notes.SetFocus()
        def work():
            try:
                from .updates import release_notes
                notes=release_notes(repository,version) or translate('No release notes were provided.')
            except Exception:
                logging.exception('Could not load release notes')
                notes=translate('Release notes could not be loaded. Download options remain available.')
            wx.CallAfter(self.set_notes,notes)
        threading.Thread(target=work,daemon=True,name='desktop-release-notes').start()

    def set_notes(self, text):
        if self: self.notes.ChangeValue(text)

    def GetSelection(self):
        return self.actions.GetSelection()


class UpdateDownloadDialog(wx.Dialog):
    def __init__(self, parent, repository, version, portable, directory, translate):
        super().__init__(parent, title=translate('Downloading update'), size=(560, 230))
        self.translate = translate
        self.result = None
        self.cancelled = threading.Event()
        self.events = queue.Queue()
        self.progress = (0, 0)
        self._last_percent = -1
        self._finished = False
        self.status = wx.StaticText(self, label=translate('Preparing verified download...'))
        self.gauge = wx.Gauge(self, range=100)
        self.gauge.SetName(translate('Download progress'))
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, translate('&Cancel'))
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.status, 0, wx.EXPAND | wx.ALL, 12)
        layout.Add(self.gauge, 0, wx.EXPAND | wx.ALL, 12)
        layout.Add(self.cancel_button, 0, wx.ALIGN_RIGHT | wx.ALL, 12)
        self.SetSizer(layout)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.cancel)
        self.Bind(wx.EVT_CLOSE, self.cancel)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.poll, self.timer)
        self.timer.Start(100)
        def work():
            try:
                asset = find_asset(repository, version, portable)
                path = download_update(asset, directory, self.cancelled,
                                       lambda done, total: setattr(self, 'progress', (done, total)))
                self.events.put(('done', (asset, path)))
            except DownloadCancelled:
                self.events.put(('cancel', None))
            except Exception:
                logging.exception('Verified update download failed')
                self.events.put(('error', None))
        threading.Thread(target=work, daemon=True, name='desktop-update-download').start()
        self.cancel_button.SetFocus()

    def cancel(self, event):
        if self._finished:
            return
        self.cancelled.set()
        self.status.SetLabel(self.translate('Cancelling download...'))
        self.cancel_button.Disable()
        if isinstance(event, wx.CloseEvent) and event.CanVeto():
            event.Veto()

    def poll(self, event):
        done, total = self.progress
        percent = min(100, int(done * 100 / total)) if total else 0
        if percent != self._last_percent and not self.cancelled.is_set():
            self._last_percent = percent
            self.gauge.SetValue(percent)
            self.status.SetLabel(self.translate('Downloading update: %d%%') % percent)
        try:
            kind, result = self.events.get_nowait()
        except queue.Empty:
            return
        self._finished = True
        self.timer.Stop()
        if kind == 'done' and not self.cancelled.is_set():
            self.result = result
            self.EndModal(wx.ID_OK)
        else:
            if kind == 'error' and not self.cancelled.is_set():
                wx.MessageBox(self.translate('The update could not be downloaded or verified. Please try again later.'),
                              self.translate('Error'), wx.OK | wx.ICON_ERROR, self)
            self.EndModal(wx.ID_CANCEL)
