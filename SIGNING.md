# Code signing policy and SignPath Foundation assessment

Reviewed: 2026-11-09. The published desktop packages are currently unsigned.
No SignPath Foundation subscription, certificate, approval or signing identity
is claimed by this project. No application has been submitted on the owner's behalf.

The application bundles BASS and its audio plug-ins. BASS has its own proprietary
licensing terms (including free non-commercial use), rather than an OSI-approved
open-source licence. SignPath Foundation's published requirements exclude
proprietary non-system components. On that basis, the present distribution does
not appear eligible; the Foundation itself makes the final eligibility decision.

- Foundation requirements: https://signpath.org/terms.html
- BASS licence information: https://www.un4seen.com/bass.html
- Verified GitHub build integration: https://docs.signpath.io/trusted-build-systems/github

Possible future routes are a suitable paid publicly trusted code-signing
certificate, or replacing proprietary runtime components with appropriately
licensed open-source alternatives and re-evaluating Foundation eligibility.
Replacing the audio engine requires separate playback, effects, time-shift,
recording, device-switching and accessibility acceptance work.

If signing becomes available, sign the application before packaging and the
installer after compilation, use a trusted timestamp, verify the signatures,
then regenerate release digests. Foundation signing additionally requires its
approval process, eligible hosted builds, named author/reviewer/approver roles,
multi-factor authentication and an approved artifact configuration. Never add
signing-service badges or claims before approval and an actual signed release.

The in-app updater validates HTTPS origins, release metadata, exact filenames,
file sizes and GitHub-provided SHA-256 digests. These checks detect changed or
incomplete downloads; they are not an Authenticode publisher signature and do
not guarantee that antivirus software accepts a release.

## Optional build integration

The build accepts `--sign-hook C:/private/sign_release.py --signtool C:/SDK/signtool.exe`. Both arguments are required together. The hook must be outside the source tree. It receives one file path and must sign and timestamp that file using an authorized signing identity. Credentials belong in the signing provider or CI secret store; never in source files or command arguments.

The main application is signed and verified before the portable ZIP and installer are built. The installer is then signed and verified before SHA256SUMS is generated. Each signature is checked with `signtool verify /pa /all /v`; any signing or verification failure aborts the build. Builds without these options remain unsigned. This integration does not create a certificate, approve a signing service, or make the current project eligible for Foundation signing. No signing credentials are configured in the public workflow.
