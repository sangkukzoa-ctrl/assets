심안(心眼) v1.5.6 Beta — Windows / Chrome / Edge
개발자: 2bornot

[사용자 설치]
1. SimanSetup.exe 실행 → 「설치 파일 준비하기」 선택
2. 「Chrome 등록하기」 또는 「Edge 등록하기」 선택
3. 확장프로그램 관리 화면에서 개발자 모드 켜기
4. 「압축해제된 확장 프로그램을 로드」 선택 → 안내 창에 복사된 app 폴더 경로 입력 → 폴더 선택
5. 브라우저 확장프로그램 메뉴에서 심안을 열고 「전체 일괄수집 시작」 실행

[기존 사용자의 업데이트 — 중요]
1. 기존 심안의 「전체 원문 백업 저장」으로 JSON 백업
2. 실행 중인 수집이 있으면 먼저 중지
3. 새 SimanSetup.exe 실행 → 같은 설치 경로에 새로운 코드 파일 설치
4. chrome://extensions 에서 기존 심안 카드의 새로고침(↻) 클릭
5. ChatGPT·Claude·ChatLLM·DeepSeek·Gemini·Grok 탭을 새로고침
6. 기존 색인이 유지되는지 심안의 기록 건수 확인

기존 Chrome 확장프로그램을 삭제하지 마세요. 삭제하면 브라우저 로컬 검색 색인이 제거될 수 있습니다.

[수집 범위]
ChatLLM / Claude / ChatGPT: 과거 대화 전체 일괄수집 시도
DeepSeek / Gemini / Grok: 웹에서 방문한 대화에 보이는 메시지 저장(부분 수집)

[진단]
심안 → 「진단 로그 TXT 저장」
방문 저장 서비스에 0건이 표시될 때는 먼저 해당 서비스의 실제 대화 탭을 열어주세요.

[배포 / 보안]
공개 테스트판(Beta), 무료 배포, 공식 GitHub: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
Windows 서명 및 Chrome Web Store 정식 게시 전으로 브라우저 개발자 모드가 필요합니다.
