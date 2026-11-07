심안(心眼) v1.5.3 Beta | Windows용 설치 안내
개발자: 2bornot

[시작하기]
1. SimanSetup.exe를 실행합니다. (CMD 실행·관리자 권한 불필요)
2. '설치 파일 준비하기' 버튼을 누릅니다.
3. 'Chrome 등록하기' 또는 'Edge 등록하기'를 누릅니다.
4. 확장프로그램 관리 페이지에서 개발자 모드를 켭니다.
5. '압축해제된 확장 프로그램을 로드' → 설치 관리자가 복사한 폴더 경로를 붙여넣고 선택합니다.
   - Chrome 관리 화면: chrome://extensions
   - Edge 관리 화면: edge://extensions
   - 설치 경로: %LOCALAPPDATA%\2bornot\Siman\app
6. 심안 확장프로그램을 실행합니다.

[기본 사용]
- '전체 일괄수집 시작': ChatLLM, Claude, ChatGPT의 대화 수집을 순차 시도합니다.
- 검색어 입력: 수집한 대화의 메시지 본문을 키워드로 찾습니다.
- '진단 로그 TXT 저장': 실패 단계와 HTTP 상태를 내보냅니다.
- DeepSeek, Gemini, Grok: 브라우저에서 실제 방문한 대화만 자동 저장합니다.

[업데이트 및 기록 보호]
- 확장프로그램을 Chrome에서 제거하면 로컬 색인이 삭제될 수 있습니다.
- 기존 기록이 있다면 먼저 심안 '전체 백업 저장'으로 JSON을 만드세요.
- 파일만 새 버전으로 교체하는 경우에는 기존 확장프로그램을 삭제하지 않고 브라우저 관리화면에서 새로고침하세요.
- 확장프로그램 자체를 제거해 새로 설치했다면 JSON 백업을 가져오세요.

[알려진 제약]
- v1.5.3은 Beta입니다. ChatLLM 전체 목록 수집이 일부 계정에서 실패할 수 있습니다.
- DeepSeek / Gemini / Grok은 과거 모든 세션을 자동으로 수집하지 않습니다.
- Chrome Web Store 게시자 인증 및 Windows Authenticode 코드 서명 미완료.
- Windows SmartScreen 경고가 나타날 수 있으며 출처는 공식 GitHub 릴리스에서 확인하세요.

공식 배포 페이지: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.3
설치 EXE 직접 링크: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-v1.5.3/SimanSetup.exe
문의 및 오류 제보: 개발자 네이버 블로그