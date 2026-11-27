# 제품 목표 및 실제 아키텍처

## 1차의 핵심 제품 철학 (보존 필수)

2026-11-02 최초 요청은 ChatLLM 전체 과거 세션의 **메시지 전문 검색**. 한 세션 검색이나 열린 페이지 Ctrl+F는 사용자의 요구가 아니다. 초기 v0.1.0~0.1.1에서 방문 대화 저장/GET 방식 시험만으로 전체 검색 목표가 완성되지 않았던 기록을 확인했다. 이후 서비스 전체로 범위 확대. 사용자·AI 원문, 결과 전후 맥락, 개별 메시지 복사, 대화 전체 복사, 원본 열기와 가능하면 해당 메시지 위치까지 이동. Everything처럼 편하게 쓸 로컬 검색 유틸. 무료 공개, 프로그램명 심안(心眼) / Siman, 개발자 2bornot. 사용자가 직접 사용 가능한 실용 품질이 우선이다.

원본 이동은 대화 URL 열기와 특정 메시지 위치 이동을 구별한다. 서비스별 직접 앵커를 사용할 수 없으면 실현 가능한 위치 탐색을 연구할 별도 과제; 미구현을 완료로 표시하지 않는다. 일반 세션 + 프로젝트 세션을 함께 검색해야 한다.

## 실제 소스 지도 (v1.5.13)
| 경로 (siman/development/ 기준) | 역할 |
|---|---|
| app/manifest.json | MV3, 1.5.13, 호스트 권한, MAIN/ISOLATED 스크립트, service_worker, options/popup |
| app/core.js | providerFromUrl, sourceUrl, 메시지 정규화/파싱, ChatGPT/Claude/ChatLLM/Gemini import, 원문 검색 |
| app/page.js | 공식 웹별 수집 runner, 목록/원문, progress/bridge, 429 보호, 재시도, 계정 수집 |
| app/network.js | 로그인된 웹에서 실제 읽기용 네트워크 요청 관찰/replay, ChatLLM 목록/상세 및 timeout |
| app/deepseek-web.js | DeepSeek 공식 웹 독립 API 어댑터; ChatLLM의 DeepSeek 모델과 별개 |
| app/gemini-web.js | Gemini 웹 MaZiqc 목록 및 hNvQHb 원문 RPC, cursor, 선택된 응답 분기 |
| app/grok-web.js | grok.com 읽기 전용 REST 목록, response-node, load-responses, 인증/분기 |
| app/content.js | ISOLATED bridge, 방문 DOM 저장, 저장소 이벤트, 스크립트 수명 관리 |
| app/store.js | chrome.storage.local 기록/카탈로그/상태/진단/merge 및 이전 데이터 보존 |
| app/db.js | 기존 DB 호환 소스 (실제 사용 관계는 소스/manifest에서 확인) |
| app/search.html + search.js + style.css | 검색·문맥·복사·필터·일괄/개별 수집·재개·가져오기/내보내기·진단 |
| app/background.js | MV3 updater receipt / 기존 AI 탭 새로고침, 초안 보호 |
| app/siman-update-*.html/.js | 구버전 호환 부트스트랩 파일들. 1.5.13 설치 관리자의 외부 이동 경로는 제거됨 |
| installer/SimanSetup.cs | WinForms C# .NET Framework 설치 관리자, R11, EXE에 ZIP payload 포함 |
| tests/*.test.cjs | Node 모의 회귀 (현재 실제 CI 15종 실행) |
| app/vendor/jszip.min.js + LICENSE | ZIP 로컬 가져오기 라이브러리 |

## 저장소 및 상태 의미

실제 보관 영역은 각 Chrome/Edge 프로필의 **chrome.storage.local**. 설치 폴더는 %LOCALAPPDATA%\\2bornot\\Siman\\app. setup.log는 상위 Siman 폴더. 기록 prefix siman:v11:record: ; catalog siman:v11:catalog: ; status siman:v11:status ; migration siman:v11:migrated ; debug siman:v15:debug. key/provider:id 기준, 더 완전한 원문을 보존하는 merge. 실제 구현을 수정 전에 확인할 것. 개인정보는 외부로 보내지 않는다. JSON 백업/복원은 사용자 선택 기능이지 업데이트 필수 단계가 아니다.

**발견 / 검색가능 / 원문완결 / 부분 / 미수집 / 재시도 / 계정 목록 완결**은 다른 개념이다. 발견된 세션 전부 원문을 저장해도 계정 전체 목록을 확인한 것이 아닐 수 있다. 401/403은 로그인 필요 또는 인증 실패; 정상 빈 HTTP 200 목록과 다름.

## 여섯 서비스
- ChatLLM: 실제 관찰된 일반/프로젝트 목록과 상세 재조회, 301건 원문 완료 기록. 현재 일괄수집 시 이미 모두 complete인 관찰 목록은 재조회 생략; 새로운 목록 발견은 개별 수집. 목록 전체성/증분 탐색 후속 검증.
- Claude: 조직/프로젝트/대화 목록/원문. 503 등 408/500/502/503/504에 3회 추가 지연 재시도 (1.5.13).
- DeepSeek: https://chat.deepseek.com/ 공식 웹 목록 + 원문. active branch, same-origin 인증. 실제 40/40 수집 기록.
- Gemini: 100건 단위 cursor 목록/원문 RPC, 빈 프레임 2회 추가 재시도, 실제 208/208 수집 기록. Google Takeout My Activity Gemini Apps JSON은 부분 자료일 수 있다.
- Grok: 공식 grok.com 목록/응답 관계/원문, 401/403 login-required 상태. 로그인된 실제 계정 수집은 미검증.
- ChatGPT: 목록/원문, 요청 간격 2.7초, HTTP429 보호 대기 최소 15분, 자동 재개 시 기존 카탈로그를 재사용. 자동 재개는 심안 검색 화면과 해당 로그인 탭이 열려 있어야 한다. 탭을 닫으면 그 안에서 실행되는 수집기는 중단. 이미 확보한 원문 보존.

일괄 순서 ChatLLM → Claude → DeepSeek 웹 → Gemini 웹 → Grok 웹 → ChatGPT. 사용자 탭과 수집 전용 탭을 분리하는 아이디어는 **아직 구현/승인되지 않음**.
