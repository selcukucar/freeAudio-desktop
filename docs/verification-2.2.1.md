# freeAudio Desktop 2.2.1 verification

Date: 2026-11-26. Windows x64. Packages remain unsigned.

187 local automated tests passed. Three new cases verify Turkish and English stock labels, switching back to Turkish, text-entry/choice/settings-style OK and Cancel buttons, explicitly localized native confirmation labels, preservation of NO_DEFAULT and the MessageBox return constants. Test confirmation dialogs are constructed without showing or answering them. All 2.2.0 playback, recording, continuation, shortcuts, sleep and catalogue tests remain included; real computer shutdown is never performed.

The Turkish wxstd catalog is copied unchanged from wxPython. The host selects translations using the application's language. Native confirmations receive explicit labels, so their buttons also follow the application language. Update Options now finds its Cancel button within its own window instead of a global ID lookup.

Packaged smoke checks assert actual Settings OK/Cancel labels in both languages as well as local BASS playback/seek and eight library tabs. Local and GitHub packaging/upgrade results are recorded separately after the build. Full NVDA/Braille listening and normal-environment global hotkey permission are not claimed as tested.
