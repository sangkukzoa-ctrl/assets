# 실제 첨부 호출 진단

v0.5.5 RC의 실제 Android 기기에서 Image Order가 호출되지 않는 문제를 조사한다. 이 도구는 앱을 수정하거나 기본 앱을 변경하지 않는다.

1. PC에 Android platform-tools가 설치되어 있고 휴대전화의 USB 디버깅이 허용되어 있어야 한다. adb devices에서 연결 상태가 device인지 확인한다.
2. PowerShell에서 아래 명령을 실행한다. adb가 PATH에 없다면 -Adb 인수에 adb.exe 전체 경로를 지정한다.

    powershell -NoProfile -ExecutionPolicy Bypass -File .\Capture-AttachmentRoute.ps1

3. 휴대전화에서 ChatGPT → Chat LLM → Chrome의 Claude 순으로 평소 첨부 버튼을 누르고 창을 닫는다. 사진을 실제 전송할 필요는 없다.
4. PC에서 Ctrl+C로 종료하고 ImageOrder-attachment-route.txt만 제공한다. 원본 logcat은 파일로 저장하지 않는다. 패키지명·Activity명·Intent action·MIME 및 OS/기종 정보만 기록한다.

로그가 비어 있거나 별도 Activity가 나오지 않아도 실패로 삭제하지 않는다. 앱 내부/임베디드 UI일 가능성을 구분하는 자료다. 실제 기기에서의 실행은 아직 검증되지 않았다.
