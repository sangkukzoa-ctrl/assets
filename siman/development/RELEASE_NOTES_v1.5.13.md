# 심안(心眼) v1.5.13 Beta — 설치 차단 오류/실사용 수집 로그 개선
2026-11-13 KST · 개발자 2bornot

## 확인한 사용자 문제

1. Windows SimanSetup v1.5.12는 코드 파일 갱신에는 성공했으나 기존 Chrome 확장프로그램 갱신 ACK 수신이 **0/1**이었음.
2. 설치 도중 Chrome에서 `chrome-extension://ecpdcpepojjaennbklooldfegcicemdco/...` 화면을 차단함: **ERR_BLOCKED_BY_CLIENT**. 기존 설치기는 `chrome-extension://<확장ID>/siman-update-1512.html?...`을 Chrome 외부 실행 파라미터 및 주소창으로 연 뒤 설치 ACK를 기대했는데, 실제 사용자 프로필에서 이 접근이 차단됨.
3. 제출한 `붙여넣은 텍스트(1).txt`에는 Chrome 확장 오류 표시에서 복사한 `content.js` 소스와 줄 번호만 약 400줄 포함됐으며, 실제 예외 메시지/stack trace는 없음. 새로고침 뒤 수집 중 `chrome.runtime` 컨텍스트 무효화로 비동기 저장 이벤트가 남는 경로를 개선.
4. `Siman_v1.5.12_Debug_20261113_224734.txt`: Gemini **208/208**, DeepSeek **40/40**, ChatLLM **301/301** 관찰된 원문 완료. Claude **119/120**, 나머지 1건 HTTP **503**. Grok HTTP **401** 로그인 필요. ChatGPT 발견 **644**, 해당 브라우저 확장 저장소의 원문 **183**건 완료·**460 pending + 1 retry**로 확인. **기존 v1.5.11 로그의 GPT 532건 완료에서 183건으로 감소**: Chrome 설치/프로필·확장 ID 또는 저장소 연속성 후속 확인 필요; 사용자의 이전 기록이 삭제됐다고 확정하지 말 것.

## v1.5.13 핵심 수정

- **Windows installer R11:** 외부 `chrome-extension://` 부트스트랩 페이지 탐색 제거. 기존 설치 폴더 안에 **128비트 일회용 토큰 + Chrome 확장 ID + 버전 + 임의 localhost 포트 + 발급시간**을 가진 `siman-updater-request.json`을 설치 도중 작성. 같은 프로필의 `chrome://extensions/` 내부 관리자 Reload 동작으로 새 확장 백그라운드를 시작.
- **Background worker:** 자신이 설치된 **동일 확장 origin**의 `siman-updater-request.json`만 읽고, 버전·확장 ID·토큰·시간을 검사. 유효하면 기존 저장소를 변경하지 않고 수집용 AI 탭 중 작성 중인 메시지가 없는 탭만 새로고침. 새 백그라운드가 기존 localhost ACK로 설치 관리자에 **확장 ID 및 사용자 원문 기록 개수(숫자만)**를 반환. 크롬 외부에서 extension page를 열 필요 없음. 온디스크 지시파일은 설치 단계 후 제거.
- **확장 ID 보호:** Chrome/Edge의 Preferences/Secure Preferences를 *읽기만* 하여 설치 경로에 연결된 정확한 기존 확장 ID로 검증. 원래 활성/비활성 상태 및 disable reasons를 개인 메모와 계정 데이터 없이 `setup.log`에 남겨, 갱신 불가능 상태를 가려냄. 설치 폴더 경로와 `chrome.storage.local`은 건드리지 않음.
- **Chrome 오류:** content.js 브리지에서 구 컨텍스트의 `Extension context invalidated` 비동기 예외를 안전하게 종료, 타이머/DOM 관찰자/리스너 해제.
- **Claude HTTP 503:** 408/500/502/503/504 임시 서버 응답에서 활성 대화만 최대 3회 지연 재시도(총 최대 4회), 다른 대화와 저장 기록은 보존.
- **보존:** Gemini 208건 페이지네이션, DeepSeek 40건, ChatLLM 301건, ChatGPT의 429 후 로컬 목록 재사용, Grok 401 로그인 상태 구분 등 v1.5.12 기능 변경 최소화.
- **검증:** 기존 Node 테스트 + 직접 백그라운드 ACK 테스트 + Windows EXE 실빌드 및 크롬 이전 버전에서의 실제 동일 ID 갱신 E2E; 배포 완료 여부는 GitHub CI 결과를 따른다.

## 고정 Beta
https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-beta

## 정확한 검증 범위
- Windows CI는 테스트용 Chrome 개발자 모드 ON / 압축해제 확장으로 검증하며, 사용자의 실제 Chrome 비활성화 상태 및 이전 확장 저장소 내용은 원격으로 열람하지 않음.
- Gemini 208건/208건은 첨부한 실제 사용자 진단로그로 확인되었음.
- 사용자 현지에서의 Chrome 관리자 오류 재발 및 ChatGPT 이전 완료 건수 회복은 새 버전 로그로 확인 대상.
