# TASKS — 2026-11-28

## 승인된 활성 개발
**없음.** 현재 사용자 지시는 Chat LLM 이관 준비 및 인계. 기존 v1.5.13 제품 코드, main, 릴리스 수정·발행 금지. 이관 검증 전용 CI 및 ZIP 생성은 이관 작업의 일부.

## 이관 상태
- [x] PDF to Image 2026-11-26 실제 브랜치/STATE/TASKS/CI/export/초기 프롬프트 비교
- [x] main의 development tree와 v1.5.13 빌드 commit 일치 검증
- [x] 공개 버전별/고정 릴리스 SHA digest 대조
- [x] 세 세션의 핵심 요구·실패·검증·현 상태와 원본 기록 보존
- [x] 이관 전용 브랜치의 실제 Windows CI 성공 (154개 원본 blob, Node 15종, EXE 설치·갱신, Chrome 실 E2E 및 후보 artifact)
- [x] CI 결과 및 run 46026757091을 STATE에 반영
- [ ] 이관 ZIP은 export workflow가 자체 검증 후 브랜치에 커밋하며, SHA256 파일과 실제 공개 파일 존재로 완료 확인
- [ ] Chat LLM 새 일반 대화에서 자료 및 권한 열람 확인 (사용자 환경에서 진행)

## 남은 기술 문제 (미승인 신규 과제)
HANDOFF/06_NEXT_DEVELOPMENT_RISKS.md 참조. 최신 실측과 증거의 우선순위를 기반으로 사용자가 다음 개발을 지시하면 작업 시작.

## 다음 과제 기록 양식
Task ID / 사용자 요청 / 승인 범위 / 수용 기준 / 브랜치 / 원본 HEAD / 변경 파일 / 마지막 commit / CI run 및 실패 단계 / artifact+SHA / 실제 Chrome·Edge·실계정 검증 / 공개 발행 승인 YES·NO / 결과 / 미완료 / 다음 정확한 행동. STATE와 함께 갱신. 진행만 외치면 승인된 마지막 업무 재개.
