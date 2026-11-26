import types
import unittest
from unittest.mock import Mock, patch
import wx

from desktop.shortcuts import Shortcuts, parse_hotkey
from desktop.storage import Settings


class WindowShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owns_app=wx.GetApp() is None
        cls.app=wx.GetApp() or wx.App(False)

    @classmethod
    def tearDownClass(cls):
        if cls.owns_app:cls.app.Destroy()

    def shortcuts(self,overrides=None):
        class Plugin:
            def script_play(self,gesture):pass
        frame=wx.Frame(None)
        action=Mock()
        settings={'desktop':{'shortcuts':overrides or {}}}
        shortcuts=Shortcuts(frame,Plugin(),settings,Mock(),{'windowTest':('Window test','control+shift+d',action)})
        self.addCleanup(frame.Destroy)
        self.addCleanup(shortcuts.close)
        return frame,shortcuts,action,settings

    def test_local_keys_use_native_accelerators_without_registering_global_hotkeys(self):
        with patch.object(wx.Frame,'RegisterHotKey') as global_register:
            frame,shortcuts,action,settings=self.shortcuts()
        global_register.assert_not_called()
        self.assertEqual(shortcuts.failures,[])
        self.assertEqual(shortcuts.command_names(local=True),['windowTest'])
        self.assertEqual(shortcuts.command_names(),['play'])
        hotkey_id=next(iter(shortcuts.local_registered))
        frame.ProcessEvent(wx.CommandEvent(wx.EVT_MENU.typeId,hotkey_id))
        action.assert_called_once_with()

    def test_rebinding_disabling_and_resetting_retains_other_custom_assignments(self):
        frame,shortcuts,action,settings=self.shortcuts({'windowTest':'control+alt+d','play':''})
        self.assertEqual(shortcuts.effective['windowTest'],'control+alt+d')
        settings['desktop']['shortcuts']['windowTest']=''
        shortcuts.register();self.assertEqual(shortcuts.local_registered,{})
        settings['desktop']['shortcuts'].pop('windowTest')
        shortcuts.register()
        self.assertEqual(shortcuts.effective['windowTest'],'control+shift+d')
        self.assertEqual(settings['desktop']['shortcuts']['play'],'')
        self.assertEqual(len(shortcuts.local_registered),1)
        shortcuts.refresh_catalog()
        self.assertIn('windowTest',shortcuts.commands)

    def test_global_conflict_and_invalid_local_key_are_reported_not_silently_registered(self):
        frame,shortcuts,action,settings=self.shortcuts({'play':'control+shift+d'})
        with patch.object(frame,'RegisterHotKey',return_value=True):shortcuts.register()
        self.assertTrue(any('Duplicate shortcut' in failure for failure in shortcuts.failures))
        self.assertFalse(shortcuts.local_registered)
        settings['desktop']['shortcuts'].update(play='',windowTest='windows+d')
        shortcuts.register()
        self.assertFalse(shortcuts.local_registered)
        self.assertTrue(any('Windows-key' in failure for failure in shortcuts.failures))
        with self.assertRaises(ValueError):parse_hotkey({'bad':'data'})


if __name__=='__main__':unittest.main()
