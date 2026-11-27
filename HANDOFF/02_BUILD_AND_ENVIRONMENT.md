# 빌드·실행·검증 방법

## 지금 기준
Manifest V3 Chrome/Edge, minimum_chrome_version 130 (manifest 기준), JS HTML CSS. WinForms C# .NET Framework 4.x csc.exe, Windows GitHub Actions windows-latest; UIAutomationClient.dll, UIAutomationTypes.dll, WindowsBase.dll .NET 4.8 참조 포함. Node 내장 assert/vm 등 테스트; 별도 npm install 기반 앱이 아님. 필요한 아이콘 원본 siman/installer-v151r2/SimanSetup.ico.base64. 제품 패키지 내부 app/ 전체를 extension_payload.zip로 만들어 EXE resource siman.extension.payload에 포함.

## 검증 전용 CI
.github/workflows/siman-handoff-ci.yml 은 v1.5.13 실제 성공 워크플로를 기반으로 **발행 단계만 제거하고** 기준 소스 검증과 후보 artifact 업로드를 추가했다. 대상 브랜치 siman-handoff/2026-11-28. 권한 contents: read. 새 제품 출시가 아니다.
- baseline: python tools/verify_baseline.py --working-tree (현재 132개 기존 siman 파일 + 22개 이전 워크플로 원본 Git blob 체크)
- Node 15종: bridge.test.cjs, collectors.test.cjs, deepseek_dom.test.cjs, v154_regressions.test.cjs, v155_archive_integrity.test.cjs, v155_capture_recovery.test.cjs, v1510_stall_recovery.test.cjs, v1513_autoapply.test.cjs, v1513_deepseek_web.test.cjs, v1513_gemini_web.test.cjs, v1513_grok_web.test.cjs, v1513_grok_auth.test.cjs, v1513_chrome_lifecycle.test.cjs, v1513_chatgpt_resume.test.cjs, v1513_claude_503.test.cjs.
- app/*.js node --check, manifest version, 소스 및 ZIP 읽기 검증.
- 실제 Windows EXE 빌드, --verify, --install, --update, --scan-browser. 테스트용 설치 경로 및 임시 Chrome Preferences에서 ID/파일/경로 보존 검사.
- Chrome for Testing stable, 실제 v1.5.12 WEBSTORE ZIP 설치 후 v1.5.13 갱신. Dev Mode ON (테스트용 disposable profile). 새 background ACK + 원래 ID 유지. 실패 시 CI 실패.
- 후보 EXE/ZIP/SHA를 Actions artifact로 업로드. **고정 릴리스와 버전별 릴리스 파일 변경 없음.**

기존 성공 CI source-of-truth: HANDOFF/production_workflows/siman-v1513-release.yml; 원래 .github/workflows/siman-v1513-release.yml을 그대로 보존한 사본. Windows runner를 활용하므로 Chat LLM 일반 채팅에 Windows GUI/컴파일러가 직접 있을 필요가 없다.

## 로컬 빠른 회귀 (Python/Node 가능 환경)
프로젝트 root에서 python tools/verify_baseline.py 실행. 아래 명령은 사용자가 새 개발을 승인했을 때 코드 검증용으로 사용. `node siman/development/tests/v1513_autoapply.test.cjs` 또는 위 테스트 목록 전체 실행. 단, Node 통과만으로 Windows/실브라우저/실계정 통과라 하지 않는다.

## 이후 버전
기준 manifest는 역사적 불변 snapshot이라 앞으로 수정된 파일을 baseline과 동일하다고 주장해서는 안 된다. 승인된 개발 시 새 작업 브랜치에서 검증 정책을 변경(기준 검증은 원본 snapshot, 변경 후보는 diff/회귀 검사)하고 manifest/app/version/bootstrap/installer revision 및 해당 버전 테스트/워크플로/문서를 정합성 있게 수정. 과거 테스트를 임의 제거하거나 실제 Chrome ACK gate를 완화해 빌드 통과로 위장 금지. GitHub Actions 로그/결론/commit SHA/artifact SHA를 기록.
