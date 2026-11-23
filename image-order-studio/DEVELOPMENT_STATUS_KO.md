# Image Order — 지속 개발 및 세션 이관 상태 (2026-11-23)

## 변하지 않는 최종 목표
[PROJECT_GOAL_KO.md](PROJECT_GOAL_KO.md)의 목표를 **그대로** 따른다.
사용자가 `진행`이라고 하면 목표를 다시 설명하게 하지 않고 다음 미완료 개발과 검증을 실제 진행한다.
현재 일부 앱에서만 호출되는 것을 목표 완료라고 보고하지 않는다. 모든 앱/웹사이트에서 단순한 한 번의 이미지 선택 UI, 원본 불변, 사용자 선택 순서의 최종 업로드 유지가 목표다.

## 최신 공개: v0.5.4 (versionCode 10)
- 공개 APK: https://github.com/sangkukzoa-ctrl/assets/releases/download/image-order-beta/ImageOrderStudio.apk
- 공식 릴리스/원본 소스: https://github.com/sangkukzoa-ctrl/assets/releases/tag/image-order-beta
- 개발 소스 CI 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45127807218
- **정식 서명, 설치 및 Android 15 계측 5개 테스트 성공**: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45128967966
- 공개 APK SHA256, 서명(v2/v3), 패키지/버전/SAF 등록 검증 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45129772988
- 패키지 고정 `com.twobornot.imageorder`; 과거 릴리스 동일 서명 인증서 유지.
- 인터넷 및 AccessibilityService 권한 없음. 사용자의 Play Protect 설치 차단을 유발했던 접근성 서비스는 재도입하지 않는다.

## 실제 변경된 소스
1. `OrderedDocumentsProvider.java`: 파일 선택기의 번호 가공물 목록 대신 **실제 MediaStore 사진/앨범/최근사진/검색**을 제공. 원본 MIME, 이름, 용량, 썸네일, 읽기 전용 `openFileDescriptor`을 구현했다. `OrderedOutbox.java` 삭제.
2. `SafDocumentIds.java` 신규: album/photo 문서 ID를 검증하고 임의 파일 경로·잘못된 ID 접근을 막는다.
3. `AndroidManifest.xml`, `MainActivity.java`, `ImageMimePolicy.java`: 이미지가 허용되는 일반 파일 첨부 요청 `ACTION_GET_CONTENT */*`도 선택 후보로 등록. 실제 반환은 이미지로만 제한.
4. `app/src/debug/.../PickerHostActivity.java`: **디버그 빌드 전용** 첨부 요청자. 정식 APK에는 포함되지 않는다.
5. `OrderedAttachmentInstrumentedTest.java`: Android 실제 MediaStore 파일의 SAF 원본 바이트/파일명/MIME/읽기 전용 접근 + 앱 내 디버그 호출자가 사진 3→1→2를 탭한 뒤 RESULT_OK로 돌려받는 전체 흐름 테스트. 기존 tests와 합하여 5개 Android 계측 테스트 성공.
6. `.github/workflows/image-order-beta-release.yml`: GitHub runner `dumpsys package`의 상대 액티비티 이름 처리 복원, `gradle -p image-order-studio` 유지. **원본 소스 ZIP에 들어 있던 과거 CI 설정을 그대로 덮어쓰지 않는다**.

## 2026-11-23 Image Order 2차 승계

- 개발 기준 커밋: 6913cc5db0b4f5afc90979834013fee0a8198fd7
- 새 개발 브랜치: image-order/dev-v2 (기존 개발 브랜치와 충돌 방지)
- 공개 v0.5.4, 진행 중 v0.5.5.
- Cross-UID E2E run 45141927988: 본 앱 5/5 통과, 외부 패키지 0/2 실패.
- 이후 비동기 실행 패치 승계, CI 실패 증거 logcat 및 Activity task dump 추가.
- 외부 패키지 원본 전달이 검증되기 전 v0.5.5 공개 배포 보류.

## 미완료로 유지할 항목
- **실제 다른 패키지/다른 UID의 첨부 요청자가** URI 읽기 권한을 수령해 바이트/순서를 읽는 외부 APK 기반 E2E 테스트. 현재 테스트 호출자는 앱의 debug 전용 Activity이므로 동일 패키지다. 이 구분을 혼동하지 않는다.
- Android 13~16의 `ACTION_PICK_IMAGES`, SDK Extension Photo Picker, Embedded Photo Picker의 기본 앱 연결 방식: 공식 API, OEM 시스템 갤러리 Role, Android 시스템 통합의 기술적 접근 경로 조사/실증. `CloudMediaProvider`의 가능성과 제약(외부 미디어 소스 공급 vs Picker UI 자체 제어)을 구별.
- 앱별 독자 첨부창 및 웹 뷰 통합을 재현하는 다중 요청자 호환성 매트릭스.
- `*/*` 첨부 결과 표시 및 갤러리 선택 품질을 삼성 실기기로 확인. 일반 Android 15 에뮬레이터의 성공을 갤럭시 실기기 성공으로 호도하지 않는다.
- 수신 측이 배열을 재정렬하는 경우의 엔드투엔드 순서 보전 전략. 파일명을 바꾸거나 이미지를 수정해 우회하지 않는다.
- SAF의 Android 시스템 파일 선택기는 자체 UI/선택 순서를 유지한다. 아직 당초 목표의 단일 네이티브 갤러리 UI와 완전히 같지는 않다.

## 개발 규약/계속 작업
- 코드 저장소: `sangkukzoa-ctrl/assets`
- 개발 브랜치: `image-order-studio/dev`, 정식 서명 브랜치: `image-order-studio/release`.
- 사용자 `진행` 입력 시 **위 미완료 과제 중 가장 실익이 있는 것부터 실제 코드 작성·검증**한다. 사용자의 목표를 재확인하는 질문은 하지 않는다.
- 사용자 파일 무수정, 선택 순서 보존, 광고/인터넷 권한 없음, 인증서 유지.
- 정식 공개는 빌드·Android 테스트·서명·공개 다운로드 검증 성공 후에만.
- 서명키는 사용자의 비공개 암호화 백업이며 소스/공개 아티팩트에 포함하지 않는다.

## v0.5.5 후속 구조 단순화 (직접 갤러리 진입)

- 외부 `ACTION_GET_CONTENT`/`ACTION_PICK` intent-filter를 `MainActivity`에서 `NativeGalleryActivity`로 옮겨 앱 간 업로드 선택 시 중간 Activity 한 단계를 삭제했다.
- 기존 `MainActivity` 직접 호출 경로는 레거시 호환·내부 계측 테스트 대상으로 보존한다.
- 외부 단일 이미지 요청은 `EXTRA_ALLOW_MULTIPLE=false`를 적용해 1장 제한, 다중 요청은 원래 선택 순서 그대로 반환한다.
- MIME `image/png`, `image/*`, `*/*` 및 `EXTRA_MIME_TYPES`를 네이티브 갤러리에서 직접 처리한다.
- 이 구조는 교차 UID 반환 E2E가 실제로 통과해야만 검증 완료로 인정한다.
