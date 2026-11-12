"""Native, theme-aware main view. Content windows and commands stay unchanged."""
from types import SimpleNamespace
import wx
import wx.lib.scrolledpanel


def build_main_view(frame, notifications, translate, volume):
    _ = translate
    panel = wx.lib.scrolledpanel.ScrolledPanel(frame, style=wx.TAB_TRAVERSAL)
    panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
    font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    font.SetPointSize(max(10, font.GetPointSize()))
    panel.SetFont(font)
    outer = wx.BoxSizer(wx.VERTICAL)
    brand = wx.StaticText(panel, label='freeAudio Desktop')
    title_font = wx.Font(font)
    title_font.SetPointSize(max(20, font.GetPointSize() + 8))
    title_font.SetWeight(wx.FONTWEIGHT_BOLD)
    brand.SetFont(title_font)
    outer.Add(brand, 0, wx.LEFT | wx.RIGHT | wx.TOP, 20)
    subtitle_text = _('Radio, podcasts, audio books and local music')
    subtitle = wx.StaticText(panel, label=subtitle_text)
    outer.Add(subtitle, 0, wx.LEFT | wx.RIGHT, 20)
    outer.AddSpacer(12)

    playback = wx.StaticBox(panel, label=_('Playback'))
    playback_sizer = wx.StaticBoxSizer(playback, wx.VERTICAL)
    status = wx.StaticText(playback, label=_('Playback stopped'))
    status_font = wx.Font(font)
    status_font.SetPointSize(font.GetPointSize() + 2)
    status_font.SetWeight(wx.FONTWEIGHT_BOLD)
    status.SetFont(status_font)
    playback_sizer.Add(status, 0, wx.EXPAND | wx.ALL, 12)

    def button(parent, label):
        control = wx.Button(parent, label=label)
        control.SetMinSize((-1, 36))
        return control

    stop = button(playback, _('&Stop playback (F8)'))
    pause = button(playback, _('&Play / pause / resume'))
    transport = wx.FlexGridSizer(cols=2, hgap=12, vgap=10)
    transport.AddGrowableCol(0)
    transport.AddGrowableCol(1)
    for item in (stop, pause): transport.Add(item, 1, wx.EXPAND)
    playback_sizer.Add(transport, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

    volume_row = wx.WrapSizer(wx.HORIZONTAL, flags=wx.REMOVE_LEADING_SPACES)
    down = button(playback, _('Decrease volume (F5)'))
    # The native edit portion takes its accessible name from the preceding label.
    volume_label = wx.StaticText(playback, label=_('Volume (%)'))
    spin = wx.SpinCtrl(playback, min=0, max=200, initial=max(0, min(200, int(volume))),
                       size=(95, -1), style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER)
    spin.SetName(_('Volume (%)'))
    up = button(playback, _('Increase volume (F6)'))
    button_width = max(down.GetBestSize().width, up.GetBestSize().width)
    down.SetMinSize((button_width, 36))
    up.SetMinSize((button_width, 36))
    for item in (down, volume_label, spin, up):
        volume_row.Add(item, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 10)
    playback_sizer.Add(volume_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
    hint_text = _('F5: decrease volume  |  F6: increase volume  |  F8: stop / play')
    hint = wx.StaticText(playback, label=hint_text)
    playback_sizer.Add(hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
    outer.Add(playback_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

    tools = wx.StaticBox(panel, label=_('Library and application'))
    tools_sizer = wx.StaticBoxSizer(tools, wx.VERTICAL)
    browser = button(tools, _('&Open library'))
    tools_sizer.Add(browser, 0, wx.EXPAND | wx.ALL, 12)
    names = [('&Settings', 'settings'), ('&Commands and shortcuts', 'commands'),
             ('&Notification history', 'messages'), ('&Language / Dil', 'language'),
             ('Check for &updates', 'updates'), ('Profile &backup and restore', 'backup'),
             ('&Help', 'help'), ('E&xit', 'exit')]
    controls = {name: button(tools, _(label)) for label, name in names}
    grid = wx.FlexGridSizer(cols=2, hgap=12, vgap=10)
    grid.AddGrowableCol(0)
    grid.AddGrowableCol(1)
    for label, name in names: grid.Add(controls[name], 1, wx.EXPAND)
    tools_sizer.Add(grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
    update_status = wx.StaticText(tools, label='')
    update_status.Hide()
    tools_sizer.Add(update_status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
    outer.Add(tools_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
    notifications.control.Reparent(panel)
    outer.Add(notifications.control, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
    panel.SetSizer(outer)
    panel.SetupScrolling(scroll_x=False)
    frame_sizer = wx.BoxSizer(wx.VERTICAL)
    frame_sizer.Add(panel, 1, wx.EXPAND)
    frame.SetSizer(frame_sizer)
    display_index = wx.Display.GetFromWindow(frame)
    work = wx.Display(max(0, display_index)).GetClientArea()
    frame.SetMinSize((min(640, work.width), min(440, work.height)))
    frame.SetSize((min(820, work.width - 24), min(760, work.height - 24)))
    busy = False

    def relayout(event=None):
        nonlocal busy
        if event is not None: event.Skip()
        if busy or not panel: return
        busy = True
        try:
            width = max(220, panel.GetClientSize().width - 72)
            for row, items in ((transport, (stop, pause)), (grid, tuple(controls.values()))):
                columns = 2 if width >= 2 * max(item.GetBestSize().width for item in items) + 24 else 1
                if columns != row.GetCols():
                    if row.GetCols() == 2: row.RemoveGrowableCol(1)
                    row.SetCols(columns)
                    if columns == 2: row.AddGrowableCol(1)
            for item, raw in ((subtitle, subtitle_text), (hint, hint_text),
                              (status, getattr(frame, '_last_playback_label', None) or status.GetLabel()),
                              (update_status, getattr(frame, '_update_notice_text', None) or update_status.GetLabel()),
                              (notifications.control, notifications.history[-1] if notifications.history else '')):
                item.SetLabel(raw)
                item.Wrap(width)
            panel.Layout()
            panel.FitInside()
        finally:
            busy = False
    panel.Bind(wx.EVT_SIZE, relayout)
    notifications.on_layout = relayout
    wx.CallAfter(relayout)
    return SimpleNamespace(panel=panel, stop=stop, pause=pause, browser=browser,
                           status=status, update_status=update_status, volume=spin,
                           volume_down=down, volume_up=up, relayout=relayout, **controls)
