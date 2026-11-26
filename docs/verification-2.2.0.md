# freeAudio Desktop 2.2.0 verification

Date: 2026-11-26. Windows x64. Packages are unsigned.

184 local automated tests passed, including the real BASS audio-device and HTTP streaming/recording checks. New coverage includes sleep deadlines and cancellation, an entire warning after a missed deadline, end-of-chapter identity, delayed completion callbacks, recording/download guards, failed stop/save and renewed playback during shutdown preparation, native application accelerators and rebinding, podcast feed metadata, listened state, disk usage, disk-full and locked-file cases, catalogue recovery and preservation of unsupported schemas. Native wx controls were checked in Turkish and English.

The Windows shutdown subprocess is mocked in all tests; the computer was never shut down. The optional shutdown action passes no force flag. Interactive inspection used a separate disposable profile with power actions disabled. Ctrl+Shift+T opened Sleep Timer; start/cancel changed its status; Ctrl+Shift+K opened the command editor and Ctrl+Shift+Q exited. Screenshots and accessibility trees showed the new labels and controls. This is not a claim of a complete NVDA/Braille listening session.

The sandbox denied global RegisterHotKey with Windows error 5. The app now reports that error separately from a conflicting shortcut (1409) and offers retry. Application-window shortcuts use native accelerators and worked independently of global-hotkey permission. Global shortcuts still require validation in the normally installed application outside this test environment.

Current public LibriVox and Gutenberg checks returned search results, chapter resolution and 4096 audio bytes. No personal GETEM account was used. Service availability may change.

Packaging, upgrade smoke tests and disposable-runner installer checks are recorded after the build; this source report describes the completed pre-release tests.
