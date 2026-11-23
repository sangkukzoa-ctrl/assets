# Image Order Studio v0.5.4 — Android 파일 선택기에서도 원본 사진 직접 제공

개발자: 2bornot · Android 8 이상 · 광고 없음 · 인터넷 권한 없음

## 주요 변경

- **업로드 경로 확대:** MIME이 `*/*`인 범용 파일 첨부창에도 이미지 선택 후보로 등록하며, 실제 반환 파일은 이미지로 제한합니다.

- **파일 선택기(SAF) 개선:** 기존 번호를 붙여 저장한 'Upload-ready batches' 공급원을 폐지하고, 휴대전화 MediaStore의 **원본 사진과 앨범**을 Image Order Studio의 문서 공급자로 직접 제공합니다.
- **원본 무변경:** 파일을 선택했을 때 원본의 사진 바이트, 형식, 파일명, EXIF를 그대로 반환합니다. 이미지 사본 생성·번호 인쇄·재압축·병합이 없습니다.
- **파일 선택기 구성:** 전체 사진, 앨범, 최근 사진, 파일명 검색, 이미지 미리보기를 지원하고 읽기 전용으로 동작합니다.
- **보안:** 사진 문서 ID를 검증하며 앱의 임의 파일 경로를 노출하지 않습니다. 사진 접근 권한을 허용한 범위에서만 표시합니다.
- 기존 v0.5.3의 **단일 갤러리, 원본 URI 즉시 전달, 사용자 선택 순서의 ClipData** 동작을 유지합니다.

## 검증 및 다음 과제

- 원본 파일과 SAF로 연 파일의 바이트 동일성, 파일명/MIME, 실제 Android 파일 선택 동작을 에뮬레이터에서 검사하도록 계측 테스트를 확장했습니다.
- SAF 내부 다중 선택의 표시 순서는 Android 파일 선택기에서 관리합니다. 사용자가 지정한 탭 순서를 반영하는 전용 갤러리는 GET_CONTENT/PICK 호환 경로에서 사용합니다.
- 운영체제 Photo Picker 및 각 앱 자체 업로드 창을 **전역 자동 대체하는 목표는 여전히 미완료**이며 지속 개발합니다.

## English

SAF now exposes live, read-only MediaStore originals (all photos, native albums, recents, search and thumbnails) instead of old numbered export batches. Source bytes, file names, MIME and EXIF are unchanged. Direct ordered MediaStore URI results remain available through the existing in-app gallery on compatible picker intents. Universal photo-picker replacement and caller-side reordering remain future work.
