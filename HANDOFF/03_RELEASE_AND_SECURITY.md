# Releases, update signing, privacy, and distribution

## Exact confirmed public release
Just PDF to Image v1.3.1 — by 2bornot (KR/EN).
Published 2026-11-06 UTC; public and latest at time of handoff.
Release: https://github.com/sangkukzoa-ctrl/assets/releases/tag/v1.3.1
APK: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1.apk
AAB: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1.aab
Source ZIP: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1-Source.zip
Checksums: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/SHA256SUMS.txt
Completed v1.3.1 release Actions run: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42159936750

Published names/title:
- Just PDF to Image (same KO/EN), author "2bornot"
- Official Android package/applicationId "com.hsiwan.pdfimage"
- versionName 1.3.1, versionCode 5
- Android 8.0+ supported (minSdk 26)
- Licensed MIT app code; PDFBox-Android under Apache 2.0

## Signing and update compatibility — highest priority
v1.3.1 release was signed with the original v1.3.0 production identity. This is why v1.3.0 signed-release users can install the v1.3.1 APK in place. Older v1.2.0 DEBUG APK uses a different certificate and is not update-compatible.

**Private keystore is NOT stored in this source bundle or public GitHub repository.** It was backed up privately in the original ChatGPT workflow; no signing key, private password, or key backup has been included in this handoff. The user retains custody of the private backup. If user asks for a new public release, first confirm signing material can be accessed safely WITHOUT publishing it or exposing password via chat, workflow log, git commit, action artifact or public ZIP. Never generate a fresh signing key and then claim existing users can update. Verify actual signing certificate fingerprint of outgoing APK against published v1.3.1, using apksigner verify --print-certs when available.

The old one-shot workflow .github/workflows/pdfimage-release-v131.yml is a historical record only: it is pinned to v1.3.1, uses an ephemeral encrypted key-transfer mechanism and deliberately refuses to overwrite an existing v1.3.1 release. It must NOT be rerun as the future release process without careful revision. Never republish/overwrite a historical release without explicit user request.

## Distribution
- Existing public distribution: GitHub Releases; link from Naver blog.
- Google Play was considered but initial $25 developer registration and testing friction were unwanted.
- Samsung Galaxy Store entry encountered eligibility restrictions in the user's account; the user declined further pursuit and chose Naver blog + GitHub.
- Do not resurrect store registration tasks without a NEW explicit request. This handoff has no pending store action.
- APK is for side-loading/website download. AAB is primarily for supported store submission and cannot directly be installed as ordinary APK.
- Android sideload/Play Protect/OEM security warnings may appear even for correctly signed APK; never promise no warning.

## Privacy and permissions
- AndroidManifest.xml has no android.permission.INTERNET; no broad MANAGE_EXTERNAL_STORAGE.
- Android's SAF file and folder pickers handle user-selected input and destination.
- No login, ad/tracker SDK, file upload, analytics, quotas or monetization in project.
- Source data never leaves device through app-owned remote infrastructure.
- Use/docs privacy text under project/docs/PRIVACY_EN_KO.md and docs/privacy-policy.html. These are content, not proof of an externally published privacy URL.
- Do not include user-submitted business documents or customer paperwork as test fixtures in public source.

## Branch and release discipline for future user-requested changes
1. Read current HANDOFF/STATE.json, TASKS.md and official release assets.
2. Implement requested change in isolated source branch, preserve appId and locale behavior.
3. Test unit cases and CI; inspect compiled APK/AAB.
4. Provide user a precise change summary and version bump proposal.
5. When user explicitly authorizes release, use securely supplied original signing identity, verify cert, and publish new vX.Y.Z APK/AAB/source/changelog/checksums.
6. Verify direct release download URLs before telling user release is live.
7. Update state/Tasks/changelog to record actual outcomes; don't invent success.
