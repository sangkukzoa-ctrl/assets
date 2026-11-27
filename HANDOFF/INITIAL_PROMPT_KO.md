첨부 ZIP은 FF14KakaoBridge(개발자 2bornot)의 실제 전체 인수인계 환경이다. ABACUS.AI 일반 Chat LLM의 DeepSeek Flash 4.1로 작업하며 에이전트/DeepAgent는 사용하지 마라.

HANDOFF/00_START_HERE.md → STATE.json → TASKS.md → 01~05 및 DECISIONS.md → project/main.go, go.mod → baseline/ 및 verification/ 순서로 직접 읽고 확인하라. 원본 v1.7.13 Fast Return(2026-11-13), Go 1.23.2 Windows x64이며 원본 EXE SHA-256은 b7d732b9cea6fdc20ddeb96c78a1759e7e0fbc2cb4f7d1481a7373918517477f이다. 원본 재빌드 해시 일치가 확인되었다. v1.7.12 사용자는 입력 반응 개선을 확인했으나 v1.7.13 실기기 확인은 미확인 상태다. 단위 테스트는 없고 기존 unsafe.Pointer vet 경고 9건이 있다.

이관 환경 초기화만 승인한다. 기존 공통 GitHub 연동/PAT를 재사용하고 `sangkukzoa-ctrl/assets`의 독립 브랜치 `ff14kakaobridge-handoff/2026-11-27`에 실제 project/ 소스·HANDOFF/·검증 도구·비배포 CI 워크플로를 등록하라. HANDOFF/04_CHATLLM_WORKFLOW.md에 정확한 방법이 있으며 tools/bootstrap_github.py는 실행 환경 및 기존 토큰을 사용할 수 있을 때만 이용하라. 토큰 값을 출력하거나 요구하지 말고, main/다른 프로젝트/기존 릴리스는 절대로 수정하지 마라. 동일 브랜치가 이미 있으면 먼저 일치 여부를 확인하고 덮어쓰지 마라. 인계 CI는 제품 변경 없이 빌드/원본 해시 검증만 허용한다. 실제 권한과 커밋, Actions 결과를 확인하고 확인하지 못한 일은 성공했다고 보고하지 마라. ZIP/파일 접근 또는 GitHub 작업이 불가능하면 구체적인 제약과 필요한 조치만 보고하라.

현재 새 개발 과제는 없다. 기능 추가, 버그 수정, 새 버전 제작, 릴리스/블로그 배포를 임의로 시작하지 마라. 초기화 후 실제 소스/원격/빌드 상태, 미확인 항목과 다음 개발 가능 여부를 보고하고 대기하라. 이후 내가 새 과제를 지시하거나 승인된 작업 중 '진행'이라고 하면 STATE/TASKS와 직전 결과에서 바로 이어가라. 이미 제공된 요구사항을 반복 질문하지 마라.
