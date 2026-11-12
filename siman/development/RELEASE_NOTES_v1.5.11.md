# 심안(心眼) v1.5.11 Beta — Grok 공식 웹 대화 전체 수집

개발자: 2bornot · 2026-11-12

## 새 기능: Grok 전체 대화 수집

- 이전 v1.5.10의 Grok 기능은 사용자 화면 방문 시 메시지 일부를 저장하는 수준이었습니다. 과거 대화 계정 목록/원문 전체 조회는 구현되지 않았습니다.
- 이제 로그인된 공식 `https://grok.com/` 웹사이트를 통해 별도 API 키 없이 계정의 기존 대화 목록을 페이지별로 수집합니다.
- 웹 내부 읽기 전용 REST 경로 `GET /rest/app-chat/conversations`, `GET /rest/app-chat/conversations_v2/{id}`, `GET /rest/app-chat/conversations/{id}/response-node`, `POST /rest/app-chat/conversations/{id}/load-responses` 사용. 마지막 POST는 응답 내용을 조회하는 웹 내 읽기 호출이며 채팅을 작성하지 않습니다.
- 프로젝트 이름이 서버 메타데이터에 포함된 경우 함께 보존하고, 재생성된 응답 중 현재 선택된 분기의 원문을 인덱싱합니다.
- 429 제한 발생 시 즉시 중지 및 쿨다운, 다음 실행 시 기존 완료 원문을 건너뛰고 남은 기록 수집.
- `전체 일괄수집`과 `고급 > Grok 공식 웹 과거기록 수집·재개` 버튼 추가. 이전의 Grok 방문 저장 기능 유지.
- Grok 원본 바로가기 `https://grok.com/c/{대화 ID}` 지원.
- Gemini·DeepSeek·ChatGPT·Claude·ChatLLM 기존 지원과 기존 로컬 저장소 ID 및 기록 보존.

## 설치 및 검증

- Windows 설치 관리자 v1.5.11/R9, Chrome·Edge 기존 확장 제자리 업데이트.
- 기존 검색 색인, 로컬 원문, 확장 ID 및 Naver 블로그용 GitHub 고정 다운로드 URL 유지.
- Grok 읽기 전용 API 구조, 페이지네이션, 분기, 검색 원문 및 기존 서비스 회귀 테스트를 Windows CI에서 검증하고 자동 브라우저 업데이트 ACK가 확인된 경우에만 공개 Beta 배포.
- Grok 웹 API는 웹사이트 내부 경로이므로 실서비스의 향후 변경에 대비하여 오류를 명시적으로 표시합니다. 실제 로그인된 Grok 계정의 수집량은 후속 실사용 검증 대상입니다.
- 다른 서비스의 비공식 API도 마찬가지로 실제 로그인 사용자 검증이 별도 필요합니다.

배포: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
