심안(心眼) v1.5.7 Beta — Windows / Chrome / Edge
개발자: 2bornot

[첫 설치]
1. SimanSetup.exe를 실행하면 파일이 자동 설치됩니다.
2. Chrome 또는 Edge에서 심안을 처음 한 번만 확장프로그램으로 등록합니다.
3. 심안 검색창에서 대화 수집을 시작합니다.

[기존 사용자: 자동 덮어쓰기 업데이트]
1. 새 SimanSetup.exe를 실행하면 기존 설치 위치에 v1.5.7 코드가 자동 덮어써집니다.
2. 기존 확장프로그램을 삭제하거나 재등록하지 않습니다. 원문 JSON 백업/복원도 필요하지 않습니다.
3. 설치 후 실행 중인 Chrome/Edge에서 심안 확장을 새로고침하거나 브라우저를 재시작하여 새 코드를 반영합니다.
4. 기존 검색 색인과 대화 원문은 브라우저 확장프로그램 ID에 연결된 저장소에 그대로 남습니다.
5. 오류가 발생하면 설치 관리자가 이전 설치 코드 복원을 시도하고 %LOCALAPPDATA%\\2bornot\\Siman\\setup.log에 기록합니다.

[수집 범위]
ChatLLM / Claude / ChatGPT: 과거 대화 전체 일괄수집 시도
DeepSeek / Gemini / Grok: 웹에서 방문한 대화에 보이는 메시지 저장(부분 수집)

[진단]
심안 → 「진단 로그 TXT 저장」
방문 저장 서비스에 0건이 표시될 때는 먼저 해당 서비스의 실제 대화 탭을 열어주세요.

[배포 / 보안]
공개 테스트판(Beta), 무료 배포, 공식 GitHub: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
Windows 서명 및 Chrome Web Store 정식 게시 전으로 브라우저 개발자 모드가 필요합니다.
