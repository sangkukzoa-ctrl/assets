# Image Order Studio 0.4.0 · Stable Beta / 정식 공개 베타

Developer / 개발자: **2bornot** · Free, no ads · Android 8.0+ · 한국어/영어

## 핵심 개선

- **삼성 갤러리 우선 연결:** `com.sec.android.gallery3d`를 대상으로 사진/앨범 선택기를 직접 요청하고, 지원되지 않는 환경에서는 다른 선택기로 안전하게 대체합니다. 시스템 Photo Picker와 실제 삼성 Gallery UI는 서로 다릅니다.
- **이미지 업로드 앱 선택권이 없는 사이트 지원:** '① 갤러리 앨범에 저장'을 누르면 `Pictures/Image Order Studio` 앨범에 순번이 직접 인쇄된 이미지가 생성됩니다. 그 사이트의 평범한 사진 첨부창에서 해당 앨범 이미지를 선택하면 됩니다.
- **이미지 한 장만 받는 사이트:** 최대 12장까지 하나의 JPG로 결합해 동일 앨범에 저장합니다. 내부 순서는 외부 파일 정렬에 영향을 받지 않습니다.
- **파일 탐색기 공급자:** Android `DocumentsProvider`를 통해 시스템 파일 선택기의 'Image Order Studio' 읽기 전용 출처에서 최근 출력 묶음에 접근할 수 있습니다.
- **어디서든 빠른 접근:** Android 빠른 설정 패널에서 Image Order Studio 타일 추가 가능. 접근성·화면 위에 표시·인터넷 권한 불필요.
- **단순한 화면:** 앨범 저장 두 버튼을 기본 동작으로, 나머지 복사/공유/필터/삭제 등은 '다른 기능·설정'으로 정리합니다.
- **기존 기능 유지:** 단일/복수 첨부 인텐트 반환, 선택순 기록, JPG/PNG, 원본 공유, 166장 순서 무결성 테스트.

## 안내 및 범위

Android는 타사 앱이 모든 앱과 웹사이트의 파일 선택창을 전역으로 대체하도록 허용하지 않습니다. 이 앱은 호환되는 `ACTION_GET_CONTENT`/`ACTION_PICK` 직접 호출, `DocumentsProvider` 표시, 일반 삼성/Android 갤러리에 결과물 생성으로 단계적 호환성을 제공합니다.

'갤러리 앨범에 저장'의 사진들은 사용자 휴대폰 갤러리에 나타나며, 필요하면 갤러리에서 직접 삭제할 수 있습니다. 내부에만 저장한 원본 이미지는 수정하지 않습니다. Android 8/9에서는 갤러리에 이미지 쓰기 권한을 요청하며 Android 10 이상은 시스템 MediaStore를 이용합니다.

## English

Samsung Gallery is now the preferred native image picker on supported Galaxy devices. If unavailable, fall back to the system picker. For apps that do not offer a picker choice, publish clearly numbered images to the ordinary device Gallery album **Image Order Studio** and attach them from the destination app's own picker. A read-only SAF DocumentsProvider and optional Quick Settings tile provide two additional paths. Global system-wide upload interception is not provided because Android does not expose such a universal third-party mechanism.
