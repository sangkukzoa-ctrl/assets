# 심안(心眼) / Siman — AI 대화 원문 통합 검색

> **개발 세션 이관:** [심안 3차 — v1.5.8 자동 확장 새로고침 작업 인수인계](HANDOFF_SIMAN_3_2026-11-12.md). 공개 검증본 v1.5.7 유지, v1.5.8 실브라우저 E2E 실패(`ERR_BLOCKED_BY_CLIENT`) 해결 후 자동 배포. 새 세션에서 '진행' 입력 시 이 파일과 GitHub 실제 소스부터 확인.

**개발자:** 2bornot  
**최신 공개 테스트판:** v1.5.7 Beta (2026-11-11)  
**환경:** Windows 설치 관리자 `SimanSetup.exe` + Chrome/Edge Manifest V3 확장프로그램

**[최신 Beta 고정 다운로드](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta)** · [고정 설치 ZIP](https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip) · [v1.5.7 개별 버전 기록](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.7)

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

**신규 설치:** 최신 `SimanSetup.exe`를 실행하면 필요한 확장프로그램 파일이 자동 설치됩니다. 이후 한 번만 Chrome 또는 Edge 확장프로그램 관리 화면에서 개발자 모드 → 압축해제된 확장프로그램 로드 → 설치 폴더 선택으로 등록합니다.

**기존 사용자:** 고정 GitHub 다운로드의 최신 `SimanSetup.exe`를 실행하면 **기존 설치 위치에 자동으로 덮어쓰기 업데이트**됩니다. 파일 관리나 확장프로그램 삭제/재등록, JSON 원문 백업/복원은 필요하지 않습니다. 브라우저 검색 색인·대화 원문은 확장프로그램 저장소에 그대로 남습니다. 실행 중인 브라우저가 이전 코드를 유지하는 경우에는 기존 심안 확장을 새로고침하거나 브라우저를 재시작하면 됩니다.

설치 실패 시 이전 설치 코드 롤백을 시도하며 로그는 `%LOCALAPPDATA%\\2bornot\\Siman\\setup.log`에 기록됩니다.

## v1.5.7 변경 사항

- 설치 관리자 실행 즉시 설치/업데이트 수행; 기존 사용자의 수동 설치 파일 준비 단계 제거
- 설치 폴더 경로를 그대로 유지하는 관리 대상 코드만의 **제자리 덮어쓰기**
- 기존 Chrome/Edge 확장프로그램 ID·`chrome.storage.local` 원문 및 색인 보존, 자동 임시 백업과 실패 시 코드 복원
- 사용자 지정 파일 보존 및 지난 버전의 관리 대상에서 제거된 불필요 코드 파일 정리
- 실제 Windows EXE에서 v1.5.6 모의 설치본 → v1.5.7 업그레이드, 폴더 동일성·원문 영역 무변경·반복 업데이트 회귀 검증

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
