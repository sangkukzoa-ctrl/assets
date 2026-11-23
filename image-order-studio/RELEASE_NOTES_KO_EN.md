# Image Order v0.5.5 — 서로 다른 Android 앱 사이의 원본 첨부 검증

개발자: 2bornot · 광고 없음 · 인터넷 권한 없음 · Android 8.0 이상

## 이번 단계

- **별도 Android 패키지 개발:** `com.twobornot.imageorder.caller`는 앱 자체 권한으로 사진을 읽지 않고, Image Order가 반환한 원본 이미지 URI만 읽을 수 있는지 테스트합니다.
- **UI Automator 연결:** 다른 앱에서 `GET_CONTENT`(`image/png`, `*/*`)를 호출하고, 실제 갤러리 타일을 순서 3→1→2로 누른 뒤 완료하도록 자동화했습니다.
- **원본 확인:** 응답을 받은 별도 앱이 URI 접근 권한, JPEG/PNG MIME, 파일명, SHA-256 원본 바이트 및 선택 순서를 검증합니다.
- **테스트 사진의 소유권 분리:** 이미지 생성은 본 앱의 디버그 구성요소가 수행하고, 호출 앱은 미리 사진 읽기 권한을 받지 않습니다. 서명 배포 APK에는 이 디버그 구성요소를 포함하지 않습니다.
- **갤러리 접근성 보강:** 사진/앨범 탭, 사진 타일, 완료 버튼에 안정적인 접근성 설명을 부여했습니다.

이 기능은 별도 테스트 패키지와 자동 검증 인프라의 강화입니다. 기존 v0.5.4의 SAF 원본 사진 제공, 단일 네이티브 갤러리, 원본 바이트 유지, 사진을 누른 순서의 `ClipData` 전달은 그대로 유지합니다.

## 아직 남은 최종 목표

일반 APK가 시스템 Photo Picker를 전역 대체하는 문제, 앱별 독자 첨부창, 수신 앱 자체 재정렬 문제 및 다양한 OEM/Android 기기의 호환성은 개발을 계속합니다. 테스트 앱 성공과 모든 앱·사이트 호환을 구분합니다.

## English

v0.5.5 adds a **separately installed Android caller APK** with no media permission and a **debug-only target-owned photo seeder**. Cross-package UI Automator tests request both `image/png` and `*/*` attachments, tap the real gallery in the order 3→1→2, and verify that only the resulting granted URIs can be read with unchanged SHA-256 bytes, names, and types. The independent caller and fixture are test infrastructure; the release APK does not include them.
