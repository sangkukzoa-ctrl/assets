# Image Order Studio v0.5.2 — 원본 무변경 업로드 / Unmodified Original Upload

## 핵심 수정

- 사진을 선택하면 이미지 자체를 수정하지 않고 원본 파일의 바이트를 그대로 전달합니다.
- 사진에 숫자를 인쇄하는 기존 업로드 경로, JPG 변환, 리사이즈, 이미지 결합을 업로드 흐름에서 제거했습니다.
- 번호는 앱의 갤러리 선택 화면에만 보입니다.
- 순서 배열은 사용자가 선택한 순서대로 ClipData/EXTRA_STREAM에 담습니다.
- 원본 파일명·MIME은 읽기 전용 content provider로 제공됩니다.
- 한 장만 지원하는 입력창에서는 사진 한 장만 선택할 수 있습니다. 여러 장을 무단으로 합치지 않습니다.
- 앱 직접 실행도 원본 사진 선택 후 Android 공유 메뉴로 이어집니다.
- 접근성 서비스는 계속 제외합니다.

## 제한

Android가 통제하는 Photo Picker를 모든 앱에서 강제로 대체할 수는 없습니다. 이미지 수신 사이트가 배열을 자체 정렬하면 송신 앱의 원본 보존과 별개로 순서가 바뀔 수 있습니다.

## English

This update sends original file bytes and original MIME/filenames in user-selected URI order. No stamping, recompression, resizing or collaging occurs in the default upload pipeline. Rank badges are UI-only. A one-file attachment receives exactly one original.
