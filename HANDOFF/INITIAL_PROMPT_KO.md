# Chat LLM 최초 입력용 지시문

아래는 ChatGPT에서 1차·2차·3차에 걸쳐 개발한 PC 유틸리티 심안(心眼) / Siman(개발자 2bornot)의 실제 인수인계 환경이다.

https://github.com/sangkukzoa-ctrl/assets/tree/siman-handoff/2026-11-28

첨부 ZIP이 있다면 함께 활용하라. GitHub의 HANDOFF/00_START_HERE.md → STATE.json → TASKS.md → 01~06 문서를 읽고, siman/CONTINUATION_2026-11-10.md, siman/HANDOFF_SIMAN_3_2026-11-12.md, siman/README.md 및 실제 siman/development/ 코드/테스트를 확인하라. 최신 기준은 v1.5.13 Beta, installer revision 11이다.
공개 기준 https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.13
고정 다운로드 https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta

너는 ABACUS.AI 일반 Chat LLM에서 작업한다. **Agent/DeepAgent/SuperComputer는 사용하지 마라.** 이전 PDF to Image 이관에서 확립된 GitHub 읽기·일반 채팅 Python REST/PAT 방식으로 실제 권한을 확인하고, 권한이 없는 동작을 했다고 보고하지 마라. 토큰은 소스/로그/문서/ZIP에 저장하지 마라.

심안의 본질은 전체 AI 과거 일반·프로젝트 세션의 메시지 전문을 한 검색창에서 검색하는 무료 로컬 유틸리티이다. 여섯 서비스, 사용자·AI 원문·문맥·복사·원본 위치, 기존 Chrome/Edge 확장 ID 및 원문/색인·설치 경로·고정 배포 URL 보존이 중요하다. 초기화나 삭제·재등록·매번 백업/복원 요구로 퇴행시키지 마라. CI 성공을 실제 사용자의 모든 계정 성공으로 주장하지 마라. 저장소는 여러 프로젝트를 공유한다. **심안 이관 브랜치를 main에 통째로 merge하지 마라.** 승인된 작업의 필요한 파일만 반영하라.

현재 지시는 인수인계 확인뿐이다. 소스·버전·검증·미해결 문제·권한을 확인하고 준비 상태를 구체적으로 보고하라. 새로운 기능, 수정, 발행은 시작하지 마라. 이후 사용자가 개발 과제를 승인하고 '진행'이라 하면 STATE/TASKS와 최신 소스·로그에서 정확히 이어가라. 기존 요구를 반복 질문하지 말고 실제 코드 수정/회귀/Windows 빌드/Chrome 검증으로 성과를 내라.
