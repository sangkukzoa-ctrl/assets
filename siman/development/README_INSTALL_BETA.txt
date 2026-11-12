심안(心眼) v1.5.12 Beta — Windows / Chrome / Edge
개발자: 2bornot

[첫 설치]
1. SimanSetup.exe를 실행하면 파일이 자동 설치됩니다.
2. Chrome 또는 Edge에서 심안을 처음 한 번만 확장프로그램으로 등록합니다.
3. 심안 검색창에서 대화 수집을 시작합니다.

[기존 사용자: 자동 덮어쓰기 업데이트]
1. 새 SimanSetup.exe를 실행하면 기존 설치 위치에 v1.5.12 코드가 자동 덮어써집니다.
2. 기존 확장프로그램을 삭제하거나 재등록하지 않습니다. 원문 JSON 백업/복원도 필요하지 않습니다.
3. 설치 관리자가 Chrome/Edge의 기존 심안 확장을 자동 재시작하고 실행 확인 ACK를 검사합니다. ACK 실패 시 진단 로그를 확인합니다.
4. 기존 검색 색인과 대화 원문은 브라우저 확장프로그램 ID에 연결된 저장소에 그대로 남습니다.
5. 오류가 발생하면 설치 관리자가 이전 설치 코드 복원을 시도하고 %LOCALAPPDATA%\\2bornot\\Siman\\setup.log에 기록합니다.

[수집 범위]
ChatLLM / Claude / ChatGPT / Gemini / Grok 공식 웹: 과거 대화 목록·원문 일괄수집 시도
DeepSeek 공식 웹(chat.deepseek.com): 계정 목록·원문 수집과 방문 저장
Grok 공식 웹(grok.com): 계정 목록·원문 수집과 방문 저장
Gemini: 100건씩 다음 페이지를 자동 수집 + 원문 일부 응답 오류 자동 재시도 + Google Takeout JSON 가져오기
Grok 웹 인증 실패(401)는 대화가 0건이라는 뜻이 아닙니다. 로그인 후 다시 수집하면 실제 0건인지 판정합니다.

[진단]
심안 → 「진단 로그 TXT 저장」
DeepSeek는 메인 검색 화면 '전체 일괄수집' 또는 'DeepSeek 공식 웹 수집·재개'로 로그인 페이지를 자동 열어 수집합니다.
Gemini는 로그인된 공식 웹의 계정 수집을 지원하며, 고급 메뉴의 Gemini 과거기록 수집을 실행할 수 있습니다.
ChatGPT 429 이후에는 심안 검색창과 ChatGPT 웹 탭을 열어두면 대기 시간 종료 후 로컬 수집 목록을 사용해 남은 원문부터 자동 재개합니다.

[배포 / 보안]
공개 테스트판(Beta), 무료 배포, 공식 GitHub: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
Windows 서명 및 Chrome Web Store 정식 게시 전으로 브라우저 개발자 모드가 필요합니다.
