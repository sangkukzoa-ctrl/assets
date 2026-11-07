# 심안(心眼) v1.5.3 — DeepSeek 웹 방문 저장 수정

- DeepSeek 실제 대화 URL `/a/chat/s/<세션ID>` 식별 오류 해결 (기존은 `s`를 세션 ID로 인식)
- `.ds-markdown` 및 가상 스크롤 메시지 목록 인식
- 사용자·AI 메시지 역할 구분, 다른 스크롤 위치에서 보이는 메시지 누적 저장
- 원본 DeepSeek 세션 URL 보존
- 방문 저장 성공 여부는 원문 없는 디버그 `VISIT_CAPTURE` 로그로 확인 가능
- ChatLLM 지연 목록, Claude, ChatGPT 수집과 Windows GUI 설치기 기존 v1.5.2 동작 유지

### 저장 범위
DeepSeek은 전체 과거 세션 일괄 수집이 아니라 **방문한 대화 중 화면에 렌더된 메시지의 부분 색인**입니다. 가상 스크롤 때문에 화면에 한 번도 나타나지 않은 메시지까지 완료된 것으로 표시하지 않습니다. 이전에 이미 방문한 기록은 설치 후 다시 방문해야 수집할 수 있습니다.

### 검증
Node DOM 모의 테스트: 실제 DeepSeek URL 식별, 2개 메시지 저장, 가상 스크롤 전환 후 4개 누적, 역할·원본 링크·원문 미포함 디버그.
ChatLLM·Claude 수집기 회귀 및 저장 브리지 테스트.
Windows GUI 설치·재설치 GitHub Actions 테스트는 릴리스 전 실행.
정식 Chrome Web Store 게시 및 Windows Authenticode 서명은 아직 아닙니다.
