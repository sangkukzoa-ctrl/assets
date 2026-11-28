# 최초 사진 선택창 실기기 진단 v2

목적: ChatGPT, Chat LLM, 네이버 리뷰의 **최초 사진 선택창**에서 실제 Activity와 Intent를 구분한다. Chrome/Claude 혼합 파일 경로는 이번 P0 진단에서 제외한다. 일반 APK 직접 PICK_IMAGES 등록은 AOSP 기반 API33~36에서 모두 차단된 것이 확인되었지만, 실기기 앱들이 정확히 동일한 action을 사용한다는 로그는 아직 없다.

## 사용

1. Windows PC에 공식 Android SDK Platform-Tools가 필요하다. https://developer.android.com/tools/releases/platform-tools 에서 Windows ZIP을 받아 이 폴더에 platform-tools 폴더가 오도록 압축을 푼다. 이미 adb가 PATH 또는 기본 Android SDK 위치에 있으면 재설치할 필요 없다.
2. 휴대전화의 USB 디버깅을 직접 허용하고 PC에 연결한다. 이 스크립트는 기기 설정을 변경하지 않는다.
3. Run-AttachmentRoute.cmd를 실행한다.
4. 각 앱을 연 상태에서 첫 Enter, 평소 사진 첨부 버튼을 누르고 첫 선택창이 보이는 상태에서 두 번째 Enter. 실제 사진 선택이나 전송은 필요 없다. 사용할 수 없는 앱은 s로 건너뛴다.
5. 마지막에 생성된 ImageOrder-attachment-route.txt만 보내면 된다.

패키지명·Activity명·Intent action·MIME·resolver priority·OS/기종/확장 버전만 보존한다. 원본 logcat, URI, 파일명, 사진, 앱 화면, 대화 내용, 장치 일련번호는 보고서에 저장하지 않는다. 로그가 없거나 picker=unknown이어도 성공 사례로 추정하지 않는다. 임베디드 선택창이나 로그 제한 가능성을 구분하기 위한 진단 자료다.

제품 권한/앱 설정/시스템 앱을 변경하지 않는다. adb 연결 인증만 사용자가 수행한다. 이 도구는 실기기의 동작을 직접 바꾸는 수정판이 아니며, 기기에서의 실행은 아직 미검증이다.
