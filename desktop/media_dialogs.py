"""Native keyboard-accessible download and listening-history windows."""
import os
from pathlib import Path
from datetime import datetime
import wx


STATES = {'queued': 'Queued', 'downloading': 'Downloading', 'completed': 'Downloaded',
          'cancelled': 'Cancelled', 'failed': 'Failed'}


def playback_station(item, manager):
    path = manager.resolve_path(item)
    if item['state'] != 'completed' or not path.is_file():
        raise ValueError('The downloaded file is not available')
    return {'url': str(path), 'name': item['title'], 'tags': 'podcast', 'media_kind': 'podcast',
            'podcast_resume_key': item['url']}


class DownloadsDialog(wx.Dialog):
    def __init__(self, parent):
        self.frame, self.manager, self._ = parent, parent.downloads, parent.translate
        _ = self._
        super().__init__(parent, title=_('Downloads and offline podcasts'), size=(760, 650),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(wx.StaticText(self, label=_('Show')), 0, wx.LEFT | wx.TOP, 12)
        self.filter = wx.Choice(self, choices=[_('All downloads'), _('Downloaded episodes')])
        self.filter.SetName(_('Show'))
        self.filter.SetSelection(0)
        outer.Add(self.filter, 0, wx.EXPAND | wx.ALL, 12)
        outer.Add(wx.StaticText(self, label=_('Podcast downloads')), 0, wx.LEFT, 12)
        self.list = wx.ListBox(self)
        self.list.SetName(_('Podcast downloads'))
        outer.Add(self.list, 1, wx.EXPAND | wx.ALL, 12)
        outer.Add(wx.StaticText(self, label=_('Download details')), 0, wx.LEFT | wx.RIGHT, 12)
        self.details = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 85))
        self.details.SetName(_('Download details'))
        outer.Add(self.details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        outer.Add(wx.StaticText(self, label=_('Download progress')), 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.progress = wx.Gauge(self, range=100)
        self.progress.SetName(_('Download progress'))
        outer.Add(self.progress, 0, wx.EXPAND | wx.ALL, 12)
        actions = [('&Play downloaded episode', 'play'), ('&Read progress', 'read'),
                   ('&Cancel download', 'cancel'), ('&Retry download', 'retry'),
                   ('Open download &folder', 'folder'), ('Remove from &list', 'remove'),
                   ('&Delete downloaded file', 'delete')]
        row = wx.WrapSizer(wx.HORIZONTAL, flags=wx.REMOVE_LEADING_SPACES)
        self.buttons = {}
        for label, name in actions:
            button = wx.Button(self, label=_(label))
            button.Bind(wx.EVT_BUTTON, lambda event, action=name: self.action(action))
            self.buttons[name] = button
            row.Add(button, 0, wx.ALL, 4)
        outer.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        close = wx.Button(self, wx.ID_CLOSE, _('&Close'))
        close.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        outer.Add(close, 0, wx.ALIGN_RIGHT | wx.ALL, 12)
        self.SetSizer(outer)
        self.SetMinSize((600, 480))
        self.rows = []
        self.list.Bind(wx.EVT_LISTBOX, lambda event: self.refresh_details())
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, lambda event: self.action('play'))
        self.filter.Bind(wx.EVT_CHOICE, lambda event: self.refresh())
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.SetEscapeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.refresh(), self.timer)
        self.timer.Start(500)
        self.refresh()
        self.list.SetFocus()

    def on_key(self, event):
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers() and wx.Window.FindFocus() == self.list:
            self.action('play')
        else:
            self.frame.playback_key(event)

    def selected(self):
        index = self.list.GetSelection()
        return self.rows[index] if 0 <= index < len(self.rows) else None

    def refresh(self):
        if not self:
            return
        selected = self.selected()
        index = self.list.GetSelection()
        rows = self.manager.snapshot()
        if self.filter.GetSelection() == 1:
            rows = [x for x in rows if x['state'] == 'completed']
        labels = [x['title'] + ' — ' + self._(STATES.get(x['state'], 'Failed')) for x in rows]
        if [x['id'] for x in rows] != [x['id'] for x in self.rows]:
            self.list.Set(labels)
            if rows:
                new_index = next((i for i, x in enumerate(rows) if selected and x['id'] == selected['id']), max(0, min(index, len(rows)-1)))
                self.list.SetSelection(new_index)
        else:
            for i, label in enumerate(labels):
                if self.list.GetString(i) != label:
                    self.list.SetString(i, label)
        self.rows = rows
        self.refresh_details()

    def refresh_details(self):
        item = self.selected()
        active = item is not None and item['state'] in self.manager.ACTIVE
        complete = item is not None and item['state'] == 'completed'
        available = complete and self.manager.resolve_path(item).is_file()
        for name, enable in {'play': available, 'read': item is not None, 'cancel': active,
                             'retry': item is not None and not active and not available,
                             'remove': item is not None and not active, 'delete': available,
                             'folder': item is not None and self.manager.resolve_path(item).parent.is_dir()}.items():
            self.buttons[name].Enable(enable)
        text = ''
        percent = 0
        if item:
            total, received = item.get('total'), item.get('received', 0)
            percent = min(100, int(received * 100 / total)) if total and total > 0 else 0
            if complete:
                percent = 100
            amount = self._('%s of %s MB') % (f'{received/1048576:.1f}', f'{total/1048576:.1f}') if total else self._('%s MB downloaded; total size unknown') % f'{received/1048576:.1f}'
            text = '\n'.join((item['title'], self._(STATES.get(item['state'], 'Failed')), amount,
                              str(self.manager.resolve_path(item)), item.get('error', ''))).strip()
            if complete and not available:
                text += '\n' + self._('The downloaded file is not available')
        if self.details.GetValue() != text:
            self.details.ChangeValue(text)
        self.progress.SetValue(percent)

    def action(self, action):
        item = self.selected()
        if not item:
            return
        _ = self._
        try:
            if action == 'play':
                self.frame.plugin._play_station(playback_station(item, self.manager))
            elif action == 'read':
                self.refresh_details()
                self.frame.notifications.message(self.details.GetValue())
            elif action == 'cancel':
                self.manager.cancel(item['id'])
                self.frame.notifications.message(_('Cancelling download...'))
            elif action == 'retry':
                self.manager.retry(item['id'])
                self.frame.notifications.message(_('Download queued'))
            elif action == 'folder':
                os.startfile(str(self.manager.resolve_path(item).parent))
            elif action == 'remove':
                self.manager.remove(item['id'])
            elif action == 'delete':
                path = self.manager.resolve_path(item)
                if wx.MessageBox(_('Delete this downloaded file?\n%s') % path, _('Delete downloaded file'),
                                 wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) == wx.YES:
                    self.manager.remove(item['id'], delete_file=True)
            self.refresh()
        except Exception as error:
            self.frame.notifications.message(_('Operation failed: %s') % str(error))

    def on_close(self, event):
        self.timer.Stop()
        self.frame._downloads_window = None
        self.Destroy()


class HistoryDialog(wx.Dialog):
    def __init__(self, parent):
        self.frame, self._ = parent, parent.translate
        _ = self._
        super().__init__(parent, title=_('Listening history'), size=(700, 480),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(wx.StaticText(self, label=_('Recently played media')), 0, wx.ALL, 12)
        self.list = wx.ListBox(self)
        self.list.SetName(_('Recently played media'))
        outer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        self.rows = []
        row = wx.BoxSizer(wx.HORIZONTAL)
        self.play = wx.Button(self, label=_('&Play selected media'))
        self.play.Enable(False)
        self.play.Bind(wx.EVT_BUTTON, self.on_play)
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_play)
        clear = wx.Button(self, label=_('Clear listening &history'))
        clear.Bind(wx.EVT_BUTTON, self.on_clear)
        close = wx.Button(self, wx.ID_CLOSE, _('&Close'))
        close.Bind(wx.EVT_BUTTON, lambda event: self.Close())
        for button in (self.play, clear, close):
            row.Add(button, 0, wx.ALL, 8)
        outer.Add(row, 0, wx.ALL, 4)
        self.SetSizer(outer)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.SetEscapeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.refresh(), self.timer)
        self.timer.Start(1000)
        self.refresh()
        self.list.SetFocus()

    def on_key(self, event):
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers() and wx.Window.FindFocus() == self.list:
            self.on_play(event)
        else:
            self.frame.playback_key(event)

    def refresh(self):
        rows = self.frame.listening_history.snapshot()
        if rows == self.rows:
            return
        index = self.list.GetSelection()
        selected = self.rows[index]['station'] if 0 <= index < len(self.rows) else None
        self.rows = rows
        labels = []
        for item in rows:
            station = item['station']
            kind = {'podcast': 'Podcast', 'audiobook': 'Audio book', 'jukebox': 'Local music'}.get(station.get('media_kind'), 'Radio')
            labels.append(station.get('name', '') + ' — ' + self._(kind) + ' — ' + datetime.fromtimestamp(item['played']).strftime('%d.%m.%Y %H:%M'))
        self.list.Set(labels)
        if rows:
            self.list.SetSelection(next((i for i,x in enumerate(rows) if x['station'] == selected), max(0,min(index,len(rows)-1))))
        self.play.Enable(bool(rows))

    def on_play(self, event):
        index = self.list.GetSelection()
        if 0 <= index < len(self.rows):
            self.frame.play_history(self.rows[index]['station'])

    def on_clear(self, event):
        if wx.MessageBox(self._('Clear listening history? Saved media files will be kept.'), self._('Listening history'),
                         wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) == wx.YES:
            try:
                self.frame.listening_history.clear()
                self.rows = []
                self.list.Clear()
                self.play.Disable()
            except Exception as error:
                self.frame.notifications.message(self._('Operation failed: %s') % str(error))

    def on_close(self, event):
        self.timer.Stop()
        self.frame._listening_window = None
        self.Destroy()
