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
- 외부 패키지 원본 전달이 검증되기 전 v0.5.5 공개 배포 보류. 이 조건은 아래 Android 15 교차 UID 테스트로 충족됨; 출시 판단은 아래의 나머지 실사용 호환성 검증을 따른다.

## 미완료로 유지할 항목
- **다른 UID의 외부 APK 기반 E2E 기본 계약 검증 완료(Android 15)**: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45148994457 에서 앱 6/6, 외부 요청자 2/2 통과. `image/png` 및 `*/*`에 대해 3→1→2 선택 순서, 외부 UID의 임시 읽기 권한, 파일명/MIME, SHA-256 원본 일치를 확인했다. 후속으로 단일 이미지 요청, `image/*` 및 Android 13/14 호환성 매트릭스를 추가하여 진행한다.
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

## Android 15 완료 버튼 무응답 수정 (2026-11-23)

- 실제 결함: `targetSdk 35`에서 Android 15의 강제 Edge-to-Edge 레이아웃 때문에 NativeGallery 완료 버튼이 시스템바 입력 영역과 겹쳤다.
- 원래 완료 버튼 Rect `(723,39)-(1039,171)`, 가운데 y=105 → 외부 테스트에서 터치 3방식 모두 앱에 도착하지 않음.
- `NativeGalleryActivity` 루트에 `WindowInsets.Type.systemBars() | displayCutout()` 상하좌우 패딩을 API 35+에 적용한 뒤 Insets top=136, bottom=66.
- 수정 후 완료 버튼 Rect `(723,175)-(1039,307)`, 가운데 y=241 → `OnTouch`, `OnClick`, `finishSelection`, 외부 `onActivityResult RESULT_OK` 모두 로그에 확인.
- Android 15 실기기와 동일한 API 35 에뮬레이터에서 `run 45148994457` 앱 내부 6개+별도 APK 2개 모두 성공.
- v0.5.5는 아직 공개하지 않는다. 추가 MIME, 단일 이미지 및 OS 매트릭스 검수 후 정식 서명/출시 여부 판단.

## 시스템 Photo Picker 순서 선택 연동 — API 35 / R Extensions 12

- Android 공식 `MediaStore.EXTRA_PICK_IMAGES_IN_ORDER`(API 35 또는 R Extensions 12 이상)은 `ACTION_PICK_IMAGES`에서 선택 순서대로 URI를 반환한다.
- Image Order가 갤러리 권한 거부로 플랫폼 Photo Picker를 대체 호출할 때, 지원 기기에 이 옵션을 설정하고 **이미 순서가 검증된 URI는 재선택 없이 바로 외부 요청 앱에 전달**하도록 구현.
- 외부에서 결과가 단 1장일 때는 정렬 모호성이 없으므로 구형 OS의 fallback도 즉시 전달.
- 순서가 보장되지 않는 구형 플랫폼의 다중 선택은 기존의 수동 순서 지정 단계 유지.
- URI/원본 바이트는 여전히 재인코딩·복사·파일명 변경을 거치지 않음.
- 참고: https://developer.android.com/reference/android/provider/MediaStore#EXTRA_PICK_IMAGES_IN_ORDER
- 직접 플랫폼 picker 호출은 시스템 Photo Picker를 교체하거나 모든 앱의 자체 첨부 창을 강제 대체하는 기능은 아니다.

## 2차 세션 기술 인수인계 — v0.5.5 검증 확대 (2026-11-23)

- 기본 Android 13/14/15 외부 APK 테스트 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45150025193 (각 OS 앱 6개+별도 패키지 4개).
- 원본 파일명/바이트/MIME와 다른 UID의 URI 읽기 권한을 실제 검증한다. 최근 확대 테스트는 PNG/JPEG/WebP 5개 이미지의 5→2→4→1→3 선택 순서를 포함한다.
- 확장 검증 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45164473132 (Android 13/14/15 모두 통과).
- Android 13/14에서 StaleObjectException을 유발한 UiAutomator 테스트는 매 클릭마다 화면 노드를 재탐색하도록 수정. 실제 앱 원본 반환 결함과 구별한다.
- Android 15 이상 강제 Edge-to-Edge 완료 버튼 가림 결함을 WindowInsets 적용으로 수정. 갤러리 완료 버튼 탭/외부 반환 통과: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45148994457
- Android MediaStore.EXTRA_PICK_IMAGES_IN_ORDER(API 35 또는 R Extensions 12+)를 권한 거부 시 시스템 Photo Picker fallback에 적용해 2차 재선택 과정을 제거하도록 구현. 단일 사진 fallback은 EXTRA_PICK_IMAGES_MAX=1이 Android에서 무효이므로 해당 extra를 넣지 않는다.
- Android 8~12 권한 거부 시 시스템 GET_CONTENT 선택창에서 NativeGalleryActivity 자체를 제외해 Image Order가 다시 자기 자신을 열어 반복하는 경로 차단.
- 개발 CI/외부 APK E2E는 소스 변경에만 동작하도록 경로 필터 조정, 동일 브랜치 오래된 실행 취소(최신 실행만 유지) 추가.
- 차기 정식 릴리스에서 공식 APK는 ImageOrder.apk, 공식 소스는 ImageOrder-Source.zip. 이전 설치 링크/사용자의 기존 사용 환경 보호를 위해 ImageOrderStudio.apk, ImageOrderStudio-Source.zip 별도 호환 별칭 제공. 정식 공개 브랜치는 아직 변경하지 않았다.
- 이 2차 세션의 최신 소스 브랜치: image-order/dev-v2. 최종 승계 기준 커밋은 git 브랜치 HEAD를 읽어 결정하며 문서에 오래된 SHA를 고정하지 않는다.
- 최신 확장 시스템 Photo Picker fallback 포함 APK 개발 CI 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45165284373
- 최신 확장 외부 UID E2E: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45165284367 (결과 완료 여부를 다음 재개 시 조회).
- 미완료: Android 16(API 36), 실제 Samsung 갤러리/브라우저의 개별 첨부창, ACTION_PICK 및 system Photo Picker fallback의 외부 APK 완전 왕복, 수신 앱의 별도 재정렬과 업로드 후 순서 검증, 비정상 Activity 재생성.
- v0.5.5 공개 배포 여부는 최신 테스트 및 실제 앱 호환성 확인 후 판단한다. 공개된 최신 APK는 아직 v0.5.4이며 기존 서명 인증서를 유지한다.

## 다음 단계: 실제 HTML 파일 첨부 통합 QA (2026-11-23)

- 별도 APK/UID(`com.twobornot.imageorder.caller`)에 테스트용 WebView 액티비티를 추가하고, 네트워크/INTERNET 권한 없이 로컬 HTML `<input type=file accept=image/* multiple>`을 실제로 클릭한다.
- WebChromeClient.onShowFileChooser()의 FileChooserParams.createIntent()를 사용하여 Image Order를 호출하고, parseResult()로 URI 배열을 돌려받아 HTML `input.files`까지 전달한다.
- PNG/JPEG/WebP 혼합 5장의 사용자 탭 순서 5→2→4→1→3이 실제 웹 페이지의 FileList 이름·형식·크기 순서와 일치하는지 검사한다.
- 별도 UID의 원본 MIME/파일명/SHA-256 및 읽기 권한도 검증한다.
- WebView는 실제 Chrome 브라우저가 아니므로 양쪽을 구분하고, Chrome과 삼성 인터넷의 실기기 개별 검증은 별도 항목으로 남긴다.
- Android 16(API 36)을 기존 Android 13/14/15 외부 APK 테스트 매트릭스에 추가했다. `ACTION_PICK` MIME+URI 및 URI-only 입력을 별도 외부 앱 테스트로 추가했다.

## WebView 다중 선택: Chromium 기본 파서 결함 진단 (2026-11-23)

- Android 13/14/15/16에서 앱 내부 8개, 일반 독립 앱의 외부 GET_CONTENT/ACTION_PICK 7개는 모두 성공했으나 신규 WebView HTML 첨부 테스트에서 `RESULT_OK=-1`임에도 `FileChooserParams.parseResult()`가 `null`을 반환.
- Chromium `AwContentsClient.parseFileChooserResult` 구현이 `intent.getData()`만 읽는 현상을 공식 소스 및 사례에서 확인. `ClipData`에 들어 있는 여러 이미지 URI를 무시하여 한 장도 전달하지 않는 경로가 발생.
- 이 문제를 숨기기 위해 Image Order 출력 이미지를 병합하거나 이름을 바꾸지 않는다. 정상 다중 파일 선택 결과는 Android 표준 `ClipData`(사용자가 누른 순서)와 읽기 권한으로 그대로 제공.
- 독립 WebView QA 호스트에는 `OrderedWebFileChooserResult`를 추가해 `ClipData` 우선, 단일 `Intent.data` 보조로 파싱하도록 수정. 실제 HTML `input.files`의 5개 파일 이름·형식·크기 순서가 유지되는지 실증한다.
- 이 호스트 측 수정이 외부 Chrome, 다른 앱의 낡은 WebChromeClient를 자동 교체하지는 않는다. 수신자가 `ClipData`를 무시하는 경우 단일 URI 제공만으로는 다중 사진 보장을 충족하지 못한다.
- Chromium 구현: https://chromium.googlesource.com/chromium/src/+/refs/heads/main/android_webview/java/src/org/chromium/android_webview/AwContentsClient.java
- 실제 WebView 앱 사례: https://github.com/home-assistant/android/issues/7548

## Android 16 계측 테스트 입력 안정화 (2026-11-23)

- 최초 Android 16 E2E에서 외부 GET_CONTENT `*/*` 테스트가 사진 3회 신속 탭 직후 `Done 2`로 나타났다. 갤러리 반응이 완료되기 전에 다음 UiAutomator 클릭을 전송해 실제 UI 선택 개수와 테스트가 어긋난 사례.
- Android 16에서 같은 실행의 독립 WebView HTML 업로드는 `FileChooserParams.parseResult` 기본 null을 우회한 뒤 실제 `FileList` 5개 항목(파일명·MIME·크기) 순서까지 완전히 도달하는 로그 확인.
- 테스트가 클릭 명령 성공을 선택 완료로 착각하지 않도록 사진마다 완료 버튼의 선택 개수를 재확인한다. 재렌더/노드 교체로 누락된 시도에 한하여 최대 2회 재시도. UI가 3회 내 응답하지 않으면 여전히 실패 처리한다.
- 일반 사용자 UI와 선택 순서 처리 로직은 변경하지 않으며, 테스트 조건만 가시적 UI 확정 상태 기준으로 강화한다.

## Android 13~16 최종 독립 앱 및 HTML 업로드 E2E 64/64 통과 (2026-11-23)

- 마지막 실제 코드 변경: `1f81002fd9f8b1e95d79b8286fa1fd263ee14c4b` (빠른 연속 선택에도 각 사진의 선택 카운터를 확인하고 다음 사진으로 진행).
- Android 개발 CI: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45178396631 — 소스/단위 검사, APK 빌드, 전체 소스 ZIP 패키징 성공.
- 독립 Android 4개 버전 E2E: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45178396640 — 33/34/35/36 모두 성공.
- 각 OS마다 **앱 내부 8개 + 별도 UID의 외부 앱 테스트 8개 = 16개**, 4개 OS 합산 **64/64 통과**.
- 실제 `ACTION_GET_CONTENT`의 `image/png`, `image/*`, `*/*`, 단일/다중 요청, `ACTION_PICK` MIME+MediaStore URI 및 URI-only 경로의 반환/읽기 권한/원본 SHA-256/파일명/MIME 검증.
- 실제 로컬 HTML `<input type=file multiple accept=image/*>`과 WebChromeClient를 사용하는 별도 Android WebView APK에서 PNG/JPEG/WebP 다섯 장을 5→2→4→1→3 순서로 선택, URI/원본 바이트 검증뿐 아니라 최종 HTML `FileList` 이름/형식/크기/순서까지 성공.
- **주의할 계약 차이:** Chromium 기본 `FileChooserParams.parseResult()`는 다중 URI의 `ClipData`를 무시하므로 별도 WebView 호스트에서 `OrderedWebFileChooserResult`로 보정했다. 이는 외부 브라우저 앱의 내부 로직을 자동 패치하는 기능이 아니다.
- 전체 개발 소스 ZIP은 GitHub CI의 `ImageOrder-v0.5.5-complete-source` 아티팩트이며, 주요 소스 89개 파일/디렉터리 항목을 포함하고 무결성 및 비밀 서명키 제외 확인.
- 공개 v0.5.4와 서명된 APK는 변경하지 않았다. 다음 우선과제: 실제 Galaxy 삼성 갤러리/삼성 인터넷/Chrome 업로드, Android 8~12 구형 OS fallback, 실제 서버 수신 후 이미지 순서 검증, 수신 앱의 내장 WebChromeClient 호환 범위 분석.

## 2026-11-23 밤 — 외부 앱 회전 검증 / 시스템 Picker 재생성 보강

- 독립 UID의 `ACTION_GET_CONTENT` 호출에서 두 장 선택 후 가로 회전→세로 복귀→세 번째 사진 선택을 실행하여 원본 URI, 선택 순서, SHA-256, 이름, MIME, 읽기 권한을 재검증함.
- Android 13/14/15/16 네 버전 모두 실제 외부 앱 테스트 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/45191830916
- Android 13/14/15/16 기본 내부 갤러리 재생성 회귀도 이전 기준 https://github.com/sangkukzoa-ctrl/assets/actions/runs/45179770404 에서 통과.
- 권한 거부 후 외부 시스템 사진 선택창을 기다리는 동안 부모 Activity가 재생성되어도 선택창/권한 창을 중복 실행하지 않도록 `fallbackPickerPending` 상태를 `onSaveInstanceState`에 보존.
- pending 상태가 Android Activity 재생성 이후 유지되는 전용 내부 계측 회귀 테스트를 추가함.
- 새 pending 수정은 CI 및 Android 매트릭스 재검증 대상으로 남겨 두며, 별도 공개 APK는 생성하지 않음.

## 2026-11-24 — 시스템 Picker 반환 QA 및 CI 외부 서버 지연 대응
- 이전 커밋 `1b12aa74`: Android 13/15/16 E2E 모두 통과. Android 14는 Gradle 의존성 다운로드 중 Maven Central HTTP 429(Too Many Requests)로 실패, 앱 계측 테스트 실패와 구분해 기록. 해당 Android 14 job만 재실행 요청.
- 테스트용 `PickerHostActivity`에서 직접 NativeGalleryActivity 선택 가능하도록 확장(릴리스 APK에는 디버그 호스트 제외).
- Android 15/16에서 OS의 선택 순서가 보장된 `ClipData` 형태를 모사해 NativeGalleryActivity의 실제 `onActivityResult` 처리 경로에 전달한 뒤, 첨부 요청자가 PNG/JPEG/WebP 원본 파일 3개를 3→1→2 순서로 받는지 검증하는 단말 계측 테스트 추가. 이 테스트는 플랫폼 Photo Picker UI 직접 조작 테스트와 구별.
- GitHub E2E에서 Maven Central 429일 때만 재시도하고, 실제 계측 테스트 실패에서는 즉시 실패하도록 제한. Gradle 빌드에도 동일한 다운로드 일시제한 복구 적용. 동시 에뮬레이터 다운로드 수를 2로 제한.
- 공개 v0.5.4 유지, v0.5.5 기능 테스트 및 실제 OEM 갤러리 호환 시험 계속.

## 2026-11-24 밤 — 에뮬레이터 CI 실행 스크립트 수정
- `24cec387` 개발 CI 성공(45333739018). 교차 앱 QA 45333739057의 네 환경은 테스트 전에 /usr/bin/sh의 함수 구문 오류로 종료됨. 앱 기능 실패와 구분.
- android-emulator-runner의 script 각 행을 독립 셸 명령으로 실행하는 방식에 맞추어 Bash 파일 `tests/run-cross-app-qa.sh` 단일 호출로 변경.
- Maven 재시도 공통 helper `tests/gradle-with-retry.sh`와 모의 Gradle 테스트 `tests/gradle-retry-test.sh` 추가. 성공/일시 429/지속 429/계측 실패/혼합 실패/컴파일 실패 여섯 시나리오를 네트워크 없이 확인.
- 앱 소스와 기존 계측 테스트 자체는 그대로 유지. 신규 커밋에서 네 Android 버전을 재검증한다.

## 2026-11-24 밤 — Android 13~16 전체 회귀 성공 / 실제 SAF 외부 앱 테스트 추가
- 기준 커밋 a03217c6: 개발 CI 45398517306 및 Android 13/14/15/16 교차 앱 QA 45398517365 전부 성공.
- 시스템 Photo Picker 순서 보장 반환 데이터를 모사한 혼합 이미지 원본 전달 계측 테스트까지 포함.
- 별도 UID의 APK에서 실제 ACTION_OPEN_DOCUMENT로 Android DocumentsUI를 열고 Image Order 공급자의 원본 한 장을 선택하는 SafExternalCallerTest 추가.
- 권한 없는 사전/미선택 URI 접근 거부, 선택한 URI의 이름/MIME/크기/SHA-256, 쓰기 거부, 지속 읽기 권한 확인을 목표로 한다.
- SAF의 다중 선택 순서는 DocumentsUI가 제어하므로 이 시험은 순서 보장을 주장하지 않는다. 새 테스트의 CI 결과는 미확정.

## 2026-11-25 — SAF DocumentsUI 파일 탐색 회귀 수정
- 3a1fba35 개발 CI 45411013086 성공. Android 13~16 QA 45411013244에서 외부 테스트 각각 9/10 통과, 신규 SAF 테스트만 WebP 파일명 탐색 단계 실패. 기존 원본 반환 기능은 정상.
- DocumentsUI 그리드의 파일명 표시 차이 및 목록 스크롤에 대응해 시스템 List view 메뉴와 정확한 파일명 탐색을 추가. 실제 문서 URI와 SHA-256 등의 기존 검증 조건 유지.
- 실패 화면/계층을 Download에 보존하고 계층 XML을 logcat으로 기록하여 다음 진단 가능하도록 개선. 이전 아티팩트의 내부 화면 자료는 현재 환경에서 직접 확인하지 못했으므로 그리드가 실패의 확정 원인이라고 단정하지 않음.

## 2026-11-25 — SAF 검증 완료 / 동명 이미지 재선택 회귀
- 기준 35cbfbb0의 개발 CI 45537277902 및 Android 13~16 실제 DocumentsUI 교차 UID QA 45537277964 모두 성공.
- 동일 파일명, 다른 앨범 및 다른 원본 바이트의 PNG 3장을 별도 APK에서 실제 선택(3→1→2→1 해제→1 재선택), 최종 3→2→1 순서와 URI ID, 파일명, MIME, SHA-256, 읽기 권한을 검사하는 계측 테스트 추가.
- 앱 기능 소스는 변경하지 않고 디버그 fixture/외부 테스트 및 정적 검사만 확장. 대량 첨부, OEM 브라우저 실기기, Android 8~12는 별도 검증 대상으로 유지.

## 2026-11-25 — 기본 100장 첨부 한도 스트레스 테스트
- 실제 MediaStore PNG 102개를 생성하고 직접 NativeGalleryActivity에서 100장의 비단조 순열(37의 배수 mod 100)로 선택하는 계측 시험 추가.
- 101번째 선택 거부, 기존 사진 해제 후 새 원본 마지막 추가, 다시 초과 선택 거부, 100개의 URI·파일명·MIME·원본 바이트·중복 여부 확인.
- 같은 UID의 디버그 호스트와 GridView 실제 선택 콜백을 사용하므로 대량 물리 터치 또는 대량 교차 UID 전송 시험과 구분. 기존 별도 UID 시험은 유지.
- 앱 기본 선택 한도(100장)는 변경하지 않음. 정식 배포 보류.

## 2026-11-25 — 100장 스트레스 통과 / Android 10~12L 검증 확대
- e124b18d 개발 CI 45576569718 및 Android 13~16 QA 45576569662 모두 성공. 실제 MediaStore 102장, 선택 한도 100장, 초과 거부/해제/대체 선택 및 전체 원본/순서 검증 통과(동일 UID 호스트, 외부 UID 시험은 별도 유지).
- API 33+ READ_MEDIA_IMAGES 테스트 준비를 API 29~32 READ_EXTERNAL_STORAGE로 분기. API 29에서는 테스트 WebP 생성에 구형 WEBP enum 사용. 실제 원본 반환 정책은 동일.
- NativeGallery의 시스템 Photo Picker fallback을 기존 PickerDecision과 통일하여 R SDK extension 2 이상에서도 지원, 정렬 보장은 extension 12/API35 이상. 플랫폼 선택창 실행 실패 시 자기 Activity를 제외한 legacy chooser로 전환.
- legacy chooser의 단일/다중 계약 및 자기 자신 제외 계측 검사 추가. Android 10(API29), 11(API30), 12L(API32)과 기존 13~16 전체 회귀 매트릭스 실행 대상으로 확대. API26~28 테스트 fixture는 별도 보강 필요.
- 신규 검증 결과는 다음 실행에서 확인. 공개판 변경 없음.

## 2026-11-25 — Android 10~16 통과 / Android 8~9와 12.0 검증 확대
- 69062295 개발 CI 45596162686 및 독립 외부 UID E2E 45596162629: API 29/30/32/33/34/35/36 전부 성공. 구형 WebView 요청자의 MODE_OPEN_MULTIPLE을 EXTRA_ALLOW_MULTIPLE에 명시한 수정 포함. 외부 브라우저 자동 교체를 의미하지 않음.
- API26~28의 테스트 원본 생성은 실제 공개 Pictures 파일과 legacy MediaStore DATA 등록을 사용하고 API29+의 scoped storage 경로는 유지. 내부/외부 계측 테스트는 동일 원본 fixture helper 사용.
- API26~27에서 UiAutomation.grantRuntimePermission 대신 테스트 셸 pm grant 사용. API26~28의 쓰기 권한은 테스트 대상 APK에만 부여. 독립 호출자는 기존처럼 저장소 권한 없음.
- QA 매트릭스 API26~36 전수 확대. 앱 본체/공개 APK/서명/기존 원본 검증 조건 변경 없음. 신규 CI 결과는 미확정.

## 2026-11-25 — 핵심 기능 우선: 실제 HTTP 업로드 / 비고정 시스템 선택창
- 8971bcf2 개발 CI 45605657883 성공. E2E 45605657945의 API26/28은 내부 13개 및 외부 10/11 성공, SAF 테스트에서 Image Order 대신 Android 기본 MediaDocumentsProvider를 선택하여 URI authority 불일치. API27은 google_apis x86_64 시스템 이미지 SDK 설치 실패. API29/30/32 전체 성공 확인, 나머지 실행 상태는 CI 기록 참조.
- 독립 WebView 호스트 기존 FileList 검증 유지. 추가로 루프백 HTTP 서버에서 실제 HTML FormData multipart POST 수신 후 파일 순서, 이름, MIME, 크기, SHA-256 검증. 별도 테스트에서 package 지정 없이 Android 시스템 chooser를 열고 Image Order를 선택하여 동일 HTTP 전송 검사.
- HTTP 권한과 서버는 externalcaller 테스트 APK에만 포함, 127.0.0.1 바인딩. Image Order 본체/공개 APK/서명 변경 없음. 실제 Chrome/삼성 인터넷 및 강제 시스템 Photo Picker 대체는 아직 미완료. 새 테스트는 CI 검증 전이며 실패 시 로그 기반 수정.

## 2026-11-25 — 실제 HTTP 전송 통과 / 시스템 호출 분기 진단
- c684e5da E2E 45609253157에서 API26/28/29/30/32의 패키지 지정 HTML multipart HTTP 원본·순서 검증 실패 없음. 비고정 시스템 chooser만 실패(API26/28/29: 항목 탐색, API30/32: 클릭 후 갤러리 미진입). API32 회전 회귀 1개 실패도 별도 확인. API27 시스템 이미지 설치 실패 지속.
- Android 공식 GET_CONTENT takeover 및 Browse→DocumentsUI 전달 경로를 확인. 비고정 테스트는 실제 chooser/Photo Picker Browse/파일 선택기 앱 목록을 탐색하며 native gallery 진입을 반드시 검증. 패키지 강제 지정이나 시스템 설정 변경 없음.
- DocumentsProvider 제목을 Image Order (Files)로 변경하여 native gallery 앱 선택 항목 Image Order와 구별. SAF 테스트는 일반 Recents에서 동명 원본을 먼저 선택하지 않도록 공급자 루트를 먼저 탐색. URI authority 및 SHA-256 검증 유지.
- 후보 ResolveInfo 및 실패 UI hierarchy를 CI 콘솔/아티팩트에 저장. API27은 x86 이미지로 시도(아직 설치 가능 여부 미확정). 신규 테스트 결과 미확정. 공개판 변경 없음.

## 2026-11-26 — DocumentsUI 통합 항목의 앱 실행 버튼 확인
- a0d6f82e CI 45613841179 성공, E2E 45613841232에서 API26/27/28 전체 성공. API29~36 시스템 chooser 실패, 일부 최신 SAF 탐색 회귀. API27 x86 설치 및 테스트 성공.
- resolver 후보: Image Order priority 0, Files 100, 최신 시스템 Photo Picker 101~110. AOSP RootsFragment는 같은 package의 root와 activity를 RootAndAppItem으로 통합한다. API34 실제 hierarchy에 별도 content-desc 'Open Image Order (Files)' 확인. 제목을 누르면 파일 공급자, 별도 버튼은 앱 실행 경로. https://android.googlesource.com/platform/packages/apps/DocumentsUI/+/265ccf6333c739b7a020478f6bf5eca2a8accf30/src/com/android/documentsui/sidebar/RootsFragment.java
- 실제 UI 버튼을 우선 탐색/클릭하도록 개선. Android16 Photo Picker의 More 메뉴 지원, 무조건 Back/화면 스와이프 제거, 스크롤 가능한 항목만 조작. SAF는 provider All photos 폴더를 명시적으로 탐색하고 stale node 재탐색, 파일명 content-desc도 지원.
- 제품 SAF 안내문 변경: 순서 지정은 앱 실행을 통해 사용한다는 의미를 명시. 파일 원본/권한/패키지/서명 변경 없음. 신규 실제 UI 검증 결과 미확정. 시스템 Photo Picker 직접 호출을 대체한 것은 아님.
