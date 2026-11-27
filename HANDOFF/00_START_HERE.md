# START HERE — 심안(心眼) / Siman, 2bornot

2026-11-28 · 한국시간 · ChatGPT 심안 1차 → 2차 → 3차 → ABACUS.AI Chat LLM 일반 채팅 이관.

## 가장 중요한 규칙

- **일반 Chat LLM (기존 PDF 이관에서 검증한 DeepSeek Flash 4.1 일반 채팅 방식), Agent/DeepAgent/SuperComputer 금지.** GitHub 커넥터 읽기 또는 일반 채팅 Python의 GitHub REST 사용. 실제 권한은 현재 세션에서 검증.
- **이관 자체는 신규 개발 지시가 아니다.** v1.5.13 공개 배포를 그대로 유지하고 소스·상태를 검증한 후 준비 완료 보고. TASKS에 승인된 작업이 없으면 "진행"만으로 새 기능이나 새 릴리스를 만들지 않는다.
- 사용자가 개발을 승인한 뒤에는 반복 계획만 작성하지 말고 실제 코드 읽기/수정/테스트/빌드/검증을 진행. "진행"은 승인된 마지막 작업의 정확한 다음 단계 재개.
- 전체 세션 통합 전문 검색이 본질이다. 제목 검색, Ctrl+F, 현재 열린 대화만 저장하는 프로그램으로 퇴행시키지 않는다.
- 기존 확장 ID, 설치 경로, chrome.storage.local 원문/색인, 블로그 고정 URL 보존. 확장 삭제·재등록 또는 백업/복원부터 요구하지 않는다.
- 원문·인증값은 사용자 브라우저에만. 개인 로그, PAT, 비밀번호, Chrome 프로필을 공개 GitHub/CI/ZIP에 올리지 않는다.

## 실제 원본
- 저장소 https://github.com/sangkukzoa-ctrl/assets
- **이관 브랜치 https://github.com/sangkukzoa-ctrl/assets/tree/siman-handoff/2026-11-28**
- 원본 소스: siman/development/ (프로덕션과 같은 경로). 기준 Git tree 3bfc7f13f88b9060a6e20b6560c2e4bf5b7288ae.
- main 스냅샷 d1a7af4196eb724d9d3327a534f48cbdd17e255c; 공개 v1.5.13 CI commit 4dc301c40bfc471ac72aef7b1e827ae4f8c23ee9. 두 commit의 development tree가 동일.
- 공개 최신: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.5.13
- 고정 Beta: https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta
- Windows 빌드 성공: https://github.com/sangkukzoa-ctrl/assets/actions/runs/43439284243
- 익명 공개 다운로드/SHA 검증: https://github.com/sangkukzoa-ctrl/assets/actions/runs/43439664742

## 읽을 순서
1. HANDOFF/STATE.json, TASKS.md (지금 상태와 승인 범위)
2. HANDOFF/01_PRODUCT_AND_ARCHITECTURE.md (제품 및 실제 소스)
3. HANDOFF/02_BUILD_AND_ENVIRONMENT.md, 03_RELEASE_AND_SECURITY.md
4. HANDOFF/04_CHATLLM_WORKFLOW.md (일반 채팅 REST 경로, 이관 브랜치와 main의 분리)
5. HANDOFF/05_VERIFICATION_AND_HISTORY.md (세 세션의 결정, 결함, 증거)
6. 심안/Siman 원본 기록: siman/CONTINUATION_2026-11-10.md, siman/HANDOFF_SIMAN_3_2026-11-12.md, siman/README.md, 모든 릴리스 노트. 과거 문서의 "현재 버전" 문장은 당시 상태이며 최신 STATE가 우선.
7. HANDOFF/BASELINE_MANIFEST.json과 tools/verify_baseline.py로 실제 파일 확인. 실제 소스를 읽고 대화 요약으로 대체하지 않는다.

이관 브랜치는 심안 전용 스냅샷. **main으로 전체 merge 금지**(다른 프로그램이 빠져 있다). 릴리스 워크플로 원본은 HANDOFF/production_workflows/에 참고용으로 보존. 실제 활성 검증 CI만 .github/workflows에 둔다. 브랜치/권한 확인 이후 별도의 사용자 승인 없이는 생산 환경을 건드리지 않는다.
