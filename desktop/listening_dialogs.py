"""Accessible continuation list and an explicit, cancellable sleep timer."""
import wx
from .continue_listening import continuation_items, time_label
from .sleep_timer import media_identity


class ContinueDialog(wx.Dialog):
    def __init__(self, parent):
        self.frame, self._ = parent, parent.translate
        _ = self._
        super().__init__(parent, title=_('Continue listening'), size=(740, 500),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(wx.StaticText(self, label=_('Unfinished podcasts and audio books')), 0, wx.ALL, 12)
        self.list = wx.ListBox(self)
        self.list.SetName(_('Unfinished podcasts and audio books'))
        outer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        outer.Add(wx.StaticText(self, label=_('Saved listening position')), 0, wx.LEFT | wx.TOP, 12)
        self.details = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 75))
        self.details.SetName(_('Saved listening position'))
        outer.Add(self.details, 0, wx.EXPAND | wx.ALL, 12)
        row = wx.WrapSizer(wx.HORIZONTAL, flags=wx.REMOVE_LEADING_SPACES)
        self.play = wx.Button(self, label=_('&Continue selected media'))
        self.play.Bind(wx.EVT_BUTTON, self.on_play)
        refresh = wx.Button(self, label=_('&Refresh positions'))
        refresh.Bind(wx.EVT_BUTTON, lambda event: self.refresh())
        close = wx.Button(self, wx.ID_CLOSE, _('&Close'))
        close.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        for button in (self.play, refresh, close): row.Add(button, 0, wx.ALL, 8)
        outer.Add(row, 0, wx.EXPAND | wx.ALL, 4)
        self.SetSizer(outer)
        self.rows = []
        self.list.Bind(wx.EVT_LISTBOX, lambda event: self.show_details())
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_play)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetEscapeId(wx.ID_CLOSE)
        self.refresh()

    def refresh(self):
        selected = self.list.GetSelection()
        identity = media_identity(self.rows[selected]['station']) if 0 <= selected < len(self.rows) else None
        try:
            self.rows = continuation_items(self.frame.listening_history, self.frame.plugin._player, self.frame.downloads)
            self.list.Set([x['station'].get('name', '') + ' — ' + time_label(x['position']) for x in self.rows])
            if self.rows:
                index = next((i for i,x in enumerate(self.rows) if media_identity(x['station']) == identity), max(0,min(selected,len(self.rows)-1)))
                self.list.SetSelection(index)
            self.show_details()
        except Exception as error:
            self.frame.notifications.message(self._('Operation failed: %s') % str(error))

    def show_details(self):
        index = self.list.GetSelection()
        item = self.rows[index] if 0 <= index < len(self.rows) else None
        self.play.Enable(bool(item and item['available']))
        text = self._('No unfinished media yet. Listen to a podcast or audio book first.')
        if item:
            text = item['station'].get('name', '') + '\n' + self._('Saved position: %s') % time_label(item['position'])
            if not item['available']: text += '\n' + self._('This media is unavailable. Check the file or library.')
        self.details.ChangeValue(text)

    def on_play(self, event):
        index = self.list.GetSelection()
        if 0 <= index < len(self.rows) and self.rows[index]['available']:
            self.frame.play_history(self.rows[index]['station'])

    def on_key(self, event):
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers() and wx.Window.FindFocus() == self.list:
            self.on_play(event)
        else: self.frame.playback_key(event)

    def on_close(self, event):
        self.frame._continue_window = None
        self.Destroy()


class SleepDialog(wx.Dialog):
    def __init__(self, parent):
        self.frame, self._ = parent, parent.translate
        _ = self._
        super().__init__(parent, title=_('Sleep timer'), size=(650, 550),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(wx.StaticText(self, label=_('When')), 0, wx.ALL, 12)
        self.mode = wx.Choice(self, choices=[_('After a duration'), _('At the end of this episode / chapter')])
        self.mode.SetName(_('When')); self.mode.SetSelection(0)
        outer.Add(self.mode, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        outer.Add(wx.StaticText(self, label=_('Minutes (1–480)')), 0, wx.LEFT | wx.TOP, 12)
        self.minutes = wx.SpinCtrl(self, min=1, max=480, initial=30)
        self.minutes.SetName(_('Minutes (1–480)'))
        outer.Add(self.minutes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        presets = wx.WrapSizer(wx.HORIZONTAL, flags=wx.REMOVE_LEADING_SPACES)
        for number in (15, 30, 60):
            button = wx.Button(self, label=_('%d minutes') % number)
            button.Bind(wx.EVT_BUTTON, lambda event, value=number: self.preset(value))
            presets.Add(button, 0, wx.ALL, 4)
        outer.Add(presets, 0, wx.ALL, 8)
        outer.Add(wx.StaticText(self, label=_('Action')), 0, wx.LEFT, 12)
        self.action = wx.Choice(self, choices=[_('Stop playback'), _('Shut down the computer')])
        self.action.SetName(_('Action')); self.action.SetSelection(0)
        outer.Add(self.action, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        help_text = wx.StaticText(self, label=_('Recordings and downloads continue when playback stops. Computer shutdown has a 60-second cancellation warning and is blocked by active recordings or downloads. Other applications are never force-closed.'))
        help_text.Wrap(590)
        outer.Add(help_text, 0, wx.EXPAND | wx.ALL, 12)
        outer.Add(wx.StaticText(self, label=_('Timer status')), 0, wx.LEFT, 12)
        self.status = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.status.SetName(_('Timer status'))
        outer.Add(self.status, 0, wx.EXPAND | wx.ALL, 12)
        row = wx.WrapSizer(wx.HORIZONTAL, flags=wx.REMOVE_LEADING_SPACES)
        start = wx.Button(self, label=_('&Set timer'))
        start.Bind(wx.EVT_BUTTON, self.arm)
        self.cancel = wx.Button(self, label=_('&Cancel timer'))
        self.cancel.Bind(wx.EVT_BUTTON, lambda event: parent.cancel_sleep())
        close = wx.Button(self, wx.ID_CLOSE, _('&Close'))
        close.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        for button in (start, self.cancel, close): row.Add(button, 0, wx.ALL, 6)
        outer.Add(row, 0, wx.EXPAND | wx.ALL, 6)
        self.SetSizer(outer)
        self.SetEscapeId(wx.ID_CLOSE)
        self.mode.Bind(wx.EVT_CHOICE, lambda event: self.minutes.Enable(self.mode.GetSelection() == 0))
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.refresh(), self.timer)
        self.timer.Start(1000)
        self.refresh()

    def preset(self, minutes):
        self.mode.SetSelection(0); self.minutes.Enable(True); self.minutes.SetValue(minutes)

    def arm(self, event):
        station = self.frame.plugin._player.get_current_station() or {}
        end = self.mode.GetSelection() == 1
        action = 'shutdown' if self.action.GetSelection() == 1 else 'stop'
        try:
            if end and (not self.frame.plugin._player.has_media() or station.get('media_kind') not in ('podcast','audiobook')):
                raise ValueError('Play a podcast episode or audio book chapter first.')
            if action == 'shutdown' and self.frame.has_background_jobs():
                raise ValueError('Computer shutdown is blocked by active recordings or downloads.')
            self.frame.sleep_timer.arm(minutes=None if end else self.minutes.GetValue(),
                                       target=media_identity(station) if end else None, action=action)
            self.frame._power_pending_since = None
            self.frame.notifications.message(self._('Sleep timer set.'))
            self.refresh()
        except Exception as error:
            self.frame.notifications.message(self._(str(error)))

    def refresh(self):
        text = self.frame.sleep_status()
        if text != self.status.GetValue(): self.status.ChangeValue(text)
        self.cancel.Enable(self.frame.sleep_timer.mode is not None or self.frame._power_pending_since is not None)

    def on_close(self, event):
        self.timer.Stop()
        self.frame._sleep_window = None
        self.Destroy()
