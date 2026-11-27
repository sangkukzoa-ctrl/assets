# 일반 Chat LLM 개발 프로토콜
2026-11-26 Just PDF to Image 인계 방식의 이 프로젝트 적용판. 이전 GitHub 브랜치: `pdfimage-handoff/2026-11-26`. 해당 원본 HANDOFF 문서에서 실제 소스/독립 브랜치/비배포 CI/STATE/TASKS/초기 읽기만 수행 원칙 확인. 공통 PAT(ChatLLM-Dev)의 쓰기/Actions 권한 시험 성공은 이전 기록이며 현재 연결에서도 실제 권한을 확인해야 한다.

## 인계 환경 초기화(제품 개발 아님)
1. ZIP에서 HANDOFF/와 project/ 실제 파일을 읽는다. `python tools/verify_baseline.py`로 원본과 소스 해시 비교. 파일을 읽을 수 없으면 정확히 무엇이 막혔는지 보고한다.
2. 공유 저장소 `sangkukzoa-ctrl/assets`의 기존 main HEAD를 조회하고 기록. 브랜치 `ff14kakaobridge-handoff/2026-11-27` 존재 여부 확인. 같은 이름 브랜치가 이미 존재하면 강제 덮어쓰기 금지. 일치하는 파일이면 재사용, 다르면 질문.
3. 최초 사용자 메시지가 환경 초기화를 승인하는 경우, **독립 브랜치에** project/, HANDOFF/, tools/verify_baseline.py, verification/, .github/workflows/ff14kakaobridge-handoff-ci.yml 및 .gitignore 등록. 원본 ZIP 및 EXE는 첨부에 보존; 민감자료 없음. 기존 브랜치 및 main에 커밋하지 않는다. GitHub Git Data API로 새 tree를 만들 수 있다. 로컬 실행 환경과 기존 토큰이 있다면 `python tools/bootstrap_github.py --apply` 사용 가능(기본 dry-run). 토큰은 GITHUB_TOKEN 또는 GH_TOKEN 환경변수에서만 읽고 출력 금지. 이 스크립트는 기존 branch 존재 시 종료하고 새 branch만 생성하며 main을 업데이트하지 않는다. main 부모를 갖는 독립 tree이므로 **main에 병합하지 않는다**.
4. 생성된 브랜치 HEAD, 원격 소스 blob/원본 SHA 확인, 기존 main HEAD 비교. CI 자동 push 실행이 있는지 실제로 확인. 수동 dispatch가 불가하면 원격에서 허용하는 경우 전용 브랜치의 CI-only 초기화 커밋으로 실행(제품 변경 없음). 실행할 수 없으면 명시하고 대기. 실제 결과 없이는 성공 보고 금지.
5. STATE/TASKS에 원격 브랜치/CI 상태와 증거 링크만 갱신. 제품 코드는 수정하지 않는다. 최초 준비 보고 후 새 과제 대기.

## 향후 작업 방식
- 에이전트 없이 일반 Chat LLM DeepSeek Flash 4.1. 필요한 경우 GLM 교차 검수. 이미 공통 PAT 설정이 있으므로 토큰 재발급 요구하지 않는다. GitHub 권한 부족 시 가능한 파일 또는 diff와 정확한 제약을 제공.
- 실제 소스 확인 → 요구사항/영향 범위 확정 → 필요한 최소 변경 → 별도 브랜치 커밋 → Actions 로그/산출물 확인 → 실제 Windows 테스트(가능한 환경에서) → 상태 기록. 사용자가 `진행` 입력 시 직전 승인 과제부터 이어간다. 한 단계씩 이어가되 불필요한 반복 승인/설명 금지.
- 컴파일 산출물의 EXE + 전체 Source ZIP 제공 선호. 사용자 테스트 결과가 오면 기존 동작과 회귀 비교. 로컬 검증과 실제 기기 검증을 분리한다. 릴리스는 별도 승인.
- 제품 변경 없이 이관만 완료한 경우 no_active_task 상태를 유지한다. 새 작업이 없는데 테스트할 버전을 임의로 만들지 않는다.
