# ABACUS.AI 일반 Chat LLM 협업·재개 절차

## 선례: 2026-11-26 PDF to Image
실제 브랜치 pdfimage-handoff/2026-11-26의 HANDOFF/00_START_HERE.md, 04_CHATLLM_WORKFLOW.md, STATE.json, TASKS.md, INITIAL_PROMPT_KO.md, CI/export workflow를 확인했다. 원본 소스 + 상태/작업판 + 독립 비배포 CI + ZIP. 이후 해당 일반 ChatLLM Python에서 GitHub REST 네트워크 접근을 확인했고 사용자 제공 PAT로 임시 브랜치 생성/삭제(201/204), workflow 파일 커밋(201), Actions enable/disable(204), /user(200), repo admin 권한을 검증했다는 후속 이관 기록이 있다. main 유지 및 임시 흔적 삭제. **이 성공은 심안 새 채팅에서 현재 PAT/권한을 자동 보장하지 않는다.** GitHub connector는 해당 선례에서 읽기 중심이었으므로 쓰기 가능 여부를 현재 환경에서 확인한다.

## 모드
Agent 금지. 일반 Chat LLM DeepSeek Flash 4.1 사용을 기본으로 하되 사용자가 선택한 일반 모델도 가능. GitHub 커넥터로 읽기 또는 Python standard library urllib/requests GitHub REST. 사용자 계정 토큰을 요구하거나 출력하기 전 현재 연결의 권한 확인. 사용자 승인 하에서만 최소 권한 fine-grained PAT(assets 저장소 Contents read/write, Actions read/write, Workflows write 필요 작업 시). 기존 PDF 인증값을 재사용할 수 있다고 가정 금지. 토큰은 파일/위키/STATE/로그에 저장 금지. 일반 채팅에서 토큰 안전 입력 수단이 없으면 사용자 로컬에서 환경변수로 실행하는 완성 패치/스크립트 대안 제공.

## 시작 순서
1. STATE/TASKS/00 읽고 소스 기준 및 최신 릴리스 비교. 첫 응답은 읽기/권한/재개 가능 상태 보고.
2. GitHub 커넥터 또는 REST로 정확한 branch/ref/파일 SHA 읽기. /user, /repos/owner/repo는 읽기 점검. 쓰기는 사용자가 승인한 뒤 격리된 작업 브랜치에서만 검증; 기존 main 및 workflow enable/disable 상태는 건드리지 않음.
3. 실제 수정할 때 GitHub blob → tree → commit → ref(기존 HEAD 검증/fast-forward) 또는 Contents API의 blob SHA 조건부 수정. 여러 파일은 한 논리 commit으로 묶는 것을 선호. 파일을 읽지 않은 채 덮어쓰지 않음. 다른 모델의 변경이 있으면 최신 commit을 다시 읽고 병합.
4. **현재 이관 브랜치를 통째로 main에 merge 금지**(다른 프로젝트가 제거된 심안 독립 snapshot). 승인 작업은 이관 브랜치 파생 검증 branch 또는 main 기반 별도 topic branch. production 적용 시 심안 관련 파일만 선택, 다른 프로젝트 변경 금지.
5. Windows CI는 GitHub Actions. branch push 또는 workflow_dispatch의 실제 사용 가능 여부 확인; workflow_dispatch가 default branch에 등록되지 않으면 branch push를 사용. 새 작업에서 branch filter, version, baseline validation policy를 조정. 일반 ChatLLM에서 Windows GUI 실행했다고 주장하지 않음.
6. Actions run ID/job/step conclusion 및 실패 로그 조회. artifact 다운로드/ZIP/SHA 확인. GitHub release는 승인 후 전용 gate. API 토큰/개인 대화 없이 코드와 요약 진단만 공유.
7. STATE.json/TASKS.md에 정확한 마지막 commit, 작업 상태, 실제 검증/실패, 다음 한 단계 기록. '진행'은 마지막 승인 과제를 이어가기. 처음부터 재설계/재요약하지 않는다.

## 역할 분리
GitHub가 공용 소스/상태/빌드 저장소. ChatGPT 및 ChatLLM 일반 채팅은 독립된 개발 도구. 서로의 대화 기억이나 tool 권한이 공유된다고 가정 금지. 한 작업의 소유 브랜치/HEAD/진행 기록을 먼저 확인. 사용자가 코드 구현 과제를 승인했다면 실제 파일 수정/테스트/후속 기록까지 처리하고, 단순 권한 부재 시 완성된 전체 파일/patch와 실행 가능한 검증 절차를 제공.

## 권한 실패 시
401/403/404/429를 구분. 403 rate limit과 write permission 차이 파악. 연결이 read-only면 사용자 승인 PAT 경로 또는 로컬 patch 경로, 에이전트 우회 금지. PAT 검증용 브랜치 삭제는 해당 임시 브랜치만, 기존 개발 브랜치는 삭제 금지. 비밀 출력 금지. 
