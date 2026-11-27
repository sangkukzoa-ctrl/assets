# 제품과 실제 구조
## 목표
FF14 전체화면 플레이 중 Alt+Tab으로 카카오톡을 오가는 공정을 없앤다. 단축키로 독립 답장 입력창을 열고, 한글 입력 후 Enter 전송, Esc 취소, 게임 화면 복귀. 우측 하단 최근 대화 및 수신 알림. 하나의 지정된 PC 카카오톡 별도 대화방 대상으로 동작. Windows 10/11 x64 대상, 무설치, 관리자 권한 UAC 승격. 기본 단축키 Numpad .; 설정에서 변경. FF14 활성 상태 제한 기본 켜짐.

## 코드 구조(실제 v1.7.13 원본 main.go 기준)
- 451 Config, 465 ChatMessage/PersistedHistory: JSON 설정 및 로컬 이력.
- 647 ensureAdministrator: ShellExecuteW runas. 승격 실패/취소 시 종료.
- 670 main: LockOSThread, Win32 창 생성, 트레이, RegisterHotKey, Shell hook, 수신 타이머, 메시지 루프. UI 스레드 Enter/Esc/Ctrl+A 처리.
- 801 loadConfig, 957 saveConfig, 967 logf: 설정 및 파일 로깅.
- 1469 openReplyFromHotkey, 1490 refreshHistoryForToggleAsync, 1506 openReply, 1541 cancelReply: 즉시 입력 우선, 토글 중 중복 갱신 atomic.Bool, 120ms 후 백그라운드 기록 갱신.
- 1567 queueOutgoingVerifyResult, 1576 finishAsyncOutgoingVerifications, 1609 verifyOutgoingAsync, 1628 sendReply: 발신 직후 원래 창으로 복귀, 별도 goroutine 확인, 결과 WM_APP_SEND_VERIFIED로 UI 전달. 대상 제목 변경 후 예전 결과 폐기.
- 1795 sendKakaoMessageDirect: 기존 카카오톡 HWND 메시지 전송 시퀀스 보존. target/입력 컨트롤 탐색 후 WM_SETTEXT 등. 이 과정 자체는 아직 동기이며 sleep 및 Win32 호출 존재.
- 1888 verifySentMessageBackground, 1898 verifySentMessageWithCopy: EVA 전용 복사로 발신 확인, 최대 4회, 실제 발신과 검증 실패는 다를 수 있음.
- 2075 restorePreviousWindow: SetForegroundWindow 단일 호출, 실제 포커스 성공 확인 없음.
- 2303 applyHotkey, 2323 activateReplyInput: 일반 Win32 포커스, 입력창 활성화 경로에서 synthetic key/AttachThreadInput/지연 재포커스 금지.
- 2657 requestIndependentReceivePoll, 2696 independentReceiveWorker, 3074 capturePassiveReceiveFingerprint: 독립 수신 감시 및 시각 fingerprint 기반 reactive body capture. 평상시 저빈도 감시(1.8s).
- 3287 suppressNativeKakaoPopup, 4524 installKakaoShowHook: 지정된 알림 억제와 수신 메시지 읽기는 별개 경로.
- 3562 selectAllAndCopyEVACommand: EVA list 명령 사이 500ms, 클립보드 변경 최대 약 800ms 확인. 단순히 전역 sleep을 줄이면 카카오톡 복사 성공률 저하 가능.
- 3605~3690 clipboard snapshot/read/write/restore: 클립보드 시퀀스 번호 고려.
- 3890 parseKakaoClipboard, 4084 replaceHistoryFromClipboard, 4111 copyChatListTextForegroundFastToggle, 4141 refreshHistoryForToggle: 토글/백그라운드 검증은 EVA-only 복사, 실패하면 캐시 유지. 함수 이름에 Foreground가 있어도 이 함수는 전면 활성화하지 않는다. kakaoCopyMu로 복사 직렬화.
- 4320 findTargetChatWindow: KakaoTalk.exe, EVA_VH_ListControl_Dblclk 소유, 제목 일치 우선. 4349 isFF14: ffxiv.exe/ffxiv_dx11.exe.
- 6035 showHistoryOverlay: 최근 대화 표시.

## 설정 호환성 및 기본값
%APPDATA%\FF14KakaoBridge: config.json, recent_messages.json, app.log. ConfigVersion 4. 기본 최근 5개(3~10), 투명도 188(100~235), 새 메시지 표시 2000ms(500~10000), 입력 위치 보정 78px. 설정 UI 및 JSON 구조는 유지한다. 실제 main()은 시작할 때 HideNativeTargetNotification=true로 덮어쓰므로 기존 사용자 비활성 설정 보존 여부는 별도 검증 대상(현재 수정 지시 아님).

## 보존 원칙
입력창을 열 때 카카오톡 복사나 디스크 로그가 첫 키 처리를 막지 않게 한다. 카카오톡 발신 확인 때문에 게임 복귀를 다시 막지 않는다. 기존에 작동하던 발신 순서는 필요 검증 없이 바꾸지 않는다. 창 숨김, 포커스 복귀, 실제 발신 확인을 서로 구분한다. 새 버전에서 편의 기능을 삭제하여 문제를 숨기지 않는다.
