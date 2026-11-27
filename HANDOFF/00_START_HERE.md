# START HERE — FF14KakaoBridge / 2bornot
인계 기준일: 2026-11-27 (Asia/Seoul). ABACUS.AI 일반 Chat LLM / DeepSeek Flash 4.1 전용. 에이전트/DeepAgent 사용 금지.

**이번 요청은 인수인계다. 신규 기능, 버그 수정, 재배포 지시는 없다.** 인수 후 STATE.json/TASKS.md와 원본을 읽고 현재 상태를 보고한다. GitHub 초기 등록은 인수인계 환경 구축에 한하며 새 개발과 구별한다.

- 최신 제작본: v1.7.13 Fast Return (2026-11-13). 네이버 블로그에 이 버전이 실제 게시되었는지, 실사용 시험이 끝났는지는 확인되지 않았다. 이전 v1.7.12 입력 반응 개선은 사용자가 체감 성공을 보고했다.
- 원본: baseline/FF14KakaoBridge_v1.7.13.zip, project/main.go와 go.mod는 압축에서 그대로 추출한 원본. 이전 버전 공개 배포 준비 ZIP도 baseline/에 보존.
- 원본 EXE SHA-256: `b7d732b9cea6fdc20ddeb96c78a1759e7e0fbc2cb4f7d1481a7373918517477f`. Go 1.23.2 Linux→Windows amd64 GUI 재빌드 결과 바이트 단위 일치.
- GitHub 저장소 `sangkukzoa-ctrl/assets`는 여러 프로젝트가 공유한다. 예정 독립 브랜치 `ff14kakaobridge-handoff/2026-11-27`. 이관 ZIP 작성 시 원격 브랜치/CI 미등록; 성공했다고 보고하지 말 것. ZIP과 실제 소스를 먼저 읽고 최초 지시문이 승인한 경우에만 독립 브랜치를 구성한다.
- 네이버 블로그 배포는 사용자가 직접 한다. 새 릴리스, 서명, main 수정, 다른 프로젝트 변경 금지.

## 읽는 순서
1. STATE.json → TASKS.md
2. 01_PRODUCT_AND_ARCHITECTURE.md → 02_BUILD_AND_ENVIRONMENT.md → 03_RELEASE_AND_SECURITY.md → 04_CHATLLM_WORKFLOW.md → 05_VERIFICATION_AND_HISTORY.md → DECISIONS.md
3. project/main.go, project/go.mod 직접 확인. baseline/ 원본 배포 ZIP과 설명서 확인.
4. verification/ 결과 및 tools/verify_baseline.py로 원본 일치 검증. GitHub 초기화는 04 문서에 따른다.
5. INITIAL_PROMPT_KO.md는 최초 사용자 메시지용.

## 증거 우선순위
원본 ZIP/실제 소스/재현된 바이너리 > 실제 사용자 테스트 기록 > 빌드 및 검증 로그 > 문서 요약/가설. 빌드 성공은 실제 FF14/카카오톡 동작 성공이 아니다.
