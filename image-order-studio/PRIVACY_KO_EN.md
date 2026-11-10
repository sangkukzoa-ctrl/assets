# Privacy / 개인정보 및 미디어 이용 — Image Order Studio v0.4.0

- 인터넷 연결, 추적, 분석, 광고, 계정 기능 없음. 이미지는 사용자의 Android 기기에서만 처리됩니다.
- 갤러리/파일 선택기를 통해 사용자가 직접 승인한 이미지 URI를 읽어 앱 비공개 저장공간에 복사합니다. 원본을 수정하지 않습니다.
- 사용자가 '갤러리 앨범에 저장'을 누르는 경우에만 순번 각인 출력물을 Android MediaStore의 `Pictures/Image Order Studio`로 기록합니다. 이 앨범은 일반 갤러리 앱에서 볼 수 있으며 사용자가 삭제할 수 있습니다.
- Android 8/9만 갤러리 저장 시 WRITE_EXTERNAL_STORAGE 동의를 요청합니다. Android 10 이상에서는 일반 갤러리 읽기/쓰기 전체 권한을 요구하지 않습니다.
- Android Files 앱에 표시되는 읽기 전용 DocumentsProvider는 사용자가 준비한 최근 12개의 출력 묶음만 표시합니다. 외부 앱은 Android 파일 선택기에서 사용자가 항목을 지정한 뒤에만 해당 항목을 읽을 수 있습니다.
- Android Quick Settings 타일은 사용자의 탭으로 앱을 열 뿐 다른 앱 내용이나 화면을 감시하지 않습니다.
- 특별 접근성 권한, 화면 오버레이 권한, 다른 앱에 대한 강제 개입 권한을 요청하지 않습니다.

English: All work is offline. User-approved selected images are copied privately. Gallery publish explicitly creates visible numbered output images under Pictures/Image Order Studio. On Android 8/9 only, legacy storage write permission is requested at publish time. The read-only SAF DocumentsProvider exposes user-prepared output batches; Quick Settings shortcut launches the app and does not monitor other apps. No networking, analytics, or advertisements.
