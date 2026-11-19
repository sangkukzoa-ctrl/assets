# Image Order Studio — 개발 상태 및 세션 이관 (2026-11-19)

**영구 목표는 PROJECT_GOAL_KO.md의 원문과 같다.** 사용자가 `진행`이라고 하면 목표 설명을 다시 요청하지 않고 다음 미완료 개발/테스트를 실행한다.

## 최신 검증 결과

- 공개 베타 **v0.5.3**: https://github.com/sangkukzoa-ctrl/assets/releases/tag/image-order-beta
- 정식 APK 서명/설치/Android 15 계측 테스트 **3개 성공**: https://github.com/sangkukzoa-ctrl/assets/actions/runs/44515904633
- 공개 파일 다운로드/서명/해시 검증 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/44516987432
- 앱 실행/Quick Settings -> 단일 NativeGalleryActivity. 사용자가 누른 순서가 검증되면 MediaStore 원본 content:// URI를 RESULT_OK + image ClipData + 읽기 권한으로 **즉시 반환**. 중간 파일 복사, 리사이즈, 번호 인쇄, 이미지 결합 없음.
- ACTION_GET_CONTENT, ACTION_PICK(MIME 미지정 MediaStore URI 포함) 처리, MIME 제한, 단일/복수 선택, 취소 동작 검증.
- 166항목 순서 회귀/10가지 MIME 테스트, Android MediaStore 실제 파일 바이트 동일성·순서(3→1→2)·공유 intent 계측 성공.
- Play Protect를 막았던 AccessibilityService 제거 상태 유지. 기존 서명 인증서 사용.

## 가장 중요한 다음 과제 (다음 `진행` 시 바로 착수)

1. **범용 첨부 진입**: ACTION_PICK_IMAGES/OS Photo Picker 및 자체 구현된 앱 첨부창은 일반 앱이 우선순위 설정만으로 전역 대체할 수 없다. OEM System Gallery, CloudMediaProvider OEM nomination 등 실제 Android 경계를 기록하면서 대체 가능 기술을 검증한다. 성공 범위를 실제 실기기 테스트로 확인할 것.
2. **원본 SAF DocumentsProvider**: 현재 OrderedDocumentsProvider/OrderedOutbox는 구버전 번호 가공물 경로다. 이를 사진 원본 MediaStore-backed read-only 갤러리/앨범으로 교체하고, ACTION_OPEN_DOCUMENT에서 사용자에게 실제 원본을 제공한다. 원본 bytes, MIME, 이름, 권한 계측 추가.
3. **실제 호출자 E2E**: 별도 테스트 Activity에서 이미지 선택 Intent를 보낸 후 갤러리 탭/선택/완료, 돌아온 Uri들의 원본 스트림 검증까지 자동화.
4. 대량 이미지, 프로세스 복구, Android의 부분 사진 액세스, 동명이미지, HEIC/WebP 안정성 검증.

## 개발 및 배포

- 저장소: sangkukzoa-ctrl/assets
- 경로: image-order-studio/
- 개발: image-order-studio/dev, 서명 배포: image-order-studio/release
- 고정 릴리스: image-order-beta
- 기존 릴리스 키 유지, CMS로 GitHub Actions 실행별 임시 공개 인증서에 암호화 전달. 공개 저장소/소스 ZIP/아티팩트에 비밀키 배포 금지.

**목표 재설명·재정의 금지. 사용자의 '진행' = 위 미완료 개발을 실제 구현.**