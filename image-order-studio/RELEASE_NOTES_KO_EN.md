# Image Order Studio v0.5.0 — Unified Gallery / 업로드 통합 갤러리

Developer: 2bornot · Android 8+ · Korean/English · no ads, no Internet permission

## 한국어

- 사진 첨부를 하나의 흐름으로 구성: **사진 선택 → 순서대로 탭 → 완료**.
- 삼성 Gallery의 내부 구현에 의존하지 않고 실제 기기 MediaStore의 사진 및 앨범을 직접 보여주는 내장 갤러리 추가.
- 외부 이미지 요청(GET_CONTENT/PICK)에서 순서대로 표시된 파일 URI를 자동 반환.
- Android 13/14+ 사진 접근권한 및 선택한 사진만 접근하는 모드 지원.
- 외부 앱의 시스템 선택기를 이용하는 경우, 사용자가 명시적으로 켠 접근성 보조 팝업에서 동일한 갤러리를 바로 열 수 있도록 추가. 이 보조 기능은 외부 앱 첨부 결과 자체를 강제 교체하지 않으며 원래 선택기에서 준비된 결과물을 선택해야 함.
- 기존 패키지/서명키 유지, versionCode 6.

## English

- Unified workflow: **Choose photos → tap in order → Done**.
- Native MediaStore gallery with Photos/Albums instead of forwarding to vendor-specific picker implementations.
- Direct content URI results for supporting GET_CONTENT/PICK requesters.
- Runtime photo permissions including Android 14+ selected-photo access.
- Opt-in accessibility shortcut for recognizable upload pickers, without changing other apps' ActivityResult contracts.
- Same package/signing identity, versionCode 6.
