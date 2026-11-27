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

## 2026-11-26 — API26~36 핵심 비고정 호출·HTTP 전체 통과
- 847b928c CI 45655160628 성공, 45655161207 종료. API26/27/28/29/30/33/34/36 전체 통과, API31/35 SAF UI 탐색만 실패, API32 회전 전환만 실패. 따라서 비고정 시스템 chooser→native gallery→HTTP 원본 순서 검증은 11/11 환경 성공. 상용 Chrome과 직접 ACTION_PICK_IMAGES 대체는 별도 미완료.
- SAF 탐색을 클릭 성공 여부가 아니라 실제 UI 상태 기반으로 재작성. Open from drawer 내 공급자 행, All photos 실제 파일 목록 행, 현재 폴더/파일을 구분하고 좌표 터치 및 단계 로그 추가. 원본 authority/doc ID/권한/크기/hash 검증 유지.
- 회전 검증은 실제 display 가로·세로 변경과 confirm UI 복귀를 각각 기다리고, UiAutomation 전환 실패 시 테스트 에뮬레이터 WindowManager 명령으로 재시도. 선택 수와 최종 원본 순서 검증 유지. 테스트 종료 후 회전 잠금 해제.
- Chrome 독립 브랜치 942d9b21, run 45663873549 API34 실행 중 / API35 대기. 본체·공개판 변경 없음, 신규 회귀 결과 미확정.

## 2026-11-26 — 실제 Chrome 검증 별도 브랜치
- 기존 847b928c API26~36 CI 45655161207 진행 중이므로 독립 image-order/chrome-qa 브랜치에서 병행. 제품 본체 변경 없음.
- 실제 설치 Chrome(com.android.chrome)에서 image/* 및 generic HTML multiple 파일 입력, 자체 갤러리 실제 진입, 5개 선택, 실제 multipart 서버의 순서/파일명/MIME/SHA-256 검증. WebView 대체 없음. Browser UA 및 APK 버전 기록.
- API34/35 Play Store emulator 이미지 사용. 초기 온보딩만 테스트 플래그로 생략 시도, picker feature flag 변경 없음. Chrome 미설치/온보딩/선택창 장애는 실패로 기록. 실제 CI 결과 미확정. 통과 후 개발 브랜치 병합 검토.

## 2026-11-26 — Chrome 1차 검증 결과와 환경 개선
- 847b928c 개발 CI 45655160628 성공. E2E 45655161207에서 API26/27/28/29/30/33/34 전부 성공(비고정 시스템 chooser 및 실제 HTTP 포함). API31은 SAF 원본 탐색, API32는 화면 회전 landscape 확인만 실패; 두 환경의 비고정 chooser 통과. API35/36 실행 중 확인.
- Chrome QA 45655688471: API34 Chrome 113.0.5672.136 실제 페이지 GET 성공, 알림 온보딩 화면으로 파일 입력 가시성 실패. API35는 Maven Central HTTP429로 APK 빌드 실패, 브라우저 미실행.
- 실제 Chrome 알림 안내의 No thanks 버튼만 UI로 처리. 파일 입력 자체를 접근성 라벨을 갖춘 가시적 HTML 기본 컨트롤로 개선, 업로드 전 5개 선택 DOM 표시 검증 추가. 브라우저 picker 플래그/반환 방식 변경 없음.
- 에뮬레이터 기동 전 APK·계측 APK 빌드 및 캐시 확보 후 기동 단계 offline 빌드 사용. HTTP429 자체의 근본 해결은 아님. Chrome 최신 버전 실기기 검증 별도 필요. 제품 본체 변경 없음, 신규 결과 미확정.

## 2026-11-26 — Chrome 테스트 실행기에서 UTP 의존성 제거
- Chrome run 45663873549: API34 Chrome 113.0.5672.136, API35 Chrome 124.0.6367.219. 두 환경 모두 host APK prebuild 성공, 오프라인 AGP connectedDebugAndroidTest 단계에서 android-test-plugin-host-additional-test-output:31.9.2 미캐시로 중단. 신규 Chrome UI 테스트 자체는 미실행.
- prebuild된 제품 debug/독립 caller/AndroidJUnitRunner APK를 그대로 adb install하고 실제 am instrument -w -r 실행으로 전환. UTP host plugin 경로 제거. 실행 결과는 stdout raw transcript 및 로그 보존. 두 지정 테스트의 시작/성공 각각 1회, JUnit OK (2 tests), 종료 코드 -1 및 skip/failure 없음까지 강제 검증. 가짜 transcript self-test 추가.
- 기존 dev-v2 ade9799d 개발 CI 45664554543 성공, 11종 E2E 45664554476 실행 중. Chrome 브랜치만 변경, 본체/공개판 변경 없음. 신규 실행 결과 미확정.

## 2026-11-26 — 전체 Android 회귀 통과, Chrome 실제 권한 분기 처리
- dev-v2 ade9799d CI 45664554543 및 45664554476 모두 성공. API26~36 11/11 전체 회귀 성공. 실제 상용 Chrome 검증은 별도.
- Chrome ADB 실행 45665625974: API34/35 APK 설치·AndroidJUnitRunner 실행·실패 검출 정상. 양쪽 generic 테스트는 실제 Chrome 알림 안내를 넘고 파일 첨부를 눌렀으나 Chrome CAMERA 권한 안내에서 정지. 이후 image 테스트는 이전 DocumentsUI 창이 전면에 남아 시작 실패. 브라우저 첨부 결과 검증에는 아직 도달하지 못함.
- Chrome 전용 UI 탐색에서 관측된 카메라 foreground-only 버튼을 사용자 동작으로 선택. 실제 Chrome 파일 선택기 Files 항목 분기 대응. 테스트 사이 Chrome 프로세스/task 종료 및 별도 task 실행, 실패 정리 전에 activity stack과 Intent action 로그 저장. Chrome picker 기능 플래그 변경 없음, 본체/공개판 변경 없음. 신규 검증 미확정.

## 2026-11-26 — 실제 Chrome 최초 원본 순서 HTTP 검증 성공
- 45750639062 API35 Chrome 124.0.6367.219 job 139677312319: chromeImageInputUploadsOriginalsInTapOrder 성공. 실제 Chrome -> Photo Picker -> Browse -> DocumentsUI -> merged app action -> NativeGalleryActivity -> 5 originals -> 실제 multipart POST. 파일명/MIME/순서/SHA-256 일치. 실제 Chrome 성공 로그 확보. generic 테스트는 최초 CAMERA 권한 승인 이후 원래 페이지의 빈 파일 입력으로 돌아와 실패. API34는 Maven 429로 사전 빌드 단계 실패.
- 관측된 camera 승인 이후 동일 페이지의 파일 선택이 비어 있을 경우에만 HTML 입력을 한 번 다시 클릭. 기존 성공 경로 유지, 웹 페이지 위에서 불필요한 메뉴/스크롤 금지. generic 여부를 성공 로그에 명시.
- Chrome CI 빌드 1회 후 3 APK 및 SHA256 manifest를 artifact로 전달, API34/35는 동일 바이너리로 검사하고 Gradle 다운로드하지 않음. 빌드 단계 자체의 Maven429 가능성은 남음. 신규 run 결과 미확정. 제품 본체 및 dev-v2/공개판 변경 없음.

## 2026-11-26 — Chrome 선택창/테스트 독립성 개선
- 45759785302 공통 APK 빌드 및 양쪽 설치 성공. API34/35 generic: camera 승인 후 다시 열어 실제 com.android.intentresolver CHOOSER 진입 확인, 이후 웹페이지로 돌아가 실패. API34 image: Chrome photos/videos 권한 안내에서 중단. API35 image: 이전 generic 실패 후 새 HTTP 페이지 GET 미도달. 이전 45750639062 API35 image 실제 HTTP 성공 기록 유지. 5차는 재현성 확보 실패.
- Chrome chooser에 Files/Browse/Media picker 등 실제 표시되는 항목을 명시적으로 선택하고, 일반 chooser에서 화면 스와이프 금지. 권한 안내에서 사진 접근 처리(격리된 합성 테스트 이미지 전용). 화면 전환 순간 text/desc/resource ID를 수집하여 종료 후 화면만 보는 문제 해소. Chrome 자체 feature flags 및 제품 권한 변경 없음.
- API34/35 x image/generic 4개 독립 에뮬레이터 job으로 분리. 한 번 빌드한 동일 APK 사용. 각 job은 단일 정확한 테스트 메서드 실행 및 결과 strict gate 통과 필요. 양쪽 테스트의 독립성과 재현성 검증. dev-v2 및 제품 본체 변경 없음, 신규 결과 미확정.

## 2026-11-26 — Chrome 4/4 실제 업로드 성공 및 개발 브랜치 통합
- 독립 Chrome run 45780368542 전체 성공, 공통 APK 빌드 성공. API34 Chrome 113.0.5672.136 및 API35 Chrome 124.0.6367.219에서 각각 이미지 전용/일반 파일 첨부 4개 job 통과. 실제 NativeGalleryActivity 실행 로그, 각 5개 원본 파일의 서버 순서/이름/MIME/SHA256 및 JUnit OK(1 test) 확인. job 139774862339/139774862344/139774862390/139774862415.
- 실제 동선: 이미지 첨부→시스템 Photo Picker→Browse→DocumentsUI의 Image Order (Files) 앱 실행 버튼→Image Order native gallery→Chrome→HTTP POST. 일반 첨부는 앞단 chooser의 Media 또는 Media picker 항목을 추가 선택. 공급자 제목 자체를 누르면 순서 보장 없는 SAF 파일 목록임.
- dev-v2 ade9799d의 API26~36 전체 회귀 성공(45664554476)을 보존하며 chrome-qa 0c1de9a의 검증 소스/CI 병합. 제품 app/ 경로 변경 없음. Chrome CI는 dev-v2에서도 실행 가능하게 변경. 기존 일반 regression에서는 chromeQa 미지정 시 Chrome 전용 두 테스트는 의도적으로 skip, Chrome 전용 CI는 skip 실패 처리. 통합 커밋 재검증 예정.
- 검증 범위는 에뮬레이터 및 위 Chrome 버전에 한정. 현재 최신 Chrome/OEM 실기기 및 직접 ACTION_PICK_IMAGES 전역 교체는 미해결. 공개 v0.5.4 및 서명 변경 없음. 목표 축소 금지.

## 2026-11-26 — v0.5.5 RC 사용자 실기기 검수: 핵심 호출 실패
- 사용자 직접 설치 후 검수 보고: ChatGPT 앱 무반응, Chat LLM 앱 무반응, Chrome의 Claude 웹 무반응(Image Order 호출 기준). 실사용 합격으로 간주하지 않는다. 기존 API26~36 및 Chrome113/124의 합격 기록은 해당 테스트 경로에만 유효.
- 제품 manifest의 GET_CONTENT/PICK 및 DocumentsProvider 경로를 재확인. 현재 실기기에서 어떤 chooser/Intent가 실제 사용되는지 미확인. ACTION_PICK_IMAGES, 명시적 시스템 컴포넌트, 자체/임베디드 picker, GET_CONTENT takeover/SAF 후보 미노출 등을 구분할 필요가 있다. Android 공식 ACTION_PICK_IMAGES 및 ordered selection extra는 호출 앱의 계약이다. https://developer.android.com/reference/android/provider/MediaStore
- PC용 읽기 전용 진단 스크립트 diagnostics/Capture-AttachmentRoute.ps1 추가. adb 등록 후보 및 Activity START action/type/component/package만 기록하고 원본 로그, URI, 파일명, 채팅 내용은 저장하지 않는다. 실제 실기기 실행 미검증. 스크린샷 또는 실제 진단 로그부터 확보한 뒤 제품 호출 경로를 수정. 접근성 서비스/원본 변경/신규 키 생성 없음. 공개판 유지.

### 사용자 추가 보고 및 최신 Chromium 호출 분기 확인
- GPT 앱 및 Chat LLM 앱은 기존 사진 첨부 UI가 직접 열리며 Image Order 설치 후에도 변화 없음. Claude 웹(Chrome)은 앱 선택 팝업이 열리나 Image Order 항목이 없음. 첨부 버튼 자체가 작동하지 않는 문제는 아님.
- Chromium HEAD SelectFileDialog.java의 showAndroidMediaPickerViaGetContent는 GET_CONTENT resolver가 지정된 Google Media Picker 패키지가 아니면 ACTION_PICK_IMAGES로 전환한다. showExternalPicker는 별도 chooser 경로. Intent priority 상승은 무조건적인 해결책이 아니다. https://chromium.googlesource.com/chromium/src/+/HEAD/ui/android/java/src/org/chromium/ui/base/SelectFileDialog.java
- 기존 Chrome113/124 검증은 Browse→DocumentsUI→merged app action 경로이며 실제 사용자의 첫 팝업 직접 후보 노출과 동일하지 않다. 실제 최신 Chrome 버전/OS/chooser UI 및 ADB action 로그 확인 우선. GPT/Chat LLM의 내부 또는 명시적 시스템 picker 여부는 로그 없이는 구분하지 않는다. 제품 코드를 근거 없이 변경하지 않음. v0.5.5 RC 실사용 합격 보류.

### 2026-11-26 실기기 스크린샷 판독 — 시스템 Photo Picker / Chrome chooser 구분
- 사용자 제공 1000018149.jpg: GPT/Chat LLM/네이버 리뷰 공통 화면. Android 시스템 Photo Picker 형태(선택한 사진 접근 안내, 사진/앨범, 직장 프로필 전환). 표시된 화면에서 Browse/overflow가 보이지 않음. ACTION_PICK_IMAGES 직접 호출 가능성이 높지만 실제 action은 ADB 등으로 확인 필요. 자체 앱 갤러리라고 분류하지 않는다.
- 1000018150.jpg: Claude 웹의 파일 또는 사진 선택 버튼. 1000018151.jpg: Chrome '작업 선택' 팝업에는 카메라, 카메라 캠코더, 파일 세 항목만 존재. Image Order 직접 후보 없음. 파일 버튼 이후 화면 미확보. 이전 Chrome113/124 E2E는 Photo Picker Browse→DocumentsUI→merged app action의 하위 경로이므로 첫 팝업 직접 노출과 구분.
- AOSP PhotoPickerActivity.onPrepareOptionsMenu: Browse visible only isGetContentAction(). https://android.googlesource.com/platform/packages/providers/MediaProvider/+/master/src/com/android/providers/media/photopicker/PhotoPickerActivity.java
- AOSP ComponentResolver의 일반 앱 intent priority 상한 0. https://android.googlesource.com/platform/frameworks/base/+/dda790354c866877613d550afe7bb27e02fe35f7/services/core/java/com/android/server/pm/resolution/ComponentResolver.java
- MediaStore EXTRA_PICK_IMAGES_IN_ORDER API35/R extension12는 호출자 extra이며 전역 사용자 설정이 아님. AndroidX system fallback picker는 시스템 앱 한정. 일반 APK에서 직접 시스템 picker 대체가 가능한지 별도 조사하고 단순 priority/manifest 변경을 성공으로 보고하지 않는다.
- 다음 증거: Chrome 팝업의 파일 버튼 이후 화면 및 왼쪽 탐색 메뉴. 직접 Photo Picker 경로는 actual action 및 OS/extension 확인. 제품 코드 변경 없음. RC 실사용 실패 상태 유지. 사용자 사진의 썸네일/개인 콘텐츠는 저장소에 복제하지 않음.

### 2026-11-27 — Chrome 파일 선택 후 DocumentsUI 진입 확인
- 사용자 화면 1000018156.jpg: Chrome 작업 선택→파일→시스템 DocumentsUI 최근 화면, 개인/직장 탭, '다른 앱의 파일 탐색' 가로 목록. 삼성 갤러리 등 외부 앱 항목이 보이고 우측 목록은 화면 밖으로 이어짐. Image Order가 전체 목록에 없는지는 아직 미확인. 햄버거 탐색 메뉴도 존재. 다음 확인은 가로 목록 전체 및 탐색 drawer에서 Image Order 또는 Image Order (Files), 별도 앱 열기 동작 확인.
- AOSP RootsFragment의 handler app/provider 동일 package 병합 및 AppsRowManager의 앱/루트 표시 구조 확인. 특히 RootsFragment는 ACTION_PICK_IMAGES로 조회되는 패키지를 외부 handler app 목록에서 제외하므로 해당 intent-filter 무조건 추가 시 기존 DocumentsUI 연동까지 손상될 수 있음. https://android.googlesource.com/platform/packages/apps/DocumentsUI/+/265ccf6333c739b7a020478f6bf5eca2a8accf30/src/com/android/documentsui/sidebar/RootsFragment.java
- 화면에서 Image Order 미노출 여부 확정 전 제품 manifest 변경하지 않음. 직접 Photo Picker 경로는 별도 과제. 스크린샷 원본/개인 사진은 저장소에 포함하지 않음.

### 2026-11-27 — 사용자 우선순위 재정렬: 최초 이미지 선택창을 직접 개선
- 사용자 명시: GPT/Chat LLM/네이버 리뷰의 최초 사진 선택창이 참고 대상이며 Claude 웹의 파일/이미지 혼합 UI는 네 사례 중 하나일 뿐. 업로드 절차를 없애려는 원래 목표와 무관한 특정 UI 최적화에 집중하지 않는다.
- P0 직접 Photo Picker 계열 최초 호출 및 원본 순서 반환. P1 GET_CONTENT/PICK 유지, P2 DocumentsUI/혼합 파일 첨부. native-entry-qa 47ea7d0, run 45950093506은 P2 보조 실험으로 분리 보존, 결과에 관계없이 P0 완료로 인정하지 않는다. 주 개발판에는 해당 실험을 병합하지 않음.
- AOSP MediaProvider 시스템 ACTION_PICK_IMAGES filter priority 100~105(https://android.googlesource.com/platform/packages/providers/MediaProvider/+/refs/tags/android-15.0.0_r28/AndroidManifest.xml), AndroidX PickMultipleVisualMedia는 플랫폼 picker 우선(https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.PickMultipleVisualMedia). 순서 extra는 호출자 계약. 다음 기술 검증은 일반 설치된 앱이 비고정 직접 호출에서 실제 후보/실행 가능 여부와 원본 순서 결과를 검증하는 독립 실험. 선언만으로 해결했다고 보지 않는다. 시스템 수준 대안은 일반 APK와 별도 평가하며 권한 및 설치 안전성을 유지한다.
- 개발 목표 문서에 최초 선택창 합격 기준 및 우선순위를 명문화. 이번 커밋은 문서만 변경, 추가 실기기 검수 요청/공개 배포 없음.

### 2026-11-27 — P0 직접 사진 선택 첫 호출 실험
- P2 native-entry-qa run 45950093506: Chrome 4/4 실제 HTTP 통과, 별도 보존, 주 개발판 병합하지 않음.
- P0 전용 image-order/direct-picker-qa: debug-only DirectPhotoPickerTrial activity-alias 등록, 기본 disabled, CI에서 해당 자사 alias만 enable. priority=1000 선언에 대한 실효 priority 및 후보 비교. 일반 release manifest 변경 없음. 실제 NativeGalleryActivity의 PICK_IMAGES max/MIME 계약 처리 추가(실험 브랜치만).
- 별도 UID caller가 package/component/chooser 없이 ACTION_PICK_IMAGES(image/*, MAX=5) 최초 호출. 일반 앱에서 ordered extra를 넘기지 않는 실제 상황을 모사. API33~36에서 actual foreground 및 resolver 기록. system picker 관측 시 취소 후 P0_BLOCKED로 별도 명시(계측 성공과 제품 성공 구분). Native gallery가 실제 나타나면 5→2→4→1→3 원본 bytes/MIME/ClipData 검증. 선택창, 미확인 화면 등은 실패. 시스템 앱/설정/권한 강제 변경 없음. 독립 실험 CI 결과 미확정, 주 개발판과 RC 유지.

### 2026-11-27 — P0 실험 준비 단계 보정
- 46011175857: 공통 APK 빌드 성공. API33/34/35/36 네 job 모두 동일 SecurityException: Shell cannot change component state for DirectPhotoPickerTrial to 1. 실제 외부 최초 PICK_IMAGES 호출에 도달하지 않음. P0_BLOCKED나 P0_NATIVE_SUCCESS로 해석 금지.
- 실험 브랜치의 debug manifest alias만 enabled=true. shell pm enable 제거. 에뮬레이터의 실험 APK 설치 전 baseline resolver/default와 설치 후 trial resolver/default를 각각 기록. shell 후보에 alias가 없어도 실제 별도 UID 호출 시험을 진행. 실제 first picker hierarchy를 취소 전 기록. 일반 release manifest, 시스템 설정, 시스템 앱/권한 정책 변경 없음. 재실행 결과 미확정.
- 공식 AOSP 정책: 비특권 앱 Intent priority를 0으로 제한(https://android.googlesource.com/platform/frameworks/base/+/0c36369480790826dffd7f2e1679a33fa0edb427/services/core/java/com/android/server/pm/resolution/ComponentResolver.java), 시스템 picker priority 100~110. 공식 AndroidX PickVisualMedia 계약은 framework picker 우선, fallback 시스템 앱 한정(https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.PickVisualMedia). MediaStore.EXTRA_PICK_IMAGES_IN_ORDER 기본 false, 요청 앱이 명시적으로 true 설정(https://developer.android.com/reference/android/provider/MediaStore). manifest만으로 해결 가능하다는 주장 없이 실제 실험 결과를 기다림. 공개판 교체 없음. 후속 검토: 실제 시스템 picker ordered extra의 동작과 OEM/OS 협력 경로, 일반 APK와 구별. CloudMediaProvider는 미디어 소스 공급 계약이지 선택 UI 및 반환 순서 제어 계약이 아님.
