# 심안(心眼) v1.5.10 Beta — ChatGPT 수집 재개 및 Gemini 과거기록 수집

개발자 2bornot · 2026-11-12

## 실제 v1.5.9 진단 (2026-11-12 18:03 KST)

- 전체 발견 1,097건 · 검색 가능 982건 · 미수집 114건 · 재시도 1건.
- ChatGPT 647건 발견 · 459건 완결 · 187건 미수집 + 1건 HTTP 429 재시도.
- ChatLLM 발견 301건 전부 저장됐지만 95초 중단 오류 발생.
- Claude 111건 / DeepSeek 38건 완료 · Gemini 0건 (기존 방문 기반 코드 외 과거기록 수집 기능 없었음).
- 크롬 확장 오류 TXT는 동일한 `content.js` 소스가 반복됐으며 실제 오류 문구/스택은 파일에 없었음.

## 변경

- **ChatGPT**: 서버 요청 간격을 2.7초로 완화; 429이 발생하면 기존 원문 보존 후 15분 이상 대기. 설정된 시각 이후 **심안 검색창과 ChatGPT 탭이 열려 있을 때** 45초 간격으로 자동 재개 여부 확인. 심안 고급 메뉴에서 자동 재개 켜고 끄기 가능. 요청 제한을 우회하거나 무제한 재시도하지 않음.
- **ChatLLM**: 이미 발견한 세션이 전부 완결된 경우 전체 일괄수집에서 재조회를 생략하고 기존 검색 기록 유지(새 대화 확인은 ChatLLM 개별 수집). 웹 응답 재조회에 20초 개별, 48초 전체 상한 적용.
- **Gemini**: `gemini.google.com` 전용 읽기 전용 웹 수집기 추가. 로그인된 사이트 자체에서 목록(`MaZiqc`)과 원문(`hNvQHb`)을 가져와 기존 브라우저 로컬 검색 색인에 저장. 선택한 답변 분기·시간순 메시지 지원. 웹 사이트 내부 RPC가 변경되면 실패를 명시하고 미수집 상태 유지. 로그인 세션 토큰을 디버그 로그/저장소로 복사하지 않음.
- Gemini 대화 JSON 브라우저 내보내기 및 Google Takeout My Activity > Gemini Apps JSON 활동 가져오기 추가. Takeout 활동 데이터는 일부 메시지만 포함할 수 있어 **부분 기록**으로 저장하며, 확보하지 않은 AI 답변을 합성하지 않음.
- **크롬 확장 오류 대응**: 이미 주입된 content/page 스크립트의 무조건 재주입을 방지. 업데이트 직후 만료된 확장 컨텍스트의 비동기 Promise 오류 처리. 기존 설치/자동 적용 로직과 Chrome 확장 ID·로컬 기록 유지.
- DeepSeek 38건 / Claude 111건 등 기존 완료 기록을 그대로 보존.

## 검증 및 배포 정책

- 기존 Node 회귀, Gemini RPC/Google Takeout 테스트, Windows EXE 컴파일, 기존 설치 위치 및 Chrome v1.5.9→v1.5.10 동일 확장 ID 실제 자동 업데이트 E2E 테스트가 모두 통과해야 GitHub 고정 Beta 게시.
- 실서비스 Gemini 계정의 내부 RPC는 테스트용 합성 응답과 별개로 사용자의 후속 진단에서 검증. 웹 API 구조가 변경되면 `GEMINI_DETAIL_ERROR` 및 실패 항목 확인.
- 고정 배포 링크 https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- 무료 Beta: Windows 코드서명/Chrome Web Store 배포 미완료.
