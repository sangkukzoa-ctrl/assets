# 심안(心眼) 3차 — 즉시 개발 재개 인수인계 (2026-11-12 KST)

이 파일은 「유틸 프로그램 개발」 프로젝트의 「심안(PC 유틸) 2차」에서 진행 중이던 실제 GitHub 코드 변경·실브라우저 검증·빌드·사용자 지시를 3차 세션으로 넘기기 위한 문서입니다.

**3차 세션에서 사용자가 "진행"이라고 입력하면 이 파일 및 GitHub 최신 소스를 확인하고, v1.5.8 브라우저 자동 갱신 실패 문제를 즉시 수정→실제 Windows Chrome E2E→고정 Beta 자동 배포 순서로 실행하십시오. 이미 사용자가 정한 목표를 다시 질문하지 말고, 이미 개발된 코드를 폐기하지 마십시오.**

## 1. 현재 실제 상태 (완성과 미완료 명확히 구분)

- 공개된 최신 검증본: **v1.5.7 Beta**. 영구 주소 https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- 다음 개발 중인 버전: **v1.5.8**. 수정된 실제 소스는 GitHub main / siman/development/ 아래에 있습니다.
- 8개 Node 회귀 테스트, Windows GUI 설치 관리자 컴파일, 기존 설치 디렉터리 제자리 덮어쓰기, 검색 원문 영역 보존을 확인하는 Windows CI는 통과.
- Chrome/Edge 확장프로그램 자체가 자동 새로고침되고 새 버전 실행 확인 ACK가 오는 **실브라우저 E2E 미완료**.
- 최신 실패한 v1.5.8 run: https://github.com/sangkukzoa-ctrl/assets/actions/runs/43083987630 (Job ID 130743532843)
- Chrome for Testing 157.0.8103.50 실브라우저. 구버전 v1.5.7의 unpacked extension ID aoiihfkacidmiggdebbfmbehnjodlian 탐색 성공. 설치 폴더에 v1.5.8 덮어쓰기 성공. 갱신 페이지 자동 주소창 이동 성공.
- 최종 CDP 진단: Chrome 새 탭이 chrome-extension://<same-id>/siman-update-158.html 로 이동했으나 **ERR_BLOCKED_BY_CLIENT**. 페이지 본문 “This page has been blocked by Chromium”, hasRuntime=false. **BROWSER AUTO RELOAD: 0/1**, 설치 관리자 ACK 없음.
- 따라서 v1.5.8은 아직 고정 베타에 배포하지 않았습니다. 이전 공개 v1.5.7이 그대로 보존됩니다. 2026-11-12 공개 다운로드 자동 검사 성공 run 43135856607은 **v1.5.7 파일**의 공개 URL/ZIP/SHA가 정상이라는 뜻입니다.
- 실브라우저 원인이 확실히 '캐시'라고 단정하는 것은 부정확. 새로운 파일명 bootstrap까지 Chromium에서 ERR_BLOCKED_BY_CLIENT로 차단됨을 실제 확인함.

## 2. 사용자 최종 확정 요구: 원클릭 완전 자동 업데이트

ChatLens처럼 **영구 GitHub 다운로드 URL 고정**. 개발자가 코드 수정→GitHub Windows 빌드·검증→새로운 버전의 EXE/ZIP 고정 릴리스 자동 게시. 네이버 블로그 수정 불필요.

사용자가 SimanSetup.exe를 단 한 번 실행하면 모두 자동:
1. 기존 심안 설치 경로를 찾아 새 파일로 **같은 위치 덮어쓰기**.
2. 기존 Chrome/Edge에 이미 등록된 같은 확장 ID의 심안을 **실제로 자동 Reload**.
3. 기존 Chrome/Edge 로컬 검색 색인·원문·데이터와 확장프로그램 ID 보존. 확장 삭제 및 재등록 금지.
4. 매번 JSON 백업/복원, 수동 설치 경로 선택, Chrome 확장프로그램 관리 페이지에서 사용자가 직접 새로고침하는 과정 불필요.
5. 자동 Reload를 성공적으로 확인한 경우에만 전체 업데이트 완료로 표시; 문제 있으면 진단 로그 남기기.
6. 작성 중인 AI 대화 입력을 가능한 한 보존하며 자동 탭 새로고침 처리.
7. 최초 설치 사용자만 기존과 같이 브라우저 확장프로그램을 1회 등록하면 됨.

사용자의 직접 발언: “유틸 프로그램 답게 설치하면 기존것을 덮어야 한다”, “네가 말한 그 뒤 기능까지 되어야 의미가 있는건데”. 설치 파일 교체만 성공해도 끝냈다고 하지 말 것.

## 3. GitHub 위치 및 보존해야 할 코드

Repo: sangkukzoa-ctrl/assets, branch main, 개발자 2bornot.
- 소스 전체: https://github.com/sangkukzoa-ctrl/assets/tree/main/siman/development
- v1.5.8 Windows QA: .github/workflows/siman-v158-release.yml
- v1.5.7/v1.5.6 워크플로는 수동 전용으로 변경되어 구버전 재배포 사고 방지
- 지속 공개 고정 릴리스: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- 설치 EXE: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/SimanSetup.exe
- ZIP: https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip
- 공개 URL 자동 확인: .github/workflows/siman-public-download-check.yml
- 이전 포괄적 상태/기능 기록: siman/CONTINUATION_2026-11-10.md, siman/README.md
- 모든 소스는 GitHub siman/development/에 읽기/쓰기 가능한 상태. v1.5.5 Base64 ZIP에서 실제 편집 가능한 소스를 복원한 상태이므로 다시 복원/설계하지 말 것.

현재 중요한 파일:
- siman/development/installer/SimanSetup.cs : AppVersion 1.5.8, InstallerRevision 5. v1.5.7의 InstallCore()는 %LOCALAPPDATA%\2bornot\Siman\app 폴더 삭제 없이 관리 대상 코드만 덮어쓰기, 사용자 파일 보존, 이전 코드 임시 롤백. v1.5.8 추가된 DiscoverBrowserExtensions()는 Chrome/Edge Default 및 Profile N의 Secure Preferences와 Preferences를 READ ONLY로 조회, app 경로 동일성을 기준으로 기존 ID 확인. ApplyBrowserUpdates()는 TcpListener localhost 1회용 token ACK를 기다리면서 브라우저 새로고침 요청. NavigateExistingBrowser()가 Windows UI Automation의 실제 Chrome/Edge 주소창 ValuePattern.SetValue 및 ENTER로 내부 URL을 전달하고, 실패 시 foreground 확인 후 키보드 대체. 현재 실브라우저 주소창 이동까지만 성공.
- siman/development/app/manifest.json : MV3, v1.5.8, background.service_worker=background.js
- siman/development/app/background.js : 새 extension 로드 시 pending 일회성 token 처리, 입력 중인 채팅탭 자동 새로고침 회피, 로컬 루프백 http://127.0.0.1:<port>/complete 로 Windows installer ACK.
- siman/development/app/search.js : 기존 search.html의 URL 파라미터 auto-apply 경로 추가했으나 실제 Chrome 구버전에서 reload 동작 불충분.
- siman/development/app/siman-update-158.html 및 siman-update-158.js : 구버전에 없던 새 이름의 갱신 전용 페이지. Node 모의 테스트에서는 업데이트 지시 및 runtime.reload 동작 통과, 그러나 실제 Chrome에서 페이지 자체가 ERR_BLOCKED_BY_CLIENT.
- siman/development/tests/v158_autoapply.test.cjs : extension pending, runtime.reload, ACK, 채팅 입력/보존 회귀 테스트.
- siman/development/tests/v158_browser_cdp_probe.cjs : 실제 Chrome 페이지 CDP 진단. 진단 출력에 일회용 token 포함 URL이 보여질 수 있음: 다음 작업에서 로그 데이터 최소화 권장.
- siman/development/RELEASE_NOTES_v1.5.8.md : 초안. 배포 완료 전 최신 실제 검증 상태에 맞춰 수정해야 함.

## 4. 실브라우저 실패 진단 세부 순서

1. 초기 v1.5.8 Chrome E2E는 기존 확장 ID가 Preferences에 없다는 이유로 실패. 실제 파일은 Chrome Secure Preferences; 두 위치를 읽도록 C# 소스 수정하여 **원래 extension ID 탐색 성공**.
2. 기존 Chrome 프로세스를 외부 명령 실행하면서 chrome-extension:// URL 전달 시 새 탭만 열림. UI Automation으로 브라우저 주소창 탐색하여 URL 직접 이동으로 변경해 **CDP에서 실제 새 갱신 페이지 탭 확인 성공**.
3. 기존 search.html을 이용한 접근도, 새로운 siman-update-158.html 접근도 결과적으로 ACK 없음.
4. **최종 확정 진단: chrome-extension 탭 자체가 Chromium ERR_BLOCKED_BY_CLIENT 페이지이며 chrome.runtime 없음.** 이는 단순한 검색 코드 오류가 아님. 해당 ID/리소스 접근을 Chromium이 허용하지 않은 상태.
5. Chrome 테스트는 GitHub Windows runner에서 이전 v1.5.7 WEBSTORE ZIP을 설치하고, Chrome for Testing 안정판을 실행, 본 설치 관리자로 업그레이드하는 실제 E2E. E2E가 실패하면 릴리스 발행이 자동 중단됨. **이 게이트를 임의로 제거해서 통과로 표시하지 말 것.**

### 3차 첫 작업의 합리적 접근

새 갱신 페이지 주소 접근이 차단된 원인을 실제 Chrome extension state, 보안/disabled 원인, 브라우저 정책, manifest 및 등록 상태에서 검증. 동시에 **기존 extension ID의 Chrome 내부 확장프로그램 관리 화면 chrome://extensions 에서 해당 카드의 '다시 로드' 컨트롤을 자동 호출**하는 방식 등 다른 실현 경로를 연구/시도. Chrome 내부 UI나 정식 브라우저 API를 통해 같은 확장 프로그램을 다시 로드할 수 있다면, 이후 v1.5.8 background.js에서 ACK까지 검증할 수 있음. 단순히 다른 chrome-extension:// 페이지를 다시 만들어 같은 실패를 반복하지 말 것.

**중요 제약:** 사용자 브라우저 프로필 파일, 저장된 검색 색인, 확장 ID를 직접 변경하지 않음. Chrome/Edge 강제 종료와 다른 응용 프로그램 키 입력 방지. 재등록, 수동 사용자 조작, 데이터 백업을 업데이트 필수 절차로 만들지 않음.

## 5. 현재 개발이 훼손해서는 안 되는 기능

원문 검색 심안은 ChatGPT, Claude, ChatLLM 계정의 원문 세션 일괄 수집/재개, Gemini/DeepSeek/Grok의 방문 대화 저장을 지원. JSON 전체 기록 내보내기/가져오기, 디버그 TXT, 검색·원문 뷰어 및 원본 서비스 열기 기능. Chrome/Edge 확장 ID를 보존하므로 기존 chrome.storage.local 데이터도 유지해야 함.

이전 사용자 디버그 실측 (v1.5.5): ChatLLM 301건 발견, 41건 완료, 260건 미수집 (HTTP200 이후 95초 중단), ChatGPT 643건 발견 198건 완료 429 제한 보호 중단, Claude 103/103 완료. v1.5.6은 HTTP200 JSON body 무응답 타임아웃, ChatLLM 단계별 진단, disconnected 상태 최대 한 번 재연결 구현. 기존 회귀 테스트 모두 지킬 것.

## 6. “진행” 시 실제 수행 순서

1. GitHub main의 이 문서, 실제 SimanSetup.cs, manifest/background, v158 workflow, 마지막 Windows run 로그 확인.
2. ERR_BLOCKED_BY_CLIENT 원인 검증 및 기존 ID extension 재로딩 경로 실제 구현.
3. Node 회귀 + Windows EXE 컴파일, **기존 v1.5.7 확장 설치 및 켜진 실제 Chrome에서 v1.5.8로 무인 업그레이드, 동일 ID 및 원문 영역 보존, 새 버전 실행/ACK 실증**.
4. 필요 시 Edge 테스트도 적용; 실패한 것은 정확히 진단.
5. E2E 성공한 빌드만 siman-v1.5.8 개별 릴리스와 siman-beta 고정 릴리스에 자동 게시. v1.5.8을 이미 발행한 적 있는지 확인 후 중복 업로드 처리. 공개 다운로드 검사 workflow가 v1.5.8 배포 뒤에도 발화하도록 workflow_run 추가.
6. 성공 결과 (빌드/다운로드/코드 링크)와 남은 문제를 사용자에게 정확히 보고, GitHub README, 릴리스 안내, 본 인수인계서를 갱신.

장시간이면 실제 테스트/코드 수정 묶음으로 진행하되, 사용자에게 “진행”만으로 계속 이어나가게 상태 기록. 단계별 유효한 산출물 우선; 원점 재시작/불필요한 질문 금지.

## 7. 새로운 대화 안내

대화 제목: **심안 3차** (같은 ChatGPT 프로젝트 「유틸 프로그램 개발」).

**첫 사용자 메시지: '진행'**. GitHub handoff 이 파일을 우선 읽고 위 문제 해결 즉시 시작.

새 대화 생성 자체는 ChatGPT 사용자 인터페이스에서 진행해야 하며, 이 파일은 GitHub에서 다음 대화가 즉시 읽을 수 있는 지속적인 작업 상태입니다.

----
**인수인계 완료는 기능 개발 완료와 다릅니다. 현재 공개는 v1.5.7. v1.5.8의 Chrome 자동 확장 갱신은 아직 실브라우저 E2E를 통과하지 못했습니다.**
