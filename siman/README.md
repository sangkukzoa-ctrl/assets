# 심안(心眼) / Siman — AI 대화 원문 통합 검색

> **2026-11-13 검증 배포:** v1.5.13 Windows EXE, Node 15종, 실제 Chrome v1.5.12→v1.5.13 동일 확장 ID 업데이트와 새 background ACK 확인. 이전 외부 `chrome-extension://...` 부트스트랩이 실제 사용자 Chrome에서 `ERR_BLOCKED_BY_CLIENT`로 막히던 경로를 제거했습니다. Gemini 실제 계정의 208/208건 수집 성공도 확인했습니다. [인수인계](HANDOFF_SIMAN_3_2026-11-12.md).

**개발자:** 2bornot  
**최신 공개 테스트판:** v1.5.13 Beta (2026-11-12)  
**환경:** Windows 설치 관리자 `SimanSetup.exe` + Chrome/Edge Manifest V3 확장프로그램

**[최신 Beta 고정 다운로드](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta)** · [고정 설치 ZIP](https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip) · [v1.5.13 개별 버전 기록](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.13)

GitHub Actions가 [`siman/development/`](development/)의 소스 변경을 감지하면 Windows 회귀 테스트·실제 EXE 설치 검사·ZIP/SHA-256 검증을 진행한 다음, 성공 시 **`siman-beta`의 동일한 URL에 최신 파일을 자동 배포**합니다. 블로그는 이 고정 주소만 안내하면 되며, 업데이트된 파일을 직접 설치할 때에는 기존 확장프로그램을 삭제하지 않습니다.

## 개요

여러 AI 서비스의 대화 기록을 브라우저 로컬 저장소(`chrome.storage.local`)에 색인하고, 세션 제목이 아니라 **대화 원문에 포함된 키워드**로 검색합니다. 검색 결과의 전후 메시지 확인, 메시지·대화 전체 복사, 가능한 경우 원본 대화 열기, 서비스별 필터, JSON 백업·복원, 진단 로그 TXT 저장을 지원합니다. 별도의 AI 모델 호출이나 외부 API 키가 필요하지 않습니다.

## 지원 범위

| 서비스 | 현재 방식 | 중요 제약 |
| --- | --- | --- |
| ChatLLM (Abacus AI) | 과거 목록·원문 일괄수집 | 프로젝트와 일반 대화 포함; 일부 원문 완결 판정은 추가 확인 필요 |
| Claude | 과거 목록·원문 일괄수집 | 로그인·서비스 응답 구조에 따라 결과 변경 가능 |
| ChatGPT | 과거 목록·원문 일괄수집 | 429 보호 중단 후 검색 화면·ChatGPT 탭이 열린 경우 로컬 완료 목록을 기반으로 미수집 원문만 자동 재개 |
| Gemini | 공식 웹 계정 원문 일괄수집 + 방문 저장 + Takeout JSON 가져오기 | 100건/페이지 커서 탐색과 빈 응답 재시도; 서버가 제공하는 웹 RPC에 따라 결과 변경 가능 |
| DeepSeek (공식 웹) | 로그인한 chat.deepseek.com 계정 목록·원문 수집 + 방문 저장 | 내부 웹 API 사용. 페이지 커서가 없으면 일부 목록만 확인될 수 있음; 실제 계정 검증 필요 |
| Grok (공식 웹) | 로그인된 grok.com 계정 대화 목록·원문 일괄수집 + 방문 저장 | HTTP 401/403은 로그인 필요로 표시하며 실제 빈 계정으로 간주하지 않음 |

일괄수집은 **ChatLLM → Claude → DeepSeek 웹 → Gemini 웹 → Grok 웹 → ChatGPT** 순서입니다. ChatLLM 기존 발견 기록이 전부 저장됐으면 전체 재수집에서 불필요한 조회를 생략합니다. 새로운 ChatLLM 대화를 찾으려면 개별 수집을 실행합니다.

## 설치와 업데이트

**신규 설치:** 최신 `SimanSetup.exe`를 실행하면 필요한 확장프로그램 파일이 자동 설치됩니다. 이후 한 번만 Chrome 또는 Edge 확장프로그램 관리 화면에서 개발자 모드 → 압축해제된 확장프로그램 로드 → 설치 폴더 선택으로 등록합니다.

**기존 사용자:** 고정 GitHub 다운로드의 최신 `SimanSetup.exe`를 실행하면 **기존 설치 위치에 자동으로 덮어쓰기 업데이트하고 기존 확장 ID를 Chrome·Edge 관리 화면에서 찾아 새 코드를 적용**합니다. Chrome 개발자 모드가 켜진 압축해제 확장 환경에서 실제 Chrome v1.5.12→v1.5.13 무인 업데이트 및 ACK 수신까지 검증했습니다. 수동 재등록과 JSON 원문 백업/복원은 요구하지 않습니다. 브라우저가 ACK를 보내지 않으면 파일 설치만 완료된 것으로 구분하고 `%LOCALAPPDATA%\\2bornot\\Siman\\setup.log`에 이유를 기록합니다. 사용자 검색 색인·대화 원문은 확장프로그램 저장소에 남습니다.

설치 실패 시 이전 설치 코드 롤백을 시도하며 로그는 `%LOCALAPPDATA%\\2bornot\\Siman\\setup.log`에 기록됩니다.

## v1.5.13 변경 사항 (2026-11-13 실사용 진단 기반)

- **설치 차단 오류 수정:** 이전 설치 관리자가 외부에서 `chrome-extension://<ID>/siman-update-*.html`을 여는 방식으로 `ERR_BLOCKED_BY_CLIENT`를 유발함. v1.5.13은 같은 설치 폴더의 `siman-updater-request.json`에 1회용 요청을 두고 Chrome 기존 확장 관리자에서 Reload 후 새 백그라운드가 직접 인증된 로컬 ACK를 보냄
- **실제 Windows EXE/Chrome 시험:** 기존 v1.5.12 확장 ID 유지·설치 파일 제자리 업데이트·기존 기록 보존·실제 백그라운드 ACK 및 Node 15종 회귀 시험 성공. [빌드 기록](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43439284243)
- **브라우저 오류 진단:** 압축 해제 확장 관리 UI에서 복사한 `content.js` 소스만으로 Chrome 예외 원문은 확인되지 않음. 비동기 저장소 브리지의 구 컨텍스트 무효화 처리를 보강하고 설치 로그에 기존 확장의 활성 상태와 로컬 원문 건수(숫자만) 기록
- **Claude HTTP 503:** 해당 원문만 점진적 지연 후 최대 3회 추가 재시도. Gemini 208건 완료, DeepSeek 40건 완료, ChatLLM 301건 완료 실사용 로그 확인
- **주의:** 이전 ChatGPT 로그의 532건 완료와 새 로그의 183건 완료 사이의 차이가 존재하며, Chrome 프로필/확장 ID/저장소 연속성의 실사용 후속 확인 대상임. 새 설치 관리자는 원문을 삭제하지 않으며 기존 확장 ID 재사용을 유지함
- [v1.5.13 상세 변경 기록](development/RELEASE_NOTES_v1.5.13.md)

## v1.5.12 변경 사항 (2026-11-12 실사용 진단 기반)

- Grok HTTP 401/403 인증 실패를 '로그인 필요 · 대화 존재 여부 미확인'으로 처리, 정상 HTTP 200 + 대화 0건과 별도 표시
- Gemini 공식 웹 대화 목록 최대 100건 제한을 따라 계속 페이지를 수집하며 커서 반복/미완료 구분; `hNvQHb` 빈 프레임 최대 2회 재시도
- ChatGPT 자동 재개 시 이미 확보한 로컬 세션 카탈로그를 재사용하고 미수집 원문 요청만 수행, 불필요한 전체 목록 요청 방지
- Chrome 압축해제 확장 업데이트 후 만료된 컨텍스트의 DOM 감시기·이벤트 리스너·타이머를 해제하도록 수명 관리 개선
- Node **14종 회귀 테스트 통과**, 실제 Windows EXE 신규·반복 설치 및 Chrome v1.5.11→v1.5.12 같은 확장 ID 자동 업데이트 ACK 실증
- Windows [최종 빌드](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43211548182) · [공개 다운로드 확인](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43211759908)
- 상세 진단·변경 내용 [RELEASE_NOTES_v1.5.12.md](development/RELEASE_NOTES_v1.5.12.md)

## v1.5.11 변경 사항 (2026-11-12)

- **Grok 공식 웹(grok.com)** 계정의 대화 목록 페이지네이션, 원문 메시지 관계·응답, 활성 재생성 답변 분기를 읽는 독립 수집기 추가
- 전체 일괄수집 및 고급 메뉴에 Grok 과거기록 단독 수집·재개 버튼 추가. Grok 원본 대화 URL 복원
- 기존 방문 DOM 저장 기능 유지, 기존 로컬 원문·색인·확장 ID 보존
- Grok 웹 API는 내부 웹서비스 호출로, 실제 Grok 계정 및 향후 응답 형식은 계속 검증 대상

## v1.5.10 변경 사항 (2026-11-12 검증 배포)

- ChatGPT의 남은 188건에 대한 HTTP 429 반복 발생을 반영해 요청 간격 조정 및 제한 종료 후 검색 화면에서 자동 이어받기 지원(검색 화면·ChatGPT 탭을 열어둬야 함)
- ChatLLM 발견 301건이 모두 완료된 상태에서 불필요한 전체 재조회 생략; 목록 재요청 타임아웃 단축 및 전체 시간 상한
- Gemini 공식 웹 과거 대화 읽기 전용 목록·원문 수집기, 선택 답변 분기/메시지 시간순 처리, Google Takeout My Activity > Gemini Apps JSON 가져오기 추가
- Chrome 확장프로그램 중복 스크립트 주입과 오래된 확장 컨텍스트 비동기 오류 보완
- Node 10종 회귀 테스트 + Windows EXE 실설치/갱신 + Chrome v1.5.9→v1.5.10 동일 확장 ID 갱신 및 ACK 확인 성공
- 실제 Gemini 로그인 계정 내 전체 기록의 수집 여부와 Chrome/Edge 개별 사용자 환경의 오류는 다음 실사용 로그로 검증

## v1.5.9 변경 사항 (2026-11-12 검증 배포)

- ChatLLM에 포함된 DeepSeek 모델과 무관한 **DeepSeek 공식 웹(chat.deepseek.com)** 독립 수집기 추가. 로그인된 웹의 세션 목록 및 원문 조회로 이전의 방문 저장 0건 문제 대응
- 세션별 원문, 편집/재생성 분기 중 활성 대화, 재시도 상태를 브라우저 로컬 저장소에 저장; API 호출 인증 토큰을 로그·원문 저장소에 보관하지 않음
- 전체 일괄수집 순서: ChatLLM → Claude → DeepSeek 공식 웹 → ChatGPT. 서비스별 DeepSeek 웹 수집·재개 버튼과 로그인/수집 진단 제공
- ChatLLM 발견 목록의 원문 301/301 저장과 전체 계정 목록 완결 미확인을 별도 표시
- Windows EXE 컴파일, 기존 설치 경로 덮어쓰기, Node 9개 회귀 테스트, Chrome v1.5.8→v1.5.9 동일 ID 무인 업데이트·ACK E2E 성공
- 실제 DeepSeek 계정에서의 로그인 토큰 응답 및 100개 초과 목록 페이지는 추가 실사용 검증 대상. Gemini/Grok은 여전히 방문 저장 지원

## v1.5.8 변경 사항 (2026-11-12 검증 배포)

- 기존 Windows 설치 폴더·확장 ID를 유지하면서 Chrome·Edge 확장 관리 화면에서 기존 ID만 찾아 자체 재로드 시도
- Manifest V3 백그라운드가 기존 원문 저장소에 손대지 않고 AI 대화 탭 입력 중인 초안은 보호, 새 확장 적용 후 설치 관리자에 일회용 ACK 전달
- Chrome for Testing 압축해제 확장(개발자 모드 ON) 실브라우저에서 v1.5.7 → v1.5.8 실제 무인 갱신, ACK, Windows EXE, 8개 Node 회귀 테스트 통과
- Chrome 개발자 모드 OFF, Edge 실브라우저 및 비표준 프로필은 아직 동일 수준의 E2E 성공을 입증하지 않음
- 고정 주소 `siman-beta`의 EXE/ZIP/SHA256 파일은 Windows 게이트 통과 후에만 자동 교체

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
