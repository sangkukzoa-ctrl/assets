# 심안(心眼) v1.5.9 Beta — DeepSeek 공식 웹 수집기

개발자: 2bornot

## 주요 변경

- **DeepSeek 공식 웹** `https://chat.deepseek.com/`을 ChatLLM과 완전히 별개의 서비스로 수집.
- 기존 방문 중 화면에 보이는 원문 저장을 유지하면서, 로그인된 DeepSeek 웹의 읽기 전용 대화 목록 `/api/v0/chat_session/fetch_page` 및 대화 원문 `/api/v0/chat/history_messages`를 이용한 독립 일괄 수집기 추가.
- 검색 화면의 'DeepSeek 공식 웹 수집·재개' 버튼 및 전체 일괄수집 단계(이제 ChatLLM → Claude → DeepSeek 웹 → ChatGPT) 제공.
- DeepSeek 웹의 메시지 분기(편집/재생성)에서 현재 활성 원문 분기를 우선 추출. 조회 실패 기록은 재시도 가능하게 유지하고, 429에서 추가 요청 중단.
- 수집 시 사용하는 DeepSeek 웹 로그인 토큰은 원래 사이트의 JavaScript 컨텍스트 안에서만 인증에 사용하며 브라우저 확장 로컬 원문 저장소, 진단 로그, GitHub로 전송하지 않음.
- ChatLLM에서 발견된 목록의 원문을 전부 처리했더라도 계정 전체 목록 검증과 구분하여 '발견 목록 완료'로 표시. 원본 데이터 유지.
- ChatGPT 기존 429 중단 및 15분 이상 재시도 보호 유지. 기존 완료 원문·색인과 Chrome/Edge 확장 ID 보존.

## 자동 업데이트 / 검증

- 기존 `SimanSetup.exe`가 같은 경로에 덮어쓰고 기존 확장 ID만 갱신한 뒤, 백그라운드 실행 ACK를 받은 경우에만 자동 적용 완료로 표시.
- 새 v1.5.9 업데이트용 bootstrap 및 Windows installer R7.
- 9종 Node 회귀 테스트(신규 DeepSeek 웹 목록/원문/분기/토큰 비유출 포함), Windows EXE 설치·반복 업데이트 및 Chrome for Testing v1.5.8→v1.5.9 자동 갱신 E2E **통과 시에만** 고정 Beta 자동 게시.
- 브라우저 사용자 계정의 실제 DeepSeek API 응답은 테스트 환경에서 로그인할 수 없으므로 별도 실사용 로그 검증 대상. 회귀 테스트는 인증 API의 합성 응답을 사용합니다.
- DeepSeek 웹 내부 API 목록이 100건 제한을 반환하고 추가 페이지 커서를 주지 않는 경우, 확보된 목록만 저장하고 전체 목록 완결은 미확인으로 표시합니다.
- 브라우저 강제 종료, 확장 재등록, 사용자 검색 색인 삭제는 수행하지 않습니다.
- Windows 코드서명 및 Chrome Web Store 게시 전 무료 Beta.

고정 배포: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
