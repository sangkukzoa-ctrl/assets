# Image Order v0.5.5 — 검수 후보 (공개하지 않음)

기준 제품 소스: d810802d557101af0880ed3c13bed112b8e943e3. 기존 public beta v0.5.4는 유지한다. Android API26~36 11/11 통과(45664554476), 실제 Chrome 113/124 image/generic 4/4 통과(45780368542). 통합 이후 CI에서 API35 이미지 test 시작 timeout으로 단일 job 재실행(45791982393 attempt 2), 나머지 3개 통과. 통합 Android 11/11 전수 재검증(45791982467)과 Chrome 4/4 재검증(45791982393 attempt 2) 모두 성공. 후보 빌드 45794623113 성공, unsigned artifact 15103988422 확보.

## 검수 APK
- 이 workflow는 unsigned v0.5.5 후보 APK, 이전 공개 APK에서 추출한 공개 인증서 fingerprint, 검수 문서만 artifact로 남긴다. 서명되지 않은 APK는 설치용이 아니다.
- 기존 개인키는 공개 저장소/아티팩트에 보관하지 않는다. 기존 PKCS#12 및 암호 파일을 확보한 안전한 서명 환경에서 sign-candidate.sh를 사용한다. 새 키 생성 금지.
- 서명 v2/v3, 기존 v0.5.4와 SHA-256 signer fingerprint 일치, package ID와 versionCode/Name, zipalign 검사 후에만 RC 파일 생성.
- 서명 후 별도 디바이스에서 공개 v0.5.4 설치 → RC 덮어쓰기 설치 → 실제 갤러리 실행 및 원본 선택 검증. 실기기 Play Protect 동작과 최신 Chrome/삼성 인터넷 호환은 실제 사용자 검수 대상.
- 공개 release 업로드/태그 이동은 이 workflow가 실행하지 않는다. 기존 목표의 direct ACTION_PICK_IMAGES 및 임의 앱 수신 정렬 문제는 미해결로 유지.

## 실제 Chrome 검수 경로
웹페이지 사진 첨부 → 시스템 Photo Picker의 찾아보기/Browse → 파일 앱 탐색 메뉴 → Image Order (Files)의 별도 앱 열기 버튼 → 선택 순서대로 사진 선택 → 완료. 일반 파일 첨부에서는 처음에 Media/Media picker/Files를 누를 수 있다. 공급자 명칭만 눌러 들어가는 SAF 목록은 선택 순서 보장 경로가 아니다. 테스트는 순서를 일부러 5→2→4→1→3으로 변경하여 확인한다.

## 서명 후 업데이트 설치 자동검증
- 공개 v0.5.4 APK와 기존 인증서로 서명한 v0.5.5 RC APK를 준비한다.
- 깨끗한 전용 에뮬레이터에서 `bash verify-candidate-upgrade.sh emulator-5554 /path/to/v0.5.4.apk /path/to/ImageOrder-v0.5.5-RC.apk` 실행. 이미 설치된 앱/실기기에서는 실행 거부한다.
- 두 APK 인증서/버전 검증 → 기존판 설치 → 제거 또는 데이터 초기화 없이 덮어쓰기 설치 → UID/appId 및 최초 설치시각 동일성 → GET_CONTENT/PICK 등록 및 갤러리 실행 확인. 결과는 imageorder-upgrade-report에 보존한다.
- 이 스크립트는 아직 실제 서명된 RC가 없으므로 실동작 미검증. 서명 APK의 실제 사진 첨부 E2E 및 물리기기 Play Protect는 별도 시험이다.

## 2026-11-26 — 서명 후보 생성 완료
- 실제 기존 PKCS#12 키 복구 및 기존 공개 APK signer SHA-256 동일 확인. 공식 SDK build-tools 35.0.0 도구는 전용 CI 45810925119 artifact에서 확보하여 로컬에서 서명. 개인키 및 암호는 GitHub에 전송하지 않았으며 임시 복호화 파일은 제거.
- unsigned artifact 15110340536 (8e710f85 기준)를 기존 인증서로 서명. APK SHA-256: 4356a664f52fd8a52b38bb8bc3a9f55a2d3b2fda6a017106cad5ea2817cc2d57. v2/v3, zipalign, package/version/minSdk 26 검사 통과. v1은 검증 결과 false이며 minSdk 26에서 v2/v3로 지원. 동일 암호 파일을 두 번 넘길 때 PasswordRetriever EOF 발생하여 별도 임시 파일 사용으로 수정.
- 실제 서명 APK 업데이트 설치 및 최신 Chrome/OEM 실기기 검수는 미실행. 공개판 변경 없음.
