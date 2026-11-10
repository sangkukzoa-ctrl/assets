# Image Order Studio — 공개 베타 v0.3.0 (2bornot)

- **주요 변경:** Android 갤러리형 사진 선택기를 바로 호출합니다. Android 15 / R Extensions 12 이상에서는 선택 순서 자동 반영 옵션을 요청합니다.
- **웹사이트 직접 첨부:** 표준 `GET_CONTENT`/`PICK` 이미지 요청의 선택 앱으로 등록했습니다. 다른 앱에서 시작한 경우 처음부터 사진 선택기를 열고, 파란색 번호로 순서를 확인한 후 **사이트에 첨부**를 누르면 `content://` 이미지 URI들을 원래 호출자에게 돌려줍니다.
- 호출자가 이미지를 한 장만 받는 경우 1장 직접 반환 또는 최대 12장 합치기를 제공합니다. 여러 장을 받는 경우 번호 표시 이미지 여러 장을 순서대로 반환합니다.
- 외부 첨부 세션은 개인 라이브러리와 분리됩니다. 원본 파일은 수정하지 않습니다.
- 일반 모드의 JPG/PNG 번호 삽입, 공유/저장, 순서 편집, 선택 우선 정렬은 유지됩니다.
- 개발자: **2bornot**, Android 8.0 이상. 광고·계정·인터넷 권한·광범위 저장소 권한 없음.
- 호환성: `ACTION_OPEN_DOCUMENT` 및 OS 전용 사진 선택기를 사용하는 사이트는 강제 대체하지 않습니다. 수신 웹사이트의 첨부 배열 UI 정렬도 Android 앱이 강제할 수 없습니다.

## English

Image Order Studio v0.3.0 public beta. The app uses the Android system photo picker from its own UI and registers as an optional image picker for `ACTION_GET_CONTENT` and `ACTION_PICK` upload flows. Compatible callers receive read-granted `content://` URIs via `RESULT_OK` without a share-sheet detour. Modern Android photo pickers can return verified tap order; the app exposes explicit order badges for all other pickers. Single-image callers can receive a combined image. No internet permission, ads, analytics or account. Existing signing identity and fixed public beta URLs are preserved.
