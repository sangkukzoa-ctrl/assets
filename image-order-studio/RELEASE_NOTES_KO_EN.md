# Image Order Studio v0.5.3 — 진짜 단일 갤러리 · 원본 URI 즉시 첨부

개발자: 2bornot · Android 8 이상 · 광고 없음 · 인터넷 권한 없음

## 이번 구현

- **중간 이미지 복사 삭제:** 외부 이미지 첨부 요청에서 NativeGallery가 반환한 원본 MediaStore/사진 선택 URI를 바로 원래 앱으로 전달합니다. 기존 앱 내부 보관함을 경유하지 않습니다.
- **앱 바로 실행:** 런처와 빠른 설정 타일에서도 하나의 갤러리 화면을 바로 열고, 확인하면 원본 URI들의 공유 선택기를 표시합니다.
- **선택 순서:** 사용자 탭 순서로 ClipData 항목을 생성합니다. 원본 JPEG/PNG/HEIC/WebP 바이트를 변경하지 않습니다.
- **ClipData MIME:** 기존 `text/uri-list` 형식 대신 실제 이미지 MIME과 `image/*`를 선언합니다. 이미지별 MediaStore/ContentResolver 유형도 확인합니다.
- **외부 앱 호환:** MIME 없이 MediaStore 이미지 컬렉션 URI만 전달하는 `ACTION_PICK` 요청도 인식합니다. JPEG·PNG 등 MIME 제한을 존중합니다.
- **단일 첨부:** 최대 선택 1장인 경우 갤러리 탭 한 번으로 즉시 결과를 반환합니다.
- **취소:** 외부 첨부를 취소하면 빈 내부 화면에 남지 않고 원래 앱으로 복귀합니다.
- 사용하지 않는 이미지 번호 삽입·병합·재인코딩 구현을 소스에서 제거했습니다. 미리보기 디코딩은 화면 출력에만 사용합니다.

## 검증과 제한

- 166장 순서 회귀 테스트, 10가지 MIME 경계 테스트, 원본 URI 반환 경로의 정적 회귀 검사, Android 컴파일·설치·서명을 검증합니다.
- `ACTION_GET_CONTENT`/`ACTION_PICK`는 우리 갤러리를 사용할 수 있지만, 시스템 `ACTION_PICK_IMAGES` 및 서드파티 자체 업로드 UI는 일반 앱에서 전역 강제 교체할 수 없습니다.
- 수신 측이 자체적으로 이미지를 다시 정렬하면 전달한 배열 순서가 바뀔 수 있습니다. 해당 문제와 완전한 범용 호출은 장기 개발 목표로 계속 유지합니다.

## English

Zero-copy, single-gallery path: original content URIs go directly from the in-app gallery to the requesting activity with ordered image ClipData and read grants. The launcher and Quick Settings tile open the same gallery. MIME-less MediaStore ACTION_PICK, image type filtering, single-select, and cancel behavior are addressed. The system-owned Photo Picker cannot be globally replaced by a regular APK.
