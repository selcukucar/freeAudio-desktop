from pathlib import Path
import unittest
from unittest.mock import patch
import wx
from desktop.standard_translation import configure_standard_translation, LocalizedMessageDialog, localized_message_box

ROOT=Path(__file__).resolve().parents[1]


def plain(label):return label.replace('&','')


class StandardTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owns_app=wx.GetApp() is None
        cls.app=wx.GetApp() or wx.App(False)

    @classmethod
    def tearDownClass(cls):
        configure_standard_translation(ROOT,'en')
        if cls.owns_app:cls.app.Destroy()

    def test_stock_and_text_choice_buttons_follow_app_language_including_switch_back(self):
        for language,ok,cancel in (('tr','Tamam','İptal'),('en','OK','Cancel'),('tr','Tamam','İptal')):
            with self.subTest(language=language):
                configure_standard_translation(ROOT,language)
                self.assertEqual(plain(wx.GetStockLabel(wx.ID_OK)),ok)
                self.assertEqual(plain(wx.GetStockLabel(wx.ID_CANCEL)),cancel)
                dialogs=[wx.TextEntryDialog(None,'Name','Title'),wx.SingleChoiceDialog(None,'Select','Title',['One'])]
                try:
                    for dialog in dialogs:
                        self.assertEqual(plain(dialog.FindWindow(wx.ID_OK).GetLabel()),ok)
                        self.assertEqual(plain(dialog.FindWindow(wx.ID_CANCEL).GetLabel()),cancel)
                finally:
                    for dialog in dialogs:dialog.Destroy()
                    self.app.ProcessPendingEvents()

    def test_settings_style_buttons_and_native_confirmation_labels_use_turkish(self):
        configure_standard_translation(ROOT,'tr')
        dialog=wx.Dialog(None)
        confirmation=LocalizedMessageDialog(None,'Test','Title',wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT)
        try:
            dialog.CreateButtonSizer(wx.OK|wx.CANCEL)
            self.assertEqual(plain(dialog.FindWindow(wx.ID_OK).GetLabel()),'Tamam')
            self.assertEqual(plain(dialog.FindWindow(wx.ID_CANCEL).GetLabel()),'İptal')
            self.assertEqual(plain(confirmation.GetYesLabel()),'Evet')
            self.assertEqual(plain(confirmation.GetNoLabel()),'Hayır')
            self.assertEqual(plain(confirmation.GetCancelLabel()),'İptal')
            self.assertTrue(confirmation.GetMessageDialogStyle() & wx.NO_DEFAULT)
        finally:
            dialog.Destroy();confirmation.Destroy();self.app.ProcessPendingEvents()

    def test_messagebox_result_constants_are_preserved_without_showing_a_confirmation(self):
        configure_standard_translation(ROOT,'tr')
        for result,expected in ((wx.ID_OK,wx.OK),(wx.ID_CANCEL,wx.CANCEL),(wx.ID_YES,wx.YES),(wx.ID_NO,wx.NO)):
            with patch.object(LocalizedMessageDialog,'ShowModal',return_value=result):
                self.assertEqual(localized_message_box('Test','Test',wx.YES_NO|wx.CANCEL),expected)
        with LocalizedMessageDialog(None,'Test','Title',wx.OK|wx.CANCEL) as dialog:
            self.assertEqual(plain(dialog.GetOKLabel()),'Tamam')
            self.assertEqual(plain(dialog.GetCancelLabel()),'İptal')


if __name__=='__main__':unittest.main()
