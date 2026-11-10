# Image Order Studio / 이미지 순서 스튜디오 v0.4.0

Developer **2bornot** · Android 8.0+ · KR/EN · offline, no ads, no network access.

## 핵심 사용법 — 웹사이트의 이미지 첨부창이 앱 선택을 막아도 동작

1. **Image Order Studio** 실행 → **＋ 삼성/기본 갤러리**. Galaxy에서는 실제 Samsung Gallery 이미지 선택 인텐트를 먼저 호출합니다. 다른 스마트폰은 시스템 갤러리로 대체됩니다. '사진 선택 설정'에서 선택 방식을 바꿀 수 있습니다.
2. 이미지 목록에서 **사용할 순서대로 사진을 누릅니다.** 파란색 순번은 원본 이름이나 확장자와 무관합니다. 순서 편집으로 조정할 수 있습니다.
3. **① 갤러리 앨범에 저장**: 휴대폰 사진 갤러리의 `Image Order Studio` 앨범에 번호가 각인된 이미지가 저장됩니다. 어느 사이트에서든 기존 사진 선택창을 이용해 이 앨범의 이미지를 골라 첨부합니다. 사이트의 첨부 목록이 재정렬되어도 각 이미지의 헤더에 순서가 남습니다.
4. **② 한 장으로 갤러리 저장**: 최대 12장의 이미지를 번호가 표시된 1장의 이미지로 결합합니다. 이미지 한 장만 받거나 첨부 순서가 강제로 뒤섞이는 사이트에서 사용합니다.

Android 표준 파일 선택기의 저장소 목록에 `Image Order Studio` 공급자도 추가됩니다. 최근 준비된 묶음은 각 폴더에서 열 수 있습니다.

## 즉시 실행

Android의 빠른 설정 패널을 아래로 두 번 끌어 내려 편집(+)을 열고 **Image Order Studio** 타일을 추가하면 어느 앱에서도 열 수 있습니다. 타일은 화면 위에 지속되는 오버레이가 아니며 특별한 접근성 권한을 사용하지 않습니다.

## 삼성 갤러리를 100% 그대로 보여주는 것과의 관계

`ACTION_GET_CONTENT`/`ACTION_PICK`로 삼성 갤러리 패키지를 직접 우선 호출합니다. 삼성 갤러리의 선택 화면 자체는 One UI 버전과 내부 인텐트 처리에 따라 달라질 수 있습니다. '다른 기능·설정 → 삼성 갤러리 앱 직접 열기'는 실제 갤러리 앱 전체를 열며, 갤러리 안에서 사진을 공유하여 Image Order Studio로 가져오는 기능도 지원합니다.

## 외부 첨부창

`ACTION_GET_CONTENT` / `ACTION_PICK`를 호출하는 웹사이트·앱에서 이 앱이 선택기에 나타나면 선택하고 원하는 순서를 지정하여 결과 이미지를 반환할 수 있습니다. 시스템 Photo Picker 자체와 모든 앱의 자체 첨부 처리에는 타사 앱이 강제로 개입할 수 없습니다. 위의 '갤러리 앨범에 저장'은 이 제한을 피해 사용자 사진 목록에 파일을 제공하는 범용 경로입니다.

## Build

- `gradle :app:assembleRelease` (Gradle 8.11.1, Java 17, Android SDK 36).
- `Image Order Studio - Android development CI` enforces pure-Java sequence, 166-image naming, Android source and permissions invariants.
- `Image Order Studio - signed stable public beta` signs with the EXISTING Image Order Studio stable private certificate (unchanged across v0.2.0→v0.3.0→v0.4.0) and verifies installation on Android emulator before publishing.
- Fixed public release: https://github.com/sangkukzoa-ctrl/assets/releases/tag/image-order-beta
- No private certificate or password should ever be committed, included in a ZIP, or published as a GitHub asset.

## Privacy

No INTERNET permission, app analytics or ads. Android 10+ MediaStore writes user-approved results to the visible device Gallery; Android 8/9 asks for legacy WRITE_EXTERNAL_STORAGE only when exporting to Gallery. No general READ_MEDIA_IMAGES permission is requested. The DocumentsProvider is read-only and serves only user-prepared outputs. Original images remain unchanged.
