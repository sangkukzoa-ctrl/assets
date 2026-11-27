# 배포·설치·데이터 보존

## 공개 배포 기준 (변경 금지)
최신 v1.5.13, installer R11. 현재 버전별 및 고정 릴리스의 EXE, Windows ZIP, source ZIP, Webstore ZIP digest가 동일.
- 고정 페이지 https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- EXE https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/SimanSetup.exe
- ZIP https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-beta/Siman-Windows.zip
- 전체 versioned source https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-v1.5.13/Siman_v1.5.13_SOURCE.zip
- 확장 ZIP https://github.com/sangkukzoa-ctrl/assets/releases/download/siman-v1.5.13/Siman_v1.5.13_WEBSTORE.zip
- STATE.json에 GitHub release API의 asset SHA-256 digest 기록. 2026-11-13 CI 43439284243 및 공개검사 43439664742 success 확인.
- 기존 siman-beta tag를 force-move하지 말 것. GitHub App 403 사례 있음. 기존 tag에 릴리스 자산/노트 갱신, notes에 실제 source SHA, 새 버전별 릴리스 유지. 네이버 블로그는 고정 주소 변경 불필요.

## 설치 관리자의 설계 및 실패 이력
1.5.7 이후 WinForms 실행 시 자동 제자리 설치. 관리 파일 목록 .siman-managed-files.txt, 코드 롤백/미관리 파일 보존. 기존 브라우저 프로필의 Preferences/Secure Preferences는 **읽기 전용**, 설치 경로와 정확히 일치하는 기존 ID를 탐색. 1.5.8~1.5.12 외부 chrome-extension:// 부트스트랩 탐색은 실제 사용자 및 Dev Mode OFF 테스트에서 ERR_BLOCKED_BY_CLIENT. 같은 주소 접근을 반복하지 않는다.
1.5.13은 동일 설치 폴더에 단기 일회용 siman-updater-request.json 작성(version, extensionId, loopback port, token, 발급시간); Chrome/Edge 기존 extension manager Reload 동작으로 새 background 시작, 새 worker가 자기 extension origin의 JSON 읽고 version/ID/token/time 확인, 실제 AI 탭 중 초안 작성 중인 탭 보호, localhost ACK(원문 개수 숫자 포함), 지시파일 제거. 설치 관리자에는 확인된 ACK 수/기존 확장 상태를 기록. 파일 복사 성공과 실제 코드 적용을 별도 판정한다.
실제 CI는 Dev Mode ON Chrome for Testing에서 성공. 사용자 환경, Edge, disabled extension 상태는 별도 확인. 수동 재로드는 오류 시 복구 안내이며 **업데이트 정상 절차를 수동 재등록/JSON 백업·복원으로 퇴행시키지 않음**.

## 일반 Chat LLM에서 production 배포할 때
이관 브랜치에서 테스트/검토. 기존 main 기반 별도 브랜치에 필요한 심안 파일/워크플로만 선별 이식. main의 자동 발행 trigger(.github/workflows/siman-v1513-release.yml)가 활성 상태이므로 개발 중 main 직접 편집 금지. 새 릴리스 승인 전 현재 active publisher를 안전하게 관리할 계획을 확정하고 실제 신규 버전 workflow를 한 덩어리로 적용. 이전 버전 workflow 수동 실행 또는 오래된 branch에서 siman-beta 덮어쓰기 금지. 새 버전의 실제 CI 통과 전 기존 Beta 파일 유지. 공개 다운로드 검증 workflow의 workflow_run 목록도 최신 버전에 맞춰 확인. SHA 검사/실제 URL과 버전별 release 확인 후 README/STATE/TASKS 업데이트. **이관 작업은 릴리스 승인 아님.**
- 공개 Web Store/Edge Add-ons 등록 및 Windows Authenticode 서명은 아직 미완료. GitHub artifact provenance와 Authenticode는 서로 다르다.
- 사용자 개인정보, 원문, 인증 토큰, 비밀번호, 실제 Chrome 프로필 파일, 설치 로그 전체를 공개 repo, Actions 로그, artifact, 이관 ZIP에 포함 금지. 진단은 필요한 오류/숫자만 비식별화.
- 개발용 PAT는 최소 권한·만료 설정, 환경변수/안전한 비밀 입력 경로로만 전달. GitHub commit, file, ZIP, output/log에 남기지 않는다. 기존 사용자 PAT는 이관하지 않는다.
