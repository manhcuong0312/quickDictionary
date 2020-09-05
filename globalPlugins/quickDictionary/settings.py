#settings.py
import addonHandler
addonHandler.initTranslation()

import gui
import wx
import config
from . import _addonName, _addonSummary
from .languages import langs


class QuickDictionarySettingsPanel(gui.SettingsPanel):
    # Translators: name of the settings dialog.
    title = _addonSummary

    def __init__(self, parent):
        super(QuickDictionarySettingsPanel, self).__init__(parent)

    def makeSettings(self, sizer):
        # Translators: Help message for a dialog.
        helpLabel = wx.StaticText(self, label=_("Select translation source and target language:"))
        helpLabel.Wrap(self.GetSize()[0])
        sizer.Add(helpLabel)
        fromSizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: A setting in addon settings dialog.
        fromLabel = wx.StaticText(self, label=_("Source language:"))
        fromSizer.Add(fromLabel)
        self._fromChoice = wx.Choice(self, choices=[])
        fromSizer.Add(self._fromChoice)
        intoSizer = wx.BoxSizer(wx.HORIZONTAL)
        # Translators: A setting in addon settings dialog.
        intoLabel = wx.StaticText(self, label=_("Target language:"))
        intoSizer.Add(intoLabel)
        self._intoChoice = wx.Choice(self, choices=[])
        intoSizer.Add(self._intoChoice)
        self.widgetMaker(self._fromChoice, sorted(langs.fromList(), key=lambda l: l.name))
        self._fromChoice.Bind(wx.EVT_CHOICE, self.onSelectFrom)
        self.widgetMaker(self._intoChoice, langs.intoList(config.conf[_addonName]['from']))
        sizer.Add(fromSizer)
        sizer.Add(intoSizer)
        langFrom = self._fromChoice.FindString(langs[config.conf[_addonName]['from']].name)
        langTo = self._intoChoice.FindString(langs[config.conf[_addonName]['into']].name)
        self._fromChoice.Select(langFrom)
        self._intoChoice.Select(langTo)
        # Translators: A setting in addon settings dialog.
        self.copyToClipboardChk = wx.CheckBox(self, label=_("Copy translation result to clipboard"))
        self.copyToClipboardChk.SetValue(config.conf[_addonName]['copytoclip'])
        sizer.Add(self.copyToClipboardChk)
        # Translators: A setting in addon settings dialog.
        self.autoSwapChk = wx.CheckBox(self, label=_("Auto-swap languages"))
        self.autoSwapChk.SetValue(config.conf[_addonName]['autoswap'])
        sizer.Add(self.autoSwapChk)
        # Translators: A setting in addon settings dialog.
        self.useMirrorChk = wx.CheckBox(self, label=_("Use mirror server"))
        self.useMirrorChk.SetValue(config.conf[_addonName]['mirror'])
        sizer.Add(self.useMirrorChk)

    def widgetMaker(self, widget, languages):
        for lang in languages:
            widget.Append(lang.name, lang)

    def onSelectFrom(self, event):
        fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
        self._intoChoice.Clear()
        self.widgetMaker(self._intoChoice, sorted(langs.intoList(fromLang), key=lambda l: l.name))

    def postInit(self):
        self._fromChoice.SetFocus()

    def onSave(self):
        fromLang = self._fromChoice.GetClientData(self._fromChoice.GetSelection()).code
        intoLang = self._intoChoice.GetClientData(self._intoChoice.GetSelection()).code
        config.conf[_addonName]['from'] = fromLang
        config.conf[_addonName]['into'] = intoLang
        config.conf[_addonName]['autoswap'] = self.autoSwapChk.GetValue()
        config.conf[_addonName]['mirror'] = self.useMirrorChk.GetValue()
