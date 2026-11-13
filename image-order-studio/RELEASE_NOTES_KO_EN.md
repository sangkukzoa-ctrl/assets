# Image Order Studio v0.5.1 — Play Protect installation fix / 설치 차단 해결

Developer: 2bornot · Android 8+ · Korean/English · no ads and no internet permission

## 한국어
- Google Play 프로텍트가 차단할 수 있는 접근성 서비스와 관련 팝업 기능을 앱에서 완전히 제거했습니다.
- 앱 내부 사진/앨범 갤러리, 순서 번호 표시, 표준 `GET_CONTENT`/`PICK` 업로드 응답, 갤러리 전용 앨범, 파일 선택기, 빠른 설정 타일을 유지합니다.
- 기존 패키지 `com.twobornot.imageorder` / 기존 서명 인증서를 유지합니다. versionCode 7, versionName 0.5.1.
- Android 시스템 전용 Photo Picker는 제3자 앱에서 강제로 대체할 수 없습니다. 자동 업로드 감지는 더 이상 제공하지 않습니다.
- Play 프로텍트 해제/무시를 권유하지 않습니다.

## English
- Removed the AccessibilityService and optional overlay entirely, to avoid Google Play Protect's sensitive-permission internet-sideloading block.
- Kept the local album gallery, ordered image picking, standard GET_CONTENT/PICK callbacks, Gallery album publishing, DocumentsProvider, and Quick Settings tile.
- Same app ID and signing certificate, versionCode 7.
- The system-only Android Photo Picker cannot be overridden by an ordinary third-party app.

## QA
Android source checks reject any accessibility service, notification listener, or SMS permissions. Release CI verifies the final compiled AndroidManifest and APK signature, installs the signed APK on an emulator, and publishes a stable beta only after success.
