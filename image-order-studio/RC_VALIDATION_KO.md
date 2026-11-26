# Image Order v0.5.5 — 검수 후보 (공개하지 않음)

기준 제품 소스: d810802d557101af0880ed3c13bed112b8e943e3. 기존 public beta v0.5.4는 유지한다. Android API26~36 11/11 통과(45664554476), 실제 Chrome 113/124 image/generic 4/4 통과(45780368542). 통합 이후 CI에서 API35 이미지 test 시작 timeout으로 단일 job 재실행(45791982393 attempt 2), 나머지 3개 통과. 통합 Android 전수 재검증은 진행 중이다.

## 검수 APK
- 이 workflow는 unsigned v0.5.5 후보 APK, 이전 공개 APK에서 추출한 공개 인증서 fingerprint, 검수 문서만 artifact로 남긴다. 서명되지 않은 APK는 설치용이 아니다.
- 기존 개인키는 공개 저장소/아티팩트에 보관하지 않는다. 기존 PKCS#12 및 암호 파일을 확보한 안전한 서명 환경에서 sign-candidate.sh를 사용한다. 새 키 생성 금지.
- 서명 v2/v3, 기존 v0.5.4와 SHA-256 signer fingerprint 일치, package ID와 versionCode/Name, zipalign 검사 후에만 RC 파일 생성.
- 서명 후 별도 디바이스에서 공개 v0.5.4 설치 → RC 덮어쓰기 설치 → 실제 갤러리 실행 및 원본 선택 검증. 실기기 Play Protect 동작과 최신 Chrome/삼성 인터넷 호환은 실제 사용자 검수 대상.
- 공개 release 업로드/태그 이동은 이 workflow가 실행하지 않는다. 기존 목표의 direct ACTION_PICK_IMAGES 및 임의 앱 수신 정렬 문제는 미해결로 유지.

## 실제 Chrome 검수 경로
웹페이지 사진 첨부 → 시스템 Photo Picker의 찾아보기/Browse → 파일 앱 탐색 메뉴 → Image Order (Files)의 별도 앱 열기 버튼 → 선택 순서대로 사진 선택 → 완료. 일반 파일 첨부에서는 처음에 Media/Media picker/Files를 누를 수 있다. 공급자 명칭만 눌러 들어가는 SAF 목록은 선택 순서 보장 경로가 아니다. 테스트는 순서를 일부러 5→2→4→1→3으로 변경하여 확인한다.
