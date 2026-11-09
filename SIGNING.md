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
