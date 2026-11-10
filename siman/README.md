# 심안(心眼) / Siman — AI 대화 원문 통합 검색

**개발자:** 2bornot  
**최신 공개 테스트판:** v1.5.6 Beta (2026-11-10)  
**환경:** Windows 설치 관리자 `SimanSetup.exe` + Chrome/Edge Manifest V3 확장프로그램

**[최신 Beta 고정 다운로드](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta)** · [고정 설치 ZIP](https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip) · [v1.5.6 개별 버전 기록](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.6)

GitHub Actions가 [`siman/development/`](development/)의 소스 변경을 감지하면 Windows 회귀 테스트·실제 EXE 설치 검사·ZIP/SHA-256 검증을 진행한 다음, 성공 시 **`siman-beta`의 동일한 URL에 최신 파일을 자동 배포**합니다. 블로그는 이 고정 주소만 안내하면 되며, 업데이트된 파일을 직접 설치할 때에는 기존 확장프로그램을 삭제하지 않습니다.

## 개요

여러 AI 서비스의 대화 기록을 브라우저 로컬 저장소(`chrome.storage.local`)에 색인하고, 세션 제목이 아니라 **대화 원문에 포함된 키워드**로 검색합니다. 검색 결과의 전후 메시지 확인, 메시지·대화 전체 복사, 가능한 경우 원본 대화 열기, 서비스별 필터, JSON 백업·복원, 진단 로그 TXT 저장을 지원합니다. 별도의 AI 모델 호출이나 외부 API 키가 필요하지 않습니다.

## 지원 범위

| 서비스 | 현재 방식 | 중요 제약 |
| --- | --- | --- |
| ChatLLM (Abacus AI) | 과거 목록·원문 일괄수집 | 프로젝트와 일반 대화 포함; 일부 원문 완결 판정은 추가 확인 필요 |
| Claude | 과거 목록·원문 일괄수집 | 로그인·서비스 응답 구조에 따라 결과 변경 가능 |
| ChatGPT | 과거 목록·원문 일괄수집 | HTTP 429 제한 시 보호 중단, 이후 미완료분 재개 |
| Gemini | 방문한 대화 화면 저장 | 전체 과거 기록 일괄수집 미지원 |
| DeepSeek | 방문한 대화 화면 저장 | 긴 대화의 화면 미표시 부분 누락 가능 |
| Grok | 방문한 대화 화면 저장 | 전체 과거 기록 일괄수집 미지원 |

일괄수집은 **ChatLLM → Claude → ChatGPT** 순서입니다. 방문 저장 서비스는 사용자가 해당 대화를 화면에 열면 저장을 시도합니다.

## 설치와 업데이트

최초 설치는 `Siman_v1.5.5_BLOG_ATTACHMENT.zip` 압축 해제 → `SimanSetup.exe` 실행 → **설치 파일 준비하기** → **Chrome 등록하기** 또는 **Edge 등록하기** → 브라우저 확장프로그램 관리 화면에서 **개발자 모드** → **압축해제된 확장 프로그램을 로드** → 복사된 설치 폴더 경로 붙여넣기(Ctrl+V, Enter) → 폴더 선택입니다.

업데이트 전에는 검색 화면의 **서비스별 수집 · 연결 복구 · 백업 (고급)** 메뉴에서 **전체 원문 백업 저장**으로 JSON을 백업하세요. 기존 확장프로그램을 삭제하지 않고 새 `SimanSetup.exe`로 파일을 교체한 뒤, `chrome://extensions` 또는 `edge://extensions`에서 기존 심안을 **새로고침**하고 열려 있던 AI 탭도 새로고침합니다.

## v1.5.6 변경 사항

- ChatLLM의 HTTP 200 이후 응답 본문 읽기가 무한 대기로 이어지지 않도록 JSON body 수신 타임아웃 유지
- 수집 중 서비스 페이지 연결이 끊기면 기록을 보존하고 최대 한 번 자동 재연결
- ChatLLM 상세 API 재조회·직접 원문 조회·HTML 내보내기 단계별 진단 추가
- 7번째 회귀 테스트: HTTP 200 후 JSON 본문이 끝나지 않는 모의 장애 및 수집기 연결 복구 검사
- v1.5.5의 Chrome 초기화·방문 저장 복구 및 v1.5.4의 ChatGPT HTTP 429 보호 유지

## v1.5.5 변경 사항

- 초기 스크립트 준비 지연 시 초기화 재시도 및 준비 상태 검증
- Gemini·DeepSeek·Grok의 SPA/동적 DOM 방문 저장 재시도
- 방문 저장·로컬 통신 진단 및 연결 복구 대상 확대
- v1.5.4의 ChatLLM 완결 판정 개선, ChatGPT 첫 HTTP 429 보호 중단 유지
- 기존 확장프로그램 ID·로컬 색인 저장 방식 유지

## 검증과 미완료

GitHub Actions의 Windows 회귀 테스트, `SimanSetup.exe` 빌드, 설치·재설치, ZIP·SHA-256 검사가 성공했습니다. 단, 모든 사용자 계정에서 모든 서비스의 과거 기록을 전수 검증한 것은 아닙니다. 일부 서비스의 특정 메시지 위치 이동과 방문 기록 누락도 개선 대상입니다.

**Chrome 웹스토어 공식 게시 및 Windows Authenticode 코드 서명은 아직 완료되지 않았습니다.** GitHub 빌드 출처 증명은 Windows 코드 서명과 다릅니다.

[개인정보 처리 안내](PRIVACY.md) · [개발 이어받기·작업 절차](CONTINUATION_2026-11-10.md) · [공개 다운로드 검증](https://github.com/sangkukzoa-ctrl/assets/actions/workflows/siman-public-download-check.yml)
