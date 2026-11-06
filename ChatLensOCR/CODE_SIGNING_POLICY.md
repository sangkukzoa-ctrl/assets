# Code signing policy — ChatLens OCR

**Software developer and copyright holder:** 2bornot. Copyright © 2026 2bornot.

**Code signing status:** SignPath Foundation application preparation; as of v0.4.1 the software is **not** Authenticode signed unless release notes and independent signature verification state otherwise. GitHub/Sigstore build provenance attestations are **not** Authenticode publisher certificates.

**Planned signing:** Free code signing provided by [SignPath.io](https://signpath.io/), certificate by [SignPath Foundation](https://signpath.org/). This policy documents the requested pathway and does **not** claim approval or active signing.

## Official source and release chain

- Repository: https://github.com/sangkukzoa-ctrl/assets (the ChatLensOCR directory, with its own MIT LICENSE).
- Official branch for next build: `chatlens-v0410-field-test`.
- Windows x64 EXE built from checked-in sources using GitHub-hosted Windows runners.
- Release downloads: https://github.com/sangkukzoa-ctrl/assets/releases
- SHA256 checksum files are published with each EXE and ZIP. Build provenance, if available, is separate from code signing.
- Signature verification after approval: Windows file Properties → Digital Signatures; certificate Subject/Publisher is **SignPath Foundation**, not 2bornot. File CompanyName, author, application branding, and copyright remain **2bornot**.
- Every SignPath signing request requires a manual approval by the project's maintainer before release; unsigned outputs must not be advertised as signed.
- Only this project's own executable is proposed for signing. Third-party dependencies retain their own copyright and signatures.

## Roles and review

- Project developer/author: **2bornot**
- GitHub repository administrator and committed-source reviewer: [sangkukzoa-ctrl](https://github.com/sangkukzoa-ctrl)
- Signing request approver: repository owner `sangkukzoa-ctrl` (once SignPath access has been approved and configured).
- External contributions require maintainer review before merging. GitHub and SignPath accounts participating in signing must have MFA.

## User privacy and security

ChatLens OCR extracts text from locally provided images. It does not transfer screenshots, recognized text, or local training samples to a remote system unless the user separately chooses to share or upload them. See [PRIVACY.md](PRIVACY.md).

The application is portable, does not modify Windows security settings, and can be uninstalled by deleting the downloaded EXE and, optionally, the app's own data under `%LOCALAPPDATA%\ChatLensOCR`. No elevation is required.

## Application procedure

The developer submits the official repository, releases, MIT license, this policy, description, and privacy notes at https://signpath.org/apply.html. Approval is controlled by SignPath Foundation. After approval, configure the SignPath trusted GitHub build, artifact configuration and manual approval before any signed production release. Never store signing tokens in source control.
