# Desktop release process

The configured target is `selcukucar/freeAudio-desktop`. Remote publication status must be verified separately; configuration alone does not publish a repository or release.

1. Put the contents of this source directory at the root of the chosen repository.
2. Set `repository` in `release-channel.json` to the real `owner/repository` name. Keep `schema` equal to 1. Never point to the NVDA add-on release repository.
3. Set the version once in `desktop/version.py`; update `CHANGELOG.md` and the documentation.
4. Run the Windows tests with an actual audio output device, then `tools/live_checks.py` for current public-service checks.
5. Build with Python 3.14 x64 and Inno Setup using the command in README.md. Run `tools/verify_release.py` against the output directory.
6. Test both language profiles and the upgrade from the preceding installer. Confirm that favourites, credentials and media positions survive. Portable users retain their own `data` directory.
7. If a code-signing certificate is available, sign the application EXE before packaging and the installer after compilation; regenerate checksums after signing. This source includes no certificate, key or publisher identity.
8. Push a matching version tag only when ready to build. The prepared GitHub workflow runs tests, builds packages, verifies checksums and creates a **draft** release. It does not publish it automatically. The workflow has not been executed against a repository yet.
9. Review and publish the draft manually. Alpha/beta/RC tags are marked as prereleases. The desktop update checker currently follows the latest stable release, excluding drafts and prereleases.

`workflow_dispatch` builds packages without creating a release. The current workflow expects Inno Setup on the Windows runner. Audio output tests are explicitly skipped on a headless hosted runner; those checks must pass on a real Windows audio device before a public release.

The updater opens a trusted release page after user confirmation. It does not run a downloaded executable in the background. No release endpoint, signing certificate or unattended update server is invented by this source tree.
