# Image Order Studio / 이미지 순서 스튜디오 v0.3.0

Android 8.0+ · **2bornot** · Free / 무료 · Offline-first, no advertisements · Korean/English UI

**Goal:** Give images an explicit, immutable *logical sequence* after they are imported. Android and third-party sites may still place attachments in a different order; visible order markers and single-image combining retain evidence of the user's intended sequence independently of filename, extension, original import order, and website UI.

## 사용법 / Usage

### 사이트의 첨부 버튼에서 시작 (권장)

1. 지원되는 사이트나 앱에서 사진 첨부를 누릅니다. Android 선택창에 **Image Order Studio**가 나타나면 선택합니다. Android의 기본앱 선택 화면이 제공되는 경우 **항상**으로 설정할 수 있습니다.
2. 앱에서 **갤러리에서 사진 선택**을 자동으로 열어 시스템 사진 선택기에서 사진을 가져옵니다. Android 15 / R Extensions 12 이상에서 Photo Picker가 순서 표시/반환을 지원하면 순번을 자동 반영합니다. 그 외 버전은 앱 안에서 원하는 순서대로 사진 타일을 누르십시오.
3. **사이트에 첨부** 버튼을 누릅니다. 앱은 번호 표시된 이미지의 `content://` URI를 원래 호출자에게 `RESULT_OK`, `ClipData`, 읽기 권한과 함께 직접 반환합니다. 추가 공유 화면 없이 첨부 요청이 완료됩니다.
4. 호출자가 **한 장만** 받으면 한 장을 선택하거나 (12장 이하) 순서대로 한 장으로 결합합니다. 여러 장을 요청한 사이트에는 정해진 순서의 여러 URI를 전달합니다.

### 앱 직접 실행

1. **＋ 갤러리에서 사진 선택**을 누릅니다. 시스템 사진 선택기가 우선 표시되고, 미지원 기기는 갤러리/파일 선택 옵션을 표시합니다.
2. 파란색 번호가 순서를 뜻합니다. 클릭해 추가/제거하고 **순서 편집**으로 수정합니다.
3. 번호 표시 JPG/PNG 공유, 폴더 저장, 하나로 결합 등을 선택합니다.

사이트마다 Android `ACTION_GET_CONTENT`, `ACTION_PICK`, 시스템 `ACTION_OPEN_DOCUMENT`, 또는 최신 Photo Picker 호출 경로를 사용합니다. 이 앱은 표준 이미지 `GET_CONTENT` 및 `PICK`를 처리합니다. `ACTION_OPEN_DOCUMENT`와 시스템 독점 사진 선택기에서는 타사 앱이 전체 화면을 대체할 수 없으므로 앱 직접 실행 / 공유로 이용할 수 있습니다. Android 13+의 Photo Picker 기본 개입도 기기별로 다릅니다.

Image byte-order is encoded into each numbered output's visible header, not inferred from filenames. Receiver apps can still display attachments in their own ordering.

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
