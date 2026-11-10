# Image Order Studio / 이미지 순서 스튜디오 v0.2.0

Android 8.0+ · **2bornot** · Free / 무료 · Offline-first, no advertisements · Korean/English UI

**Goal:** Give images an explicit, immutable *logical sequence* after they are imported. Android and third-party sites may still place attachments in a different order; visible order markers and single-image combining retain evidence of the user's intended sequence independently of filename, extension, original import order, and website UI.

## Usage / 사용법

1. Import images or share them into this app from the system gallery. **Imported photos have no rank yet**, since the external picker may return an arbitrary order.
2. Tap the images one by one in your required order. Blue badges show 1,2,3… A second tap removes a photo from the selection.
3. Use **Selected first** to see the selected photos at the top in your definitive order, or **Selected only** to review just chosen images. **Edit order** swaps individual positions without changing the underlying files. Long-press deletes an imported *copy*, without deleting the original image.
4. **Share compact JPG** creates images containing a prominent `ORDER 0001 / 0005` header and uses 90%-quality JPEG for upload compatibility. **Share numbered PNG** uses lossless PNG for screenshots and text. File names are also number-prefixed, but filenames alone are not the guarantee.
5. **Save to folder** saves ordered JPGs for use with websites' regular file selectors. **Combine to one** creates one tall PNG (<=12 pictures and within 14,000 px height). **Copy sequence** copies the ordered image name list to clipboard for pasting into a text prompt or report. **Share originals** preserves image bytes but DOES NOT guarantee third-party ordering.

For example, if image files A.png,B.jpg,C.webp are imported, and the user taps B,C,A, every visible rank and numbered export is in order B=1, C=2, A=3 even if a receiving site sorts attachments A,B,C.

## Privacy

No INTERNET permission, analytics SDKs, ads, account creation, external uploading, or broad gallery read permission. Image access is initiated via Android's document picker or other apps' explicit share actions. Images and ordering information are stored as local private copies; originals remain unchanged. Rendering creates temporary export files in app cache. You choose the external app or website and when to upload. See [PRIVACY_KO_EN.md](PRIVACY_KO_EN.md).

## Limitations / 주의

- The app **does not control** how unrelated website attachment lists are sorted. The visible header and single-image export are the universal fallbacks, not a bypass for external APIs.
- All ranks must be applied inside this app, independently of picker-selected order.
- Numbered JPEG is resized to limit resource use. PNG is lossless *after decoding and size sampling*, but large originals may be downsampled. Use original sharing to preserve original bytes.
- Preview thumbnails are limited in size. HEIC/WebP and animation support depend on Android codecs; GIF rendering uses a static frame.
- Combining 12+ images or too-tall pages is intentionally limited to prevent OOM errors. Select fewer or use individual numbered images.
- The app cannot guarantee upload order when a site removes visible headers or aggressively crops, or when a site rejects attachments altogether.

## Build & release

Source tree is `image-order-studio/`. Dev CI `.github/workflows/image-order-ci.yml` builds and checks unsigned release and debug artifacts. Beta release CI `.github/workflows/image-order-beta-release.yml` builds, validates, **signs** and publicly releases an installable APK with Android's APK signing schemes v2/v3 (Android 8+), only when provided a private release key encrypted to a one-use runner certificate. Public release tag `image-order-beta` is stable; assets are versionless and only overwritten after validations. **Never publish `.p12` signing keys or passwords** in GitHub, Actions artifacts or source ZIP. The release key is to be retained privately for upgrades.

## QA

- 166-image ledger regression, restore after restart, duplicate/cross-extension names, swap/deselect and malformed input are covered by `tests/SequenceLedgerTest.java`.
- CI verifies minimum Android API 26, applicationId `com.twobornot.imageorder`, no INTERNET permission, source metadata and signability.
- Physical-device installation and target-site image attachment order (ChatGPT, review websites) should be tested from the public beta APK. They are separate from compilation and static signing checks.

## License

Copyright 2026 2bornot. This source snapshot is provided for inspection and personal test use. See RELEASE_NOTES_KO_EN.md.
