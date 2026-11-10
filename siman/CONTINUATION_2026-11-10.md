# 심안(心眼) 개발 이어받기 — 2026-11-10 (2차 세션 기준)

이 문서는 요약 보고서가 아닌 **실제 작업을 재개하기 위한 기준표**다. 코드는 이 문서가 아니라 아래 GitHub 원본·ZIP 소스·CI에 있다. ChatLens OCR / RGB Blocks / Just PDF to Image와 혼동하지 않는다.

## 사용자 목표 및 유지해야 할 지시

1. Everything에 가까운 **한 개 검색창으로 AI 서비스의 일반 세션과 프로젝트 세션을 모두 키워드 전문 검색**한다. 세션 제목 검색으로 축소해서는 안 된다. 사용자 발언과 AI 발언 원문, 앞뒤 문맥 및 복사를 제공한다.
2. 검색에서 원본 대화를 열고 가능하면 **그 메시지 위치까지 이동**한다. 원본 링크를 찾지 못했다는 문구로 작업을 종료하지 않는다. 직접 메시지 앵커가 없는 서비스는 위치 이동을 별도 개발 과제로 유지한다.
3. ChatLLM(Abacus AI), ChatGPT, Claude를 우선 **전체 기록 수집·증분 재수집**, 여기에 DeepSeek / Gemini / Grok을 지원한다. 현재 후자 3개는 방문 화면 저장 방식으로 **전체 일괄수집 구현 완료라고 홍보하지 않는다**.
4. API 키, AI 호출·과금, 별도 서버 없이 브라우저 로컬 색인. 민감한 원문과 실제 사용자 파일·디버그 데이터는 GitHub 공개 저장소에 업로드하지 않는다.
5. 설치·업데이트는 일반 사용자에게 쉬운 Windows EXE 원스톱 설치를 지향한다. 사용자가 일일이 파일을 편집·직접 빌드·복잡하게 등록하도록 떠넘기지 않는다. 코드 서명과 웹스토어 게시 문제도 완료 목표로 유지한다.
6. 기존 확장프로그램 ID/설치 데이터/로컬 저장소 키를 보존한다. 업데이트 과정에서 기존 확장프로그램 삭제를 요구하지 않는다. 전체 원문 JSON 백업·복원과 오류 진단 TXT 기능을 유지한다.
7. 코드 수정은 회귀 테스트·Windows 실 EXE 빌드·ZIP 검증·GitHub Beta 프리릴리스까지 수행한다. UI가 지원하는 실제 범위를 기준으로 블로그 안내를 수정한다. 개발자 2bornot, 프로그램명 심안(心眼) / Siman을 유지한다.

## 실제 저장소/작업 기준

- 저장소: `sangkukzoa-ctrl/assets` (기본 브랜치 `main`)
- 현재 배포: `siman-v1.5.5` 프리릴리스
- 릴리스: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.5
- 버전별 **원본 소스 ZIP**: `siman/release/v155/Siman_v1.5.5_SOURCE.zip.base64`
- 버전별 **웹스토어 확장 ZIP**: `siman/release/v155/Siman_v1.5.5_WEBSTORE.zip.base64`
- 빌드 워크플로: `.github/workflows/siman-v155-release.yml`
- 실제 성공한 Windows Actions 실행: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42755517312
- 주요 배포 산출물: `SimanSetup.exe`, `Siman_EasySetup_v1.5.5.zip`, `Siman_v1.5.5_BLOG_ATTACHMENT.zip`, `Siman_v1.5.5_SOURCE.zip`, `Siman_v1.5.5_WEBSTORE.zip`, `SHA256SUMS.txt`.
- 확장프로그램은 Manifest V3; 설치 관리자는 Windows C# WinForms, 파일 위치 `%LOCALAPPDATA%\2bornot\Siman\app`; 사용자 검색 색인은 `chrome.storage.local`에 유지된다.

## 실제 사용자 검증 기록(2026-11-10의 v1.5.3 디버그 로그)

- **ChatLLM**: 발견 301개, 원문 읽기 301개, 완결 96개, 부분/완결 미확인 205개. 프로젝트·일반 세션 목록/중복 페이지/원문 완결 판정이 중점 과제.
- **Claude**: 발견 91개, 91개 저장 완료.
- **ChatGPT**: 624개 발견, 31개 완료, 593개 미완료. HTTP 429 연속 발생으로 재시도 보호 필수. 로컬 저장소 통신 시간초과 진단도 관측됨.
- **Gemini, DeepSeek, Grok**: 각 0건. 실제 방문 저장 성공 여부 재확인이 필요한 상태.
- 개인 대화 로그 전체를 이 문서나 공개 릴리스에 붙이지 않는다.

## 버전별 변경 내역

- **v1.5.4**: ChatLLM `totalEvents`와 실제 메시지 수의 차이를 고려한 완결 판정 수정, ChatGPT 첫 HTTP 429 시 보호 중단 및 최소 15분 재시도, 목록 수집과 원문 저장 상태 분리.
- **v1.5.5**: `content.js` 초기 의존성 지연 시 최대 20회 재시도, 저장 브리지 초기 검사 최대 8회, 방문 저장 실패 재시도, SPA 텍스트 변경 관찰/4.5초 내 저장 시도/12초 주기 점검, `VISIT_CAPTURE`, `VISIT_SKIP`, `VISIT_ERROR` 진단, 방문 저장 3개 서비스 연결 재설정, 기존 색인 보존.
- **CI 검증**: `bridge.test.cjs`, `collectors.test.cjs`, `deepseek_dom.test.cjs`, `v154_regressions.test.cjs`, `v155_archive_integrity.test.cjs`, `v155_capture_recovery.test.cjs`, JS syntax, 설치 파일 실제 컴파일·Fresh install·clean replacement, 배포 ZIP 해시 및 릴리스 업로드 모두 통과.
- **검증 한계**: 위 결과는 Windows 빌드 및 모의/회귀 테스트 성공이다. 실계정의 전 서비스 전수 원문 수집·모든 서비스 화면의 100% 방문 저장·원문 특정 메시지 이동 성공을 증명하지는 않는다.

## 개발을 이어갈 때의 작업 순서

1. **최신 상태 동기화**: GitHub의 `main` HEAD, `siman-v1.5.5` 릴리스 파일, `siman/release/v155` 원본 ZIP, 성공한 Windows Actions를 비교한다. 문서 버전과 실제 배포를 혼동하지 않는다.
2. **소스 복원 및 테스트**: Base64 ZIP을 디코딩하고 SHA256으로 배포 파일과 교차 확인한다. 소스 디렉터리 구조는 `app/` (`content.js`, `page.js`, `core.js`, `db.js`, `store.js`, `search.js`, `network.js` 등), `installer/`, `tests/`. 기존 6개 회귀 테스트와 manifest 검증을 반드시 유지한다.
3. **실사용 재검증**: 사용자 v1.5.5 최신 진단 로그에서 ChatLLM '부분 205'의 실제 누락/오탐 여부, ChatGPT 429 이후 미완료분 재개, Gemini/DeepSeek/Grok 방문 저장 0건의 원인을 분리한다. 완료하지 않은 수집을 전체 성공이라고 표시하지 않는다.
4. **핵심 미완료 개발**: ChatLLM 프로젝트/일반 세션의 누락 없는 원문 수집 및 정확한 상태 판정, ChatGPT 제한 후 안전한 이어받기, Claude 회귀 없는 유지, 방문 저장의 실제 사이트별 DOM 호환, 원본 메시지 위치 바로가기, 설치 원스톱 UX를 우선한다.
5. **배포 파이프라인**: 새 버전을 만들면 소스 및 확장 ZIP 생성 → 소스/테스트 검증 → Base64 ZIP GitHub 보관 → 워크플로의 SHA 해시·버전 변경 → Windows CI 실제 테스트 → GitHub 프리릴리스 자산 공개·다운로드/해시 확인 → 블로그 변경 문구/첨부 ZIP 업데이트. 실패하면 이전 정상 배포를 유지한다.
6. **안전한 업데이트 확인**: 브라우저 확장프로그램 ID와 로컬 저장소 키가 유지되는지, JSON 백업·복원과 6개 서비스 인덱스가 손상되지 않았는지 검사한다. 개인 원문이나 계정·인증 정보를 CI/진단 로그에 출력하지 않는다.
7. **공개 채널 과제**: Chrome Web Store/Edge Add-ons 공식 게시(최초 개발자 모드 없애기)와 Windows Authenticode 서명은 미완료 목표다. 무료 배포이므로 서명/등록 비용과 실제 플랫폼 제한을 정확히 구분한다.

## 사용자가 확인할 실제 버튼/표현

`설치 파일 준비하기` → `Chrome 등록하기` / `Edge 등록하기` → `압축해제된 확장 프로그램을 로드` → Ctrl+V → `폴더 선택`.

검색 화면: `▶ 전체 일괄수집 시작`, `진단 로그 TXT 저장`, `서비스별 수집 · 연결 복구 · 백업 (고급)`, `↻ 열린 탭 연결 재설정`, `전체 원문 백업 저장`, `ZIP / JSON 기록 가져오기`, `메시지 복사`, `대화 전체 복사`, `원본 서비스에서 열기`.

**최근 릴리스나 Actions가 성공했다는 사실만으로 실제 사용자의 모든 계정에서 기능이 정상 동작했다고 판단하지 않는다.**


## 2026-11-10 추가 확립: ChatLens 방식의 영구 Beta 배포

- 블로그에는 **버전별 `siman-v1.5.5` 릴리스가 아닌** 아래 고정 주소만 노출:
  - 공개 릴리스: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
  - 설치 ZIP: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip
  - 단독 설치 관리자: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/SimanSetup.exe
- 자동 배포 파이프라인: `.github/workflows/siman-v155-release.yml`, 입력 `siman/release/v155/**` 변경 또는 워크플로 변경 시 자동 실행. 기존 Node 검증→Windows 빌드→실제 설치·재설치→버전 기록→**고정 배포 자산 갱신**. 개발자가 향후 v1.5.6 등을 만들 때는 소스/확장 패키지와 버전별 워크플로 변수도 함께 갱신할 것. 블로그 URL은 바꾸지 않는다.
- 별도 공개 다운로드 검사: `.github/workflows/siman-public-download-check.yml`, 매일 04:35 KST, 성공한 빌드 이후 또는 수동 실행. 인증 없이 공개 ZIP과 EXE를 직접 다운로드하고 SHA-256, ZIP 무결성, 필수 파일을 검사.
- 최신 배포 결과: GitHub Actions `42772522126` (Windows 빌드·고정 릴리스 성공); 공개 다운로드 검사 `42772943715` (성공).
- 고정 URL은 자동으로 최신 빌드를 **제공**하지만, 기존 사용자 PC에 설치된 Chrome/Edge의 개발자모드 확장프로그램을 원격으로 자동 갱신하는 방식은 아니다. 사용자가 새 설치 관리자로 업데이트한 후 확장프로그램 새로고침이 필요하다. 추가 자동 업데이트는 독립된 개발 목표로 다룬다.
- 이전 실패 공개 검사 2회는 Windows CRLF의 `SHA256SUMS-LATEST.txt`를 Linux `awk`로 처리할 때 파일명 끝의 `\\r`가 비교에 들어간 검사 도구 측 문제였으며, `tr -d '\\r'` 선행 정규화 후 통과했다. 실제 파일 SHA 자체는 일치했다.


## 2026-11-10 23:41 KST 이후: v1.5.6 오류 수정 및 실제 배포

- 사용자가 업로드한 실사용 진단: `Siman_v1.5.5_Debug_20261110_234114.txt` (민감한 전체 원문은 GitHub에 올리지 않음).
- **ChatLLM**: 301 발견 · 41 완료 · 260 미수집. `/api/getDeploymentConversation` 200 이후 진행 기록이 끊겨 watchdog 95초 중단.
- **ChatGPT**: 643 발견 · 198 완료 · 444 pending · 1 retry. 첫 HTTP 429에 중단해 재개를 대기하는 기존 로직 정상.
- **Claude**: 103/103 완료. **Gemini/DeepSeek/Grok**: 당시 열린 탭 없음, 0건.
- GitHub 원본 압축 ZIP에서 개발 소스를 `siman/development/`으로 복원. 이제 개발용 원본 소스를 직접 수정하며 빌드는 GitHub Actions가 수행한다.
- 코드 변경:
  1. `app/network.js`: 관찰된 요청 replay의 AbortController 타이머를 `response.json()` 완료까지 유지.
  2. `app/page.js`: 직접 API 응답의 JSON body를 읽는 동안에도 60초 AbortController 동작, 오류 로그 및 ChatLLM 단계별 진행 신호 강화.
  3. `app/search.js`: 95초 이상 진행되지 않고 수집 페이지가 사라진 상황에서 보관 데이터 보존 + 최대 1회 재연결.
  4. `tests/v156_stall_recovery.test.cjs`: HTTP 200 이후 본문이 무기한 대기하는 응답을 재현하여 타임아웃을 검사, 연결 재시도·429 보호 회귀 검사.
  5. `app/manifest.json`, `installer/SimanSetup.cs`, 검색 UI, 설치 안내를 v1.5.6으로 수정. 확장프로그램 ID/로컬 저장소 키는 변경하지 않음.
- 배포 워크플로: `.github/workflows/siman-v156-release.yml` — `siman/development/**` 변경 시 자동 실행, 7개 Node 테스트 및 Windows GUI 실 설치·재설치 후 `siman-v1.5.6` 개별 릴리스 + `siman-beta` 동일 URL 갱신.
- 성공한 Windows 빌드: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42838603463
- 다운로드된 공개 EXE·ZIP·소스/확장 ZIP 무결성 검사 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42838805988
- **영구 배포 링크(블로그 수정 불필요)**: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- 고정 Windows ZIP: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip
- 버전별 이력: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.6
- 개발자 지침: 다음 사용자 실사용 로그에서 **ChatLLM 301개 중 미완료 건수 감소·타임아웃 해소**를 우선 검증. 개선이 충분하지 않다면 다음 오류 위치를 기준으로 코드 수정. v1.5.6의 모의/CI 성공을 실제 로그인 계정 301건 전수 수집 성공이라고 표현하지 말 것.

## 2026-11-11 03:22 KST — v1.5.7 원클릭 자동 덮어쓰기 업데이트 완성

### 사용자 요청
- 매 버전마다 JSON 백업, 확장프로그램 삭제·재설치·다시 등록·폴더 선택하는 방식이 번거롭다.
- **설치 관리자 실행만 하면 기존 심안 코드가 자동으로 덮어써져야 한다.**
- ChatLens와 동일하게 블로그의 GitHub `siman-beta` 고정 다운로드 주소 유지.

### 수정 구현
- `siman/development/installer/SimanSetup.cs`: `AppVersion=1.5.7`, `InstallerRevision=4`.
  - WinForms `Shown` 시 `DoInstall(true)` 자동 호출. 버튼은 반복 설치/복구용으로 유지.
  - `--install` 및 `--update` CLI 동일 설치 경로 수행.
  - `%LOCALAPPDATA%\\2bornot\\Siman\\app` 설치 루트를 **폴더 자체를 지우지 않고 관리 대상 코드 파일만 제자리 덮어쓰기**, 설치 전 .siman-rollback- 임시 복사본 마련.
  - `.siman-managed-files.txt`로 이전 설치기 관리 대상 코드 중 불필요한 파일만 삭제, 사용자 지정 파일은 보존.
  - 설치 중 오류 발생 시 이전 코드 파일 복원 시도; browser profile, `chrome.storage.local`, 확장프로그램 ID를 수정·제거하지 않음.
  - 새 설치에는 브라우저 최초 등록 1회 필요. 기존 설치 업데이트에서 재등록/JSON 내보내기 단계는 불필요. 실행 중 Chrome/Edge에는 확장 새로고침 또는 브라우저 재시작 필요할 수 있음.
  - 기존 UI의 무조건 백업·재등록하라는 잘못된 안내 제거.
- `siman/development/app/manifest.json`, `page.js`, `search.js` 버전 v1.5.7.
- `siman/development/README_INSTALL_BETA.txt`, `BLOG_UPDATE_COPY.txt`, `BLOGGER_INSTRUCTIONS.txt`: 원클릭 업그레이드·고정 다운로드 주소 기준 개편.
- `.github/workflows/siman-v157-release.yml`: Node 7종 회귀 + **실제 Windows EXE 신규 설치, v1.5.6 모의 구버전 덮어쓰기, 디렉터리 생성 시각 동일성, 관리 대상 구 코드 제거, 사용자 미관리 파일 보존, 반복 업데이트** 테스트. 롤백 경로 정적 검사. 빌드·검증 후 `siman-v1.5.7` 버전 기록과 `siman-beta` 자산 업데이트.
- v1.5.6 빌드 워크플로우는 수동 전용으로 전환해 오래된 릴리스가 최신 베타를 덮어쓰지 않도록 함.
- Github App이 기존 `siman-beta` 태그 강제 이동을 거부(403)하므로 고정 태그 이름을 유지하고 릴리스에 있는 파일과 notes만 갱신. 현재 빌드 소스 SHA는 beta notes에 기록; 버전별 릴리스 `siman-v1.5.7` 별도 보존. 업로드 충돌 시 재시도 및 Actions 동시 배포 직렬화 추가.

### 완료 및 검증 링크
- 최종 v1.5.7 Windows 모든 빌드·실제 업데이트 테스트·고정 Beta 배포 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42876693700
- 익명 public URL에서 EXE·설치 ZIP·Source ZIP·Webstore ZIP·해시와 안내문 다운로드 및 SHA-256·압축 검증 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42876853630
- 고정 배포: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- 고정 Windows ZIP: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip
- 개별 버전: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.7
- CI 최종 커밋: `47a365ef0bd54461869e288d17c0adc6808a0a8b`.
- **정확한 한계:** Chrome/Edge 확장프로그램 자체를 자동으로 재로딩하는 기능은 구현되지 않았다. 현재는 EXE 실행 → 기존 설치 디렉터리에 자동 덮어쓰기까지 구현. 브라우저 새 코드 반영에 확장 새로고침/재시작이 필요할 수 있다. 기존 크롬 프로필의 실 데이터가 다른 환경에서 자동 보존됨을 검증한 것이 아니라, CI가 디렉터리 유지·파일 보존을 테스트했고 설치 코드가 Chrome 프로필 저장소에 손대지 않는 구조다.
