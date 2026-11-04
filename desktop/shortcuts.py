"""Windows global hotkeys and an independent command catalogue."""
import logging
from types import SimpleNamespace
import wx
from .host import invoke


def desktop_defaults(defaults):
    """Avoid Windows shortcuts and the original NVDA add-on's bindings."""
    result = {}
    special = {
        'addBookmark': 'control+alt+shift+b',
        'playbackRateUp': 'control+alt+shift+f8',
        'playbackRateDown': 'control+alt+shift+f7',
        'transposeUp': 'control+shift+f8',
        'transposeDown': 'control+shift+f7',
        'timeshiftRewindFine': 'control+alt+shift+f9',
        'timeshiftForwardFine': 'control+alt+shift+f10',
        'navPrevGroup': 'control+alt+shift+f5',
        'navNextGroup': 'control+alt+shift+f6',
        'toggleObligato': 'control+alt+shift+a',
    }
    for name, gesture in defaults.items():
        result[name] = special.get(name, 'control+alt+shift+' + gesture.split('+')[-1])
    return result


def parse_hotkey(value):
    tokens = [token.strip() for token in value.lower().strip().removeprefix('kb:').split('+')]
    modifiers = 0
    flags = {'control': wx.MOD_CONTROL, 'ctrl': wx.MOD_CONTROL,
             'alt': wx.MOD_ALT, 'shift': wx.MOD_SHIFT, 'windows': wx.MOD_WIN, 'win': wx.MOD_WIN}
    for token in tokens[:-1]:
        if token not in flags:
            raise ValueError('Unknown modifier: ' + token)
        modifiers |= flags[token]
    key = tokens[-1]
    # RegisterHotKey takes Win32 virtual-key codes, not wx key-event codes.
    names = {'leftarrow': 0x25, 'rightarrow': 0x27,
             'uparrow': 0x26, 'downarrow': 0x28,
             'space': 0x20, 'enter': 0x0D}
    if key in names:
        code = names[key]
    elif key.startswith('f') and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        code = 0x70 + int(key[1:]) - 1
    elif len(key) == 1 and key.isascii() and key.isalnum():
        code = ord(key.upper())
    else:
        raise ValueError('Unknown key: ' + key)
    if not modifiers:
        raise ValueError('A global shortcut needs a modifier (control, alt, shift, windows).')
    if code == 0x7B:
        raise ValueError('F12 is reserved by Windows. Choose another key.')
    return modifiers, code


class Shortcuts:
    def __init__(self, frame, plugin, settings, notify):
        self.frame, self.plugin, self.settings, self.notify = frame, plugin, settings, notify
        self.registered = {}
        self.failures = []
        self.commands = {}
        defaults = {}
        for cls in reversed(type(plugin).__mro__):
            defaults.update(getattr(cls, '_' + cls.__name__ + '__gestures', {}))
        for name in dir(plugin):
            if not name.startswith('script_'):
                continue
            command = getattr(plugin, name)
            if not callable(command):
                continue
            label = (command.__doc__ or name[7:]).strip().splitlines()[0]
            self.commands[name[7:]] = (label, command)
            if getattr(command, 'gesture', None):
                defaults[command.gesture] = name[7:]
        self.defaults = desktop_defaults({name: gesture for gesture, name in defaults.items()})
        frame.Bind(wx.EVT_HOTKEY, self.on_hotkey)
        self.register()

    def register(self):
        self.close()
        self.failures = []
        overrides = self.settings['desktop'].get('shortcuts', {})
        self.effective = {}
        used = set()
        for command_index, (name, (_, command)) in enumerate(self.commands.items()):
            value = overrides.get(name, self.defaults.get(name, ''))
            self.effective[name] = value
            if not value:
                continue
            try:
                modifiers, key = parse_hotkey(value)
                if (modifiers, key) in used:
                    raise ValueError('Duplicate shortcut: ' + value)
                # RegisterHotKey requires an application ID in 0x0000..0xBFFF;
                # wx.NewIdRef returns negative IDs on Windows.
                hotkey_id = 0x4000 + command_index
                if not self.frame.RegisterHotKey(hotkey_id, modifiers, key):
                    raise ValueError('Windows could not register shortcut: ' + value)
                used.add((modifiers, key))
                self.registered[hotkey_id] = (name, command, value)
            except ValueError as error:
                self.failures.append(f'{name}: {error}')
                logging.warning('%s', self.failures[-1])

    def close(self):
        for hotkey_id in self.registered:
            self.frame.UnregisterHotKey(hotkey_id)
        self.registered.clear()

    def on_hotkey(self, event):
        item = self.registered.get(event.GetId())
        if item:
            self.execute(item[0])

    def execute(self, name):
        command = self.commands[name][1]
        # A Windows hotkey is consumed by RegisterHotKey. The upstream's
        # no-media pass-through branches are harmless no-ops in this host.
        invoke(command, SimpleNamespace(send=lambda: None))

    def refresh_catalog(self):
        commands = {}
        for name in dir(self.plugin):
            if name.startswith('script_'):
                command = getattr(self.plugin, name)
                if callable(command):
                    label = (command.__doc__ or name[7:]).strip().splitlines()[0]
                    commands[name[7:]] = (label, command)
        if commands != self.commands:
            self.commands = commands
            self.register()

    def show(self, parent, translate):
        self.refresh_catalog()
        _ = translate
        dialog = wx.Dialog(parent, title=_('Commands and shortcuts'), size=(820, 580),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        def entries():
            active = {item[0] for item in self.registered.values()}
            return [label + ' — ' + (self.effective.get(name) or _('No shortcut')) +
                    (' — ' + _('Unavailable') if self.effective.get(name) and name not in active else '')
                    for name, (label, fn) in self.commands.items()]
        listing = wx.ListBox(dialog, choices=entries())
        listing.SetName(_('Commands'))
        sizer.Add(listing, 1, wx.EXPAND | wx.ALL, 8)
        label = wx.StaticText(dialog, label=_('Global shortcut (for example control+alt+shift+r; empty disables):'))
        field = wx.TextCtrl(dialog)
        field.SetName(label.GetLabel())
        sizer.Add(label, 0, wx.ALL, 8)
        sizer.Add(field, 0, wx.EXPAND | wx.ALL, 8)
        status = wx.TextCtrl(dialog, value='\n'.join(self.failures), style=wx.TE_MULTILINE | wx.TE_READONLY)
        status.SetName(_('Unavailable shortcuts'))
        sizer.Add(status, 0, wx.EXPAND | wx.ALL, 8)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        run = wx.Button(dialog, label=_('&Run command'))
        save = wx.Button(dialog, label=_('&Save shortcut'))
        reset = wx.Button(dialog, label=_('Use &default shortcut'))
        close = wx.Button(dialog, wx.ID_CANCEL, _('&Close'))
        for button in (run, save, reset, close):
            buttons.Add(button, 0, wx.ALL, 8)
        sizer.Add(buttons)
        dialog.SetSizer(sizer)
        names = list(self.commands)
        def select(event=None):
            index = listing.GetSelection()
            if index != wx.NOT_FOUND:
                name = names[index]
                field.SetValue(self.settings['desktop'].get('shortcuts', {}).get(name, self.defaults.get(name, '')))
        def save_shortcut(event):
            if listing.GetSelection() == wx.NOT_FOUND:
                return
            name = names[listing.GetSelection()]
            value = field.GetValue().strip()
            try:
                if value:
                    parsed = parse_hotkey(value)
                    overrides_now = self.settings['desktop'].get('shortcuts', {})
                    for other in names:
                        other_value = overrides_now.get(other, self.defaults.get(other, ''))
                        if other != name and other_value and parse_hotkey(other_value) == parsed:
                            raise ValueError(_('This shortcut is assigned to another command.'))
            except ValueError as error:
                wx.MessageBox(str(error), _('Error'), wx.OK | wx.ICON_ERROR, dialog)
                return
            overrides = self.settings['desktop'].setdefault('shortcuts', {})
            previous = overrides.get(name)
            overrides[name] = value
            self.register()
            if any(failure.startswith(name + ':') for failure in self.failures):
                if previous is None:
                    overrides.pop(name)
                else:
                    overrides[name] = previous
                message = '\n'.join(self.failures)
                self.register()
                wx.MessageBox(message, _('Error'), wx.OK | wx.ICON_ERROR, dialog)
                return
            try:
                self.settings.save()
            except (OSError, ValueError):
                if previous is None:
                    overrides.pop(name, None)
                else:
                    overrides[name] = previous
                self.register()
                status.SetValue('\n'.join(self.failures))
                wx.MessageBox(_('Settings could not be saved. Check that the profile folder is writable.'),
                              _('Error'), wx.OK | wx.ICON_ERROR, dialog)
                return
            status.SetValue('\n'.join(self.failures))
            selected = listing.GetSelection()
            listing.Set(entries())
            listing.SetSelection(selected)
            self.notify(_('Shortcut saved.'))
        def reset_shortcut(event):
            index = listing.GetSelection()
            if index != wx.NOT_FOUND:
                field.SetValue(self.defaults.get(names[index], ''))
                save_shortcut(event)
        listing.Bind(wx.EVT_LISTBOX, select)
        run.Bind(wx.EVT_BUTTON, lambda event: self.execute(names[listing.GetSelection()]))
        save.Bind(wx.EVT_BUTTON, save_shortcut)
        reset.Bind(wx.EVT_BUTTON, reset_shortcut)
        if names:
            listing.SetSelection(0)
            select()
        else:
            run.Disable()
            save.Disable()
            reset.Disable()
        dialog.ShowModal()
        dialog.Destroy()
