# 심안 1~3차 개발 역사 및 실증 기준

## 1차: 2026-11-02부터
- ChatLLM 전체 과거 세션의 전문검색, 검색 결과의 실제 원문·문맥·복사·원본 위치 이동 목표. 처음의 열린 대화 저장 중심 v0.1.0/0.1.1은 충분하지 않았다는 기록.
- 이후 통합 AI 검색과 무료 공개 Beta, 브라우저 로컬 방식, Windows EXE + MV3, 2bornot 이름 및 심안 명칭 정립. 과거 release/installer ZIP 및 Base64 원본은 siman/ 아래 보존. v1.3.0, 1.3.1, 1.4.0, 1.5.0~1.5.5 관련 원본 파일과 release notes를 그대로 제공.
- 1차 모든 발언의 전문은 현재 확보되지 않음. v0.1.x 이후 각 초기 버전의 상세 날짜/변경점이 필요한 경우 GitHub 원본 release/commit/ZIP을 열어 재구성한다. 확인되지 않은 1차 이력을 창작하지 않는다.

## 2차: 2026-11-10 ~ 12
- 원전 siman/CONTINUATION_2026-11-10.md (당시 v1.5.5→1.5.7 기록), siman/HANDOFF_SIMAN_3_2026-11-12.md 맨 아래 '원본: 2차→3차 인수인계'.
- v1.5.3 진단: ChatLLM 301개 읽음, 96 완결/205 부분; Claude 91/91, GPT 31/624, HTTP429, Gemini/DeepSeek/Grok 0.
- v1.5.4: totalEvents vs 메시지 수의 완결 오판 수정, 429 최초 발생 보호 중단·15분 이상 대기.
- v1.5.5: 초기 bridge/의존성 지연 재시도, SPA DOM 방문 저장, VISIT_CAPTURE/SKIP/ERROR, 기존 색인 보존. 다음 진단 ChatLLM 41/301, HTTP200 후 본문 멈춤, GPT 198/643, Claude 103/103.
- v1.5.6: JSON body 완료까지 AbortController 유지, watchdog 재연결, 실제 7종 회귀 Windows 빌드 성공. 원본 ZIP에서 현재 편집용 siman/development/ 복원. 더 이상 Base64를 최신 편집 원본으로 사용하지 않음.
- v1.5.7: 원클릭 EXE 자동 설치/제자리 덮어쓰기, 관리파일/롤백/사용자 파일 보존, 고정 Beta 구축. 브라우저 확장 자체 자동 적용은 아직 미완료였음.
- v1.5.8 초기 실패: Secure Preferences 탐색, 외부 chrome-extension:// 주소 차단, Dev Mode OFF fixture에서 ENABLED→DISABLED, ACK 0/1. 이관 당시 v1.5.7 공개, v1.5.8 미배포. 3차에서 후속 해결.

## 3차: v1.5.8~1.5.13
| 버전 | 핵심 조치 | 증거/한계 |
|---|---|---|
| 1.5.8 | 기존 확장 자동 갱신, 관리자 UI reload, 새 ACK; Dev Mode ON Chrome 실검증 | Edge/OFF 미검증 |
| 1.5.9 | 공식 DeepSeek 웹 별도 일괄 수집, ChatLLM 관찰 완료 구분 | 사용자 다음 진단 DeepSeek 38/38; GPT 459/647 |
| 1.5.10 | Gemini 계정 과거 RPC + Takeout, ChatGPT 429 후 자동 재개, ChatLLM 20초/48초 timeout, 중복 주입 완화 | Node 10종, 실제 Gemini 다음 진단 97/100 |
| 1.5.11 | Grok 계정 원문 REST, 페이지·분기·개별 수집 | Node 11종, 실제 Grok 401 로그인 필요 |
| 1.5.12 | Grok 401/정상 빈 계정 분리, Gemini 100개 페이지 커서 및 빈 프레임 재시도, GPT 로컬 카탈로그 재개, Chrome 타이머/리스너 종료 | Node 14종, Gemini 다음 실제 208/208 |
| 1.5.13 | 외부 extension:// bootstrap 제거, 자기 origin 요청 파일/ACK, C# 기존 ID 확인과 archive count, stale context 추가 처리, Claude 503 재시도 | Node 15종, Windows/Chrome Dev Mode ON E2E, 공개 다운로드 확인 |

최신 원전 siman/HANDOFF_SIMAN_3_2026-11-12.md (상단 최신, 하단 과거 기록). 자세한 구현/버전별 run은 원본 문서와 release notes를 열 것.

## 실사용 최신 수치 (v1.5.12, 2026-11-13 22:47)
| 서비스 | 완료/발견 | 설명 |
|---|---|---|
| ChatLLM | 301/301 | 관찰 목록; 계정 전체 목록 완결 미확인 |
| Claude | 119/120 | 한 건 503 (v1.5.13 추가 retry, 실계정 후속 필요) |
| DeepSeek | 40/40 | 공식 사이트 수집 |
| Gemini | 208/208 | 목록 100+100+8, 실제 계정 수집 |
| Grok | 0 / 확인 불가 | HTTP401, 사용자는 대화하지 않았지만 인증 성공 빈 목록 아님 |
| ChatGPT | 183/644 | 460 pending, 1 retry, 429; 이전 532/647 대비 감소 |

ChatGPT 수치 차이는 **저장소 삭제라고 단정하지 말고** 동일 프로필, 확장 ID, 보관 키, 실제 원문 개수, 계정 및 catalog/complete 상태를 대조. 진단 수치와 전체 UI 카운터는 분모·기준 시점이 다를 수 있다. 로그에서 확인된 사실만 유지.
Chrome 관리자 오류 파일에는 content.js 소스 및 줄 번호가 반복되었고 실제 예외 문자열/stack trace는 빠져 있었다. 설치 이미지의 ERR_BLOCKED_BY_CLIENT + 0/1 ACK는 직접 확인. 1.5.13 사용자 실제 설치 성공은 아직 자료 없음. 이전 코드·새 코드의 실제 재발 구별. setup.log의 상태/ID suffix/record count 및 새 진단을 확인. 
- 실제 v1.5.13 GitHub CI 43439284243: success, HEAD 4dc301c40bfc471ac72aef7b1e827ae4f8c23ee9, Node 15종, Windows EXE/재설치, Chrome for Testing 이전 1.5.12→1.5.13 실제 동일 ID ACK. Mock storage 보존 및 설치 파일 보존과 사용자 Chrome 데이터의 실측은 구분.
- 공개 SHA 검사 43439664742: success. 2026-11-28 release API 기준 버전별/고정 자산 digest 일치. development tree 3bfc7f13f88b9060a6e20b6560c2e4bf5b7288ae가 main d1a7af4196eb724d9d3327a534f48cbdd17e255c과 build commit에서 동일.
- 기존 v1.5.13은 최신 검증 공개본이지 모든 계정/브라우저에서 완벽하게 작동했다는 뜻이 아니다.
- 원시 개인 로그 및 스크린샷은 공개 ZIP에 넣지 않았으며 과거 세션 전체 전사는 제공하지 않는다. 비식별 집계와 실제 코드·회귀·CI 및 이관 원전으로 개발에 필요한 맥락 보존.
