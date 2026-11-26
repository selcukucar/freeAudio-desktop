"""Localize wx stock buttons independently of the Windows display language."""
from pathlib import Path
import wx


class LocalizedMessageDialog(wx.MessageDialog):
    """Give native confirmation buttons explicit application-language labels."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        style=self.GetMessageDialogStyle()
        label=wx.GetStockLabel
        if style & wx.YES_NO:
            if style & wx.CANCEL:
                self.SetYesNoCancelLabels(label(wx.ID_YES),label(wx.ID_NO),label(wx.ID_CANCEL))
            else:
                self.SetYesNoLabels(label(wx.ID_YES),label(wx.ID_NO))
        elif style & wx.CANCEL:
            self.SetOKCancelLabels(label(wx.ID_OK),label(wx.ID_CANCEL))
        else:
            self.SetOKLabel(label(wx.ID_OK))
        if style & wx.HELP:self.SetHelpLabel(label(wx.ID_HELP))


def localized_message_box(message,caption='Message',style=wx.OK|wx.CENTRE,parent=None,x=-1,y=-1):
    with LocalizedMessageDialog(parent,message,caption,style,pos=(x,y)) as dialog:
        result=dialog.ShowModal()
    return {wx.ID_OK:wx.OK,wx.ID_CANCEL:wx.CANCEL,wx.ID_YES:wx.YES,
            wx.ID_NO:wx.NO,wx.ID_HELP:wx.HELP}.get(result,wx.CANCEL)


def configure_standard_translation(root, language):
    translations = wx.Translations()
    translations.SetLanguage(language)
    wx.FileTranslationsLoader.AddCatalogLookupPathPrefix(str(Path(root)/'locale'))
    if not translations.AddCatalog('wxstd') and language == 'tr':
        raise RuntimeError('The Turkish standard-control translation is missing.')
    # wx owns this object until it is replaced or the application exits.
    wx.Translations.Set(translations)
