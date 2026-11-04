# freeAudio Desktop 1.0.1 — recording verification

Date: 2026-11-04. Windows x64.

- 63 automated tests pass locally, including real audio output. New cases exercise actual HTTP recording, failed connections, unwritable destinations, stopping a stalled stream, repeated recordings, menu command availability, pointer selection, nonblocking startup, duplicate clicks, switching playback and shutdown during connection resolution.
- Radio and Favourites expose the same menu through right-click, Applications and Shift+F10. Recording targets the currently playing live station; changing list selection never changes the recording source. Stop remains available after playback switches to a podcast.
- Startup success requires received audio bytes. Empty recordings are not reported as saved. Direct/ICY reads and HLS requests have bounded waits, and conversion starts only after the writer exits.
- New recording paths include seconds and a unique suffix. Independent recordings cannot append to a previous recording from the same minute.
- TGRT FM was recorded from its live public stream; 114072 bytes were saved and the result played through the BASS engine at zero volume with a reported duration of 7.12 seconds.
- Recording notifications include the final saved path; Turkish and English menu labels and help are included.

Packaged startup, archive integrity and remote publication results are recorded in the adjacent versioned verification report. Physical braille, every screen-reader dialog, long-duration recordings and every online station remain outside these checks.

---

# freeAudio Desktop 1.0.0 — verification status

Date: 2026-11-04. Target: Windows 10/11 x64.

## Completed checks

- The user confirmed successful installation and many working functions in alpha.1, including radio search and Enter-to-play. This supersedes the earlier uncertainty about ordinary-user installation.
- 55 automated tests passed locally, without skipping the real audio-output test. The final run and packaged checks are recorded in the adjacent verification report.
- All 30 default hotkeys registered in the normal Windows session. Actual key delivery was verified for information, volume down and speed up; no media was playing during these key-delivery checks.
- A clean dependency restore downloaded all 83 pinned vendor files and verified every SHA-256 digest.
- The user confirmed authenticated GETEM audiobook playback, radio and podcast playback.
- Desktop default bindings avoid Windows-key shortcuts and reserved F12. Tests verify distinct bindings for all 30 default commands, explicit custom overrides, disabled bindings and unregister cleanup.
- New regression tests cover semantic settings validation, malformed favourites, preserving an existing valid backup, recording-close cancellation, final-save failures, update results arriving after shutdown, duplicate update checks and recursive source-package exclusions.
- Native checklist names, roles, checked/disabled states and accessible default actions were verified.
- Settings now refer to application startup and Screen Reader / Windows Voice. Quick Save before voice/device enumeration completes preserves the saved selections.
- Existing alpha.1 voice, resume and braille preferences migrate without being discarded.
- Profile backup and staged restore round-trip successfully. Credentials are excluded; traversal and checksum failures are rejected. A simulated file replacement failure rolls back the current profile.
- A real local HTTP server was used for podcast subscription/reload, instant recording and time-shift capture/cleanup. The recording test confirms the player was not stopped or modified.
- The bundled BASS process played and sought a generated WAV at zero volume, then applied 1.25x speed and a two-semitone pitch change.
- The original HLS segment-identity and recording recurrence/power-request regression tests pass.
- The previous live check on November 2 returned two LibriVox results; the selected book resolved to 61 chapters, and 4096 audio bytes were retrieved.
- The previous Gutenberg live check on November 2 returned one result and resolved its audio file; 4096 audio bytes were retrieved.
- Release channel configuration, stable-version comparison and trusted release-page construction are tested. The configured target is selcukucar/freeAudio-desktop; remote publication is a separate step.
- Turkish and English desktop help now uses semantic headings, links and paragraphs, with developer instructions kept in separate documentation.

Packaged startup checks and archive/checksum validation are recorded in the adjacent verification report.

## Checks requiring external resources

These are pending acceptance checks, not claims that the port is fully certified:

- A physical braille display; NVDA, JAWS and Narrator listening tests across every dialog and notification.
- GETEM downloads using the user's own account (authenticated streaming was confirmed by the user).
- Two distinct physical audio outputs and Bluetooth/USB removal during playback.
- Full live-station song-boundary recording, long-running time shift, reconnect/disk pressure and A-B/voice-note workflows.
- Optional FFmpeg-dependent conversion and music recognition on a clean machine with FFmpeg configured.
- Windows 10 clean-machine installation and high-DPI/high-contrast manual acceptance.
- A trusted code-signing certificate is not configured. The target desktop repository needs remote publication verification.

The GitHub workflow creates draft releases when a matching tag is pushed, or preserves packages as artifacts on a manual run. Remote CI has been started; its final result is recorded separately in the release verification report. Hosted headless CI explicitly skips the physical-audio test; release acceptance still requires that test on a real Windows device.

No telemetry is added. Rotating diagnostic logs remain in the selected local profile directory.
