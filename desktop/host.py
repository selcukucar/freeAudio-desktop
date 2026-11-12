"""Explicit adapters for services previously supplied by NVDA.

The upstream modules stay separate from this host, making upstream merges possible.
No NVDA installation or NVDA Python process is used.
"""
import gettext
import inspect
import logging
import sys
import time
import types
import threading
from pathlib import Path
from .version import VERSION
import wx
import wx.lib.scrolledpanel


def module(name, **values):
    result = types.ModuleType(name)
    result.__dict__.update(values)
    sys.modules[name] = result
    return result


class AlertAccessible(wx.Accessible):
    def GetName(self, childId):
        return wx.ACC_OK, self.GetWindow().GetLabel()

    def GetRole(self, childId):
        return wx.ACC_OK, wx.ROLE_SYSTEM_ALERT


class CheckListAccessible(wx.Accessible):
    """Expose checklist items as individually named, checkable objects."""
    def GetChildCount(self):
        return wx.ACC_OK, self.GetWindow().GetCount()

    def GetName(self, childId):
        window = self.GetWindow()
        if childId == 0:
            return wx.ACC_OK, window.GetName()
        if 1 <= childId <= window.GetCount():
            return wx.ACC_OK, window.GetString(childId - 1)
        return wx.ACC_NOT_IMPLEMENTED, ''

    def GetRole(self, childId):
        return wx.ACC_OK, wx.ROLE_SYSTEM_LIST if childId == 0 else wx.ROLE_SYSTEM_CHECKBUTTON

    def GetState(self, childId):
        window = self.GetWindow()
        state = wx.ACC_STATE_SYSTEM_FOCUSABLE
        if not window.IsEnabled():
            state |= wx.ACC_STATE_SYSTEM_UNAVAILABLE
        if childId == 0:
            if window.HasFocus():
                state |= wx.ACC_STATE_SYSTEM_FOCUSED
        elif 1 <= childId <= window.GetCount():
            state |= wx.ACC_STATE_SYSTEM_SELECTABLE
            if window.IsChecked(childId - 1):
                state |= wx.ACC_STATE_SYSTEM_CHECKED
            if window.GetSelection() == childId - 1:
                state |= wx.ACC_STATE_SYSTEM_SELECTED
                if window.HasFocus():
                    state |= wx.ACC_STATE_SYSTEM_FOCUSED
        else:
            return wx.ACC_NOT_IMPLEMENTED, 0
        return wx.ACC_OK, state

    def DoDefaultAction(self, childId):
        window = self.GetWindow()
        if not window.IsEnabled() or not 1 <= childId <= window.GetCount():
            return wx.ACC_NOT_SUPPORTED
        window.Check(childId - 1, not window.IsChecked(childId - 1))
        event = wx.CommandEvent(wx.EVT_CHECKLISTBOX.typeId, window.GetId())
        event.SetInt(childId - 1)
        event.SetEventObject(window)
        window.ProcessWindowEvent(event)
        return wx.ACC_OK


class AccessibleCheckListBox(wx.CheckListBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetAccessible(CheckListAccessible(self))
        self.Bind(wx.EVT_CHECKLISTBOX, self.changed)

    def changed(self, event):
        wx.Accessible.NotifyEvent(wx.ACC_EVENT_OBJECT_STATECHANGE, self,
                                  wx.OBJID_CLIENT, event.GetInt() + 1)
        event.Skip()


class Notifications:
    def __init__(self, parent):
        self.control = wx.StaticText(parent, label='')
        self.control.SetName('Notifications')
        self.control.SetAccessible(AlertAccessible(self.control))
        self.history = []
        self.outputs = []
        for name, class_name in [('nvda', 'NVDA'), ('jaws', 'Jaws')]:
            try:
                from importlib import import_module
                output = getattr(import_module('accessible_output2.outputs.' + name), class_name)()
                self.outputs.append(output)
            except Exception:
                logging.debug('Screen reader bridge unavailable: %s', name, exc_info=True)

    def active_output(self):
        for output in self.outputs:
            try:
                if output.is_active():
                    return output
            except Exception:
                logging.debug('Screen reader detection failed', exc_info=True)
        return None

    def braille(self, text):
        if not wx.IsMainThread():
            wx.CallAfter(self.braille, text)
            return
        output = self.active_output()
        if output is not None:
            try:
                output.braille(str(text))
            except Exception:
                logging.debug('Braille notification failed', exc_info=True)

    def message(self, text, **kwargs):
        if not wx.IsMainThread():
            wx.CallAfter(self.message, text)
            return
        if not self.control:
            return
        text = str(text)
        self.history.append(text)
        self.history = self.history[-100:]
        self.control.SetLabel(text)
        if getattr(self, 'on_layout', None) is not None:
            try:
                self.on_layout()
            except Exception:
                logging.exception('Could not lay out notification')
        output = self.active_output()
        delivered = False
        if output is not None:
            try:
                output.speak(text, interrupt=False)
                delivered = True
            except Exception:
                logging.debug('Speech notification failed', exc_info=True)
        if not delivered:
            wx.Accessible.NotifyEvent(wx.ACC_EVENT_SYSTEM_ALERT, self.control,
                                      wx.OBJID_CLIENT, 0)
        logging.info('Notification: %s', text)


class BoxSizerHelper:
    def __init__(self, parent, orientation=wx.VERTICAL, sizer=None):
        self.parent = parent
        self.sizer = sizer if sizer is not None else wx.BoxSizer(orientation)

    def addItem(self, item, flag=wx.EXPAND, **kwargs):
        self.sizer.Add(item, flag=flag | wx.ALL, border=5, **kwargs)
        return item

    def addLabeledControl(self, label, controlClass, **kwargs):
        self.addItem(wx.StaticText(self.parent, label=label))
        control = controlClass(self.parent, **kwargs)
        control.SetName(label.replace('&', '').rstrip(':'))
        self.addItem(control)
        return control


class ButtonHelper:
    def __init__(self, orientation=wx.HORIZONTAL):
        self.sizer = wx.BoxSizer(orientation)

    def addButton(self, parent, **kwargs):
        button = wx.Button(parent, **kwargs)
        self.sizer.Add(button, flag=wx.ALL, border=5)
        return button


class SettingsPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent):
        super().__init__(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.makeSettings(sizer)
        self.SetSizer(sizer)
        self.SetupScrolling(scroll_x=False)

    def postInit(self):
        pass


class SettingsDialog(wx.Dialog):
    categoryClasses = []

    def __init__(self, parent, panelClass, settings, translate):
        super().__init__(parent, title=translate('Settings'), size=(760, 680),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.panel = panelClass(self)
        if not settings['desktop'].get('update_repository'):
            self.panel._auto_check_updates.Hide()
            self.panel._check_now_btn.Hide()
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.panel, 1, wx.EXPAND | wx.ALL, 8)
        outer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(outer)
        self.panel.postInit()
        def save(event):
            try:
                self.panel.onSave()
                settings.save()
            except Exception as error:
                logging.exception('Settings save failed')
                wx.MessageBox(str(error), translate('Error'), wx.OK | wx.ICON_ERROR, self)
                return
            self.EndModal(wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, save, id=wx.ID_OK)


class PluginBase:
    def __init__(self):
        pass

    def terminate(self):
        pass


_repeat = 0
_last_command = None
_last_time = 0


def invoke(command, gesture):
    global _repeat, _last_command, _last_time
    now = time.monotonic()
    _repeat = _repeat + 1 if _last_command == command and now - _last_time < .5 else 0
    _last_command, _last_time = command, now
    try:
        command(gesture)
    except Exception as error:
        logging.exception('Command failed')
        sys.modules['ui'].message(str(error))


def install(root, settings, frame, language):
    translation = gettext.translation('nvda', str(Path(root) / 'locale'),
                                      languages=[language], fallback=True)
    def initTranslation():
        caller = inspect.currentframe().f_back.f_globals
        caller['_'] = translation.gettext
        caller['ngettext'] = translation.ngettext
    module('addonHandler', initTranslation=initTranslation,
           getCodeAddon=lambda: types.SimpleNamespace(path=str(root), manifest={'version': VERSION}))
    module('globalVars', appArgs=types.SimpleNamespace(configPath=str(settings.directory)))
    module('languageHandler', getLanguage=lambda: language)
    module('config', conf=settings)
    notifications = Notifications(frame)
    module('ui', message=notifications.message,
           browseableMessage=lambda text, title='', **kwargs: wx.MessageBox(str(text), title, parent=frame))
    module('braille', handler=types.SimpleNamespace(message=notifications.braille))
    speech_state = types.SimpleNamespace(speechMode=0)
    speech = module('speech', speakMessage=notifications.message,
                    getState=lambda: speech_state, setSpeechMode=lambda mode: setattr(speech_state, 'speechMode', mode),
                    SpeechMode=types.SimpleNamespace(talk=0))
    class CallbackCommand:
        def __init__(self, callback):
            self.callback = callback
    def speak(sequence):
        # Text bookmark playback must wait for speech completion. The NVDA
        # controller interface doesn't expose the in-process NVDA callback queue;
        # use synchronous SAPI speech on a worker instead of signalling too early.
        def worker():
            import comtypes
            comtypes.CoInitialize()
            try:
                from comtypes.client import CreateObject
                voice = CreateObject('SAPI.SpVoice', dynamic=True)
                selected = settings['freeAudio'].get('sapi5_voice_name', '')
                if selected:
                    voices = voice.GetVoices()
                    for index in range(voices.Count):
                        candidate = voices.Item(index)
                        if candidate.GetDescription() == selected:
                            voice.Voice = candidate
                            break
                for item in sequence:
                    if not isinstance(item, CallbackCommand):
                        voice.Speak(str(item), 0)
            except Exception:
                logging.exception('Blocking bookmark speech failed')
                for item in sequence:
                    if not isinstance(item, CallbackCommand):
                        notifications.message(item)
            finally:
                comtypes.CoUninitialize()
                for item in sequence:
                    if isinstance(item, CallbackCommand):
                        item.callback()
        threading.Thread(target=worker, daemon=True, name='bookmark-speech').start()
    speech.speak = speak
    speech.commands = module('speech.commands', CallbackCommand=CallbackCommand)
    module('globalPluginHandler', GlobalPlugin=PluginBase, runningPlugins=[])
    module('inputCore')  # Imported by the upstream dynamic command catalogue, no services used.
    def script(**metadata):
        def decorate(function):
            function.__dict__.update(metadata)
            if metadata.get('description'):
                function.__doc__ = metadata['description']
            return function
        return decorate
    module('scriptHandler', script=script, getLastScriptRepeatCount=lambda: _repeat)
    helper = module('gui.guiHelper', BoxSizerHelper=BoxSizerHelper, ButtonHelper=ButtonHelper,
                    BORDER_FOR_DIALOGS=10)
    controls = module('gui.nvdaControls', CustomCheckListBox=AccessibleCheckListBox)
    dialogs = module('gui.settingsDialogs', SettingsPanel=SettingsPanel)
    module('gui', mainFrame=frame, guiHelper=helper, nvdaControls=controls,
           settingsDialogs=dialogs, NVDASettingsDialog=SettingsDialog,
           messageBox=wx.MessageBox)
    return translation.gettext, notifications
