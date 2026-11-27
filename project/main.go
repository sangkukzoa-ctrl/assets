package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
	"unicode/utf16"
	"unsafe"
)

const (
	WM_DESTROY       = 0x0002
	WM_CLOSE         = 0x0010
	WM_COMMAND       = 0x0111
	WM_TIMER         = 0x0113
	WM_HOTKEY        = 0x0312
	WM_KEYDOWN       = 0x0100
	WM_CHAR          = 0x0102
	WM_SETTEXT       = 0x000C
	EM_SETSEL        = 0x00B1
	WM_PAINT         = 0x000F
	WM_ERASEBKGND    = 0x0014
	WM_SETFONT       = 0x0030
	WM_LBUTTONDBLCLK = 0x0203
	WM_RBUTTONUP     = 0x0205
	WM_CONTEXTMENU   = 0x007B
	WM_PRINTCLIENT   = 0x0318
	WM_APP           = 0x8000

	WS_OVERLAPPED  = 0x00000000
	WS_CAPTION     = 0x00C00000
	WS_SYSMENU     = 0x00080000
	WS_MINIMIZEBOX = 0x00020000
	WS_CHILD       = 0x40000000
	WS_VISIBLE     = 0x10000000
	WS_BORDER      = 0x00800000
	WS_TABSTOP     = 0x00010000
	WS_POPUP       = 0x80000000

	WS_EX_TOPMOST     = 0x00000008
	WS_EX_TOOLWINDOW  = 0x00000080
	WS_EX_NOACTIVATE  = 0x08000000
	WS_EX_TRANSPARENT = 0x00000020
	WS_EX_LAYERED     = 0x00080000

	ES_MULTILINE    = 0x0004
	ES_AUTOHSCROLL  = 0x0080
	ES_READONLY     = 0x0800
	GWL_STYLE       = -16
	VK_BACK         = 0x08
	BS_PUSHBUTTON   = 0x00000000
	BS_AUTOCHECKBOX = 0x00000003

	SW_HIDE       = 0
	SW_SHOWNORMAL = 1
	SW_SHOW       = 5
	SW_RESTORE    = 9
	SW_MINIMIZE   = 6

	BST_CHECKED   = 1
	BST_UNCHECKED = 0
	BM_GETCHECK   = 0x00F0
	BM_SETCHECK   = 0x00F1

	COLOR_WINDOW     = 5
	DEFAULT_GUI_FONT = 17

	SWP_NOSIZE     = 0x0001
	SWP_NOMOVE     = 0x0002
	SWP_NOACTIVATE = 0x0010
	HWND_TOPMOST   = ^uintptr(0) // -1

	LWA_ALPHA = 0x00000002

	MOD_ALT      = 0x0001
	MOD_CONTROL  = 0x0002
	MOD_SHIFT    = 0x0004
	MOD_WIN      = 0x0008
	MOD_NOREPEAT = 0x4000

	VK_RETURN  = 0x0D
	VK_ESCAPE  = 0x1B
	VK_SHIFT   = 0x10
	VK_CONTROL = 0x11
	VK_MENU    = 0x12
	VK_LWIN    = 0x5B
	VK_RWIN    = 0x5C
	VK_A       = 0x41
	VK_C       = 0x43

	WM_KEYUP       = 0x0101
	WM_LBUTTONDOWN = 0x0201
	WM_LBUTTONUP   = 0x0202
	WA_ACTIVE      = 1

	CF_UNICODETEXT = 13
	GMEM_MOVEABLE  = 0x0002

	HSHELL_REDRAW = 6
	HSHELL_FLASH  = 0x8006

	FLASHW_STOP = 0

	PW_CLIENTONLY        = 0x00000001
	PW_RENDERFULLCONTENT = 0x00000002
	PRF_CLIENT           = 0x00000004
	PRF_ERASEBKGND       = 0x00000008
	PRF_CHILDREN         = 0x00000010
	BI_RGB               = 0
	DIB_RGB_COLORS       = 0

	TH32CS_SNAPPROCESS   = 0x00000002
	INVALID_HANDLE_VALUE = ^uintptr(0)

	INPUT_KEYBOARD    = 1
	KEYEVENTF_KEYUP   = 0x0002
	KEYEVENTF_UNICODE = 0x0004

	MOUSEEVENTF_LEFTDOWN = 0x0002
	MOUSEEVENTF_LEFTUP   = 0x0004

	ID_HOTKEY             = 1
	TIMER_POLL            = 11
	TIMER_TOAST_HIDE      = 12
	TIMER_CAPTURE         = 13
	TIMER_HISTORY_HIDE    = 14
	TIMER_HISTORY_CAPTURE = 16
	TIMER_INITIAL_SYNC    = 17
	TIMER_INDEPENDENT_RX  = 18

	WM_APP_TRAY            = WM_APP + 1
	WM_APP_KAKAO_SHOW      = WM_APP + 2
	WM_APP_HISTORY_UPDATED = WM_APP + 3
	WM_APP_INCOMING_HINT   = WM_APP + 4
	WM_APP_SEND_VERIFIED   = WM_APP + 5

	ID_SAVE          = 1001
	ID_CAPTURE       = 1002
	ID_HIDE_SETTINGS = 1003
	ID_HOTKEY_EDIT   = 2001
	ID_TARGET_EDIT   = 2002
	ID_ONLY_FF14     = 3001
	ID_NOTIFY        = 3002 // legacy config/UI id, kept for compatibility
	ID_OFFSET_EDIT   = 3003
	ID_HIDE_NATIVE   = 3004
	ID_HISTORY_COUNT = 3005
	ID_OVERLAY_ALPHA = 3006
	ID_INCOMING_MS   = 3007

	ID_TRAY_REPLY    = 4001
	ID_TRAY_SETTINGS = 4002
	ID_TRAY_EXIT     = 4003

	NIF_MESSAGE = 0x00000001
	NIF_ICON    = 0x00000002
	NIF_TIP     = 0x00000004
	NIM_ADD     = 0x00000000
	NIM_DELETE  = 0x00000002

	MF_STRING       = 0x00000000
	TPM_RIGHTBUTTON = 0x0002
	TPM_RETURNCMD   = 0x0100

	SPI_GETWORKAREA = 0x0030

	DT_LEFT         = 0x00000000
	DT_RIGHT        = 0x00000002
	DT_WORDBREAK    = 0x00000010
	DT_SINGLELINE   = 0x00000020
	DT_END_ELLIPSIS = 0x00008000
	DT_VCENTER      = 0x00000004
	DT_NOPREFIX     = 0x00000800
	TRANSPARENT     = 1

	EVENT_SYSTEM_ALERT             = 0x0002
	EVENT_OBJECT_CREATE            = 0x8000
	EVENT_OBJECT_SHOW              = 0x8002
	EVENT_OBJECT_STATECHANGE       = 0x800A
	EVENT_OBJECT_NAMECHANGE        = 0x800C
	EVENT_OBJECT_DESCRIPTIONCHANGE = 0x800D
	EVENT_OBJECT_VALUECHANGE       = 0x800E
	EVENT_OBJECT_LIVEREGIONCHANGED = 0x8019
	WINEVENT_OUTOFCONTEXT          = 0x0000
	WINEVENT_SKIPOWNPROCESS        = 0x0002
	GA_ROOT                        = 2

	GWLP_HINSTANCE = -6
)

var (
	user32   = syscall.NewLazyDLL("user32.dll")
	kernel32 = syscall.NewLazyDLL("kernel32.dll")
	shell32  = syscall.NewLazyDLL("shell32.dll")
	gdi32    = syscall.NewLazyDLL("gdi32.dll")
	combase  = syscall.NewLazyDLL("combase.dll")
	oleacc   = syscall.NewLazyDLL("oleacc.dll")
	oleaut32 = syscall.NewLazyDLL("oleaut32.dll")
	ole32    = syscall.NewLazyDLL("ole32.dll")

	pRegisterClassExW           = user32.NewProc("RegisterClassExW")
	pCreateWindowExW            = user32.NewProc("CreateWindowExW")
	pDefWindowProcW             = user32.NewProc("DefWindowProcW")
	pShowWindow                 = user32.NewProc("ShowWindow")
	pUpdateWindow               = user32.NewProc("UpdateWindow")
	pGetMessageW                = user32.NewProc("GetMessageW")
	pTranslateMessage           = user32.NewProc("TranslateMessage")
	pDispatchMessageW           = user32.NewProc("DispatchMessageW")
	pPostQuitMessage            = user32.NewProc("PostQuitMessage")
	pPostMessageW               = user32.NewProc("PostMessageW")
	pSendMessageW               = user32.NewProc("SendMessageW")
	pSetWindowTextW             = user32.NewProc("SetWindowTextW")
	pGetWindowTextW             = user32.NewProc("GetWindowTextW")
	pGetWindowTextLengthW       = user32.NewProc("GetWindowTextLengthW")
	pGetClassNameW              = user32.NewProc("GetClassNameW")
	pGetWindowLongW             = user32.NewProc("GetWindowLongW")
	pMapVirtualKeyW             = user32.NewProc("MapVirtualKeyW")
	pGetForegroundWindow        = user32.NewProc("GetForegroundWindow")
	pSetForegroundWindow        = user32.NewProc("SetForegroundWindow")
	pSetActiveWindow            = user32.NewProc("SetActiveWindow")
	pBringWindowToTop           = user32.NewProc("BringWindowToTop")
	pSetFocus                   = user32.NewProc("SetFocus")
	pGetDlgItem                 = user32.NewProc("GetDlgItem")
	pGetWindowRect              = user32.NewProc("GetWindowRect")
	pGetClientRect              = user32.NewProc("GetClientRect")
	pClientToScreen             = user32.NewProc("ClientToScreen")
	pGetCursorPos               = user32.NewProc("GetCursorPos")
	pSetCursorPos               = user32.NewProc("SetCursorPos")
	pMouseEvent                 = user32.NewProc("mouse_event")
	pEnumWindows                = user32.NewProc("EnumWindows")
	pEnumChildWindows           = user32.NewProc("EnumChildWindows")
	pIsWindowVisible            = user32.NewProc("IsWindowVisible")
	pIsIconic                   = user32.NewProc("IsIconic")
	pGetWindowThreadProcessId   = user32.NewProc("GetWindowThreadProcessId")
	pRegisterHotKey             = user32.NewProc("RegisterHotKey")
	pUnregisterHotKey           = user32.NewProc("UnregisterHotKey")
	pSetTimer                   = user32.NewProc("SetTimer")
	pKillTimer                  = user32.NewProc("KillTimer")
	pMessageBoxW                = user32.NewProc("MessageBoxW")
	pSetWindowPos               = user32.NewProc("SetWindowPos")
	pSetLayeredWindowAttributes = user32.NewProc("SetLayeredWindowAttributes")
	pInvalidateRect             = user32.NewProc("InvalidateRect")
	pBeginPaint                 = user32.NewProc("BeginPaint")
	pEndPaint                   = user32.NewProc("EndPaint")
	pFillRect                   = user32.NewProc("FillRect")
	pDrawTextW                  = user32.NewProc("DrawTextW")
	pSetBkMode                  = gdi32.NewProc("SetBkMode")
	pSetTextColor               = gdi32.NewProc("SetTextColor")
	pSystemParametersInfoW      = user32.NewProc("SystemParametersInfoW")
	pLoadCursorW                = user32.NewProc("LoadCursorW")
	pLoadIconW                  = user32.NewProc("LoadIconW")
	pCreatePopupMenu            = user32.NewProc("CreatePopupMenu")
	pAppendMenuW                = user32.NewProc("AppendMenuW")
	pTrackPopupMenu             = user32.NewProc("TrackPopupMenu")
	pDestroyMenu                = user32.NewProc("DestroyMenu")
	pSetProcessDPIAware         = user32.NewProc("SetProcessDPIAware")
	pRegisterWindowMessageW     = user32.NewProc("RegisterWindowMessageW")
	pRegisterShellHookWindow    = user32.NewProc("RegisterShellHookWindow")
	pDeregisterShellHookWindow  = user32.NewProc("DeregisterShellHookWindow")
	pAttachThreadInput          = user32.NewProc("AttachThreadInput")
	pGetKeyboardState           = user32.NewProc("GetKeyboardState")
	pGetKeyState                = user32.NewProc("GetKeyState")
	pSetKeyboardState           = user32.NewProc("SetKeyboardState")
	pOpenClipboard              = user32.NewProc("OpenClipboard")
	pCloseClipboard             = user32.NewProc("CloseClipboard")
	pGetClipboardData           = user32.NewProc("GetClipboardData")
	pSetClipboardData           = user32.NewProc("SetClipboardData")
	pEmptyClipboard             = user32.NewProc("EmptyClipboard")
	pIsClipboardFormatAvailable = user32.NewProc("IsClipboardFormatAvailable")
	pGetClipboardSequenceNumber = user32.NewProc("GetClipboardSequenceNumber")
	pCountClipboardFormats      = user32.NewProc("CountClipboardFormats")
	pSetWinEventHook            = user32.NewProc("SetWinEventHook")
	pUnhookWinEvent             = user32.NewProc("UnhookWinEvent")
	pGetAncestor                = user32.NewProc("GetAncestor")
	pGetGUIThreadInfo           = user32.NewProc("GetGUIThreadInfo")
	pFlashWindowEx              = user32.NewProc("FlashWindowEx")
	pPrintWindow                = user32.NewProc("PrintWindow")

	pAccessibleObjectFromEvent  = oleacc.NewProc("AccessibleObjectFromEvent")
	pAccessibleObjectFromWindow = oleacc.NewProc("AccessibleObjectFromWindow")
	pSysStringLen               = oleaut32.NewProc("SysStringLen")
	pSysFreeString              = oleaut32.NewProc("SysFreeString")
	pCoInitializeEx             = ole32.NewProc("CoInitializeEx")
	pCoUninitialize             = ole32.NewProc("CoUninitialize")

	pGetModuleHandleW         = kernel32.NewProc("GetModuleHandleW")
	pGetCurrentThreadId       = kernel32.NewProc("GetCurrentThreadId")
	pGlobalAlloc              = kernel32.NewProc("GlobalAlloc")
	pGlobalLock               = kernel32.NewProc("GlobalLock")
	pGlobalUnlock             = kernel32.NewProc("GlobalUnlock")
	pGlobalSize               = kernel32.NewProc("GlobalSize")
	pCreateToolhelp32Snapshot = kernel32.NewProc("CreateToolhelp32Snapshot")
	pProcess32FirstW          = kernel32.NewProc("Process32FirstW")
	pProcess32NextW           = kernel32.NewProc("Process32NextW")
	pCloseHandle              = kernel32.NewProc("CloseHandle")

	pShellNotifyIconW = shell32.NewProc("Shell_NotifyIconW")
	pShellExecuteW    = shell32.NewProc("ShellExecuteW")
	pIsUserAnAdmin    = shell32.NewProc("IsUserAnAdmin")

	pRoInitialize              = combase.NewProc("RoInitialize")
	pRoUninitialize            = combase.NewProc("RoUninitialize")
	pRoGetActivationFactory    = combase.NewProc("RoGetActivationFactory")
	pWindowsCreateString       = combase.NewProc("WindowsCreateString")
	pWindowsDeleteString       = combase.NewProc("WindowsDeleteString")
	pWindowsGetStringRawBuffer = combase.NewProc("WindowsGetStringRawBuffer")

	pGetStockObject     = gdi32.NewProc("GetStockObject")
	pCreateSolidBrush   = gdi32.NewProc("CreateSolidBrush")
	pCreateFontW        = gdi32.NewProc("CreateFontW")
	pSelectObject       = gdi32.NewProc("SelectObject")
	pDeleteObject       = gdi32.NewProc("DeleteObject")
	pCreateCompatibleDC = gdi32.NewProc("CreateCompatibleDC")
	pCreateDIBSection   = gdi32.NewProc("CreateDIBSection")
	pDeleteDC           = gdi32.NewProc("DeleteDC")
)

type POINT struct{ X, Y int32 }
type RECT struct{ Left, Top, Right, Bottom int32 }

type BITMAPINFOHEADER struct {
	BiSize          uint32
	BiWidth         int32
	BiHeight        int32
	BiPlanes        uint16
	BiBitCount      uint16
	BiCompression   uint32
	BiSizeImage     uint32
	BiXPelsPerMeter int32
	BiYPelsPerMeter int32
	BiClrUsed       uint32
	BiClrImportant  uint32
}
type RGBQUAD struct{ Blue, Green, Red, Reserved byte }
type BITMAPINFO struct {
	BmiHeader BITMAPINFOHEADER
	BmiColors [1]RGBQUAD
}

type passiveVisualFingerprint struct {
	Cells  [140]uint16 // 14 x 10 coarse color blocks
	Width  int32
	Height int32
	Source uint8 // 1=target top-level client, 2=message-list fallback
	Valid  bool
}

type FLASHWINFO struct {
	CbSize    uint32
	Hwnd      uintptr
	DwFlags   uint32
	UCount    uint32
	DwTimeout uint32
}
type GUID struct {
	Data1 uint32
	Data2 uint16
	Data3 uint16
	Data4 [8]byte
}

// VARIANT is 24 bytes on Windows/amd64 (8-byte header + 16-byte union).
// FF14KakaoBridge is shipped as amd64, and MSAA passes VARIANT arguments by
// reference under the x64 ABI. Only VT_I4 / the first 64-bit union slot are
// needed here.
type MSAAVARIANT struct {
	Vt                   uint16
	Reserved1, Reserved2 uint16
	Reserved3            uint16
	Val                  int64
	Val2                 int64
}
type GUITHREADINFO struct {
	CbSize        uint32
	Flags         uint32
	HwndActive    uintptr
	HwndFocus     uintptr
	HwndCapture   uintptr
	HwndMenuOwner uintptr
	HwndMoveSize  uintptr
	HwndCaret     uintptr
	RcCaret       RECT
}
type MSG struct {
	Hwnd     uintptr
	Message  uint32
	_        uint32
	WParam   uintptr
	LParam   uintptr
	Time     uint32
	Pt       POINT
	LPrivate uint32
}
type WNDCLASSEXW struct {
	CbSize        uint32
	Style         uint32
	LpfnWndProc   uintptr
	CbClsExtra    int32
	CbWndExtra    int32
	HInstance     uintptr
	HIcon         uintptr
	HCursor       uintptr
	HbrBackground uintptr
	LpszMenuName  *uint16
	LpszClassName *uint16
	HIconSm       uintptr
}
type PAINTSTRUCT struct {
	Hdc         uintptr
	FErase      int32
	RcPaint     RECT
	FRestore    int32
	FIncUpdate  int32
	RgbReserved [32]byte
}
type NOTIFYICONDATAW struct {
	CbSize           uint32
	HWnd             uintptr
	UID              uint32
	UFlags           uint32
	UCallbackMessage uint32
	HIcon            uintptr
	SzTip            [128]uint16
	DwState          uint32
	DwStateMask      uint32
	SzInfo           [256]uint16
	UVersion         uint32
	SzInfoTitle      [64]uint16
	DwInfoFlags      uint32
	GuidItem         [16]byte
	HBalloonIcon     uintptr
}

type timedMSAAText struct {
	Text string
	At   time.Time
}

type Config struct {
	ConfigVersion                int    `json:"config_version"`
	Hotkey                       string `json:"hotkey"`
	TargetChatTitle              string `json:"target_chat_title"`
	OnlyWhenFF14                 bool   `json:"only_when_ff14"`
	CompactNotifications         bool   `json:"compact_notifications"` // legacy
	NotifyDurationMS             int    `json:"notify_duration_ms"`
	InputYOffset                 int    `json:"input_y_offset"`
	HideNativeTargetNotification bool   `json:"hide_native_target_notification"`
	RecentMessageCount           int    `json:"recent_message_count"`
	OverlayAlpha                 int    `json:"overlay_alpha"`
	IncomingOverlayDurationMS    int    `json:"incoming_overlay_duration_ms"`
}

type ChatMessage struct {
	Sender string    `json:"sender,omitempty"`
	Body   string    `json:"body"`
	At     time.Time `json:"at"`
	Mine   bool      `json:"mine,omitempty"`
}

type PersistedHistory struct {
	TargetTitle string        `json:"target_title"`
	Messages    []ChatMessage `json:"messages"`
}

var (
	cfgMu sync.Mutex
	cfg   = Config{
		ConfigVersion:                4,
		Hotkey:                       "Numpad .",
		OnlyWhenFF14:                 true,
		CompactNotifications:         false,
		NotifyDurationMS:             3200,
		InputYOffset:                 78,
		HideNativeTargetNotification: true,
		RecentMessageCount:           5,
		OverlayAlpha:                 188,
		IncomingOverlayDurationMS:    2000,
	}
	configPath  string
	logPath     string
	historyPath string

	hInstance      uintptr
	controllerHwnd uintptr
	settingsHwnd   uintptr
	replyHwnd      uintptr
	replyEdit      uintptr
	replyLabel     uintptr
	toastHwnd      uintptr
	historyHwnd    uintptr

	previousHwnd   uintptr
	replyVisible   bool
	registeredMods uint32
	registeredVK   uint32

	toastTitle      = "카카오톡"
	toastBody       = ""
	toastBrush      uintptr
	historyBrush    uintptr
	historyMineFont uintptr

	historyMu       sync.Mutex
	recentMessages  []ChatMessage
	lastCapturedSig string
	lastCapturedAt  time.Time

	enumMu           sync.Mutex
	enumWindowsAccum []uintptr
	enumChildAccum   []string
	popupSignatures  = map[uintptr]string{}

	processNameCacheMu    sync.Mutex
	processNameCache      = map[uint32]string{}
	processNameCacheUntil time.Time
	monitorPrimed         bool
	popupInspectMu        sync.Mutex
	popupInspecting       = map[uintptr]bool{}

	msaaEventMu    sync.Mutex
	msaaEventTexts = map[uintptr][]timedMSAAText{}

	taskbarCreatedMsg  uint32
	shellHookMsg       uint32
	trayRegistered     bool
	winEventHook       uintptr
	winEventA11yHook   uintptr
	winEventAlertHook  uintptr
	historyAutoVisible bool
	replyFocusRetries  int
	lastShellCaptureAt time.Time
	suppressShellUntil time.Time

	incomingProbeMu              sync.Mutex
	incomingProbeGeneration      uint64
	incomingProbeActive          bool
	lastPopupCapturedAt          time.Time
	lastFallbackHintAt           time.Time
	lastReliableHistoryReceiveAt time.Time

	chatA11yMu     sync.Mutex
	chatA11ySeen   = map[string]bool{}
	chatA11yPrimed bool

	// v1.4.0: read the Windows notification platform directly. This path never
	// activates KakaoTalk and never touches keyboard/IME state. It is independent
	// from Kakao's detached chat-window accessibility quirks.
	systemNotificationAccess bool
	winRTMainInitialized     bool

	enumClassMu     sync.Mutex
	enumClassNeedle string
	enumClassResult uintptr

	captureMu              sync.Mutex
	captureRunning         bool
	capturePending         bool
	capturePendingAnnounce bool

	// v1.6.0: the periodic watcher is truly passive. It fingerprints the rendered
	// Kakao message-list surface without activating the room, sending keys, or
	// touching the clipboard. A substantial visual change itself becomes the
	// notification; transcript text is loaded only when the user presses the reply
	// hotkey. This prevents the old 900 ms Ctrl+A/C loop from silently marking
	// every incoming message read.
	independentRxMu        sync.Mutex
	independentRxRunning   bool
	passiveRxPrimed        bool
	passiveRxNeedsReprime  bool
	passiveRxLast          passiveVisualFingerprint
	passiveRxTarget        uintptr
	passiveRxList          uintptr
	passiveRxSuppressUntil time.Time
	passiveRxPending       bool
	passiveRxPendingSince  time.Time
	lastIndependentFailLog time.Time
	lastPassiveVisualLog   time.Time
	lastPassiveAlertAt     time.Time

	// v1.7.4: the low-rate watcher still detects arrivals without keyboard/focus
	// activity. Only after a real arrival signal do we make one short-lived body
	// resolution attempt. The first path uses Kakao's EVA list copy command with
	// no activation/thread-input sharing; the proven virtual-active copy is only
	// a fallback. This removes the old continuous Ctrl+A/C polling while restoring
	// actual message text in the overlay.
	passiveBodyMu             sync.Mutex
	passiveBodyResolving      bool
	passiveBodyPending        bool
	passiveBodyPendingTarget  uintptr
	passiveBodyPendingTrigger string
	passiveBodyPendingSince   time.Time
	lastPassiveBodySig        string
	lastPassiveBodyAt         time.Time

	// v1.7.2: a Kakao popup/taskbar transition can momentarily move the Windows
	// foreground away from FF14. Do not let that tiny race disable native
	// suppression or force the passive watcher to swallow the arriving frame as
	// a new baseline. Keep a short, thread-safe memory of the last real FF14
	// foreground state.
	gamingContextMu      sync.Mutex
	lastFF14ForegroundAt time.Time

	nativeSuppressMu  sync.Mutex
	nativeSuppressing = map[uintptr]bool{}
	kakaoCopyMu       sync.Mutex

	controllerClass = "FF14KakaoBridgeController"
	settingsClass   = "FF14KakaoBridgeSettings"
	replyClass      = "FF14KakaoBridgeReply"
	toastClass      = "FF14KakaoBridgeToast"
	historyClass    = "FF14KakaoBridgeHistory"
)

func u16(s string) *uint16 {
	p, _ := syscall.UTF16PtrFromString(s)
	return p
}

func copyUTF16(dst []uint16, s string) {
	enc := utf16.Encode([]rune(s))
	if len(enc) >= len(dst) {
		enc = enc[:len(dst)-1]
	}
	copy(dst, enc)
	dst[len(enc)] = 0
}

func loword(v uintptr) uint16 { return uint16(v & 0xffff) }

// ensureAdministrator makes every normal launch elevate through the Windows
// UAC path before the Bridge creates hooks, hotkeys, or UI. This is equivalent
// in day-to-day use to "always run as administrator" without depending on a
// shortcut property. If elevation is declined or cannot be started, the
// unelevated copy exits instead of continuing with mixed integrity levels.
func ensureAdministrator() bool {
	if r, _, _ := pIsUserAnAdmin.Call(); r != 0 {
		return true
	}
	exe, err := os.Executable()
	if err != nil || strings.TrimSpace(exe) == "" {
		pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16("관리자 권한으로 다시 실행할 프로그램 경로를 찾지 못했습니다."))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge"))), 0x10)
		return false
	}
	cwd, _ := os.Getwd()
	verb := u16("runas")
	file := u16(exe)
	var dirPtr uintptr
	if strings.TrimSpace(cwd) != "" {
		dirPtr = uintptr(unsafe.Pointer(u16(cwd)))
	}
	r, _, _ := pShellExecuteW.Call(0, uintptr(unsafe.Pointer(verb)), uintptr(unsafe.Pointer(file)), 0, dirPtr, SW_SHOWNORMAL)
	if r <= 32 {
		pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16("관리자 권한 승격이 취소되었거나 실패했습니다. 프로그램을 종료합니다."))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge"))), 0x30)
	}
	return false
}

func main() {
	runtime.LockOSThread()
	if !ensureAdministrator() {
		return
	}
	pSetProcessDPIAware.Call()
	initPaths()
	defer func() {
		if r := recover(); r != nil {
			logf("PANIC: %v", r)
			pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16(fmt.Sprintf("프로그램 시작 중 오류가 발생했습니다.\n\n%v\n\n로그: %s", r, logPath)))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge 오류"))), 0x10)
		}
	}()
	loadConfig()
	// v1.7.0 migration: the requested operating mode is Bridge-owned notification.
	// Start with Kakao native notification suppression enabled even if an older
	// config had it disabled; the user can still turn it off explicitly later.
	cfg.HideNativeTargetNotification = true
	loadHistory()
	removeIncomingFallbackHints()
	logf("starting v1.7.13-fast-return; hotkey=%q target=%q passiveVisualReceive=hybrid-target-window+safe-reactive-body safeToggle=eva-only replyInput=plain-window+async-history+no-keylog send=fast-return+background-eva-verify admin=required", cfg.Hotkey, cfg.TargetChatTitle)

	h, _, _ := pGetModuleHandleW.Call(0)
	hInstance = h
	if hInstance == 0 {
		logf("GetModuleHandleW failed")
		pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16("프로그램 모듈 핸들을 가져오지 못했습니다."))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge 오류"))), 0x10)
		return
	}

	registerClasses()
	createController()
	if controllerHwnd == 0 {
		pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16("백그라운드 컨트롤러 창 생성에 실패했습니다.\n로그를 확인해 주세요."))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge 오류"))), 0x10)
		return
	}
	createSettingsWindow()
	createReplyWindow()
	createToastWindow()
	createHistoryWindow()
	if settingsHwnd == 0 || replyHwnd == 0 || toastHwnd == 0 || historyHwnd == 0 {
		logf("critical window creation failed settings=%x reply=%x toast=%x history=%x", settingsHwnd, replyHwnd, toastHwnd, historyHwnd)
		pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16("프로그램 UI 생성에 실패했습니다.\n로그를 확인해 주세요."))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge 오류"))), 0x10)
		return
	}

	msgID, _, _ := pRegisterWindowMessageW.Call(uintptr(unsafe.Pointer(u16("TaskbarCreated"))))
	taskbarCreatedMsg = uint32(msgID)
	shellID, _, _ := pRegisterWindowMessageW.Call(uintptr(unsafe.Pointer(u16("SHELLHOOK"))))
	shellHookMsg = uint32(shellID)
	if shellHookMsg != 0 {
		if r, _, e := pRegisterShellHookWindow.Call(controllerHwnd); r == 0 {
			logf("RegisterShellHookWindow failed: %v", e)
		} else {
			logf("shell hook registered msg=%x", shellHookMsg)
		}
	}
	if !addTrayIconWithRetry() {
		logf("tray registration failed after retries")
		pMessageBoxW.Call(0, uintptr(unsafe.Pointer(u16("작업표시줄 알림 영역 아이콘 등록에 실패했습니다.\n프로그램은 종료하지 않고 설정창을 열어 둡니다.\n\n로그: "+logPath))), uintptr(unsafe.Pointer(u16("FF14 Kakao Bridge"))), 0x30)
		showSettings()
	}

	if err := applyHotkey(cfg.Hotkey); err != nil {
		logf("hotkey registration failed: %v", err)
		messageBox("단축키 등록 실패", fmt.Sprintf("%s 단축키를 등록할 수 없습니다.\n설정에서 다른 키로 바꿔 주세요.", cfg.Hotkey))
		showSettings()
	} else if strings.TrimSpace(cfg.TargetChatTitle) == "" {
		showSettings()
	}

	// v1.7.0: native Kakao popup/FLASH suppression and receive detection are
	// separate. SHOW/FLASH is blocked event-by-event; it is never a message source.
	// The receive source is a low-rate passive visual fingerprint of the detached
	// room. No Ctrl+A/C is sent during ordinary polling.
	installKakaoShowHook()
	pSetTimer.Call(controllerHwnd, TIMER_POLL, 350, 0) // low-cost native-popup/flash suppression fallback
	if strings.TrimSpace(cfg.TargetChatTitle) != "" {
		pSetTimer.Call(controllerHwnd, TIMER_INITIAL_SYNC, 450, 0)
		pSetTimer.Call(controllerHwnd, TIMER_INDEPENDENT_RX, 1800, 0)
	}

	var msg MSG
	for {
		r, _, _ := pGetMessageW.Call(uintptr(unsafe.Pointer(&msg)), 0, 0, 0)
		if int32(r) <= 0 {
			break
		}

		if replyVisible && msg.Hwnd == replyEdit && msg.Message == WM_KEYDOWN {
			// No synchronous disk I/O in the real keystroke path.
			if msg.WParam == VK_RETURN {
				sendReply()
				continue
			}
			if msg.WParam == VK_ESCAPE {
				cancelReply()
				continue
			}
			// Standard Win32 EDIT controls do not consistently implement Ctrl+A.
			// Handle it only for the Bridge reply box; no Kakao/receive behavior changes.
			if msg.WParam == VK_A {
				ctrl, _, _ := pGetKeyState.Call(VK_CONTROL)
				if int16(ctrl&0xFFFF) < 0 {
					pSendMessageW.Call(replyEdit, EM_SETSEL, 0, ^uintptr(0))
					continue
				}
			}
		}
		pTranslateMessage.Call(uintptr(unsafe.Pointer(&msg)))
		pDispatchMessageW.Call(uintptr(unsafe.Pointer(&msg)))
	}

	cleanup()
}

func initPaths() {
	base, err := os.UserConfigDir()
	if err != nil || base == "" {
		base = os.Getenv("APPDATA")
	}
	if base == "" {
		base = "."
	}
	dir := filepath.Join(base, "FF14KakaoBridge")
	_ = os.MkdirAll(dir, 0755)
	configPath = filepath.Join(dir, "config.json")
	logPath = filepath.Join(dir, "app.log")
	historyPath = filepath.Join(dir, "recent_messages.json")
}

func loadConfig() {
	b, err := os.ReadFile(configPath)
	if err != nil {
		return
	}
	var loaded Config
	if json.Unmarshal(b, &loaded) != nil {
		return
	}
	if strings.TrimSpace(loaded.Hotkey) == "" {
		loaded.Hotkey = "Numpad ."
	}
	if loaded.NotifyDurationMS <= 0 {
		loaded.NotifyDurationMS = 3200
	}
	if loaded.InputYOffset <= 30 || loaded.InputYOffset > 250 {
		loaded.InputYOffset = 78
	}
	if loaded.ConfigVersion < 2 {
		loaded.HideNativeTargetNotification = true
		loaded.RecentMessageCount = 5
		loaded.OverlayAlpha = 188
		loaded.CompactNotifications = false
	}
	if loaded.ConfigVersion < 3 || loaded.IncomingOverlayDurationMS <= 0 {
		loaded.IncomingOverlayDurationMS = 2000
	}
	if loaded.ConfigVersion < 4 {
		loaded.HideNativeTargetNotification = true
	}
	loaded.ConfigVersion = 4
	if loaded.RecentMessageCount < 3 || loaded.RecentMessageCount > 10 {
		loaded.RecentMessageCount = 5
	}
	if loaded.OverlayAlpha < 100 || loaded.OverlayAlpha > 235 {
		loaded.OverlayAlpha = 188
	}
	if loaded.IncomingOverlayDurationMS < 500 || loaded.IncomingOverlayDurationMS > 10000 {
		loaded.IncomingOverlayDurationMS = 2000
	}
	cfg = loaded
}

func loadHistory() {
	b, err := os.ReadFile(historyPath)
	if err != nil {
		return
	}
	var h PersistedHistory
	if json.Unmarshal(b, &h) != nil {
		return
	}
	if !strings.EqualFold(strings.TrimSpace(h.TargetTitle), strings.TrimSpace(cfg.TargetChatTitle)) {
		return
	}
	// v1.2.3: v1.2.2 could persist a whole notification/UI dump as one
	// synthetic message (Sender == "").  Only keep messages parsed from the
	// actual Kakao chat list so the overlay is made of real individual messages.
	valid := make([]ChatMessage, 0, len(h.Messages))
	for _, m := range h.Messages {
		if strings.TrimSpace(m.Sender) == "" || strings.TrimSpace(m.Body) == "" {
			continue
		}
		valid = append(valid, m)
	}
	if len(valid) > 40 {
		valid = valid[len(valid)-40:]
	}
	historyMu.Lock()
	recentMessages = append([]ChatMessage(nil), valid...)
	historyMu.Unlock()
}

func saveHistory() {
	historyMu.Lock()
	msgs := append([]ChatMessage(nil), recentMessages...)
	historyMu.Unlock()
	if len(msgs) > 40 {
		msgs = msgs[len(msgs)-40:]
	}
	h := PersistedHistory{TargetTitle: cfg.TargetChatTitle, Messages: msgs}
	b, err := json.MarshalIndent(h, "", "  ")
	if err != nil {
		return
	}
	_ = os.WriteFile(historyPath, b, 0644)
}

func clearHistory() {
	historyMu.Lock()
	recentMessages = nil
	lastCapturedSig = ""
	lastCapturedAt = time.Time{}
	historyMu.Unlock()
	_ = os.Remove(historyPath)
	if historyHwnd != 0 {
		pInvalidateRect.Call(historyHwnd, 0, 1)
	}
}

func appendRecentMessage(body, sig string) {
	body = strings.TrimSpace(body)
	if body == "" {
		return
	}
	now := time.Now()
	historyMu.Lock()
	if sig != "" && sig == lastCapturedSig && now.Sub(lastCapturedAt) < 3*time.Second {
		historyMu.Unlock()
		return
	}
	if len(recentMessages) > 0 {
		last := recentMessages[len(recentMessages)-1]
		if last.Body == body && now.Sub(last.At) < 1500*time.Millisecond {
			lastCapturedSig = sig
			lastCapturedAt = now
			historyMu.Unlock()
			return
		}
	}
	recentMessages = append(recentMessages, ChatMessage{Sender: strings.TrimSpace(cfg.TargetChatTitle), Body: body, At: now, Mine: false})
	if len(recentMessages) > 40 {
		recentMessages = recentMessages[len(recentMessages)-40:]
	}
	lastCapturedSig = sig
	lastCapturedAt = now
	historyMu.Unlock()
	saveHistory()
	if historyHwnd != 0 {
		positionHistoryWindow()
		pInvalidateRect.Call(historyHwnd, 0, 1)
		if replyVisible {
			pShowWindow.Call(historyHwnd, SW_SHOWNORMAL)
			pSetWindowPos.Call(historyHwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE)
		} else {
			showIncomingHistoryOverlay()
		}
	}
}

func historySnapshot(limit int) []ChatMessage {
	if limit < 3 {
		limit = 3
	}
	if limit > 10 {
		limit = 10
	}
	historyMu.Lock()
	defer historyMu.Unlock()
	start := 0
	if len(recentMessages) > limit {
		start = len(recentMessages) - limit
	}
	return append([]ChatMessage(nil), recentMessages[start:]...)
}

func saveConfig() error {
	cfgMu.Lock()
	defer cfgMu.Unlock()
	b, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(configPath, b, 0644)
}

func logf(f string, args ...any) {
	if logPath == "" {
		return
	}
	fp, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return
	}
	defer fp.Close()
	_, _ = fmt.Fprintf(fp, "%s %s\n", time.Now().Format("2006-01-02 15:04:05.000"), fmt.Sprintf(f, args...))
}

func registerClass(name string, proc uintptr, background uintptr) {
	cur, _, _ := pLoadCursorW.Call(0, 32512) // IDC_ARROW
	ico, _, _ := pLoadIconW.Call(0, 32512)   // IDI_APPLICATION
	wc := WNDCLASSEXW{
		CbSize:        uint32(unsafe.Sizeof(WNDCLASSEXW{})),
		LpfnWndProc:   proc,
		HInstance:     hInstance,
		HIcon:         ico,
		HCursor:       cur,
		HbrBackground: background,
		LpszClassName: u16(name),
		HIconSm:       ico,
	}
	r, _, e := pRegisterClassExW.Call(uintptr(unsafe.Pointer(&wc)))
	if r == 0 {
		logf("RegisterClassEx %s: %v", name, e)
	}
}

func registerClasses() {
	bg := uintptr(COLOR_WINDOW + 1)
	registerClass(controllerClass, syscall.NewCallback(controllerProc), bg)
	registerClass(settingsClass, syscall.NewCallback(settingsProc), bg)
	registerClass(replyClass, syscall.NewCallback(replyProc), bg)
	registerClass(toastClass, syscall.NewCallback(toastProc), bg)
	registerClass(historyClass, syscall.NewCallback(historyProc), bg)
}

func createController() {
	controllerHwnd = createWindow(0, controllerClass, "FF14 Kakao Bridge", WS_OVERLAPPED, 0, 0, 0, 0, 0, 0)
}

func createSettingsWindow() {
	style := uint32(WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX)
	settingsHwnd = createWindow(0, settingsClass, "FF14 Kakao Bridge 설정", style, 0, 0, 580, 455, 0, 0)
}

func createReplyWindow() {
	// v1.7.8: keep the reply editor a normal foreground tool window rather than
	// a TOPMOST overlay.  The recent FFXIV build appears to react only when a
	// keyboard-capable topmost overlay starts receiving real user input.
	ex := uint32(WS_EX_TOOLWINDOW)
	replyHwnd = createWindow(ex, replyClass, "", WS_POPUP, 0, 0, 760, 58, 0, 0)
}

func createToastWindow() {
	ex := uint32(WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT | WS_EX_LAYERED)
	toastHwnd = createWindow(ex, toastClass, "", WS_POPUP, 0, 0, 350, 68, 0, 0)
	pSetLayeredWindowAttributes.Call(toastHwnd, 0, 226, LWA_ALPHA)
	b, _, _ := pCreateSolidBrush.Call(rgb(24, 24, 24))
	toastBrush = b
}

func createHistoryWindow() {
	ex := uint32(WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT | WS_EX_LAYERED)
	historyHwnd = createWindow(ex, historyClass, "", WS_POPUP, 0, 0, 430, 240, 0, 0)
	pSetLayeredWindowAttributes.Call(historyHwnd, 0, uintptr(cfg.OverlayAlpha), LWA_ALPHA)
	b, _, _ := pCreateSolidBrush.Call(rgb(18, 18, 18))
	historyBrush = b

	// Outgoing messages are deliberately rendered a little smaller/lighter,
	// similar to the compact visual weight of "my" messages in a chat view.
	fontHeight := int32(-13)
	f, _, _ := pCreateFontW.Call(
		uintptr(fontHeight), 0, 0, 0, 400,
		0, 0, 0, 1, 0, 0, 5, 0,
		uintptr(unsafe.Pointer(u16("Segoe UI"))),
	)
	historyMineFont = f
}

func createWindow(ex uint32, class, title string, style uint32, x, y, w, h int32, parent uintptr, id uintptr) uintptr {
	hwnd, _, e := pCreateWindowExW.Call(
		uintptr(ex), uintptr(unsafe.Pointer(u16(class))), uintptr(unsafe.Pointer(u16(title))), uintptr(style),
		uintptr(x), uintptr(y), uintptr(w), uintptr(h), parent, id, hInstance, 0,
	)
	if hwnd == 0 {
		logf("CreateWindow %s failed: %v", class, e)
	}
	return hwnd
}

func createControl(class, text string, style uint32, x, y, w, h int32, parent uintptr, id uintptr) uintptr {
	hwnd := createWindow(0, class, text, WS_CHILD|WS_VISIBLE|style, x, y, w, h, parent, id)
	font, _, _ := pGetStockObject.Call(DEFAULT_GUI_FONT)
	pSendMessageW.Call(hwnd, WM_SETFONT, font, 1)
	return hwnd
}

func controllerProc(hwnd uintptr, msg uint32, wParam, lParam uintptr) uintptr {
	if shellHookMsg != 0 && msg == shellHookMsg {
		// v1.6.0: only FLASH is actionable. Calling FlashWindowEx(STOP) can itself
		// generate REDRAW, so handling REDRAW created the 0.9 s feedback loop seen
		// in v1.5.0 logs.
		if uint32(wParam) == HSHELL_FLASH {
			handleShellSignal(lParam, uint32(wParam))
		}
		return 0
	}
	if taskbarCreatedMsg != 0 && msg == taskbarCreatedMsg {
		logf("TaskbarCreated received; restoring tray icon")
		trayRegistered = false
		addTrayIconWithRetry()
		return 0
	}
	switch msg {
	case WM_HOTKEY:
		if wParam == ID_HOTKEY {
			openReplyFromHotkey()
		}
		return 0
	case WM_TIMER:
		switch wParam {
		case TIMER_POLL:
			// Fallback only. The WinEvent SHOW hook normally hides Kakao popups
			// immediately; this slow timer catches animations/re-created HWNDs.
			if !replyVisible {
				suppressNativeKakaoPopupsWhileGaming()
			}
		case TIMER_TOAST_HIDE:
			pKillTimer.Call(controllerHwnd, TIMER_TOAST_HIDE)
			pShowWindow.Call(toastHwnd, SW_HIDE)
		case TIMER_CAPTURE:
			pKillTimer.Call(controllerHwnd, TIMER_CAPTURE)
			finishCaptureTarget()
		case TIMER_HISTORY_HIDE:
			pKillTimer.Call(controllerHwnd, TIMER_HISTORY_HIDE)
			historyAutoVisible = false
			if !replyVisible {
				pShowWindow.Call(historyHwnd, SW_HIDE)
			}
		case TIMER_HISTORY_CAPTURE:
			pKillTimer.Call(controllerHwnd, TIMER_HISTORY_CAPTURE)
			requestIndependentReceivePoll()
		case TIMER_INITIAL_SYNC:
			pKillTimer.Call(controllerHwnd, TIMER_INITIAL_SYNC)
			requestIndependentReceivePoll()
		case TIMER_INDEPENDENT_RX:
			requestIndependentReceivePoll()
		}
		return 0
	case WM_COMMAND:
		switch loword(wParam) {
		case ID_TRAY_REPLY:
			openReply(false)
		case ID_TRAY_SETTINGS:
			showSettings()
		case ID_TRAY_EXIT:
			cleanup()
			pPostQuitMessage.Call(0)
		}
		return 0
	case WM_APP_TRAY:
		switch uint32(lParam) {
		case WM_RBUTTONUP, WM_CONTEXTMENU:
			showTrayMenu()
		case WM_LBUTTONDBLCLK:
			showSettings()
		}
		return 0
	case WM_APP_HISTORY_UPDATED:
		newCount := int(wParam)
		announce := lParam != 0
		if historyHwnd != 0 {
			positionHistoryWindow()
			pInvalidateRect.Call(historyHwnd, 0, 1)
			if replyVisible {
				pShowWindow.Call(historyHwnd, SW_SHOWNORMAL)
				pSetWindowPos.Call(historyHwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE)
			} else if announce && newCount > 0 {
				showIncomingHistoryOverlay()
			}
		}
		return 0
	case WM_APP_KAKAO_SHOW:
		suppressNativeKakaoPopup(wParam)
		return 0
	case WM_APP_INCOMING_HINT:
		showIncomingFallbackHint()
		return 0
	case WM_APP_SEND_VERIFIED:
		finishAsyncOutgoingVerifications()
		return 0
	case WM_DESTROY:
		pPostQuitMessage.Call(0)
		return 0
	}
	r, _, _ := pDefWindowProcW.Call(hwnd, uintptr(msg), wParam, lParam)
	return r
}

func settingsProc(hwnd uintptr, msg uint32, wParam, lParam uintptr) uintptr {
	switch msg {
	case 0x0001: // WM_CREATE
		createControl("STATIC", "답장 단축키", 0, 24, 24, 120, 22, hwnd, 0)
		createControl("EDIT", cfg.Hotkey, WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 150, 20, 210, 26, hwnd, ID_HOTKEY_EDIT)
		createControl("STATIC", "예: Numpad .   /   F10   /   Ctrl+Alt+K", 0, 150, 50, 340, 20, hwnd, 0)

		createControl("STATIC", "답장 대상 카톡방", 0, 24, 84, 120, 22, hwnd, 0)
		createControl("EDIT", cfg.TargetChatTitle, WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 150, 80, 210, 26, hwnd, ID_TARGET_EDIT)
		createControl("BUTTON", "3초 뒤 활성 카톡방 지정", BS_PUSHBUTTON|WS_TABSTOP, 372, 78, 155, 30, hwnd, ID_CAPTURE)
		createControl("STATIC", "카톡방을 별도 창으로 열어 둔 뒤 위 버튼을 누르고 해당 창을 클릭하세요.", 0, 24, 114, 500, 20, hwnd, 0)

		only := createControl("BUTTON", "FF14가 활성 상태일 때만 Bridge 동작", BS_AUTOCHECKBOX|WS_TABSTOP, 24, 151, 310, 24, hwnd, ID_ONLY_FF14)
		hideNative := createControl("BUTTON", "FF14 중 카카오 기본 알림 차단 (Bridge 독립 알림 사용)", BS_AUTOCHECKBOX|WS_TABSTOP, 24, 180, 410, 24, hwnd, ID_HIDE_NATIVE)
		if cfg.OnlyWhenFF14 {
			pSendMessageW.Call(only, BM_SETCHECK, BST_CHECKED, 0)
		}
		if cfg.HideNativeTargetNotification {
			pSendMessageW.Call(hideNative, BM_SETCHECK, BST_CHECKED, 0)
		}
		createControl("STATIC", "※ Bridge는 저부하 화면 변화 감시로 도착을 찾고, 감지된 순간에만 본문을 동기화합니다. 평상시에는 카톡 입력을 건드리지 않습니다.", 0, 42, 207, 500, 22, hwnd, 0)

		createControl("STATIC", "최근 대화 표시 개수", 0, 24, 244, 155, 22, hwnd, 0)
		createControl("EDIT", strconv.Itoa(cfg.RecentMessageCount), WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 184, 240, 58, 26, hwnd, ID_HISTORY_COUNT)
		createControl("STATIC", "3~10개", 0, 251, 244, 70, 22, hwnd, 0)

		createControl("STATIC", "대화창 투명도", 0, 337, 244, 110, 22, hwnd, 0)
		createControl("EDIT", strconv.Itoa(cfg.OverlayAlpha), WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 449, 240, 58, 26, hwnd, ID_OVERLAY_ALPHA)
		createControl("STATIC", "100~235", 0, 512, 244, 55, 22, hwnd, 0)

		createControl("STATIC", "새 메시지 표시시간(ms)", 0, 24, 292, 175, 22, hwnd, 0)
		createControl("EDIT", strconv.Itoa(cfg.IncomingOverlayDurationMS), WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 204, 288, 78, 26, hwnd, ID_INCOMING_MS)
		createControl("STATIC", "500~10000 · 기본 2000", 0, 294, 292, 180, 20, hwnd, 0)

		createControl("STATIC", "카톡 입력칸 하단 보정(px)", 0, 24, 334, 180, 22, hwnd, 0)
		createControl("EDIT", strconv.Itoa(cfg.InputYOffset), WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 210, 330, 74, 26, hwnd, ID_OFFSET_EDIT)
		createControl("STATIC", "기본 78 · 전송 클릭 위치가 어긋날 때만 조정", 0, 296, 334, 230, 20, hwnd, 0)

		createControl("BUTTON", "저장", BS_PUSHBUTTON|WS_TABSTOP, 350, 389, 82, 32, hwnd, ID_SAVE)
		createControl("BUTTON", "닫기", BS_PUSHBUTTON|WS_TABSTOP, 444, 389, 82, 32, hwnd, ID_HIDE_SETTINGS)
		return 0
	case WM_COMMAND:
		switch loword(wParam) {
		case ID_SAVE:
			saveSettingsFromUI()
		case ID_CAPTURE:
			beginCaptureTarget()
		case ID_HIDE_SETTINGS:
			pShowWindow.Call(settingsHwnd, SW_HIDE)
		}
		return 0
	case WM_CLOSE:
		pShowWindow.Call(settingsHwnd, SW_HIDE)
		return 0
	}
	r, _, _ := pDefWindowProcW.Call(hwnd, uintptr(msg), wParam, lParam)
	return r
}

func replyProc(hwnd uintptr, msg uint32, wParam, lParam uintptr) uintptr {
	switch msg {
	case 0x0001: // WM_CREATE
		replyLabel = createControl("STATIC", "카카오톡 →", 0, 14, 8, 150, 20, hwnd, 0)
		replyEdit = createControl("EDIT", "", WS_BORDER|ES_AUTOHSCROLL|WS_TABSTOP, 14, 28, 620, 25, hwnd, 5001)
		createControl("STATIC", "Enter 전송 · Esc 취소", 0, 642, 31, 108, 20, hwnd, 0)
		return 0
	case WM_CLOSE:
		cancelReply()
		return 0
	}
	r, _, _ := pDefWindowProcW.Call(hwnd, uintptr(msg), wParam, lParam)
	return r
}

func toastProc(hwnd uintptr, msg uint32, wParam, lParam uintptr) uintptr {
	switch msg {
	case WM_ERASEBKGND:
		return 1
	case WM_PAINT:
		var ps PAINTSTRUCT
		hdc, _, _ := pBeginPaint.Call(hwnd, uintptr(unsafe.Pointer(&ps)))
		var rc RECT
		pGetClientRect.Call(hwnd, uintptr(unsafe.Pointer(&rc)))
		if toastBrush != 0 {
			pFillRect.Call(hdc, uintptr(unsafe.Pointer(&rc)), toastBrush)
		}
		pSetBkMode.Call(hdc, TRANSPARENT)

		pSetTextColor.Call(hdc, rgb(235, 235, 235))
		titleRc := RECT{Left: 12, Top: 8, Right: rc.Right - 12, Bottom: 29}
		pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16(toastTitle))), ^uintptr(0), uintptr(unsafe.Pointer(&titleRc)), DT_LEFT|DT_SINGLELINE|DT_END_ELLIPSIS|DT_VCENTER)

		pSetTextColor.Call(hdc, rgb(185, 185, 185))
		bodyRc := RECT{Left: 12, Top: 31, Right: rc.Right - 12, Bottom: rc.Bottom - 7}
		pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16(toastBody))), ^uintptr(0), uintptr(unsafe.Pointer(&bodyRc)), DT_LEFT|DT_SINGLELINE|DT_END_ELLIPSIS|DT_VCENTER)
		pEndPaint.Call(hwnd, uintptr(unsafe.Pointer(&ps)))
		return 0
	}
	r, _, _ := pDefWindowProcW.Call(hwnd, uintptr(msg), wParam, lParam)
	return r
}

func historyProc(hwnd uintptr, msg uint32, wParam, lParam uintptr) uintptr {
	switch msg {
	case WM_ERASEBKGND:
		return 1
	case WM_PAINT:
		var ps PAINTSTRUCT
		hdc, _, _ := pBeginPaint.Call(hwnd, uintptr(unsafe.Pointer(&ps)))
		var rc RECT
		pGetClientRect.Call(hwnd, uintptr(unsafe.Pointer(&rc)))
		if historyBrush != 0 {
			pFillRect.Call(hdc, uintptr(unsafe.Pointer(&rc)), historyBrush)
		}
		pSetBkMode.Call(hdc, TRANSPARENT)

		baseFont, _, _ := pGetStockObject.Call(DEFAULT_GUI_FONT)
		oldFont := uintptr(0)
		if baseFont != 0 {
			oldFont, _, _ = pSelectObject.Call(hdc, baseFont)
		}

		pSetTextColor.Call(hdc, rgb(238, 238, 238))
		header := cfg.TargetChatTitle
		if strings.TrimSpace(header) == "" {
			header = "카카오톡"
		}
		headerRc := RECT{Left: 14, Top: 8, Right: rc.Right - 14, Bottom: 30}
		pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16(header+" · 최근 대화"))), ^uintptr(0), uintptr(unsafe.Pointer(&headerRc)), DT_LEFT|DT_SINGLELINE|DT_END_ELLIPSIS|DT_VCENTER|DT_NOPREFIX)

		msgs := historySnapshot(cfg.RecentMessageCount)
		if len(msgs) == 0 {
			pSetTextColor.Call(hdc, rgb(170, 170, 170))
			emptyRc := RECT{Left: 14, Top: 38, Right: rc.Right - 14, Bottom: rc.Bottom - 12}
			pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16("아직 수집된 대화가 없습니다.\n토글하면 현재 카톡방의 최근 대화를 불러옵니다."))), ^uintptr(0), uintptr(unsafe.Pointer(&emptyRc)), DT_LEFT|DT_WORDBREAK|DT_NOPREFIX)
		} else {
			y := int32(36)
			for _, m := range msgs {
				if m.Mine {
					if historyMineFont != 0 {
						pSelectObject.Call(hdc, historyMineFont)
					}
					pSetTextColor.Call(hdc, rgb(176, 176, 176))
					line := "나 · " + m.At.Local().Format("15:04") + "   " + abbreviate(strings.ReplaceAll(m.Body, "\n", " "), 92)
					bodyRc := RECT{Left: 82, Top: y + 2, Right: rc.Right - 14, Bottom: y + 34}
					pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16(line))), ^uintptr(0), uintptr(unsafe.Pointer(&bodyRc)), DT_RIGHT|DT_SINGLELINE|DT_END_ELLIPSIS|DT_VCENTER|DT_NOPREFIX)
					if baseFont != 0 {
						pSelectObject.Call(hdc, baseFont)
					}
				} else {
					pSetTextColor.Call(hdc, rgb(145, 145, 145))
					timeRc := RECT{Left: 14, Top: y, Right: 58, Bottom: y + 19}
					pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16(m.At.Local().Format("15:04")))), ^uintptr(0), uintptr(unsafe.Pointer(&timeRc)), DT_LEFT|DT_SINGLELINE|DT_VCENTER|DT_NOPREFIX)

					pSetTextColor.Call(hdc, rgb(225, 225, 225))
					bodyRc := RECT{Left: 61, Top: y, Right: rc.Right - 14, Bottom: y + 42}
					pDrawTextW.Call(hdc, uintptr(unsafe.Pointer(u16(abbreviate(strings.ReplaceAll(m.Body, "\n", " "), 110)))), ^uintptr(0), uintptr(unsafe.Pointer(&bodyRc)), DT_LEFT|DT_WORDBREAK|DT_END_ELLIPSIS|DT_NOPREFIX)
				}
				y += 44
			}
		}
		if oldFont != 0 {
			pSelectObject.Call(hdc, oldFont)
		}
		pEndPaint.Call(hwnd, uintptr(unsafe.Pointer(&ps)))
		return 0
	}
	r, _, _ := pDefWindowProcW.Call(hwnd, uintptr(msg), wParam, lParam)
	return r
}

func showSettings() {
	syncSettingsUI()
	centerWindow(settingsHwnd, 580, 455)
	pShowWindow.Call(settingsHwnd, SW_SHOW)
	pSetForegroundWindow.Call(settingsHwnd)
}

func syncSettingsUI() {
	if settingsHwnd == 0 {
		return
	}
	setText(pGetDlgItemHandle(settingsHwnd, ID_HOTKEY_EDIT), cfg.Hotkey)
	setText(pGetDlgItemHandle(settingsHwnd, ID_TARGET_EDIT), cfg.TargetChatTitle)
	setText(pGetDlgItemHandle(settingsHwnd, ID_OFFSET_EDIT), strconv.Itoa(cfg.InputYOffset))
	setText(pGetDlgItemHandle(settingsHwnd, ID_HISTORY_COUNT), strconv.Itoa(cfg.RecentMessageCount))
	setText(pGetDlgItemHandle(settingsHwnd, ID_OVERLAY_ALPHA), strconv.Itoa(cfg.OverlayAlpha))
	setText(pGetDlgItemHandle(settingsHwnd, ID_INCOMING_MS), strconv.Itoa(cfg.IncomingOverlayDurationMS))
	setCheck(pGetDlgItemHandle(settingsHwnd, ID_ONLY_FF14), cfg.OnlyWhenFF14)
	setCheck(pGetDlgItemHandle(settingsHwnd, ID_HIDE_NATIVE), cfg.HideNativeTargetNotification)
}

func saveSettingsFromUI() {
	newCfg := cfg
	newCfg.ConfigVersion = 4
	newCfg.Hotkey = strings.TrimSpace(getText(pGetDlgItemHandle(settingsHwnd, ID_HOTKEY_EDIT)))
	newCfg.TargetChatTitle = strings.TrimSpace(getText(pGetDlgItemHandle(settingsHwnd, ID_TARGET_EDIT)))
	newCfg.OnlyWhenFF14 = getCheck(pGetDlgItemHandle(settingsHwnd, ID_ONLY_FF14))
	newCfg.HideNativeTargetNotification = getCheck(pGetDlgItemHandle(settingsHwnd, ID_HIDE_NATIVE))
	newCfg.CompactNotifications = false

	off, err := strconv.Atoi(strings.TrimSpace(getText(pGetDlgItemHandle(settingsHwnd, ID_OFFSET_EDIT))))
	if err != nil || off < 30 || off > 250 {
		messageBox("설정 오류", "입력칸 하단 보정값은 30~250 사이의 숫자로 입력해 주세요.")
		return
	}
	newCfg.InputYOffset = off

	count, err := strconv.Atoi(strings.TrimSpace(getText(pGetDlgItemHandle(settingsHwnd, ID_HISTORY_COUNT))))
	if err != nil || count < 3 || count > 10 {
		messageBox("설정 오류", "최근 대화 표시 개수는 3~10 사이로 입력해 주세요.")
		return
	}
	newCfg.RecentMessageCount = count

	alpha, err := strconv.Atoi(strings.TrimSpace(getText(pGetDlgItemHandle(settingsHwnd, ID_OVERLAY_ALPHA))))
	if err != nil || alpha < 100 || alpha > 235 {
		messageBox("설정 오류", "대화창 투명도는 100~235 사이로 입력해 주세요.\n값이 높을수록 더 진하게 보입니다.")
		return
	}
	newCfg.OverlayAlpha = alpha

	incomingMS, err := strconv.Atoi(strings.TrimSpace(getText(pGetDlgItemHandle(settingsHwnd, ID_INCOMING_MS))))
	if err != nil || incomingMS < 500 || incomingMS > 10000 {
		messageBox("설정 오류", "새 메시지 표시시간은 500~10000ms 사이로 입력해 주세요.")
		return
	}
	newCfg.IncomingOverlayDurationMS = incomingMS

	if _, _, err := parseHotkey(newCfg.Hotkey); err != nil {
		messageBox("단축키 오류", err.Error())
		return
	}
	old := cfg
	targetChanged := !strings.EqualFold(strings.TrimSpace(old.TargetChatTitle), strings.TrimSpace(newCfg.TargetChatTitle))
	cfg = newCfg
	if err := applyHotkey(cfg.Hotkey); err != nil {
		cfg = old
		_ = applyHotkey(cfg.Hotkey)
		messageBox("단축키 등록 실패", "다른 프로그램이 이미 사용 중인 키일 수 있습니다. 다른 단축키를 선택해 주세요.")
		return
	}
	if targetChanged {
		clearHistory()
		resetPassiveReceiveState()
	}
	if strings.TrimSpace(cfg.TargetChatTitle) != "" {
		pSetTimer.Call(controllerHwnd, TIMER_INDEPENDENT_RX, 1800, 0)
		pKillTimer.Call(controllerHwnd, TIMER_INITIAL_SYNC)
		pSetTimer.Call(controllerHwnd, TIMER_INITIAL_SYNC, 250, 0)
	} else {
		pKillTimer.Call(controllerHwnd, TIMER_INDEPENDENT_RX)
	}
	if historyHwnd != 0 {
		pSetLayeredWindowAttributes.Call(historyHwnd, 0, uintptr(cfg.OverlayAlpha), LWA_ALPHA)
	}
	if err := saveConfig(); err != nil {
		messageBox("저장 실패", err.Error())
		return
	}
	logf("settings saved: hotkey=%q target=%q onlyFF14=%v hideNative=%v history=%d alpha=%d incomingMS=%d offset=%d", cfg.Hotkey, cfg.TargetChatTitle, cfg.OnlyWhenFF14, cfg.HideNativeTargetNotification, cfg.RecentMessageCount, cfg.OverlayAlpha, cfg.IncomingOverlayDurationMS, cfg.InputYOffset)
	showToast("설정 저장됨", fmt.Sprintf("답장 단축키: %s", cfg.Hotkey))
	pShowWindow.Call(settingsHwnd, SW_HIDE)
}

func beginCaptureTarget() {
	pShowWindow.Call(settingsHwnd, SW_HIDE)
	showToast("카톡방 지정", "3초 안에 대상 카톡방 창을 클릭하세요")
	pSetTimer.Call(controllerHwnd, TIMER_CAPTURE, 3000, 0)
}

func finishCaptureTarget() {
	hwnd, _, _ := pGetForegroundWindow.Call()
	if hwnd == 0 || !isProcess(hwnd, "KakaoTalk.exe") {
		messageBox("카톡방 지정 실패", "활성 창이 카카오톡이 아닙니다. 카톡방을 별도 창으로 열고 다시 지정해 주세요.")
		showSettings()
		return
	}
	title := strings.TrimSpace(getWindowText(hwnd))
	if title == "" {
		messageBox("카톡방 지정 실패", "카카오톡 창 제목을 읽지 못했습니다.")
		showSettings()
		return
	}
	if !strings.EqualFold(strings.TrimSpace(cfg.TargetChatTitle), title) {
		clearHistory()
	}
	cfg.TargetChatTitle = title
	_ = saveConfig()
	syncSettingsUI()
	logf("target captured: hwnd=%x title=%q", hwnd, title)
	resetPassiveReceiveState()
	pSetTimer.Call(controllerHwnd, TIMER_INDEPENDENT_RX, 1800, 0)
	pKillTimer.Call(controllerHwnd, TIMER_INITIAL_SYNC)
	pSetTimer.Call(controllerHwnd, TIMER_INITIAL_SYNC, 250, 0)
	showToast("답장 대상 지정 완료", title)
	showSettings()
}

func openReplyFromHotkey() {
	// The same hotkey is a true toggle. Once the reply UI is open, close it
	// before applying the FF14-only foreground check (the foreground is our edit box then).
	if replyVisible {
		cancelReply()
		return
	}
	if cfg.OnlyWhenFF14 {
		fg, _, _ := pGetForegroundWindow.Call()
		if !isFF14(fg) {
			logf("reply hotkey ignored by FF14-only gate foreground=%x process=%q", fg, processBaseName(fg))
			return
		}
	}
	openReply(true)
}

// Only one toggle-triggered transcript update at a time. Additional toggles
// immediately use the cached history instead of queueing slow Kakao requests.
var toggleRefreshRunning atomic.Bool

func refreshHistoryForToggleAsync() {
	if !toggleRefreshRunning.CompareAndSwap(false, true) {
		return
	}
	go func() {
		defer toggleRefreshRunning.Store(false)
		// The Win32 reply EDIT is already visible and focused at this point.
		// Yield a moment so the first user's keystroke never competes with
		// Kakao's clipboard exchange or the clipboard backup.
		time.Sleep(120 * time.Millisecond)
		started := time.Now()
		refreshHistoryForToggle()
		logf("input-priority async history refresh finished in %s", time.Since(started))
	}()
}

func openReply(fromHotkey bool) {
	if strings.TrimSpace(cfg.TargetChatTitle) == "" {
		showToast("답장 대상이 없습니다", "설정에서 대상 카톡방을 먼저 지정하세요")
		showSettings()
		return
	}
	// Do not enumerate Kakao windows before accepting the user's typing.
	// The async refresh and the send path retain their own target validation.
	if replyVisible {
		pSetForegroundWindow.Call(replyHwnd)
		pSetFocus.Call(replyEdit)
		return
	}

	// Remember FF14 (or whichever window the user was actually in) BEFORE the
	// foreground history refresh briefly activates Kakao.
	fg, _, _ := pGetForegroundWindow.Call()
	previousHwnd = fg

	suppressShellUntil = time.Now().Add(1400 * time.Millisecond)

	setText(replyEdit, "")
	setText(replyLabel, "카카오톡 → "+cfg.TargetChatTitle)
	positionReplyWindow()
	replyVisible = true
	pShowWindow.Call(replyHwnd, SW_SHOW)
	// Keep it above the game as the active foreground window, but do not promote
	// it into the system-wide TOPMOST band.
	pSetWindowPos.Call(replyHwnd, 0, 0, 0, 0, 0, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE)
	showHistoryOverlay()
	activateReplyInput()
	// Never block the foreground reply window on Kakao's 500-1300ms copy.
	refreshHistoryForToggleAsync()
}

func cancelReply() {
	if !replyVisible {
		return
	}
	pShowWindow.Call(replyHwnd, SW_HIDE)
	if !historyAutoVisible {
		pShowWindow.Call(historyHwnd, SW_HIDE)
	}
	replyVisible = false
	restorePreviousWindow()
}

// Outgoing verification is never allowed to keep Kakao in the foreground.
// Results are marshalled back to the Win32 UI thread for overlays and toast.
type outgoingVerifyResult struct {
	targetTitle string
	msg         string
	sender      string
	raw         string
	input       uintptr
	verified    bool
}

var outgoingVerifyResultsMu sync.Mutex
var outgoingVerifyResults []outgoingVerifyResult

func queueOutgoingVerifyResult(result outgoingVerifyResult) {
	outgoingVerifyResultsMu.Lock()
	outgoingVerifyResults = append(outgoingVerifyResults, result)
	outgoingVerifyResultsMu.Unlock()
	if controllerHwnd != 0 {
		pPostMessageW.Call(controllerHwnd, WM_APP_SEND_VERIFIED, 0, 0)
	}
}

func finishAsyncOutgoingVerifications() {
	outgoingVerifyResultsMu.Lock()
	results := outgoingVerifyResults
	outgoingVerifyResults = nil
	outgoingVerifyResultsMu.Unlock()
	for _, result := range results {
		// A changed target means this verification belongs to an old chat room.
		if !strings.EqualFold(strings.TrimSpace(cfg.TargetChatTitle), strings.TrimSpace(result.targetTitle)) {
			logf("background send verify skipped: target changed from %q to %q", result.targetTitle, cfg.TargetChatTitle)
			continue
		}
		if result.verified && strings.TrimSpace(result.raw) != "" {
			replaceHistoryFromClipboard(result.raw)
			if historyHwnd != 0 {
				positionHistoryWindow()
				pInvalidateRect.Call(historyHwnd, 0, 1)
			}
			if !replyVisible {
				showToast("카톡 전송 완료", abbreviate(result.msg, 58))
				showIncomingHistoryOverlay()
			}
			logf("reply verified sent to %q (%d chars) sender=%q input=%x", result.targetTitle, len([]rune(result.msg)), result.sender, result.input)
		} else {
			// EVA-only verification can fail independently of a successful send.
			// Preserve the old honest status without stealing game focus to retry.
			if !replyVisible {
				showToast("전송 확인 실패", "카톡 입력은 수행했지만 실제 발신 내역을 확인하지 못했습니다")
			}
			logf("reply send NOT VERIFIED in background to %q (%d chars) input=%x", result.targetTitle, len([]rune(result.msg)), result.input)
		}
	}
}

func verifyOutgoingAsync(target uintptr, targetTitle, msg string, input uintptr) {
	go func() {
		// Kakao needs a short interval to commit the posted Enter.  This delay
		// no longer holds the Kakao window above FF14 or blocks the Win32 UI.
		time.Sleep(130 * time.Millisecond)
		verifyStarted := time.Now()
		verified, raw, sender := verifySentMessageBackground(target, msg)
		logf("background send verification finished in %s; verified=%v", time.Since(verifyStarted), verified)
		queueOutgoingVerifyResult(outgoingVerifyResult{
			targetTitle: targetTitle,
			msg:         msg,
			sender:      sender,
			raw:         raw,
			input:       input,
			verified:    verified,
		})
	}()
}

func sendReply() {
	if !replyVisible {
		return
	}
	started := time.Now()
	msg := strings.TrimSpace(getText(replyEdit))
	if msg == "" {
		cancelReply()
		return
	}

	target := findTargetChatWindow()
	if target == 0 {
		pShowWindow.Call(replyHwnd, SW_HIDE)
		pShowWindow.Call(historyHwnd, SW_HIDE)
		replyVisible = false
		restorePreviousWindow()
		showToast("전송 실패", "대상 카톡방 창을 찾지 못했습니다")
		return
	}

	// Keep the known-good Kakao direct-HWND send sequence intact.  What was
	// slow was waiting for four foreground transcript verification attempts
	// before minimising Kakao and restoring the game.
	suppressShellUntil = time.Now().Add(2600 * time.Millisecond)
	pKillTimer.Call(controllerHwnd, TIMER_HISTORY_CAPTURE)
	wasMinimized, _, _ := pIsIconic.Call(target)
	pShowWindow.Call(replyHwnd, SW_HIDE)
	pShowWindow.Call(historyHwnd, SW_HIDE)
	replyVisible = false

	if wasMinimized != 0 {
		pShowWindow.Call(target, SW_RESTORE)
	}
	input, ok := sendKakaoMessageDirect(target, msg)
	if wasMinimized != 0 {
		pShowWindow.Call(target, SW_MINIMIZE)
	}
	// Restore FF14 immediately after the send dispatch, not after Kakao's
	// slow clipboard copy/verification. The verification never activates Kakao.
	restorePreviousWindow()
	if !ok {
		showToast("전송 실패", "카카오톡 입력 컨트롤을 찾거나 전송하지 못했습니다")
		return
	}
	markPassiveReceiveNeedsReprime(2200 * time.Millisecond)
	logf("reply sent to Kakao input=%x (%d chars); game foreground restored in %s; background verification queued", input, len([]rune(msg)), time.Since(started))
	verifyOutgoingAsync(target, cfg.TargetChatTitle, msg, input)
}

var enumEditableComposerMu sync.Mutex
var enumEditableComposerResult uintptr

var enumEditableComposerCb = syscall.NewCallback(func(hwnd uintptr, lParam uintptr) uintptr {
	if !strings.EqualFold(strings.TrimSpace(getClassName(hwnd)), "RICHEDIT50W") {
		return 1
	}
	idx := int32(GWL_STYLE)
	style, _, _ := pGetWindowLongW.Call(hwnd, uintptr(idx))
	st := uint32(style)
	isEditable := st&ES_READONLY == 0
	isMultiline := st&ES_MULTILINE != 0
	var rc RECT
	pGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&rc)))
	logf("composer candidate hwnd=%x class=%q style=0x%x editable=%v multiline=%v rect=%d,%d-%d,%d", hwnd, getClassName(hwnd), st, isEditable, isMultiline, rc.Left, rc.Top, rc.Right, rc.Bottom)
	if isEditable && isMultiline {
		enumEditableComposerMu.Lock()
		enumEditableComposerResult = hwnd
		enumEditableComposerMu.Unlock()
		return 0
	}
	return 1
})

func findEditableKakaoComposer(parent uintptr) uintptr {
	if parent == 0 {
		return 0
	}
	enumEditableComposerMu.Lock()
	enumEditableComposerResult = 0
	enumEditableComposerMu.Unlock()
	pEnumChildWindows.Call(parent, enumEditableComposerCb, 0)
	enumEditableComposerMu.Lock()
	out := enumEditableComposerResult
	enumEditableComposerResult = 0
	enumEditableComposerMu.Unlock()
	if out == 0 {
		logf("editable multiline RICHEDIT50W not found under target=%x", parent)
	}
	return out
}

func makeKeyLParam(vk uintptr) uintptr {
	scan, _, _ := pMapVirtualKeyW.Call(vk, 0)
	return uintptr(uint32(scan&0xffff) << 16)
}

func postTextboxClick(hwnd uintptr) {
	if hwnd == 0 {
		return
	}
	lp := uintptr(uint32(15) | (uint32(20) << 16))
	pPostMessageW.Call(hwnd, WM_LBUTTONDOWN, 1, lp)
	time.Sleep(10 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_LBUTTONUP, 0, lp)
}

func postKeyToKakaoInput(hwnd uintptr, vk uintptr) {
	if hwnd == 0 {
		return
	}
	targetThread, _, _ := pGetWindowThreadProcessId.Call(hwnd, 0)
	curThread, _, _ := pGetCurrentThreadId.Call()
	attached := false
	if targetThread != 0 && curThread != 0 && targetThread != curThread {
		if r, _, _ := pAttachThreadInput.Call(curThread, targetThread, 1); r != 0 {
			attached = true
		}
	}
	if attached {
		defer pAttachThreadInput.Call(curThread, targetThread, 0)
	}

	oldState := make([]byte, 256)
	if r, _, _ := pGetKeyboardState.Call(uintptr(unsafe.Pointer(&oldState[0]))); r != 0 {
		newState := make([]byte, 256)
		copy(newState, oldState)
		newState[int(vk&0xff)] |= 0x80
		pSetKeyboardState.Call(uintptr(unsafe.Pointer(&newState[0])))
		defer pSetKeyboardState.Call(uintptr(unsafe.Pointer(&oldState[0])))
	}

	lp := makeKeyLParam(vk)
	pPostMessageW.Call(hwnd, WM_KEYDOWN, vk, lp)
	time.Sleep(10 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_KEYUP, vk, lp|(1<<30)|(1<<31))
}

func postEnterToKakaoInput(hwnd uintptr) {
	if hwnd == 0 {
		return
	}
	targetThread, _, _ := pGetWindowThreadProcessId.Call(hwnd, 0)
	curThread, _, _ := pGetCurrentThreadId.Call()
	attached := false
	if targetThread != 0 && curThread != 0 && targetThread != curThread {
		if r, _, _ := pAttachThreadInput.Call(curThread, targetThread, 1); r != 0 {
			attached = true
		}
	}
	if attached {
		defer pAttachThreadInput.Call(curThread, targetThread, 0)
	}
	lp := makeKeyLParam(VK_RETURN)
	pPostMessageW.Call(hwnd, WM_KEYDOWN, VK_RETURN, lp)
	time.Sleep(15 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_CHAR, uintptr('\r'), lp)
	time.Sleep(15 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_KEYUP, VK_RETURN, lp|(1<<30)|(1<<31))
}

func normalizeKakaoLineEndings(s string) string {
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	return strings.ReplaceAll(s, "\n", "\r\n")
}

func sendKakaoMessageDirect(target uintptr, msg string) (uintptr, bool) {
	input := findEditableKakaoComposer(target)
	if input == 0 {
		return 0, false
	}

	// Mirror the known-working Kakao PC interaction sequence: activate parent,
	// click the textbox HWND, clear selection state, WM_SETTEXT, move caret to the
	// end, click again, then send KEYDOWN + WM_CHAR + KEYUP for Enter.
	pSendMessageW.Call(target, 0x0006, WA_ACTIVE, 0)
	pSetForegroundWindow.Call(target) // helpful when Windows allows it; not required for HWND delivery
	time.Sleep(10 * time.Millisecond)
	postTextboxClick(input)
	time.Sleep(10 * time.Millisecond)
	postKeyToKakaoInput(input, VK_C)
	time.Sleep(10 * time.Millisecond)
	postKeyToKakaoInput(input, VK_BACK)
	postTextboxClick(input)
	time.Sleep(10 * time.Millisecond)
	postKeyToKakaoInput(input, VK_A)
	time.Sleep(10 * time.Millisecond)
	postKeyToKakaoInput(input, VK_BACK)
	postTextboxClick(input)
	time.Sleep(10 * time.Millisecond)

	normalized := normalizeKakaoLineEndings(msg)
	pSendMessageW.Call(input, WM_SETTEXT, 0, uintptr(unsafe.Pointer(u16(normalized))))
	time.Sleep(20 * time.Millisecond)
	minusOne := ^uintptr(0)
	pSendMessageW.Call(input, EM_SETSEL, minusOne, minusOne)
	time.Sleep(10 * time.Millisecond)
	postTextboxClick(input)
	time.Sleep(10 * time.Millisecond)
	postEnterToKakaoInput(input)

	fg, _, _ := pGetForegroundWindow.Call()
	focus := kakaoThreadFocus(target)
	logf("direct Kakao send dispatched input=%x class=%q foreground=%x focus=%x focusClass=%q", input, getClassName(input), fg, focus, getClassName(focus))
	return input, true
}

func releaseModifierKeys() {
	inputs := []rawInput{
		keyInput(uint16(VK_CONTROL), 0, KEYEVENTF_KEYUP),
		keyInput(uint16(VK_SHIFT), 0, KEYEVENTF_KEYUP),
		keyInput(uint16(VK_MENU), 0, KEYEVENTF_KEYUP),
		keyInput(uint16(VK_LWIN), 0, KEYEVENTF_KEYUP),
		keyInput(uint16(VK_RWIN), 0, KEYEVENTF_KEYUP),
	}
	sendInputs(inputs)
}

func senderMatchesTarget(sender string) bool {
	s := strings.TrimSpace(sender)
	t := strings.TrimSpace(cfg.TargetChatTitle)
	if s == "" || t == "" {
		return false
	}
	if strings.EqualFold(s, t) {
		return true
	}
	sl, tl := strings.ToLower(s), strings.ToLower(t)
	return strings.Contains(tl, sl) || strings.Contains(sl, tl)
}

func conversationMessagesFromClipboard(raw string) []ChatMessage {
	parsed := parseKakaoClipboard(raw)
	if len(parsed) == 0 {
		logf("clipboard parse produced no messages (%d chars)", len([]rune(raw)))
		return nil
	}
	out := make([]ChatMessage, 0, len(parsed))
	for _, m := range parsed {
		body := strings.TrimSpace(m.Body)
		if body == "" || strings.TrimSpace(m.Sender) == "" {
			continue
		}
		out = append(out, ChatMessage{
			Sender: m.Sender,
			Body:   body,
			At:     m.At,
			Mine:   !senderMatchesTarget(m.Sender),
		})
	}
	if len(out) > 40 {
		out = out[len(out)-40:]
	}
	return out
}

// verifySentMessageBackground reuses the proven outgoing-content matching
// logic but NEVER restores, focuses, or activates the detached Kakao window.
// The EVA-only clipboard command is already used by the fast-toggle path.
func verifySentMessageBackground(target uintptr, msg string) (bool, string, string) {
	return verifySentMessageWithCopy(target, msg, copyChatListTextForegroundFastToggle)
}

// Legacy foreground verification remains available for manual diagnostics,
// but must not run in the hotkey send/return path.
func verifySentMessage(target uintptr, msg string) (bool, string, string) {
	return verifySentMessageWithCopy(target, msg, copyChatListTextForeground)
}

func verifySentMessageWithCopy(target uintptr, msg string, copyTranscript func(uintptr, uintptr) (string, bool)) (bool, string, string) {

	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		logf("send verify: Kakao message list not found target=%x", target)
		return false, "", ""
	}
	want := strings.TrimSpace(msg)
	for attempt := 0; attempt < 4; attempt++ {
		if attempt > 0 {
			time.Sleep(time.Duration(110+attempt*80) * time.Millisecond)
		}
		raw, ok := copyTranscript(target, list)
		if !ok {
			logf("send verify attempt=%d copy failed target=%x list=%x", attempt+1, target, list)
			continue
		}
		parsed := parseKakaoClipboard(raw)
		now := time.Now()
		start := len(parsed) - 8
		if start < 0 {
			start = 0
		}
		for i := len(parsed) - 1; i >= start; i-- {
			m := parsed[i]
			if strings.TrimSpace(m.Body) != want {
				continue
			}
			if senderMatchesTarget(m.Sender) {
				continue
			}
			d := now.Sub(m.At)
			if d < 0 {
				d = -d
			}
			if d <= 3*time.Minute {
				logf("send verify ok attempt=%d sender=%q at=%s", attempt+1, m.Sender, m.At.Format("15:04:05"))
				return true, raw, m.Sender
			}
		}
		logf("send verify attempt=%d: outgoing body not found among %d parsed messages", attempt+1, len(parsed))
	}
	return false, "", ""
}

func foregroundWindowReliable(target uintptr) bool {
	if target == 0 {
		return false
	}
	for i := 0; i < 4; i++ {
		pBringWindowToTop.Call(target)
		pSetForegroundWindow.Call(target)
		time.Sleep(time.Duration(28+i*18) * time.Millisecond)
		fg, _, _ := pGetForegroundWindow.Call()
		if fg == target {
			return true
		}
	}
	fg, _, _ := pGetForegroundWindow.Call()
	logf("send foreground mismatch: wanted=%x got=%x title=%q", target, fg, getWindowText(fg))
	return false
}

func kakaoThreadFocus(target uintptr) uintptr {
	if target == 0 {
		return 0
	}
	tid, _, _ := pGetWindowThreadProcessId.Call(target, 0)
	if tid == 0 {
		return 0
	}
	var gi GUITHREADINFO
	gi.CbSize = uint32(unsafe.Sizeof(gi))
	if r, _, _ := pGetGUIThreadInfo.Call(tid, uintptr(unsafe.Pointer(&gi))); r == 0 {
		return 0
	}
	return gi.HwndFocus
}

func isLikelyComposerFocus(hwnd uintptr) bool {
	if hwnd == 0 || !isProcess(hwnd, "KakaoTalk.exe") {
		return false
	}
	cl := strings.ToLower(strings.TrimSpace(getClassName(hwnd)))
	if strings.Contains(cl, "listcontrol") || strings.Contains(cl, "list") {
		return false
	}
	if strings.Contains(cl, "edit") || strings.Contains(cl, "rich") {
		return true
	}
	// Some Kakao builds wrap the actual composer in an EVA child class. A focus
	// change away from the message list after clicking the lower input region is
	// still a stronger signal than the old unverified fixed-offset click.
	return cl != ""
}

func focusKakaoComposerByClick(target uintptr) (uintptr, bool) {
	if target == 0 {
		return 0, false
	}
	var rc RECT
	if r, _, _ := pGetClientRect.Call(target, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return 0, false
	}
	pt := POINT{X: rc.Left, Y: rc.Top}
	if r, _, _ := pClientToScreen.Call(target, uintptr(unsafe.Pointer(&pt))); r == 0 {
		return 0, false
	}
	w := rc.Right - rc.Left
	h := rc.Bottom - rc.Top
	if w < 180 || h < 160 {
		return 0, false
	}

	// First try a real edit HWND if the current Kakao build exposes one.
	if input := findKakaoComposer(target); input != 0 {
		var ir RECT
		if r, _, _ := pGetWindowRect.Call(input, uintptr(unsafe.Pointer(&ir))); r != 0 && ir.Right > ir.Left && ir.Bottom > ir.Top {
			if clickScreenPoint(ir.Left+(ir.Right-ir.Left)/2, ir.Top+(ir.Bottom-ir.Top)/2) {
				time.Sleep(35 * time.Millisecond)
				f := kakaoThreadFocus(target)
				logf("send composer HWND probe input=%x class=%q focus=%x focusClass=%q", input, getClassName(input), f, getClassName(f))
				if isLikelyComposerFocus(f) {
					return f, true
				}
			}
		}
	}

	base := int32(cfg.InputYOffset)
	offsets := []int32{base, 95, 115, 135, 60, 155}
	seen := map[int32]bool{}
	for _, off := range offsets {
		if off < 28 || off > h-20 || seen[off] {
			continue
		}
		seen[off] = true
		x := pt.X + w/2
		y := pt.Y + h - off
		if !clickScreenPoint(x, y) {
			continue
		}
		time.Sleep(32 * time.Millisecond)
		f := kakaoThreadFocus(target)
		cl := getClassName(f)
		logf("send composer offset probe offset=%d point=%d,%d focus=%x class=%q", off, x, y, f, cl)
		if isLikelyComposerFocus(f) {
			return f, true
		}
	}
	return 0, false
}

func clickScreenPoint(x, y int32) bool {
	var old POINT
	if r, _, _ := pGetCursorPos.Call(uintptr(unsafe.Pointer(&old))); r == 0 {
		return false
	}
	pSetCursorPos.Call(uintptr(x), uintptr(y))
	time.Sleep(7 * time.Millisecond)
	pMouseEvent.Call(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
	pMouseEvent.Call(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
	time.Sleep(12 * time.Millisecond)
	pSetCursorPos.Call(uintptr(old.X), uintptr(old.Y))
	return true
}

func sendCtrlV() {
	inputs := []rawInput{
		keyInput(uint16(VK_CONTROL), 0, 0),
		keyInput(uint16('V'), 0, 0),
		keyInput(uint16('V'), 0, KEYEVENTF_KEYUP),
		keyInput(uint16(VK_CONTROL), 0, KEYEVENTF_KEYUP),
	}
	sendInputs(inputs)
}

func restorePreviousWindow() {
	if previousHwnd != 0 {
		pSetForegroundWindow.Call(previousHwnd)
	}
}

var enumComposerMu sync.Mutex
var enumComposerResult uintptr
var enumComposerBestScore int64
var enumComposerParentRect RECT
var enumComposerParentValid bool

var enumComposerCb = syscall.NewCallback(func(hwnd uintptr, lParam uintptr) uintptr {
	className := strings.ToLower(strings.TrimSpace(getClassName(hwnd)))
	if className == "" || !strings.Contains(className, "edit") {
		return 1
	}
	vis, _, _ := pIsWindowVisible.Call(hwnd)
	if vis == 0 {
		return 1
	}
	var rc RECT
	if r, _, _ := pGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return 1
	}
	w, h := int64(rc.Right-rc.Left), int64(rc.Bottom-rc.Top)
	if w < 100 || h < 20 {
		return 1
	}

	enumComposerMu.Lock()
	parent := enumComposerParentRect
	parentOK := enumComposerParentValid
	enumComposerMu.Unlock()

	// Reject edit controls that are clearly outside the target chat window.
	if parentOK {
		cx := (rc.Left + rc.Right) / 2
		cy := (rc.Top + rc.Bottom) / 2
		if cx < parent.Left || cx > parent.Right || cy < parent.Top || cy > parent.Bottom {
			return 1
		}
	}

	// The message composer is the large, low edit control.  Do not simply take
	// the first RICHEDIT50W: Kakao revisions can expose more than one edit-like
	// child, which was the source of false "send succeeded" results in v1.2.6.
	score := w * h
	if strings.EqualFold(className, "richedit50w") {
		score += 8_000_000_000
	} else if strings.Contains(className, "richedit") {
		score += 4_000_000_000
	}
	if parentOK {
		ph := int64(parent.Bottom - parent.Top)
		pw := int64(parent.Right - parent.Left)
		relBottom := int64(rc.Bottom - parent.Top)
		if relBottom > 0 {
			score += relBottom * 1_000_000
		}
		if ph > 0 && int64(rc.Top-parent.Top) > ph/2 {
			score += 12_000_000_000
		}
		if pw > 0 && w > pw/3 {
			score += 3_000_000_000
		}
	}

	enumComposerMu.Lock()
	if score > enumComposerBestScore {
		enumComposerBestScore = score
		enumComposerResult = hwnd
	}
	enumComposerMu.Unlock()
	return 1
})

func findKakaoComposer(parent uintptr) uintptr {
	if parent == 0 {
		return 0
	}
	var pr RECT
	valid := false
	if r, _, _ := pGetWindowRect.Call(parent, uintptr(unsafe.Pointer(&pr))); r != 0 && pr.Right > pr.Left && pr.Bottom > pr.Top {
		valid = true
	}
	enumComposerMu.Lock()
	enumComposerResult = 0
	enumComposerBestScore = -1
	enumComposerParentRect = pr
	enumComposerParentValid = valid
	enumComposerMu.Unlock()
	pEnumChildWindows.Call(parent, enumComposerCb, 0)
	enumComposerMu.Lock()
	out := enumComposerResult
	enumComposerResult = 0
	enumComposerBestScore = 0
	enumComposerParentValid = false
	enumComposerMu.Unlock()
	return out
}

// clickKakaoComposer performs an actual mouse click inside the selected Kakao
// edit control.  We temporarily move the cursor and restore it immediately so
// the user does not have to chase the pointer after sending.
func clickKakaoComposer(target uintptr) bool {
	input := findKakaoComposer(target)
	if input == 0 {
		logf("Kakao composer HWND not found under target=%x", target)
		return false
	}
	var rc RECT
	if r, _, _ := pGetWindowRect.Call(input, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return false
	}
	w := rc.Right - rc.Left
	h := rc.Bottom - rc.Top
	if w < 40 || h < 18 {
		return false
	}

	pBringWindowToTop.Call(target)
	pSetForegroundWindow.Call(target)
	time.Sleep(35 * time.Millisecond)

	// Click near the center of the real edit surface. Icons/buttons are usually
	// separate sibling HWNDs, so the center is safer than a guessed parent offset.
	x := rc.Left + w/2
	y := rc.Top + h/2
	var old POINT
	pGetCursorPos.Call(uintptr(unsafe.Pointer(&old)))
	pSetCursorPos.Call(uintptr(x), uintptr(y))
	time.Sleep(8 * time.Millisecond)
	pMouseEvent.Call(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
	pMouseEvent.Call(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
	time.Sleep(28 * time.Millisecond)
	pSetCursorPos.Call(uintptr(old.X), uintptr(old.Y))
	logf("composer click hwnd=%x class=%q rect=%d,%d-%d,%d", input, getClassName(input), rc.Left, rc.Top, rc.Right, rc.Bottom)
	return true
}

func clickKakaoInput(hwnd uintptr) bool {
	var rc RECT
	if r, _, _ := pGetClientRect.Call(hwnd, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return false
	}
	pt := POINT{X: rc.Left, Y: rc.Top}
	if r, _, _ := pClientToScreen.Call(hwnd, uintptr(unsafe.Pointer(&pt))); r == 0 {
		return false
	}
	w := rc.Right - rc.Left
	h := rc.Bottom - rc.Top
	if w < 180 || h < 160 {
		return false
	}
	x := pt.X + w/2
	y := pt.Y + h - int32(cfg.InputYOffset)
	var old POINT
	pGetCursorPos.Call(uintptr(unsafe.Pointer(&old)))
	pSetCursorPos.Call(uintptr(x), uintptr(y))
	pMouseEvent.Call(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
	pMouseEvent.Call(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
	time.Sleep(20 * time.Millisecond)
	pSetCursorPos.Call(uintptr(old.X), uintptr(old.Y))
	fg, _, _ := pGetForegroundWindow.Call()
	logf("legacy composer click target=%x point=%d,%d client=%dx%d offset=%d foreground=%x", hwnd, x, y, w, h, cfg.InputYOffset, fg)
	return true
}

type rawInput struct {
	Type uint32
	Pad  uint32
	Data [32]byte
}
type keybdInput struct {
	WVk         uint16
	WScan       uint16
	DwFlags     uint32
	Time        uint32
	DwExtraInfo uintptr
}

func keyInput(vk, scan uint16, flags uint32) rawInput {
	var in rawInput
	in.Type = INPUT_KEYBOARD
	ki := (*keybdInput)(unsafe.Pointer(&in.Data[0]))
	ki.WVk = vk
	ki.WScan = scan
	ki.DwFlags = flags
	return in
}

func sendInputs(inputs []rawInput) {
	if len(inputs) == 0 {
		return
	}
	proc := user32.NewProc("SendInput")
	proc.Call(uintptr(len(inputs)), uintptr(unsafe.Pointer(&inputs[0])), unsafe.Sizeof(rawInput{}))
}

func sendUnicodeText(s string) {
	units := utf16.Encode([]rune(s))
	inputs := make([]rawInput, 0, len(units)*2)
	for _, u := range units {
		inputs = append(inputs, keyInput(0, u, KEYEVENTF_UNICODE))
		inputs = append(inputs, keyInput(0, u, KEYEVENTF_UNICODE|KEYEVENTF_KEYUP))
	}
	sendInputs(inputs)
}

func sendVirtualKey(vk uintptr) {
	inputs := []rawInput{
		keyInput(uint16(vk), 0, 0),
		keyInput(uint16(vk), 0, KEYEVENTF_KEYUP),
	}
	sendInputs(inputs)
}

func sendCtrlComboInput(vk uintptr) {
	inputs := []rawInput{
		keyInput(uint16(VK_CONTROL), 0, 0),
		keyInput(uint16(vk), 0, 0),
		keyInput(uint16(vk), 0, KEYEVENTF_KEYUP),
		keyInput(uint16(VK_CONTROL), 0, KEYEVENTF_KEYUP),
	}
	sendInputs(inputs)
}

func applyHotkey(s string) error {
	mods, vk, err := parseHotkey(s)
	if err != nil {
		return err
	}
	if registeredVK != 0 {
		pUnregisterHotKey.Call(controllerHwnd, ID_HOTKEY)
	}
	r, _, _ := pRegisterHotKey.Call(controllerHwnd, ID_HOTKEY, uintptr(mods|MOD_NOREPEAT), uintptr(vk))
	if r == 0 {
		registeredVK = 0
		return errors.New("RegisterHotKey failed")
	}
	registeredMods, registeredVK = mods, vk
	return nil
}

// activateReplyInput gives keyboard focus to the Bridge reply edit exactly once.
// It deliberately avoids input-queue attachment, synthetic input, delayed refocus,
// and any interaction with another process' keyboard state.
func activateReplyInput() {
	if !replyVisible || replyHwnd == 0 || replyEdit == 0 {
		return
	}

	// v1.7.8: plain Win32 focus only.  No input-queue attachment, no synthetic
	// keyboard input, no activation of another process and no TOPMOST promotion.
	// This path is intentionally indistinguishable from focusing a normal editor.
	pSetForegroundWindow.Call(replyHwnd)
	pSetFocus.Call(replyEdit)
}

func showIncomingHistoryOverlay() {
	if historyHwnd == 0 {
		return
	}
	historyAutoVisible = true
	positionHistoryWindow()
	pSetLayeredWindowAttributes.Call(historyHwnd, 0, uintptr(cfg.OverlayAlpha), LWA_ALPHA)
	pInvalidateRect.Call(historyHwnd, 0, 1)
	pShowWindow.Call(historyHwnd, SW_SHOWNORMAL)
	pSetWindowPos.Call(historyHwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE)
	pKillTimer.Call(controllerHwnd, TIMER_HISTORY_HIDE)
	d := cfg.IncomingOverlayDurationMS
	if d < 500 {
		d = 500
	}
	if d > 10000 {
		d = 10000
	}
	pSetTimer.Call(controllerHwnd, TIMER_HISTORY_HIDE, uintptr(d), 0)
}

func handleShellSignal(hwnd uintptr, code uint32) {
	if time.Now().Before(suppressShellUntil) || code != HSHELL_FLASH {
		return
	}
	if hwnd == 0 || strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return
	}
	root, _, _ := pGetAncestor.Call(hwnd, GA_ROOT)
	if root == 0 {
		root = hwnd
	}
	fg, _, _ := pGetForegroundWindow.Call()
	if !gamingContextAllowsNativeSuppression(fg) {
		return
	}

	// Native-notification blocking is broader than receive routing: while gaming,
	// stop taskbar FLASH from any KakaoTalk window. The Bridge overlay itself only
	// watches the configured target room.
	if cfg.HideNativeTargetNotification && isProcess(root, "KakaoTalk.exe") {
		stopKakaoTaskbarFlash(root)
		hideLikelyKakaoNotificationWindows(findTargetChatWindow())
		now := time.Now()
		if now.Sub(lastShellCaptureAt) >= 1500*time.Millisecond {
			lastShellCaptureAt = now
			logf("native Kakao taskbar FLASH suppressed hwnd=%x; receive source=passive-visual-watch", root)
		}
	}

	target := findTargetChatWindow()
	if target == 0 || fg == target || (root != target && hwnd != target) {
		return
	}

	// The periodic render watcher is the primary source. HSHELL_FLASH is retained
	// only as a zero-input safety net because some Kakao builds fail to expose a
	// renderable offscreen message surface while still asking Windows to flash the
	// target room. We suppress the native flash and immediately replace it with
	// our own overlay; this cannot mark the room read.
	independentRxMu.Lock()
	logFallback := time.Since(lastPassiveAlertAt) >= 850*time.Millisecond
	if logFallback {
		lastPassiveAlertAt = time.Now()
	}
	independentRxMu.Unlock()
	if logFallback {
		logf("bridge receive fallback from target taskbar FLASH target=%x; reactive body resolve queued", target)
	}
	// v1.7.4: do not debounce the actual receive signal.  The pending resolver
	// coalesces duplicate FLASH events safely, while dropping a FLASH here could
	// lose a fast second message on systems where the passive render snapshot is
	// temporarily unavailable.
	startPassiveBodyResolve(target, "taskbar-flash")

	// Also ask the passive watcher for an early sample; the normal 1.8 s polling
	// remains armed even if Kakao never emits a FLASH.
	pKillTimer.Call(controllerHwnd, TIMER_HISTORY_CAPTURE)
	pSetTimer.Call(controllerHwnd, TIMER_HISTORY_CAPTURE, 120, 0)
}

const incomingFallbackBody = "새 메시지 감지됨 · 내용을 읽지 못했습니다"

func popupCapturedSince(t time.Time) bool {
	incomingProbeMu.Lock()
	defer incomingProbeMu.Unlock()
	return !lastPopupCapturedAt.IsZero() && !lastPopupCapturedAt.Before(t)
}

func noteIncomingPopupCaptured() {
	incomingProbeMu.Lock()
	lastPopupCapturedAt = time.Now()
	incomingProbeMu.Unlock()
}

func removeIncomingFallbackHints() {
	historyMu.Lock()
	if len(recentMessages) == 0 {
		historyMu.Unlock()
		return
	}
	out := recentMessages[:0]
	changed := false
	for _, m := range recentMessages {
		if !m.Mine && strings.TrimSpace(m.Body) == incomingFallbackBody {
			changed = true
			continue
		}
		out = append(out, m)
	}
	recentMessages = out
	historyMu.Unlock()
	if changed {
		saveHistory()
	}
}

func showIncomingFallbackHint() {
	now := time.Now()
	incomingProbeMu.Lock()
	if now.Sub(lastFallbackHintAt) < 5*time.Second {
		incomingProbeMu.Unlock()
		return
	}
	lastFallbackHintAt = now
	incomingProbeMu.Unlock()

	logf("shell flash unresolved: showing generic incoming overlay")
	appendRecentMessage(incomingFallbackBody, fmt.Sprintf("shell-flash-unresolved:%d", now.Unix()/5))
}

func startShellFlashProbe(signalAt time.Time, target uintptr) {
	incomingProbeMu.Lock()
	// Kakao flashes/redraws the same chat HWND roughly once a second until the
	// notification is acknowledged. Treat that stream as one receive burst so
	// workers do not cancel one another or fight over the clipboard.
	if incomingProbeActive {
		incomingProbeMu.Unlock()
		return
	}
	incomingProbeActive = true
	incomingProbeGeneration++
	generation := incomingProbeGeneration
	incomingProbeMu.Unlock()

	logf("shell receive probe started target=%x mode=virtual-active-background", target)
	go func() {
		defer func() {
			incomingProbeMu.Lock()
			if incomingProbeGeneration == generation {
				incomingProbeActive = false
			}
			incomingProbeMu.Unlock()
		}()

		// v1.4.6: Kakao can update the detached chat list noticeably later than
		// the first HSHELL_FLASH/REDRAW.  Keep the first probes fast, then taper
		// out instead of giving up after ~1.2 s.  The atomic queued Ctrl+A/C helper
		// below removes the larger source of intermittent failures, while this
		// longer tail covers genuinely late list refreshes without touching the
		// real foreground window.
		delays := []time.Duration{
			120 * time.Millisecond,
			180 * time.Millisecond,
			260 * time.Millisecond,
			400 * time.Millisecond,
			650 * time.Millisecond,
			950 * time.Millisecond,
			1300 * time.Millisecond,
		}
		for attempt, delay := range delays {
			time.Sleep(delay)
			if popupCapturedSince(signalAt) {
				logf("shell receive resolved by native notification target=%x", target)
				return
			}

			// Keep the native popup reader as a cheap first chance, but the actual
			// body source for this Kakao build is the chat list snapshot below.
			scanKakaoPopupsRich()
			if popupCapturedSince(signalAt) {
				logf("shell receive resolved by delayed native notification target=%x", target)
				return
			}

			newCount, ok := captureTargetHistoryVirtualActive(target)
			if ok && newCount > 0 {
				removeIncomingFallbackHints()
				incomingProbeMu.Lock()
				lastReliableHistoryReceiveAt = time.Now()
				incomingProbeMu.Unlock()
				logf("shell receive resolved by virtual-active background history target=%x new=%d attempt=%d", target, newCount, attempt+1)
				if controllerHwnd != 0 {
					pPostMessageW.Call(controllerHwnd, WM_APP_HISTORY_UPDATED, uintptr(newCount), 1)
				}
				return
			}
			if ok {
				logf("shell receive background snapshot had no new message target=%x attempt=%d", target, attempt+1)
			}
		}

		incomingProbeMu.Lock()
		recentSuccess := !lastReliableHistoryReceiveAt.IsZero() && time.Since(lastReliableHistoryReceiveAt) < 2500*time.Millisecond
		incomingProbeMu.Unlock()
		if recentSuccess {
			// Kakao keeps flashing/redrawing the same detached room for a short
			// period even after the message has already been imported.  Do not turn
			// that trailing signal into a false "could not read" overlay.
			logf("shell receive trailing signal suppressed after recent successful history receive target=%x", target)
			return
		}
		logf("shell receive unresolved: reliable background history produced no new message target=%x", target)
		if controllerHwnd != 0 {
			pPostMessageW.Call(controllerHwnd, WM_APP_INCOMING_HINT, 0, 0)
		}
	}()
}

// copyChatListTextVirtualActive recreates the background-control sequence that
// was actually successful in v1.2.0 and in long-standing Kakao PC automation
// code, but isolates it on a dedicated OS thread. Kakao's EVA list checks its
// thread keyboard state instead of trusting a posted VK_CONTROL message. We
// therefore join only this worker thread to Kakao's thread, set Ctrl there,
// and send WM_ACTIVATE only as an internal message. SetForegroundWindow,
// SetFocus and SendInput are never called here, so FF14 keeps the real input
// focus and IME queue.
func copyChatListTextVirtualActive(target, list uintptr) (string, bool) {
	kakaoCopyMu.Lock()
	defer kakaoCopyMu.Unlock()
	if target == 0 || list == 0 {
		return "", false
	}

	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	foregroundBefore, _, _ := pGetForegroundWindow.Call()
	// v1.7.6 hard guard: this legacy reader mutates Kakao-thread keyboard state.
	// It must never run while FF14 owns the foreground, even if an old/unused
	// caller is accidentally re-enabled later.
	if isFF14(foregroundBefore) {
		logf("virtual-active background blocked while FF14 foreground target=%x list=%x", target, list)
		return "", false
	}
	clip := clipboardSnapshotNow()
	oldSeq := clip.seq

	// This is deliberately a message, not SetForegroundWindow. Some Kakao EVA
	// controls ignore background Ctrl+A/C while their internal active flag is
	// false even though the HWND remains perfectly readable.
	pSendMessageW.Call(list, 0x0006, WA_ACTIVE, 0) // WM_ACTIVATE to EVA list only
	time.Sleep(8 * time.Millisecond)

	cleanup := func() {
		// v1.4.4: do NOT send Escape to Kakao here.  A detached Kakao chat
		// treats ESC as close, so the old "clear selection" cleanup could close
		// the target room immediately after a successful background snapshot.
		// Restoring the internal active state is sufficient; leaving the list
		// selection alone is harmless and avoids synthesizing user input.
		if foregroundBefore != target {
			pSendMessageW.Call(list, 0x0006, 0, foregroundBefore) // WA_INACTIVE
		}
	}
	defer cleanup()

	newSeq, copied := selectAllAndCopyReliable(list, oldSeq)
	if !copied {
		fgAfter, _, _ := pGetForegroundWindow.Call()
		logf("virtual-active background: clipboard unchanged target=%x list=%x fgBefore=%x fgAfter=%x", target, list, foregroundBefore, fgAfter)
		return "", false
	}

	raw, ok := readClipboardUnicode()
	restoreClipboardSnapshot(clip, newSeq)
	fgAfter, _, _ := pGetForegroundWindow.Call()
	if fgAfter != foregroundBefore {
		// Diagnostic only: this function never changes the real foreground. If
		// this appears, Kakao/Windows changed it independently and the log proves it.
		logf("virtual-active background: foreground changed externally before=%x after=%x", foregroundBefore, fgAfter)
	}
	if !ok || strings.TrimSpace(raw) == "" {
		return "", false
	}
	return raw, true
}

func captureTargetHistoryVirtualActiveRaw(target uintptr) (string, bool) {
	if target == 0 || strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return "", false
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		return "", false
	}
	return copyChatListTextVirtualActive(target, list)
}

func resetPassiveReceiveState() {
	independentRxMu.Lock()
	passiveRxPrimed = false
	passiveRxNeedsReprime = true
	passiveRxLast = passiveVisualFingerprint{}
	passiveRxTarget = 0
	passiveRxList = 0
	passiveRxPending = false
	passiveRxPendingSince = time.Time{}
	independentRxMu.Unlock()
}

func markPassiveReceiveNeedsReprime(suppressFor time.Duration) {
	independentRxMu.Lock()
	passiveRxNeedsReprime = true
	if suppressFor > 0 {
		until := time.Now().Add(suppressFor)
		if until.After(passiveRxSuppressUntil) {
			passiveRxSuppressUntil = until
		}
	}
	independentRxMu.Unlock()
}

func requestIndependentReceivePoll() {
	if controllerHwnd == 0 || strings.TrimSpace(cfg.TargetChatTitle) == "" || replyVisible {
		return
	}
	fg, _, _ := pGetForegroundWindow.Call()
	target := findTargetChatWindow()
	if target == 0 {
		return
	}

	// v1.7.2: only visiting the actual target chat invalidates the passive
	// baseline. Explorer, a Kakao notification popup, the taskbar, or any other
	// transient foreground must NOT re-prime the watcher: doing so exactly when a
	// message arrives can absorb that new message as the next baseline.
	if fg == target {
		markPassiveReceiveNeedsReprime(0)
		return
	}
	if cfg.OnlyWhenFF14 && !isFF14(fg) {
		return
	}
	if isFF14(fg) {
		noteFF14Foreground()
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		return
	}

	independentRxMu.Lock()
	if independentRxRunning {
		independentRxMu.Unlock()
		return
	}
	independentRxRunning = true
	independentRxMu.Unlock()
	go independentReceiveWorker(target, list)
}

func independentReceiveWorker(target, list uintptr) {
	defer func() {
		independentRxMu.Lock()
		independentRxRunning = false
		independentRxMu.Unlock()
	}()

	// Kakao's custom EVA message-list control often refuses PrintWindow when it is
	// covered by a borderless-fullscreen game. The detached chat's top-level
	// client, however, is a much better rendering boundary because Kakao itself
	// composites the header/message area/input into it. Try the top-level client
	// first, then retain the list-control path only as a fallback.
	fp, ok := capturePassiveReceiveFingerprint(target, list)
	if !ok {
		independentRxMu.Lock()
		now := time.Now()
		if now.Sub(lastIndependentFailLog) >= 12*time.Second {
			lastIndependentFailLog = now
			logf("passive receive visual snapshot unavailable target=%x list=%x; periodic watcher remains armed", target, list)
		}
		independentRxMu.Unlock()
		return
	}

	now := time.Now()
	independentRxMu.Lock()
	if !passiveRxPrimed || passiveRxNeedsReprime || passiveRxTarget != target || passiveRxList != list ||
		now.Before(passiveRxSuppressUntil) || passiveRxLast.Source != fp.Source ||
		passiveRxLast.Width != fp.Width || passiveRxLast.Height != fp.Height {
		passiveRxPrimed = true
		passiveRxNeedsReprime = false
		passiveRxLast = fp
		passiveRxTarget = target
		passiveRxList = list
		passiveRxPending = false
		passiveRxPendingSince = time.Time{}
		independentRxMu.Unlock()
		logf("passive receive baseline primed target=%x list=%x source=%d size=%dx%d", target, list, fp.Source, fp.Width, fp.Height)
		return
	}
	base := passiveRxLast
	diff := passiveFingerprintDistance(base, fp)
	smallPersistent := false
	if diff <= 2 {
		// One or two coarse cells are normally antialiasing/repaint noise.
		passiveRxLast = fp
		passiveRxPending = false
		passiveRxPendingSince = time.Time{}
		independentRxMu.Unlock()
		return
	}
	if diff < 7 {
		// v1.7.2: a very short incoming bubble can affect only 3-6 of the
		// 14x10 fingerprint cells. v1.7.1 immediately folded those cells into the
		// baseline, permanently losing the message. Keep the old baseline and
		// require the small change to survive a second periodic sample instead.
		if !passiveRxPending {
			passiveRxPending = true
			passiveRxPendingSince = now
			independentRxMu.Unlock()
			return
		}
		if now.Sub(passiveRxPendingSince) < 900*time.Millisecond {
			independentRxMu.Unlock()
			return
		}
		smallPersistent = true
	}
	independentRxMu.Unlock()

	// Confirm after Kakao's bubble animation has settled. This path remains
	// completely input-free: no activation, keyboard, clipboard or focus changes.
	time.Sleep(220 * time.Millisecond)
	fp2, ok2 := capturePassiveReceiveFingerprint(target, list)
	if ok2 && fp2.Source == base.Source && fp2.Width == base.Width && fp2.Height == base.Height {
		d2 := passiveFingerprintDistance(base, fp2)
		if smallPersistent {
			// The small change already survived two periodic samples. Require the
			// 220 ms confirmation frame to remain essentially the same rather than
			// applying the old >=7 threshold again.
			stableDelta := passiveFingerprintDistance(fp, fp2)
			if d2 <= 2 {
				independentRxMu.Lock()
				passiveRxLast = fp2
				passiveRxPending = false
				passiveRxPendingSince = time.Time{}
				independentRxMu.Unlock()
				return
			}
			if stableDelta > 3 {
				// Still animating/repainting. Keep the original baseline and pending
				// state so the next low-rate poll can decide.
				return
			}
		} else if d2 < 7 {
			independentRxMu.Lock()
			passiveRxLast = fp2
			passiveRxPending = false
			passiveRxPendingSince = time.Time{}
			independentRxMu.Unlock()
			return
		}
		fp = fp2
		diff = d2
	}

	independentRxMu.Lock()
	passiveRxLast = fp
	passiveRxPending = false
	passiveRxPendingSince = time.Time{}
	// v1.7.4: every confirmed visual transition is a receive event.  Do not
	// suppress the body resolver here: the resolver itself coalesces overlapping
	// work into a pending queue.  The old 850 ms gate could permanently lose a
	// second message after the fingerprint baseline had already advanced to it.
	lastPassiveAlertAt = time.Now()
	independentRxMu.Unlock()

	logf("passive receive detected visual change target=%x diff=%d source=%d no-input=true", target, diff, fp.Source)
	startPassiveBodyResolve(target, "visual-change")
}

// copyChatListTextEVACommandPassive asks Kakao's own EVA transcript control to
// select/copy its text through its private list command. It never activates the
// chat, shares input queues, changes keyboard state, or moves foreground focus.
// This is the preferred body reader after the passive visual watcher has already
// proven that something changed.
func copyChatListTextEVACommandPassive(target, list uintptr) (string, bool) {
	kakaoCopyMu.Lock()
	defer kakaoCopyMu.Unlock()
	if target == 0 || list == 0 {
		return "", false
	}

	fgBefore, _, _ := pGetForegroundWindow.Call()
	clip := clipboardSnapshotNow()
	oldSeq := clip.seq
	newSeq, copied := selectAllAndCopyEVACommand(list, oldSeq)
	if !copied {
		return "", false
	}
	raw, ok := readClipboardUnicode()
	restoreClipboardSnapshot(clip, newSeq)
	fgAfter, _, _ := pGetForegroundWindow.Call()
	if fgAfter != fgBefore {
		logf("reactive EVA transcript: foreground changed externally before=%x after=%x", fgBefore, fgAfter)
	}
	if !ok || strings.TrimSpace(raw) == "" {
		return "", false
	}
	return raw, true
}

func latestIncomingBodies(count int) (string, string) {
	if count < 1 {
		count = 1
	}
	if count > 4 {
		count = 4
	}
	historyMu.Lock()
	defer historyMu.Unlock()
	if len(recentMessages) == 0 {
		return "", ""
	}
	parts := make([]string, 0, count)
	lastSig := ""
	for i := len(recentMessages) - 1; i >= 0 && len(parts) < count; i-- {
		m := recentMessages[i]
		if m.Mine || strings.TrimSpace(m.Body) == "" {
			continue
		}
		if lastSig == "" {
			lastSig = messageSig(m)
		}
		parts = append(parts, strings.TrimSpace(m.Body))
	}
	if len(parts) == 0 {
		return "", ""
	}
	for i, j := 0, len(parts)-1; i < j; i, j = i+1, j-1 {
		parts[i], parts[j] = parts[j], parts[i]
	}
	return strings.Join(parts, "\n"), lastSig
}

func passiveBodyLatestWasJustResolved() bool {
	_, sig := latestIncomingBodies(1)
	if sig == "" {
		return false
	}
	passiveBodyMu.Lock()
	defer passiveBodyMu.Unlock()
	return sig == lastPassiveBodySig && !lastPassiveBodyAt.IsZero() && time.Since(lastPassiveBodyAt) < 8*time.Second
}

func reactiveIncomingDisplayCount(newCount int, historyWasEmpty bool) int {
	if newCount < 1 {
		return 1
	}
	// If there was no persisted baseline, the first full transcript import can
	// classify many historical incoming lines as "new". The visual detector only
	// proved one arrival, so announce just the newest incoming body while still
	// keeping the imported history for the reply panel.
	if historyWasEmpty && newCount > 1 {
		return 1
	}
	return newCount
}

func finishPassiveBodyResolve(body, sig, method string, newCount int) bool {
	body = strings.TrimSpace(body)
	if body == "" || sig == "" {
		return false
	}

	passiveBodyMu.Lock()
	duplicate := sig == lastPassiveBodySig && time.Since(lastPassiveBodyAt) < 10*time.Second
	if !duplicate {
		lastPassiveBodySig = sig
		lastPassiveBodyAt = time.Now()
	}
	passiveBodyMu.Unlock()
	if duplicate {
		return true
	}

	toastText := strings.ReplaceAll(body, "\n", " / ")
	showToast(cfg.TargetChatTitle, abbreviate(toastText, 116))
	if controllerHwnd != 0 {
		pPostMessageW.Call(controllerHwnd, WM_APP_HISTORY_UPDATED, uintptr(newCount), 1)
	}
	logf("reactive incoming body resolved method=%s target=%x new=%d body=%q", method, findTargetChatWindow(), newCount, abbreviate(toastText, 96))
	return true
}

// startPassiveBodyResolve is event-driven, not a polling loop. The 1.8 s visual
// fingerprint watcher stays completely input-free.  v1.7.4 keeps a tiny pending
// queue for confirmed arrival signals so a second message cannot disappear while
// the first message body is still being copied.  Only the short-lived resolver
// touches the transcript, and it stops again as soon as the pending arrivals are
// accounted for.
func startPassiveBodyResolve(target uintptr, trigger string) {
	if target == 0 || strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return
	}

	passiveBodyMu.Lock()
	if !passiveBodyPending {
		passiveBodyPendingSince = time.Now()
	}
	passiveBodyPending = true
	passiveBodyPendingTarget = target
	passiveBodyPendingTrigger = trigger
	if passiveBodyResolving {
		logf("reactive incoming signal queued while resolver busy trigger=%s target=%x", trigger, target)
		passiveBodyMu.Unlock()
		return
	}
	passiveBodyResolving = true
	passiveBodyMu.Unlock()

	go passiveBodyResolveLoop()
}

// passiveBodyResolveLoop serializes event-driven transcript reads.  The important
// invariant is that an arrival signal is never discarded merely because another
// body read is in flight.  A queued signal is re-checked after the current read;
// if the first read already captured both messages, the duplicate/no-new check
// cheaply consumes the trailing signal without showing a false generic alert.
func passiveBodyResolveLoop() {
	for {
		passiveBodyMu.Lock()
		if !passiveBodyPending {
			passiveBodyResolving = false
			passiveBodyMu.Unlock()
			return
		}
		target := passiveBodyPendingTarget
		trigger := passiveBodyPendingTrigger
		pendingSince := passiveBodyPendingSince
		passiveBodyPending = false
		passiveBodyPendingSince = time.Time{}
		passiveBodyMu.Unlock()

		handled := resolvePassiveBodyEvent(target, trigger)
		if !handled {
			// A confirmed visual/FLASH arrival must not be abandoned because Kakao's
			// EVA list happened to reject one copy sequence.  Retry the same pending
			// event twice with a tapering delay.  This is bounded and event-driven;
			// there is still no continuous transcript polling.
			for retry, delay := range []time.Duration{650 * time.Millisecond, 1400 * time.Millisecond} {
				time.Sleep(delay)
				if resolvePassiveBodyEvent(target, fmt.Sprintf("%s-retry-%d", trigger, retry+1)) {
					handled = true
					break
				}
			}
		}

		passiveBodyMu.Lock()
		queuedAgain := passiveBodyPending
		passiveBodyMu.Unlock()
		if !handled && !queuedAgain {
			age := time.Since(pendingSince)
			logf("reactive incoming body unresolved trigger=%s target=%x age=%s; generic fallback shown", trigger, target, age.Round(time.Millisecond))
			showToast(cfg.TargetChatTitle, "새 메시지가 도착했습니다")
		}
		// If another arrival was queued while we were resolving/retrying, loop and
		// account for it before dropping passiveBodyResolving.
	}
}

// resolvePassiveBodyEvent performs one bounded body-resolution pass.  A true
// result means either an actual body was displayed or the signal was proven to
// be a trailing duplicate of a body that was just imported.
func resolvePassiveBodyEvent(target uintptr, trigger string) bool {
	// Detached chat HWNDs can be recreated. Prefer the currently validated target
	// when available so an in-flight event does not fail solely on a stale handle.
	if current := findTargetChatWindow(); current != 0 {
		target = current
	}
	if target == 0 {
		logf("reactive incoming body unavailable trigger=%s reason=target-not-found", trigger)
		return false
	}

	historyMu.Lock()
	historyWasEmpty := len(recentMessages) == 0
	historyMu.Unlock()

	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		logf("reactive incoming body unavailable trigger=%s reason=list-not-found target=%x", trigger, target)
		return false
	}

	// Let Kakao finish laying out the new bubble before requesting transcript text.
	time.Sleep(90 * time.Millisecond)

	// Preferred path: no activation and no input-thread manipulation at all.
	if raw, ok := copyChatListTextEVACommandPassive(target, list); ok {
		newCount := syncHistoryFromClipboard(raw)
		if newCount > 0 {
			displayCount := reactiveIncomingDisplayCount(newCount, historyWasEmpty)
			body, sig := latestIncomingBodies(displayCount)
			if finishPassiveBodyResolve(body, sig, "eva-command-passive", displayCount) {
				return true
			}
		}
		if passiveBodyLatestWasJustResolved() {
			logf("reactive incoming trailing signal already resolved trigger=%s target=%x", trigger, target)
			return true
		}
		logf("reactive EVA transcript copied but no new incoming message trigger=%s target=%x", trigger, target)
	} else {
		logf("reactive EVA transcript copy unavailable trigger=%s target=%x", trigger, target)
	}

	// v1.7.6 strict safety boundary: automatic receive stops here. Do not send
	// even HWND-only synthetic Ctrl+A/C to the Kakao transcript during gameplay.
	// Although PostMessage does not share the game's input queue, Kakao may still
	// interpret keyboard activity on the transcript as user interaction. The
	// private EVA copy command above is the only automatic body reader because it
	// neither activates the room nor injects keyboard/focus state.

	// NEVER escalate an automatic arrival into the old
	// virtual-active reader. That reader sends WM_ACTIVATE to the EVA list and
	// uses AttachThreadInput + SetKeyboardState while waiting for Kakao. Two real
	// user-visible failures match those side effects: an unread room can become
	// read, and restoring a stale 256-key keyboard-state snapshot can clobber a
	// direction key that changed while FF14 was being played. If the passive
	// reader fails, let the bounded pending resolver retry it later; after the
	// retries expire we prefer a generic Bridge alert over touching Kakao/FF14
	// input state or falsely acknowledging the room.
	logf("reactive incoming safe reader exhausted trigger=%s target=%x; unsafe keyboard/activation fallbacks disabled", trigger, target)
	return false
}

func capturePassiveReceiveFingerprint(target, list uintptr) (passiveVisualFingerprint, bool) {
	if target != 0 {
		if fp, ok := captureWindowFingerprint(target, 14, 80, 74, 1); ok {
			return fp, true
		}
	}
	if list != 0 {
		if fp, ok := captureWindowFingerprint(list, 12, 98, 72, 2); ok {
			return fp, true
		}
	}
	return passiveVisualFingerprint{}, false
}

// captureWindowFingerprint asks Kakao to render a window/client into an offscreen
// DIB and reduces only the message-bearing left/center area to a tiny 14x10
// fingerprint. It performs no keyboard/mouse/focus operation and therefore does
// not mark the room read.
func captureWindowFingerprint(hwnd uintptr, topPct, bottomPct, sampleWidthPct int, source uint8) (passiveVisualFingerprint, bool) {
	var out passiveVisualFingerprint
	if hwnd == 0 {
		return out, false
	}
	var rc RECT
	if r, _, _ := pGetClientRect.Call(hwnd, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return out, false
	}
	w, h := rc.Right-rc.Left, rc.Bottom-rc.Top
	if w < 80 || h < 100 || w > 2200 || h > 1800 {
		return out, false
	}

	dc, _, _ := pCreateCompatibleDC.Call(0)
	if dc == 0 {
		return out, false
	}
	defer pDeleteDC.Call(dc)
	bmi := BITMAPINFO{BmiHeader: BITMAPINFOHEADER{
		BiSize: uint32(unsafe.Sizeof(BITMAPINFOHEADER{})), BiWidth: w, BiHeight: -h,
		BiPlanes: 1, BiBitCount: 32, BiCompression: BI_RGB,
	}}
	var bits uintptr
	bmp, _, _ := pCreateDIBSection.Call(dc, uintptr(unsafe.Pointer(&bmi)), DIB_RGB_COLORS, uintptr(unsafe.Pointer(&bits)), 0, 0)
	if bmp == 0 || bits == 0 {
		return out, false
	}
	defer pDeleteObject.Call(bmp)
	old, _, _ := pSelectObject.Call(dc, bmp)
	if old != 0 {
		defer pSelectObject.Call(dc, old)
	}
	buf := unsafe.Slice((*byte)(unsafe.Pointer(bits)), int(w*h*4))
	clear(buf)

	r, _, _ := pPrintWindow.Call(hwnd, dc, PW_CLIENTONLY|PW_RENDERFULLCONTENT)
	if r == 0 {
		// EVA children often do not implement PrintWindow themselves; top-level
		// Kakao windows more commonly honor WM_PRINT and paint their child tree.
		pSendMessageW.Call(hwnd, WM_PRINTCLIENT, dc, PRF_CLIENT|PRF_ERASEBKGND|PRF_CHILDREN)
	}

	y0 := int(h) * topPct / 100
	y1 := int(h) * bottomPct / 100
	if y0 < 0 {
		y0 = 0
	}
	if y1 > int(h) {
		y1 = int(h)
	}
	if y1-y0 < 80 {
		y0 = int(h) / 8
		y1 = int(h) * 7 / 8
	}
	sampleW := int(w) * sampleWidthPct / 100
	if sampleW < 80 || sampleW > int(w) {
		sampleW = int(w)
	}

	const gx, gy = 14, 10
	minCell, maxCell := uint16(0xffff), uint16(0)
	for yy := 0; yy < gy; yy++ {
		for xx := 0; xx < gx; xx++ {
			var sr, sg, sb, n int
			for sy := 1; sy <= 3; sy++ {
				py := y0 + ((yy*3+sy)*(y1-y0))/(gy*3+1)
				if py >= int(h) {
					py = int(h) - 1
				}
				for sx := 1; sx <= 4; sx++ {
					px := ((xx*4 + sx) * sampleW) / (gx*4 + 1)
					if px >= int(w) {
						px = int(w) - 1
					}
					off := (py*int(w) + px) * 4
					if off+2 >= len(buf) {
						continue
					}
					sb += int(buf[off+0])
					sg += int(buf[off+1])
					sr += int(buf[off+2])
					n++
				}
			}
			if n == 0 {
				continue
			}
			r5, g5, b5 := (sr/n)>>3, (sg/n)>>3, (sb/n)>>3
			cell := uint16((r5 << 10) | (g5 << 5) | b5)
			idx := yy*gx + xx
			out.Cells[idx] = cell
			if cell < minCell {
				minCell = cell
			}
			if cell > maxCell {
				maxCell = cell
			}
		}
	}

	// A constant/near-black render means Kakao did not actually paint this
	// offscreen request. Let the caller fall back to the other rendering boundary.
	if maxCell == minCell || int(maxCell)-int(minCell) < 3 {
		return passiveVisualFingerprint{}, false
	}
	out.Width, out.Height, out.Source, out.Valid = w, h, source, true
	return out, true
}

func passiveFingerprintDistance(a, b passiveVisualFingerprint) int {
	if !a.Valid || !b.Valid || a.Source != b.Source || a.Width != b.Width || a.Height != b.Height {
		return 140
	}
	diff := 0
	abs := func(v int) int {
		if v < 0 {
			return -v
		}
		return v
	}
	for i := range a.Cells {
		av, bv := a.Cells[i], b.Cells[i]
		ar, ag, ab := int((av>>10)&31), int((av>>5)&31), int(av&31)
		br, bg, bb := int((bv>>10)&31), int((bv>>5)&31), int(bv&31)
		if abs(ar-br)+abs(ag-bg)+abs(ab-bb) >= 5 {
			diff++
		}
	}
	return diff
}

func captureTargetHistoryVirtualActive(target uintptr) (int, bool) {
	if target == 0 || strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return 0, false
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		logf("virtual-active background: Kakao message list not found target=%x", target)
		return 0, false
	}
	raw, ok := copyChatListTextVirtualActive(target, list)
	if !ok {
		return 0, false
	}
	newCount := syncHistoryFromClipboard(raw)
	logf("virtual-active background history ok: %d chars new=%d target=%x fg=%x", len([]rune(raw)), newCount, target, func() uintptr { v, _, _ := pGetForegroundWindow.Call(); return v }())
	return newCount, true
}

func noteFF14Foreground() {
	gamingContextMu.Lock()
	lastFF14ForegroundAt = time.Now()
	gamingContextMu.Unlock()
}

func gamingContextAllowsNativeSuppression(fg uintptr) bool {
	if target := findTargetChatWindow(); target != 0 && fg == target {
		return false
	}
	if !cfg.OnlyWhenFF14 {
		return true
	}
	if isFF14(fg) {
		noteFF14Foreground()
		return true
	}
	gamingContextMu.Lock()
	last := lastFF14ForegroundAt
	gamingContextMu.Unlock()
	// Kakao/Explorer can own foreground for a split second while producing a
	// popup or taskbar transition. Preserve the gaming context through that race.
	return !last.IsZero() && time.Since(last) <= 3*time.Second
}

func nativeNotificationSuppressionActive() bool {
	if !cfg.HideNativeTargetNotification || strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return false
	}
	fg, _, _ := pGetForegroundWindow.Call()
	return gamingContextAllowsNativeSuppression(fg)
}

func stopKakaoTaskbarFlash(hwnd uintptr) {
	if hwnd == 0 {
		return
	}
	info := FLASHWINFO{CbSize: uint32(unsafe.Sizeof(FLASHWINFO{})), Hwnd: hwnd, DwFlags: FLASHW_STOP}
	pFlashWindowEx.Call(uintptr(unsafe.Pointer(&info)))
}

// suppressNativeKakaoPopup is intentionally content-blind. Kakao's popup body
// is not reliable enough to be our source of truth, so while gaming we hide
// any compact Kakao notification window and let the independent transcript
// watcher decide whether a new target-room message exists.
func suppressNativeKakaoPopup(hwnd uintptr) {
	if hwnd == 0 || !nativeNotificationSuppressionActive() {
		return
	}
	root, _, _ := pGetAncestor.Call(hwnd, GA_ROOT)
	if root == 0 {
		root = hwnd
	}
	target := findTargetChatWindow()
	if !isLikelyKakaoNativeNotification(root, target, true) {
		return
	}
	pShowWindow.Call(root, SW_HIDE)
	startNativePopupHideBurst(root)
	logf("native Kakao compact popup suppressed hwnd=%x class=%q", root, getClassName(root))
}

func startNativePopupHideBurst(root uintptr) {
	if root == 0 {
		return
	}
	nativeSuppressMu.Lock()
	if nativeSuppressing[root] {
		nativeSuppressMu.Unlock()
		return
	}
	nativeSuppressing[root] = true
	nativeSuppressMu.Unlock()
	go func() {
		defer func() {
			nativeSuppressMu.Lock()
			delete(nativeSuppressing, root)
			nativeSuppressMu.Unlock()
		}()
		// Kakao animates/re-shows the same popup HWND for a few hundred ms. Hide
		// that one HWND a handful of times rather than scanning all windows at high
		// frequency forever.
		for _, d := range []time.Duration{0, 30, 70, 140, 260, 430, 700} {
			if d > 0 {
				time.Sleep(d)
			}
			if !nativeNotificationSuppressionActive() || !isProcess(root, "KakaoTalk.exe") {
				return
			}
			target := findTargetChatWindow()
			if !isLikelyKakaoNativeNotification(root, target, false) {
				return
			}
			pShowWindow.Call(root, SW_HIDE)
		}
	}()
}

func suppressNativeKakaoPopupsWhileGaming() {
	if !nativeNotificationSuppressionActive() {
		return
	}
	// Do not call FlashWindowEx here. v1.5.0 did that every timer tick and the
	// resulting REDRAW fed the shell hook indefinitely. FLASH is stopped only in
	// handleShellSignal when Windows actually reports one.
	hideLikelyKakaoNotificationWindows(findTargetChatWindow())
}

func isLikelyKakaoNativeNotification(hwnd, target uintptr, requireVisible bool) bool {
	if hwnd == 0 || hwnd == target || !isProcess(hwnd, "KakaoTalk.exe") {
		return false
	}
	if findChildByClass(hwnd, "EVA_VH_ListControl_Dblclk") != 0 {
		return false
	}
	if requireVisible {
		vis, _, _ := pIsWindowVisible.Call(hwnd)
		if vis == 0 {
			return false
		}
	}
	var wr RECT
	if r, _, _ := pGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&wr))); r == 0 {
		return false
	}
	w, h := wr.Right-wr.Left, wr.Bottom-wr.Top
	if w < 80 || h < 24 || w > 900 || h > 360 {
		return false
	}

	// Known Kakao desktop-notification windows. Class-based matching is
	// intentionally independent of monitor coordinates; v1.7.1 could miss a
	// popup when Kakao placed it on a monitor/edge different from FF14's rect.
	cls := getClassName(hwnd)
	if cls == "EVA_Window_Dblclk" || cls == "KakaoTalkShadowWndClass" {
		return true
	}

	// Keep the old geometry rule as a compatibility fallback for future/older
	// Kakao popup classes.
	rc := referenceRect()
	return wr.Right >= rc.Right-1000 && wr.Bottom >= rc.Bottom-650
}

func hideLikelyKakaoNotificationWindows(target uintptr) {
	for _, hwnd := range enumTopWindows() {
		if hwnd == 0 || !isProcess(hwnd, "KakaoTalk.exe") {
			continue
		}

		// v1.7.2: STOP is idempotent and HSHELL_REDRAW is ignored by our shell
		// handler, so periodically clearing Kakao's flash state no longer creates
		// the v1.5.0 feedback loop. This closes the gap when HSHELL_FLASH itself is
		// missed/coalesced.
		stopKakaoTaskbarFlash(hwnd)

		if !isLikelyKakaoNativeNotification(hwnd, target, true) {
			continue
		}
		var wr RECT
		pGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&wr)))
		w, h := wr.Right-wr.Left, wr.Bottom-wr.Top
		pShowWindow.Call(hwnd, SW_HIDE)
		startNativePopupHideBurst(hwnd)
		logf("native Kakao popup hidden hwnd=%x class=%q size=%dx%d", hwnd, getClassName(hwnd), w, h)
	}
}

func getClassName(hwnd uintptr) string {
	buf := make([]uint16, 256)
	r, _, _ := pGetClassNameW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
	if r == 0 {
		return ""
	}
	return syscall.UTF16ToString(buf[:r])
}

var enumClassCb = syscall.NewCallback(func(hwnd uintptr, lParam uintptr) uintptr {
	enumClassMu.Lock()
	need := enumClassNeedle
	enumClassMu.Unlock()
	if need == "" {
		return 1
	}
	if getClassName(hwnd) == need {
		enumClassMu.Lock()
		if enumClassResult == 0 {
			enumClassResult = hwnd
		}
		enumClassMu.Unlock()
		return 0
	}
	return 1
})

func findChildByClass(parent uintptr, className string) uintptr {
	if parent == 0 {
		return 0
	}
	enumClassMu.Lock()
	enumClassNeedle = className
	enumClassResult = 0
	enumClassMu.Unlock()
	pEnumChildWindows.Call(parent, enumClassCb, 0)
	enumClassMu.Lock()
	out := enumClassResult
	enumClassNeedle = ""
	enumClassResult = 0
	enumClassMu.Unlock()
	return out
}

func pressCtrlCombo(hwnd uintptr, key uintptr) {
	if hwnd == 0 {
		return
	}
	// Never use AttachThreadInput or SetKeyboardState for automatic capture.
	// Send the modifier sequence only to Kakao's own message-list HWND.
	keyUpLP := uintptr(1 | (1 << 30) | (1 << 31))
	pPostMessageW.Call(hwnd, WM_KEYDOWN, VK_CONTROL, 1)
	time.Sleep(3 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_KEYDOWN, key, 1)
	time.Sleep(6 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_KEYUP, key, keyUpLP)
	time.Sleep(3 * time.Millisecond)
	pPostMessageW.Call(hwnd, WM_KEYUP, VK_CONTROL, keyUpLP)
}

// selectAllAndCopyReliable performs Ctrl+A then Ctrl+C as one atomic Kakao
// input-queue operation. Kakao's EVA list expects keyboard messages to arrive
// through its queued input path; SendMessage bypasses that path and can leave
// the clipboard unchanged. Keep this goroutine pinned to one OS thread, attach
// only to Kakao's UI thread, assert Ctrl in the shared keyboard state, post A/C,
// and do not restore/detach until Kakao has actually changed the clipboard.
// v1.7.6: this helper is explicit/manual-only; automatic receive must never call it while FF14 is active.
func selectAllAndCopyReliable(hwnd uintptr, oldSeq uint32) (uint32, bool) {
	if hwnd == 0 {
		return oldSeq, false
	}
	// v1.7.6 absolute safety gate: this helper snapshots/restores thread keyboard
	// state. Never allow it to run while FF14 is the real foreground, regardless
	// of which caller reached it. Explicit Kakao foreground paths remain allowed.
	if fg, _, _ := pGetForegroundWindow.Call(); isFF14(fg) {
		logf("attached keyboard-state copy blocked while FF14 foreground hwnd=%x", hwnd)
		return oldSeq, false
	}

	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	targetThread, _, _ := pGetWindowThreadProcessId.Call(hwnd, 0)
	curThread, _, _ := pGetCurrentThreadId.Call()
	if targetThread == 0 || curThread == 0 {
		return oldSeq, false
	}

	attached := false
	if targetThread != curThread {
		if r, _, _ := pAttachThreadInput.Call(curThread, targetThread, 1); r == 0 {
			return oldSeq, false
		}
		attached = true
	}
	defer func() {
		if attached {
			pAttachThreadInput.Call(curThread, targetThread, 0)
		}
	}()

	oldState := make([]byte, 256)
	if r, _, _ := pGetKeyboardState.Call(uintptr(unsafe.Pointer(&oldState[0]))); r == 0 {
		return oldSeq, false
	}
	newState := make([]byte, 256)
	copy(newState, oldState)
	newState[VK_CONTROL] |= 0x80
	if r, _, _ := pSetKeyboardState.Call(uintptr(unsafe.Pointer(&newState[0]))); r == 0 {
		return oldSeq, false
	}
	defer pSetKeyboardState.Call(uintptr(unsafe.Pointer(&oldState[0])))

	keyUpLP := uintptr(1 | (1 << 30) | (1 << 31))
	postKey := func(vk uintptr) bool {
		if r, _, _ := pPostMessageW.Call(hwnd, WM_KEYDOWN, vk, 1); r == 0 {
			return false
		}
		time.Sleep(5 * time.Millisecond)
		if r, _, _ := pPostMessageW.Call(hwnd, WM_KEYUP, vk, keyUpLP); r == 0 {
			return false
		}
		return true
	}

	// Let the attached queue observe Ctrl before posting the shortcuts. Keep Ctrl
	// asserted across both shortcuts so delayed Kakao queue processing cannot see
	// an unmodified A or C.
	time.Sleep(4 * time.Millisecond)
	if !postKey(VK_A) {
		return oldSeq, false
	}
	time.Sleep(16 * time.Millisecond)
	if !postKey(VK_C) {
		return oldSeq, false
	}

	// Crucially, stay attached with Ctrl asserted until the copy really occurs.
	// Kakao occasionally processes the posted shortcut tens or hundreds of ms
	// later while the game is busy.
	for i := 0; i < 55; i++ { // up to ~440 ms
		seq, _, _ := pGetClipboardSequenceNumber.Call()
		newSeq := uint32(seq)
		if newSeq != oldSeq {
			time.Sleep(4 * time.Millisecond)
			return newSeq, true
		}
		time.Sleep(8 * time.Millisecond)
	}
	return oldSeq, false
}

func selectAllAndCopyEVACommand(hwnd uintptr, oldSeq uint32) (uint32, bool) {
	if hwnd == 0 {
		return oldSeq, false
	}
	// EVA private list command observed in long-standing Kakao PC automation:
	// 0x65 selects all, then 0x64 copies the selected transcript.  v1.7.3+ may
	// invoke it only after a confirmed arrival signal to resolve the message body;
	// it is never part of the passive 1.8 s periodic watcher itself.
	if r, _, _ := pPostMessageW.Call(hwnd, 0x07E9, 0x65, 0); r == 0 {
		return oldSeq, false
	}
	time.Sleep(500 * time.Millisecond)
	if r, _, _ := pPostMessageW.Call(hwnd, 0x07E9, 0x64, 0); r == 0 {
		return oldSeq, false
	}
	for i := 0; i < 80; i++ { // up to ~800 ms
		seq, _, _ := pGetClipboardSequenceNumber.Call()
		newSeq := uint32(seq)
		if newSeq != oldSeq {
			time.Sleep(4 * time.Millisecond)
			return newSeq, true
		}
		time.Sleep(10 * time.Millisecond)
	}
	return oldSeq, false
}

func deselectChatList(hwnd uintptr) {
	if hwnd == 0 {
		return
	}
	lp := uintptr(uint32(5) | (uint32(30) << 16))
	pPostMessageW.Call(hwnd, WM_LBUTTONDOWN, 1, lp)
	pPostMessageW.Call(hwnd, WM_LBUTTONUP, 0, lp)
}

type clipboardSnapshot struct {
	text    string
	hadText bool
	count   int
	seq     uint32
}

func clipboardSnapshotNow() clipboardSnapshot {
	s := clipboardSnapshot{}
	seq, _, _ := pGetClipboardSequenceNumber.Call()
	s.seq = uint32(seq)
	cnt, _, _ := pCountClipboardFormats.Call()
	s.count = int(cnt)
	if t, ok := readClipboardUnicode(); ok {
		s.text = t
		s.hadText = true
	}
	return s
}

func readClipboardUnicode() (string, bool) {
	for i := 0; i < 8; i++ {
		if r, _, _ := pOpenClipboard.Call(0); r != 0 {
			defer pCloseClipboard.Call()
			avail, _, _ := pIsClipboardFormatAvailable.Call(CF_UNICODETEXT)
			if avail == 0 {
				return "", false
			}
			h, _, _ := pGetClipboardData.Call(CF_UNICODETEXT)
			if h == 0 {
				return "", false
			}
			ptr, _, _ := pGlobalLock.Call(h)
			if ptr == 0 {
				return "", false
			}
			sz, _, _ := pGlobalSize.Call(h)
			max := int(sz / 2)
			if max <= 0 || max > 2_000_000 {
				max = 2_000_000
			}
			u := unsafe.Slice((*uint16)(unsafe.Pointer(ptr)), max)
			n := 0
			for n < len(u) && u[n] != 0 {
				n++
			}
			out := syscall.UTF16ToString(u[:n])
			pGlobalUnlock.Call(h)
			return out, true
		}
		time.Sleep(8 * time.Millisecond)
	}
	return "", false
}

func setClipboardUnicode(text string) bool {
	enc := utf16.Encode([]rune(text + "\x00"))
	bytes := uintptr(len(enc) * 2)
	h, _, _ := pGlobalAlloc.Call(GMEM_MOVEABLE, bytes)
	if h == 0 {
		return false
	}
	ptr, _, _ := pGlobalLock.Call(h)
	if ptr == 0 {
		return false
	}
	dst := unsafe.Slice((*uint16)(unsafe.Pointer(ptr)), len(enc))
	copy(dst, enc)
	pGlobalUnlock.Call(h)
	for i := 0; i < 8; i++ {
		if r, _, _ := pOpenClipboard.Call(0); r != 0 {
			pEmptyClipboard.Call()
			r2, _, _ := pSetClipboardData.Call(CF_UNICODETEXT, h)
			pCloseClipboard.Call()
			return r2 != 0
		}
		time.Sleep(8 * time.Millisecond)
	}
	return false
}

func clearClipboard() {
	for i := 0; i < 5; i++ {
		if r, _, _ := pOpenClipboard.Call(0); r != 0 {
			pEmptyClipboard.Call()
			pCloseClipboard.Call()
			return
		}
		time.Sleep(6 * time.Millisecond)
	}
}

func restoreClipboardSnapshot(s clipboardSnapshot, ourSeq uint32) {
	seq, _, _ := pGetClipboardSequenceNumber.Call()
	if ourSeq != 0 && uint32(seq) != ourSeq {
		// Something else changed the clipboard after our copy; never overwrite it.
		return
	}
	if s.hadText {
		setClipboardUnicode(s.text)
	} else if s.count == 0 {
		clearClipboard()
	}
}

func copyChatListText(target, list uintptr, allowForeground bool) (string, bool) {
	kakaoCopyMu.Lock()
	defer kakaoCopyMu.Unlock()
	if target == 0 || list == 0 {
		return "", false
	}
	clip := clipboardSnapshotNow()
	oldSeq := clip.seq

	// First try HWND-only background key delivery. This never shares FF14 keyboard state.
	pressCtrlCombo(list, VK_A)
	time.Sleep(10 * time.Millisecond)
	pressCtrlCombo(list, VK_C)
	var newSeq uint32
	for i := 0; i < 12; i++ {
		seq, _, _ := pGetClipboardSequenceNumber.Call()
		newSeq = uint32(seq)
		if newSeq != oldSeq {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}

	if newSeq == oldSeq && allowForeground {
		prev, _, _ := pGetForegroundWindow.Call()
		minimized, _, _ := pIsIconic.Call(target)
		if minimized != 0 {
			pShowWindow.Call(target, SW_RESTORE)
		}
		pSendMessageW.Call(target, 0x0006, WA_ACTIVE, 0) // WM_ACTIVATE
		pSetForegroundWindow.Call(target)
		time.Sleep(20 * time.Millisecond)
		pressCtrlCombo(list, VK_A)
		time.Sleep(10 * time.Millisecond)
		pressCtrlCombo(list, VK_C)
		for i := 0; i < 14; i++ {
			seq, _, _ := pGetClipboardSequenceNumber.Call()
			newSeq = uint32(seq)
			if newSeq != oldSeq {
				break
			}
			time.Sleep(10 * time.Millisecond)
		}
		deselectChatList(list)
		if minimized != 0 {
			pShowWindow.Call(target, SW_MINIMIZE)
		}
		if prev != 0 {
			pSetForegroundWindow.Call(prev)
		}
	}
	if newSeq == oldSeq {
		return "", false
	}
	raw, ok := readClipboardUnicode()
	restoreClipboardSnapshot(clip, newSeq)
	if !ok || strings.TrimSpace(raw) == "" {
		return "", false
	}
	return raw, true
}

// copyChatListTextForeground performs the one manual/explicit snapshot used by
// the toggle key.  Unlike the automatic monitor this path may briefly activate
// Kakao, because the EVA list only produces a dependable full selection/copy
// when its window is active and its thread sees Ctrl as pressed.
func copyChatListTextForeground(target, list uintptr) (string, bool) {
	kakaoCopyMu.Lock()
	defer kakaoCopyMu.Unlock()
	if target == 0 || list == 0 {
		return "", false
	}

	// This function is used only for an explicit user action (open reply/history)
	// and outgoing verification. Prefer real foreground keyboard delivery here:
	// it is dramatically more reliable than trying to synthesize Ctrl state into
	// EVA's private queue, and automatic receive never calls this function.
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	clip := clipboardSnapshotNow()
	oldSeq := clip.seq
	prev, _, _ := pGetForegroundWindow.Call()
	minimized, _, _ := pIsIconic.Call(target)
	if minimized != 0 {
		pShowWindow.Call(target, SW_RESTORE)
	}

	targetThread, _, _ := pGetWindowThreadProcessId.Call(target, 0)
	curThread, _, _ := pGetCurrentThreadId.Call()
	attached := false
	if targetThread != 0 && curThread != 0 && targetThread != curThread {
		if r, _, _ := pAttachThreadInput.Call(curThread, targetThread, 1); r != 0 {
			attached = true
		}
	}

	cleanupFocus := func() {
		if attached {
			pAttachThreadInput.Call(curThread, targetThread, 0)
		}
		if minimized != 0 {
			pShowWindow.Call(target, SW_MINIMIZE)
		}
		if prev != 0 && prev != target {
			pSetForegroundWindow.Call(prev)
		}
	}

	pSendMessageW.Call(target, 0x0006, WA_ACTIVE, 0) // WM_ACTIVATE
	pSetForegroundWindow.Call(target)
	time.Sleep(35 * time.Millisecond)
	if attached {
		pSetFocus.Call(list)
	}
	// Give the custom EVA list an internal focus/selection anchor without using
	// ESC (which closes detached Kakao rooms).
	lp := uintptr(uint32(12) | (uint32(28) << 16))
	pPostMessageW.Call(list, WM_LBUTTONDOWN, 1, lp)
	pPostMessageW.Call(list, WM_LBUTTONUP, 0, lp)
	time.Sleep(20 * time.Millisecond)
	if attached {
		pSetFocus.Call(list)
	}

	sendCtrlComboInput(VK_A)
	time.Sleep(28 * time.Millisecond)
	sendCtrlComboInput(VK_C)

	var newSeq uint32
	for i := 0; i < 90; i++ { // up to ~900 ms
		seq, _, _ := pGetClipboardSequenceNumber.Call()
		newSeq = uint32(seq)
		if newSeq != oldSeq {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}

	// A few Kakao builds still require the legacy attached-state queue path.
	// Keep it only as an explicit/manual fallback, never in automatic receive.
	if newSeq == oldSeq {
		if ns, copied := selectAllAndCopyReliable(list, oldSeq); copied {
			newSeq = ns
		}
	}

	// v1.7.2 explicit-action last resort: older/current EVA list builds have an
	// internal select/copy command path (0x07E9, 0x65 -> 0x64). It does not run
	// during passive receive; at this point the user has already invoked the
	// reply/history UI (or an outgoing verification), so using it only when both
	// normal copy paths failed cannot create a new automatic-read behavior.
	if newSeq == oldSeq {
		if ns, copied := selectAllAndCopyEVACommand(list, oldSeq); copied {
			newSeq = ns
			logf("foreground transcript recovered by EVA command fallback target=%x list=%x", target, list)
		}
	}

	if attached {
		pAttachThreadInput.Call(curThread, targetThread, 0)
		attached = false
	}
	if newSeq == oldSeq {
		cleanupFocus()
		logf("foreground transcript copy failed after SendInput+queue fallback target=%x list=%x", target, list)
		return "", false
	}

	raw, ok := readClipboardUnicode()
	restoreClipboardSnapshot(clip, newSeq)
	cleanupFocus()
	if !ok || strings.TrimSpace(raw) == "" {
		return "", false
	}
	return raw, true
}

type parsedKakaoMessage struct {
	Sender string
	Body   string
	At     time.Time
}

var kakaoDateRx = regexp.MustCompile(`^\s*(\d{4})년\s+(\d{1,2})월\s+(\d{1,2})일(?:\s+[일월화수목금토]요일)?\s*$`)
var kakaoMsgRx = regexp.MustCompile(`^\[(.+?)\]\s+\[(오전|오후)\s*(\d{1,2}):(\d{2})\](?:\s*(.*))?$`)

func parseKakaoClipboard(raw string) []parsedKakaoMessage {
	lines := strings.Split(strings.ReplaceAll(raw, "\r\n", "\n"), "\n")
	now := time.Now()
	currentDate := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
	var out []parsedKakaoMessage
	var sender string
	var at time.Time
	var body []string
	flush := func() {
		if sender != "" && !at.IsZero() {
			out = append(out, parsedKakaoMessage{Sender: strings.TrimSpace(sender), Body: strings.TrimSpace(strings.Join(body, "\n")), At: at})
		}
		sender = ""
		at = time.Time{}
		body = nil
	}
	for _, line := range lines {
		line = strings.TrimRight(line, "\r")
		if m := kakaoDateRx.FindStringSubmatch(line); m != nil {
			flush()
			y, _ := strconv.Atoi(m[1])
			mo, _ := strconv.Atoi(m[2])
			d, _ := strconv.Atoi(m[3])
			currentDate = time.Date(y, time.Month(mo), d, 0, 0, 0, 0, now.Location())
			continue
		}
		if m := kakaoMsgRx.FindStringSubmatch(line); m != nil {
			flush()
			sender = strings.TrimSpace(m[1])
			h, _ := strconv.Atoi(m[3])
			mi, _ := strconv.Atoi(m[4])
			if m[2] == "오후" && h < 12 {
				h += 12
			}
			if m[2] == "오전" && h == 12 {
				h = 0
			}
			at = time.Date(currentDate.Year(), currentDate.Month(), currentDate.Day(), h, mi, 0, 0, now.Location())
			if len(m) > 5 && m[5] != "" {
				body = append(body, m[5])
			}
			continue
		}
		if sender != "" {
			body = append(body, line)
		}
	}
	flush()
	return out
}

func messageSig(m ChatMessage) string {
	return fmt.Sprintf("%s|%s|%s", strings.TrimSpace(m.Sender), m.At.Local().Format("2006-01-02 15:04"), strings.TrimSpace(m.Body))
}

func sameChatMessage(a, b ChatMessage) bool {
	return strings.EqualFold(strings.TrimSpace(a.Sender), strings.TrimSpace(b.Sender)) &&
		a.At.Local().Format("2006-01-02 15:04") == b.At.Local().Format("2006-01-02 15:04") &&
		strings.TrimSpace(a.Body) == strings.TrimSpace(b.Body)
}

func sequenceEqual(a, b []ChatMessage) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if !sameChatMessage(a[i], b[i]) {
			return false
		}
	}
	return true
}

// mergeParsedHistory keeps a rolling history instead of replacing it with every
// clipboard snapshot. Kakao can expose only part of the list on a given capture;
// replacing the history made v1.2.2 show one stale block plus the newest message.
func mergeParsedHistory(filtered []ChatMessage) int {
	if len(filtered) == 0 {
		return 0
	}
	if len(filtered) > 40 {
		filtered = filtered[len(filtered)-40:]
	}

	historyMu.Lock()
	defer historyMu.Unlock()

	// Remove synthetic legacy entries that came from notification/UI dumps.
	old := make([]ChatMessage, 0, len(recentMessages))
	for _, m := range recentMessages {
		if strings.TrimSpace(m.Sender) != "" && strings.TrimSpace(m.Body) != "" {
			old = append(old, m)
		}
	}

	if len(old) == 0 {
		recentMessages = append([]ChatMessage(nil), filtered...)
		incoming := 0
		for _, m := range filtered {
			if !m.Mine {
				incoming++
			}
		}
		return incoming
	}

	// Find the longest suffix of our stored history inside the newly captured
	// sequence. Everything after that overlap is genuinely new.
	bestK, bestI := 0, -1
	maxK := len(old)
	if len(filtered) < maxK {
		maxK = len(filtered)
	}
	for k := maxK; k >= 1 && bestK == 0; k-- {
		suffix := old[len(old)-k:]
		for i := 0; i+k <= len(filtered); i++ {
			if sequenceEqual(suffix, filtered[i:i+k]) {
				bestK, bestI = k, i
				break
			}
		}
	}

	added := make([]ChatMessage, 0)
	if bestK > 0 {
		added = append(added, filtered[bestI+bestK:]...)
	} else {
		// No overlap usually means Kakao returned a shorter/new viewport. Append
		// only messages at/after the last known minute and avoid exact repeats.
		lastAt := old[len(old)-1].At
		for _, m := range filtered {
			if m.At.Before(lastAt.Add(-1 * time.Minute)) {
				continue
			}
			dup := false
			for i := len(old) - 1; i >= 0 && i >= len(old)-12; i-- {
				if sameChatMessage(old[i], m) {
					dup = true
					break
				}
			}
			if !dup {
				added = append(added, m)
			}
		}
	}

	if len(added) > 0 {
		old = append(old, added...)
	}
	if len(old) > 40 {
		old = old[len(old)-40:]
	}
	recentMessages = append([]ChatMessage(nil), old...)
	incoming := 0
	for _, m := range added {
		if !m.Mine {
			incoming++
		}
	}
	return incoming
}

func targetMessagesFromClipboard(raw string) []ChatMessage {
	parsed := parseKakaoClipboard(raw)
	if len(parsed) == 0 {
		logf("clipboard parse produced no messages (%d chars)", len([]rune(raw)))
		return nil
	}
	targetName := strings.TrimSpace(cfg.TargetChatTitle)
	var filtered []ChatMessage
	for _, m := range parsed {
		if targetName != "" && strings.EqualFold(strings.TrimSpace(m.Sender), targetName) {
			filtered = append(filtered, ChatMessage{Sender: m.Sender, Body: m.Body, At: m.At})
		}
	}
	if len(filtered) == 0 {
		// Room titles can contain decoration while the sender name is shorter.
		for _, m := range parsed {
			if strings.Contains(strings.ToLower(targetName), strings.ToLower(strings.TrimSpace(m.Sender))) || strings.Contains(strings.ToLower(strings.TrimSpace(m.Sender)), strings.ToLower(targetName)) {
				filtered = append(filtered, ChatMessage{Sender: m.Sender, Body: m.Body, At: m.At})
			}
		}
	}
	if len(filtered) == 0 {
		logf("clipboard parse: target sender %q not found among %d messages", targetName, len(parsed))
		return nil
	}
	if len(filtered) > 40 {
		filtered = filtered[len(filtered)-40:]
	}
	return filtered
}

func replaceHistoryFromClipboard(raw string) int {
	filtered := conversationMessagesFromClipboard(raw)
	if len(filtered) == 0 {
		return 0
	}
	historyMu.Lock()
	recentMessages = append([]ChatMessage(nil), filtered...)
	historyMu.Unlock()
	saveHistory()
	return len(filtered)
}

func syncHistoryFromClipboard(raw string) int {
	filtered := conversationMessagesFromClipboard(raw)
	if len(filtered) == 0 {
		return 0
	}
	newCount := mergeParsedHistory(filtered)
	saveHistory()
	return newCount
}

// copyChatListTextForegroundFastToggle is the explicit hotkey-refresh path.
// Keep the proven v1.7.4 transcript fallbacks, but return the real foreground
// to the game as soon as the physical Ctrl+A/C has been delivered.  Slow EVA
// fallbacks then finish behind the game instead of leaving Kakao visible for up
// to a second or more.
func copyChatListTextForegroundFastToggle(target, list uintptr) (string, bool) {
	kakaoCopyMu.Lock()
	defer kakaoCopyMu.Unlock()
	if target == 0 || list == 0 {
		return "", false
	}

	// v1.7.8 safe-toggle path: EVA private command only.
	//
	// v1.7.7 still had a background PostMessage Ctrl+A/C fallback.  It did not
	// join FF14's input queue, but the new game build can observe an elevated
	// companion process emitting keyboard-shaped messages immediately before its
	// own user input starts.  Do not emit any synthetic key message at all while
	// opening the reply editor.  If EVA does not answer, keep cached history.
	clip := clipboardSnapshotNow()
	oldSeq := clip.seq
	newSeq, copied := selectAllAndCopyEVACommand(list, oldSeq)

	if !copied || newSeq == oldSeq {
		logf("toggle transcript EVA-only copy unavailable target=%x list=%x; using cached history", target, list)
		return "", false
	}
	raw, ok := readClipboardUnicode()
	restoreClipboardSnapshot(clip, newSeq)
	if !ok || strings.TrimSpace(raw) == "" {
		return "", false
	}
	return raw, true
}

func refreshHistoryForToggle() {
	target := findTargetChatWindow()
	if target == 0 {
		logf("toggle refresh: target chat not found")
		return
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		logf("toggle refresh: Kakao message list control not found in %x", target)
		return
	}
	raw, ok := copyChatListTextForegroundFastToggle(target, list)
	if !ok {
		logf("toggle refresh: safe background copy unavailable target=%x list=%x; cached history retained", target, list)
		return
	}
	count := replaceHistoryFromClipboard(raw)
	markPassiveReceiveNeedsReprime(1800 * time.Millisecond)
	logf("toggle refresh ok: %d chars, target messages=%d", len([]rune(raw)), count)
	// Marshal window layout/painting back to the main Win32 event loop.
	if controllerHwnd != 0 {
		pPostMessageW.Call(controllerHwnd, WM_APP_HISTORY_UPDATED, 0, 0)
	}
}

func captureTargetHistoryOnce() (int, bool) {
	if strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return 0, false
	}
	target := findTargetChatWindow()
	if target == 0 {
		logf("history capture: target chat not found")
		return 0, false
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		logf("history capture: Kakao message list control not found in %x", target)
		return 0, false
	}
	// Background-only: never activate Kakao, merge input queues, or alter global
	// keyboard state. Only the Kakao message-list HWND receives Ctrl+A/C.
	raw, ok := copyChatListText(target, list, false)
	if !ok {
		logf("history capture: background copy failed target=%x list=%x", target, list)
		return 0, false
	}
	newCount := syncHistoryFromClipboard(raw)
	logf("history capture ok: %d chars, new=%d", len([]rune(raw)), newCount)
	return newCount, true
}

func requestHistoryCapture(announce bool) {
	captureMu.Lock()
	if captureRunning {
		capturePending = true
		capturePendingAnnounce = capturePendingAnnounce || announce
		captureMu.Unlock()
		return
	}
	captureRunning = true
	captureMu.Unlock()
	go historyCaptureWorker(announce)
}

func historyCaptureWorker(announce bool) {
	for {
		totalNew := 0
		okAny := false
		// A shell flash can arrive a few milliseconds before Kakao commits the
		// new list item. Retry briefly, entirely off the UI thread.
		// Manual/initial refreshes get a second attempt as well. Kakao can update
		// the backing list a little later than the shell/UI state, and retries are
		// off the UI thread so they do not slow typing.
		tries := 2
		if announce {
			tries = 3
		}
		for i := 0; i < tries; i++ {
			if i > 0 {
				time.Sleep(time.Duration(70+i*70) * time.Millisecond)
			}
			newCount, ok := captureTargetHistoryOnce()
			if ok {
				okAny = true
				totalNew += newCount
				if newCount > 0 || !announce {
					break
				}
			}
		}
		if okAny && controllerHwnd != 0 {
			lp := uintptr(0)
			if announce {
				lp = 1
			}
			pPostMessageW.Call(controllerHwnd, WM_APP_HISTORY_UPDATED, uintptr(totalNew), lp)
		}

		captureMu.Lock()
		if capturePending {
			announce = capturePendingAnnounce
			capturePending = false
			capturePendingAnnounce = false
			captureMu.Unlock()
			continue
		}
		captureRunning = false
		captureMu.Unlock()
		return
	}
}

func parseHotkey(s string) (uint32, uint32, error) {
	raw := strings.TrimSpace(s)
	raw = strings.ReplaceAll(raw, "Numpad +", "NumpadAdd")
	raw = strings.ReplaceAll(raw, "numpad +", "numpadadd")
	if raw == "" {
		return 0, 0, errors.New("단축키가 비어 있습니다.")
	}
	parts := strings.Split(raw, "+")
	mods := uint32(0)
	key := ""
	for _, p := range parts {
		t := strings.ToLower(strings.TrimSpace(p))
		switch t {
		case "ctrl", "control":
			mods |= MOD_CONTROL
		case "alt":
			mods |= MOD_ALT
		case "shift":
			mods |= MOD_SHIFT
		case "win", "windows":
			mods |= MOD_WIN
		default:
			if key != "" {
				return 0, 0, errors.New("단축키 형식을 확인해 주세요. 예: Numpad . / F10 / Ctrl+Alt+K")
			}
			key = t
		}
	}
	if key == "" {
		return 0, 0, errors.New("단축키의 실제 키가 없습니다.")
	}

	keyMap := map[string]uint32{
		"numpad .": 0x6E, "numpad.": 0x6E, "numpaddot": 0x6E, "numpad decimal": 0x6E,
		"numpad -": 0x6D, "numpad-": 0x6D, "numpadsub": 0x6D,
		"numpad +": 0x6B, "numpad+": 0x6B, "numpadadd": 0x6B,
		"numpad /": 0x6F, "numpad/": 0x6F, "numpaddiv": 0x6F,
		"numpad *": 0x6A, "numpad*": 0x6A, "numpadmult": 0x6A,
		"insert": 0x2D, "ins": 0x2D, "delete": 0x2E, "del": 0x2E,
		"home": 0x24, "end": 0x23, "pageup": 0x21, "pgup": 0x21,
		"pagedown": 0x22, "pgdn": 0x22, "space": 0x20, "pause": 0x13,
		"scrolllock": 0x91, ".": 0xBE, "`": 0xC0,
	}
	for i := 0; i <= 9; i++ {
		keyMap[fmt.Sprintf("numpad %d", i)] = uint32(0x60 + i)
		keyMap[fmt.Sprintf("numpad%d", i)] = uint32(0x60 + i)
	}
	if vk, ok := keyMap[key]; ok {
		return mods, vk, nil
	}
	if strings.HasPrefix(key, "f") {
		if n, err := strconv.Atoi(strings.TrimPrefix(key, "f")); err == nil && n >= 1 && n <= 24 {
			return mods, uint32(0x70 + n - 1), nil
		}
	}
	if len(key) == 1 {
		c := key[0]
		if c >= 'a' && c <= 'z' {
			return mods, uint32(c - 'a' + 'A'), nil
		}
		if c >= '0' && c <= '9' {
			return mods, uint32(c), nil
		}
	}
	return 0, 0, fmt.Errorf("지원하지 않는 단축키입니다: %s\n예: Numpad . / Numpad - / F10 / Ctrl+Alt+K", raw)
}

func findTargetChatWindow() uintptr {
	titleNeedle := strings.TrimSpace(cfg.TargetChatTitle)
	if titleNeedle == "" {
		return 0
	}
	wins := enumTopWindows()
	var contains uintptr
	for _, hwnd := range wins {
		if !isProcess(hwnd, "KakaoTalk.exe") {
			continue
		}
		// v1.4.4: a configured detached chat must actually own Kakao's
		// message-list control.  Notification/transient windows can carry the
		// chat title too, and selecting one of those as the target made later
		// receive probes operate on the wrong HWND.
		if findChildByClass(hwnd, "EVA_VH_ListControl_Dblclk") == 0 {
			continue
		}
		title := strings.TrimSpace(getWindowText(hwnd))
		if strings.EqualFold(title, titleNeedle) {
			return hwnd
		}
		if contains == 0 && strings.Contains(strings.ToLower(title), strings.ToLower(titleNeedle)) {
			contains = hwnd
		}
	}
	return contains
}

func isFF14(hwnd uintptr) bool {
	if hwnd == 0 {
		return false
	}
	p := strings.ToLower(processBaseName(hwnd))
	return p == "ffxiv_dx11.exe" || p == "ffxiv.exe"
}

func isProcess(hwnd uintptr, exe string) bool {
	return strings.EqualFold(processBaseName(hwnd), exe)
}

type processEntry32 struct {
	Size            uint32
	CntUsage        uint32
	ProcessID       uint32
	DefaultHeapID   uintptr
	ModuleID        uint32
	CntThreads      uint32
	ParentProcessID uint32
	PriClassBase    int32
	Flags           uint32
	ExeFile         [260]uint16
}

func processBaseName(hwnd uintptr) string {
	if hwnd == 0 {
		return ""
	}

	// v1.7.10: resolve HWND -> PID through USER32, then look the PID up in a
	// system process snapshot. This never opens a handle to FFXIV/Kakao (or any
	// other target process), while still working for windows owned by another
	// process. GetWindowModuleFileNameW(hwnd), used briefly in v1.7.9, is not a
	// reliable cross-process executable-name lookup and caused the FF14-only
	// hotkey gate to reject the real game window.
	var pid uint32
	pGetWindowThreadProcessId.Call(hwnd, uintptr(unsafe.Pointer(&pid)))
	if pid == 0 {
		return ""
	}
	return processBaseNameByPID(pid)
}

func processBaseNameByPID(pid uint32) string {
	now := time.Now()
	processNameCacheMu.Lock()
	if now.Before(processNameCacheUntil) {
		if name, ok := processNameCache[pid]; ok {
			processNameCacheMu.Unlock()
			return name
		}
	}
	processNameCacheMu.Unlock()

	names := snapshotProcessNames()
	if names == nil {
		return ""
	}
	processNameCacheMu.Lock()
	processNameCache = names
	processNameCacheUntil = now.Add(time.Second)
	name := processNameCache[pid]
	processNameCacheMu.Unlock()
	return name
}

func snapshotProcessNames() map[uint32]string {
	snapshot, _, _ := pCreateToolhelp32Snapshot.Call(TH32CS_SNAPPROCESS, 0)
	if snapshot == 0 || snapshot == INVALID_HANDLE_VALUE {
		return nil
	}
	defer pCloseHandle.Call(snapshot)

	names := make(map[uint32]string)
	var entry processEntry32
	entry.Size = uint32(unsafe.Sizeof(entry))
	ok, _, _ := pProcess32FirstW.Call(snapshot, uintptr(unsafe.Pointer(&entry)))
	for ok != 0 {
		if entry.ProcessID != 0 {
			name := filepath.Base(syscall.UTF16ToString(entry.ExeFile[:]))
			if name != "" {
				names[entry.ProcessID] = name
			}
		}
		ok, _, _ = pProcess32NextW.Call(snapshot, uintptr(unsafe.Pointer(&entry)))
	}
	return names
}

var enumWindowsCb = syscall.NewCallback(func(hwnd uintptr, lParam uintptr) uintptr {
	enumMu.Lock()
	enumWindowsAccum = append(enumWindowsAccum, hwnd)
	enumMu.Unlock()
	return 1
})
var enumChildCb = syscall.NewCallback(func(hwnd uintptr, lParam uintptr) uintptr {
	t := strings.TrimSpace(getWindowText(hwnd))
	if t != "" {
		enumMu.Lock()
		enumChildAccum = append(enumChildAccum, t)
		enumMu.Unlock()
	}
	return 1
})

func enumTopWindows() []uintptr {
	enumMu.Lock()
	enumWindowsAccum = nil
	enumMu.Unlock()
	pEnumWindows.Call(enumWindowsCb, 0)
	enumMu.Lock()
	out := append([]uintptr(nil), enumWindowsAccum...)
	enumMu.Unlock()
	return out
}

func childTexts(hwnd uintptr) []string {
	enumMu.Lock()
	enumChildAccum = nil
	enumMu.Unlock()
	pEnumChildWindows.Call(hwnd, enumChildCb, 0)
	enumMu.Lock()
	out := append([]string(nil), enumChildAccum...)
	enumMu.Unlock()
	return out
}

func primePopupMonitor() {
	for _, hwnd := range enumTopWindows() {
		if !isNotificationHostProcess(hwnd) {
			continue
		}
		if sig, ok := popupSignature(hwnd, false); ok {
			popupSignatures[hwnd] = sig
		}
	}
	monitorPrimed = true
}

var winEventCb = syscall.NewCallback(func(hook uintptr, event uint32, hwnd uintptr, idObject int32, idChild int32, eventThread uint32, eventTime uint32) uintptr {
	if hwnd == 0 || controllerHwnd == 0 {
		return 0
	}
	switch event {
	case EVENT_SYSTEM_ALERT, EVENT_OBJECT_CREATE, EVENT_OBJECT_SHOW, EVENT_OBJECT_STATECHANGE,
		EVENT_OBJECT_NAMECHANGE, EVENT_OBJECT_DESCRIPTIONCHANGE, EVENT_OBJECT_VALUECHANGE, EVENT_OBJECT_LIVEREGIONCHANGED:
	default:
		return 0
	}

	root, _, _ := pGetAncestor.Call(hwnd, GA_ROOT)
	if root == 0 {
		root = hwnd
	}
	if !isNotificationHostProcess(root) {
		return 0
	}

	// v1.4.2: only cache accessibility text originating from KakaoTalk itself.
	// v1.4.1 shared this callback with the global SHOW hook and consequently
	// cached Explorer's taskbar text (e.g. "알림 오버플로") as if it were a
	// Kakao notification.  The process-specific hooks below catch Kakao's own
	// CREATE/SHOW/STATE/NAME/VALUE/LIVE-REGION/ALERT events without touching focus.
	if isProcess(root, "KakaoTalk.exe") {
		if text := msaaTextFromEvent(hwnd, idObject, idChild); text != "" {
			stashMSAAEventText(root, text)
		}
	}

	// Preserve the original event HWND; handler also checks its root.
	pPostMessageW.Call(controllerHwnd, WM_APP_KAKAO_SHOW, hwnd, 0)
	return 0
})

func installKakaoShowHook() {
	h, _, e := pSetWinEventHook.Call(EVENT_OBJECT_SHOW, EVENT_OBJECT_SHOW, 0, winEventCb, 0, 0, WINEVENT_OUTOFCONTEXT|WINEVENT_SKIPOWNPROCESS)
	if h == 0 {
		logf("SetWinEventHook failed: %v; polling fallback remains active", e)
		return
	}
	winEventHook = h
	logf("Kakao popup show hook installed")
}

func installKakaoA11yHook() {
	if winEventA11yHook != 0 {
		pUnhookWinEvent.Call(winEventA11yHook)
		winEventA11yHook = 0
	}
	if winEventAlertHook != 0 {
		pUnhookWinEvent.Call(winEventAlertHook)
		winEventAlertHook = 0
	}
	target := findTargetChatWindow()
	if target == 0 {
		logf("Kakao MSAA text hook deferred: target chat not open")
		return
	}
	var pid uint32
	pGetWindowThreadProcessId.Call(target, uintptr(unsafe.Pointer(&pid)))
	if pid == 0 {
		logf("Kakao MSAA text hook deferred: target pid unavailable")
		return
	}

	// Kakao's owner-drawn notification has varied between releases: some builds
	// announce text on NAME/VALUE changes, others only CREATE/STATE/LIVE-REGION.
	// Hook the object-event range for Kakao's PID only. The callback itself keeps
	// only the small set of events above, so this does not create desktop-wide
	// accessibility noise and never joins Kakao's input queue.
	h, _, e := pSetWinEventHook.Call(EVENT_OBJECT_CREATE, EVENT_OBJECT_LIVEREGIONCHANGED, 0, winEventCb, uintptr(pid), 0, WINEVENT_OUTOFCONTEXT|WINEVENT_SKIPOWNPROCESS)
	if h == 0 {
		logf("Kakao MSAA object hook failed pid=%d: %v", pid, e)
	} else {
		winEventA11yHook = h
	}

	// EVENT_SYSTEM_ALERT sits outside the object-event range and is a common
	// accessibility notification signal, so subscribe to it separately.
	ha, _, ea := pSetWinEventHook.Call(EVENT_SYSTEM_ALERT, EVENT_SYSTEM_ALERT, 0, winEventCb, uintptr(pid), 0, WINEVENT_OUTOFCONTEXT|WINEVENT_SKIPOWNPROCESS)
	if ha == 0 {
		logf("Kakao MSAA alert hook failed pid=%d: %v", pid, ea)
	} else {
		winEventAlertHook = ha
	}

	if winEventA11yHook != 0 || winEventAlertHook != 0 {
		logf("Kakao MSAA text hooks installed pid=%d object=%t alert=%t", pid, winEventA11yHook != 0, winEventAlertHook != 0)
	}
}

const (
	msaaVT_I4       = 3
	msaaOBJIDClient = 0xFFFFFFFC
	msaaChildSelf   = 0
)

var iidIAccessible = GUID{
	Data1: 0x618736E0,
	Data2: 0x3C3D,
	Data3: 0x11CF,
	Data4: [8]byte{0x81, 0x0C, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71},
}

func hresultOK(v uintptr) bool { return int32(v) >= 0 }

func msaaVariantI4(v int32) MSAAVARIANT {
	return MSAAVARIANT{Vt: msaaVT_I4, Val: int64(v)}
}

func msaaVtableMethod(obj uintptr, index uintptr) uintptr {
	if obj == 0 {
		return 0
	}
	vtbl := *(*uintptr)(unsafe.Pointer(obj))
	if vtbl == 0 {
		return 0
	}
	return *(*uintptr)(unsafe.Pointer(vtbl + index*unsafe.Sizeof(uintptr(0))))
}

func msaaRelease(obj uintptr) {
	if fn := msaaVtableMethod(obj, 2); fn != 0 {
		syscall.SyscallN(fn, obj)
	}
}

func bstrToStringAndFree(bstr uintptr) string {
	if bstr == 0 {
		return ""
	}
	n, _, _ := pSysStringLen.Call(bstr)
	if n == 0 {
		pSysFreeString.Call(bstr)
		return ""
	}
	chars := unsafe.Slice((*uint16)(unsafe.Pointer(bstr)), int(n))
	copyChars := append([]uint16(nil), chars...)
	pSysFreeString.Call(bstr)
	return strings.TrimSpace(syscall.UTF16ToString(copyChars))
}

func msaaBSTRProperty(acc uintptr, v MSAAVARIANT, methodIndex uintptr) string {
	fn := msaaVtableMethod(acc, methodIndex)
	if fn == 0 {
		return ""
	}
	var out uintptr
	// On Windows/amd64 VARIANT (24 bytes) is passed indirectly by the ABI.
	hr, _, _ := syscall.SyscallN(fn, acc, uintptr(unsafe.Pointer(&v)), uintptr(unsafe.Pointer(&out)))
	if !hresultOK(hr) || out == 0 {
		if out != 0 {
			pSysFreeString.Call(out)
		}
		return ""
	}
	return bstrToStringAndFree(out)
}

func msaaTextsForVariant(acc uintptr, v MSAAVARIANT) []string {
	parts := []string{}
	// IAccessible vtable: get_accName=10, get_accValue=11, get_accDescription=12.
	parts = appendUniqueText(parts, msaaBSTRProperty(acc, v, 10))
	parts = appendUniqueText(parts, msaaBSTRProperty(acc, v, 11))
	parts = appendUniqueText(parts, msaaBSTRProperty(acc, v, 12))
	return parts
}

func msaaTextFromEvent(hwnd uintptr, idObject, idChild int32) string {
	if hwnd == 0 {
		return ""
	}
	var acc uintptr
	var child MSAAVARIANT
	hr, _, _ := pAccessibleObjectFromEvent.Call(
		hwnd,
		uintptr(uint32(idObject)),
		uintptr(uint32(idChild)),
		uintptr(unsafe.Pointer(&acc)),
		uintptr(unsafe.Pointer(&child)),
	)
	if !hresultOK(hr) || acc == 0 {
		return ""
	}
	defer msaaRelease(acc)
	parts := msaaTextsForVariant(acc, child)
	// Some providers expose useful context only on the parent/self object.
	if child.Vt == msaaVT_I4 && int32(child.Val) != msaaChildSelf {
		parts = appendUniqueText(parts, msaaTextsForVariant(acc, msaaVariantI4(msaaChildSelf))...)
	}
	return strings.Join(parts, " | ")
}

func stashMSAAEventText(root uintptr, text string) {
	text = strings.TrimSpace(text)
	if root == 0 || text == "" {
		return
	}
	now := time.Now()
	msaaEventMu.Lock()
	list := msaaEventTexts[root]
	for _, item := range list {
		if now.Sub(item.At) < 2500*time.Millisecond && strings.EqualFold(normalizeA11yKey(item.Text), normalizeA11yKey(text)) {
			msaaEventMu.Unlock()
			return
		}
	}
	list = append(list, timedMSAAText{Text: text, At: now})
	if len(list) > 24 {
		list = list[len(list)-24:]
	}
	msaaEventTexts[root] = list
	// Opportunistically prune stale roots to keep this diagnostic cache bounded.
	for k, items := range msaaEventTexts {
		keep := items[:0]
		for _, item := range items {
			if now.Sub(item.At) <= 4*time.Second {
				keep = append(keep, item)
			}
		}
		if len(keep) == 0 {
			delete(msaaEventTexts, k)
		} else {
			msaaEventTexts[k] = keep
		}
	}
	msaaEventMu.Unlock()
}

func recentMSAAEventTexts(root uintptr) []string {
	now := time.Now()
	out := []string{}
	msaaEventMu.Lock()
	for _, item := range msaaEventTexts[root] {
		if now.Sub(item.At) <= 2500*time.Millisecond {
			out = appendUniqueText(out, item.Text)
		}
	}
	msaaEventMu.Unlock()
	return out
}

func msaaWindowTexts(hwnd uintptr) []string {
	if hwnd == 0 {
		return nil
	}
	// The worker is a goroutine; pin it while using a COM proxy.
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	cohr, _, _ := pCoInitializeEx.Call(0, 2) // COINIT_APARTMENTTHREADED
	coInit := hresultOK(cohr)
	if coInit {
		defer pCoUninitialize.Call()
	}

	var acc uintptr
	hr, _, _ := pAccessibleObjectFromWindow.Call(
		hwnd,
		uintptr(uint32(msaaOBJIDClient)),
		uintptr(unsafe.Pointer(&iidIAccessible)),
		uintptr(unsafe.Pointer(&acc)),
	)
	if !hresultOK(hr) || acc == 0 {
		return nil
	}
	defer msaaRelease(acc)

	parts := msaaTextsForVariant(acc, msaaVariantI4(msaaChildSelf))
	// IAccessible::get_accChildCount is vtable slot 8.
	if fn := msaaVtableMethod(acc, 8); fn != 0 {
		var count int32
		hr2, _, _ := syscall.SyscallN(fn, acc, uintptr(unsafe.Pointer(&count)))
		if hresultOK(hr2) && count > 0 {
			if count > 64 {
				count = 64
			}
			for i := int32(1); i <= count; i++ {
				parts = appendUniqueText(parts, msaaTextsForVariant(acc, msaaVariantI4(i))...)
				if len(parts) >= 24 {
					break
				}
			}
		}
	}
	if len(parts) > 0 {
		logf("MSAA popup probe hwnd=%x parts=%d text=%q", hwnd, len(parts), abbreviate(strings.Join(parts, " | "), 180))
	}
	return parts
}

func handleKakaoPopup(hwnd uintptr) {
	if hwnd == 0 || strings.TrimSpace(cfg.TargetChatTitle) == "" {
		return
	}
	root, _, _ := pGetAncestor.Call(hwnd, GA_ROOT)
	if root == 0 {
		root = hwnd
	}
	if !isProcess(root, "KakaoTalk.exe") || !isCompactPopupGeometryAnyVisibility(root) {
		return
	}
	// EVENT_OBJECT_SHOW also fires for children of the real chat window. Never
	// treat the configured detached chat (or any Kakao window owning a message
	// list) as a notification source.
	if target := findTargetChatWindow(); target != 0 && root == target {
		return
	}
	if isProcess(root, "KakaoTalk.exe") && findChildByClass(root, "EVA_VH_ListControl_Dblclk") != 0 {
		return
	}
	queueKakaoPopupInspection(root)
}

func queueKakaoPopupInspection(root uintptr) {
	if root == 0 {
		return
	}
	popupInspectMu.Lock()
	if popupInspecting[root] {
		popupInspectMu.Unlock()
		return
	}
	popupInspecting[root] = true
	popupInspectMu.Unlock()
	go inspectKakaoPopup(root)
}

func inspectKakaoPopup(root uintptr) {
	defer func() {
		popupInspectMu.Lock()
		delete(popupInspecting, root)
		popupInspectMu.Unlock()
	}()

	targetName := strings.TrimSpace(cfg.TargetChatTitle)
	if targetName == "" {
		return
	}
	for attempt := 0; attempt < 4; attempt++ {
		if attempt > 0 {
			time.Sleep(time.Duration(70+attempt*80) * time.Millisecond)
		}
		if !isProcess(root, "KakaoTalk.exe") || !isCompactPopupGeometryAnyVisibility(root) {
			return
		}

		// v1.4.1: first use MSAA. Kakao's owner-drawn popup can expose sender/body
		// through accessibility even when GetWindowText/UIA sees only control names.
		// This path is completely focus-neutral.
		msaaParts := recentMSAAEventTexts(root)
		msaaParts = appendUniqueText(msaaParts, msaaWindowTexts(root)...)
		msaaSig := strings.Join(msaaParts, " | ")

		// Keep the legacy non-invasive Win32/UIA scan as a secondary source.
		// Fullscreen/borderless Kakao can create a notification HWND and hide it
		// before this worker runs, so hidden handles are still eligible.
		sig, ok := popupSignatureAnyVisibility(root, true)
		if msaaSig != "" {
			if ok && sig != "" {
				sig = msaaSig + " | " + sig
			} else {
				sig, ok = msaaSig, true
			}
		}
		if !ok {
			continue
		}
		if !strings.Contains(strings.ToLower(sig), strings.ToLower(targetName)) {
			continue
		}

		body := cleanPopupText(sig, targetName)
		if isPopupControlNoise(body) {
			logf("notification text rejected as UI/control noise hwnd=%x body=%q", root, abbreviate(body, 80))
			continue
		}
		if strings.TrimSpace(body) == "" {
			body = "새 메시지가 도착했습니다."
		}
		noteIncomingPopupCaptured()
		removeIncomingFallbackHints()
		appendRecentMessage(body, sig)
		if cfg.HideNativeTargetNotification {
			hideVerifiedKakaoNotification(root, sig)
		}
		logf("incoming notification captured hwnd=%x process=%q body=%q", root, processBaseName(root), abbreviate(body, 80))
		return
	}
}

func hideVerifiedKakaoNotification(root uintptr, sig string) {
	if root == 0 || !isCompactPopupGeometry(root) {
		return
	}
	// Never hide the configured detached chat itself, even if the user resized it
	// to notification-like dimensions.
	title := strings.TrimSpace(getWindowText(root))
	targetName := strings.TrimSpace(cfg.TargetChatTitle)
	if targetName != "" && strings.EqualFold(title, targetName) {
		return
	}
	if target := findTargetChatWindow(); target != 0 && root == target {
		return
	}
	// A real Kakao chat window owns the message-list control. This is the hard
	// safety guard that prevents the target chat from disappearing again.
	if isProcess(root, "KakaoTalk.exe") && findChildByClass(root, "EVA_VH_ListControl_Dblclk") != 0 {
		return
	}
	if targetName == "" || !strings.Contains(strings.ToLower(sig), strings.ToLower(targetName)) {
		return
	}
	var rc RECT
	if r, _, _ := pGetWindowRect.Call(root, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return
	}
	w, h := rc.Right-rc.Left, rc.Bottom-rc.Top
	// Use stricter dimensions than the discovery scan before hiding anything.
	if w < 120 || h < 35 || w > 760 || h > 360 {
		return
	}
	pShowWindow.Call(root, SW_HIDE)
	logf("verified Kakao notification hidden hwnd=%x process=%q class=%q size=%dx%d", root, processBaseName(root), getClassName(root), w, h)
}

func scanKakaoPopupsRich() {
	// FLASH can arrive while Kakao's compact notification HWND is already hidden.
	// EnumWindows still exposes hidden top-level windows, so include compact
	// hidden candidates here. The hard guards in handleKakaoPopup prevent real
	// chat windows from being treated as notifications.
	for _, hwnd := range enumTopWindows() {
		if !isProcess(hwnd, "KakaoTalk.exe") || !isCompactPopupGeometryAnyVisibility(hwnd) {
			continue
		}
		// A real detached chat owns the EVA message list. Never feed such a
		// window into popup parsing/hiding, even during its creation animation.
		if findChildByClass(hwnd, "EVA_VH_ListControl_Dblclk") != 0 {
			continue
		}
		handleKakaoPopup(hwnd)
	}
}

func pollKakaoPopups() {
	if !monitorPrimed {
		primePopupMonitor()
		return
	}
	current := map[uintptr]bool{}
	for _, hwnd := range enumTopWindows() {
		if !isNotificationHostProcess(hwnd) {
			continue
		}
		sig, ok := popupSignature(hwnd, false)
		if !ok {
			continue
		}
		current[hwnd] = true
		prev, existed := popupSignatures[hwnd]
		if !existed || (prev != sig && sig != "") {
			handleKakaoPopup(hwnd)
		}
		popupSignatures[hwnd] = sig
	}
	for hwnd := range popupSignatures {
		if !current[hwnd] {
			delete(popupSignatures, hwnd)
		}
	}
}

func isCompactPopupGeometry(hwnd uintptr) bool {
	return isCompactPopupGeometryMode(hwnd, true)
}

func isCompactPopupGeometryAnyVisibility(hwnd uintptr) bool {
	return isCompactPopupGeometryMode(hwnd, false)
}

func isCompactPopupGeometryMode(hwnd uintptr, requireVisible bool) bool {
	if hwnd == 0 {
		return false
	}
	if requireVisible {
		vis, _, _ := pIsWindowVisible.Call(hwnd)
		if vis == 0 {
			return false
		}
	}
	var rc RECT
	if r, _, _ := pGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&rc))); r == 0 {
		return false
	}
	w, h := rc.Right-rc.Left, rc.Bottom-rc.Top
	if w < 80 || h < 24 || w > 900 || h > 500 {
		return false
	}
	wa := referenceRect()
	return rc.Right >= wa.Right-1000 && rc.Bottom >= wa.Bottom-650
}

func isNotificationHostProcess(hwnd uintptr) bool {
	p := strings.ToLower(processBaseName(hwnd))
	switch p {
	case "kakaotalk.exe", "shellexperiencehost.exe", "shellhost.exe", "explorer.exe", "startmenuexperiencehost.exe":
		return true
	default:
		return false
	}
}

var kakaoA11yTimeRx = regexp.MustCompile(`(?:오전|오후)\s*\d{1,2}:\d{2}`)
var kakaoA11yDateRx = regexp.MustCompile(`^\s*(?:\d{4}년\s*)?\d{1,2}월\s*\d{1,2}일(?:\s*[일월화수목금토]요일)?\s*$`)
var numericOnlyRx = regexp.MustCompile(`^\s*\d+\s*$`)

func normalizeA11yKey(text string) string {
	text = strings.ReplaceAll(text, "\r\n", "\n")
	text = strings.ReplaceAll(text, "\r", "\n")
	text = strings.TrimSpace(text)
	if text == "" {
		return ""
	}
	return strings.ToLower(strings.Join(strings.Fields(text), " "))
}

func decodeA11yLines(raw []byte) []string {
	var out []string
	seen := map[string]bool{}
	for _, line := range strings.Split(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		b, err := base64.StdEncoding.DecodeString(line)
		if err != nil || len(b) == 0 {
			continue
		}
		text := strings.TrimSpace(string(b))
		key := normalizeA11yKey(text)
		if key == "" || seen[key] {
			continue
		}
		seen[key] = true
		out = append(out, text)
		if len(out) >= 260 {
			break
		}
	}
	return out
}

// chatAccessibilityTexts reads only accessibility metadata from the already-open
// Kakao chat. It never activates Kakao, never sends input, and never changes the
// clipboard. UIA is tried first, then MSAA/IAccessible because Kakao's custom
// EVA list exposes different accessibility providers across PC client builds.
func chatAccessibilityTexts(target, list uintptr) ([]string, bool) {
	if target == 0 || list == 0 {
		return nil, false
	}
	script := fmt.Sprintf(`
$ErrorActionPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
try { Add-Type -AssemblyName Accessibility } catch {}

if(-not ("FF14BridgeOleAcc" -as [type])) {
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FF14BridgeOleAcc {
    [DllImport("oleacc.dll")]
    public static extern int AccessibleObjectFromWindow(
        IntPtr hwnd,
        uint dwId,
        ref Guid riid,
        [MarshalAs(UnmanagedType.Interface)] out object ppvObject);
}
"@
}

$seen = New-Object 'System.Collections.Generic.HashSet[string]'
$out = New-Object 'System.Collections.Generic.List[string]'
function Emit([string]$s) {
    if([string]::IsNullOrWhiteSpace($s)) { return }
    $s=$s.Trim()
    if($s.Length -gt 12000) { $s=$s.Substring(0,12000) }
    if($seen.Add($s)) {
        $bytes=[System.Text.Encoding]::UTF8.GetBytes($s)
        [void]$out.Add([Convert]::ToBase64String($bytes))
    }
}

function ProbePatterns($e) {
    if($null -eq $e) { return }
    try { Emit ([string]$e.Current.Name) } catch {}
    try { Emit ([string]$e.Current.HelpText) } catch {}
    try {
        $p=$e.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
        if($null -ne $p) { Emit ([string]$p.DocumentRange.GetText(-1)) }
    } catch {}
    try {
        $v=$e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
        if($null -ne $v) { Emit ([string]$v.Current.Value) }
    } catch {}
}

function ProbeUIA([IntPtr]$h) {
    if($h -eq [IntPtr]::Zero) { return }
    try {
        $root=[System.Windows.Automation.AutomationElement]::FromHandle($h)
        if($null -eq $root) { return }
        ProbePatterns $root
        $els=$root.FindAll(
            [System.Windows.Automation.TreeScope]::Subtree,
            [System.Windows.Automation.Condition]::TrueCondition)
        $n=[Math]::Min($els.Count,180)
        for($i=0; $i -lt $n; $i++) {
            ProbePatterns $els.Item($i)
            if($out.Count -ge 220) { break }
        }
    } catch {}
}

$script:accNodes=0
function EmitAccField($a,[object]$id,[string]$field) {
    try {
        if($field -eq 'name') { Emit ([string]$a.get_accName($id)); return }
        if($field -eq 'value') { Emit ([string]$a.get_accValue($id)); return }
        if($field -eq 'desc') { Emit ([string]$a.get_accDescription($id)); return }
    } catch {}
}
function WalkAcc($a,[int]$depth) {
    if($null -eq $a -or $depth -gt 6 -or $script:accNodes -ge 220) { return }
    $script:accNodes++
    EmitAccField $a 0 'name'
    EmitAccField $a 0 'value'
    EmitAccField $a 0 'desc'
    $count=0
    try { $count=[int]$a.accChildCount } catch { $count=0 }
    if($count -gt 80) { $start=[Math]::Max(1,$count-80+1) } else { $start=1 }
    for($i=$start; $i -le $count; $i++) {
        if($script:accNodes -ge 220) { break }
        $child=$null
        try { $child=$a.get_accChild($i) } catch {}
        if($null -ne $child -and $child -is [Accessibility.IAccessible]) {
            WalkAcc $child ($depth+1)
        } else {
            EmitAccField $a $i 'name'
            EmitAccField $a $i 'value'
            EmitAccField $a $i 'desc'
            $script:accNodes++
        }
    }
}
function ProbeMSAA([IntPtr]$h) {
    if($h -eq [IntPtr]::Zero) { return }
    try {
        $iid=[Guid]'618736E0-3C3D-11CF-810C-00AA00389B71'
        $obj=$null
        $hr=[FF14BridgeOleAcc]::AccessibleObjectFromWindow(
            $h, [uint32]4294967292, [ref]$iid, [ref]$obj)
        if($hr -eq 0 -and $null -ne $obj -and $obj -is [Accessibility.IAccessible]) {
            WalkAcc ([Accessibility.IAccessible]$obj) 0
        }
    } catch {}
}

$list=[IntPtr]::new([Int64]%d)
$target=[IntPtr]::new([Int64]%d)
ProbeUIA $list
if($out.Count -lt 4) { ProbeUIA $target }
ProbeMSAA $list
if($out.Count -lt 4) { ProbeMSAA $target }
[Console]::Write(($out -join [Environment]::NewLine))
`, list, target)

	ctx, cancel := context.WithTimeout(context.Background(), 2400*time.Millisecond)
	defer cancel()
	cmd := exec.CommandContext(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	out, err := cmd.Output()
	if err != nil || ctx.Err() != nil {
		logf("chat accessibility probe failed target=%x list=%x err=%v timeout=%v", target, list, err, ctx.Err())
		return nil, false
	}
	texts := decodeA11yLines(out)
	if len(texts) == 0 {
		logf("chat accessibility probe returned no text target=%x list=%x", target, list)
		return nil, false
	}
	return texts, true
}

func chatAccessibilityDiff(texts []string) (newTexts []string, wasPrimed bool) {
	chatA11yMu.Lock()
	defer chatA11yMu.Unlock()
	wasPrimed = chatA11yPrimed
	if len(chatA11ySeen) > 4000 {
		chatA11ySeen = map[string]bool{}
		chatA11yPrimed = false
		wasPrimed = false
	}
	for _, text := range texts {
		key := normalizeA11yKey(text)
		if key == "" {
			continue
		}
		if !chatA11ySeen[key] && wasPrimed {
			newTexts = append(newTexts, text)
		}
		chatA11ySeen[key] = true
	}
	chatA11yPrimed = true
	return newTexts, wasPrimed
}

func primeChatAccessibilityBaseline() {
	target := findTargetChatWindow()
	if target == 0 {
		return
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		return
	}
	texts, ok := chatAccessibilityTexts(target, list)
	if !ok {
		return
	}
	chatA11yMu.Lock()
	for _, text := range texts {
		if key := normalizeA11yKey(text); key != "" {
			chatA11ySeen[key] = true
		}
	}
	chatA11yPrimed = true
	count := len(chatA11ySeen)
	chatA11yMu.Unlock()
	logf("chat accessibility baseline primed target=%x list=%x texts=%d seen=%d", target, list, len(texts), count)
}

func recentBodyKnown(body string) bool {
	key := normalizeA11yKey(body)
	if key == "" {
		return true
	}
	historyMu.Lock()
	defer historyMu.Unlock()
	start := 0
	if len(recentMessages) > 16 {
		start = len(recentMessages) - 16
	}
	for _, m := range recentMessages[start:] {
		if normalizeA11yKey(m.Body) == key {
			return true
		}
	}
	return false
}

func cleanA11yMessageCandidate(text, target string) string {
	s := strings.ReplaceAll(text, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	s = strings.TrimSpace(s)
	if s == "" {
		return ""
	}
	s = strings.ReplaceAll(s, "카카오톡", " ")
	if target != "" {
		s = strings.ReplaceAll(s, target, " ")
	}
	s = kakaoA11yTimeRx.ReplaceAllString(s, " ")
	for _, noise := range []string{
		"읽지 않음", "읽음", "받은 메시지", "새 메시지", "메시지 수신",
		"프로필 사진", "프로필", "채팅방", "대화방",
	} {
		s = strings.ReplaceAll(s, noise, " ")
	}
	s = strings.Trim(s, " \t\r\n|·,-:;()[]{}<>")
	s = strings.Join(strings.Fields(s), " ")
	return s
}

func usefulA11yBody(text, target string) bool {
	text = strings.TrimSpace(text)
	if text == "" || text == incomingFallbackBody {
		return false
	}
	if strings.EqualFold(normalizeA11yKey(text), normalizeA11yKey(target)) {
		return false
	}
	if kakaoA11yTimeRx.MatchString(text) && len([]rune(cleanA11yMessageCandidate(text, target))) == 0 {
		return false
	}
	if kakaoA11yDateRx.MatchString(text) || numericOnlyRx.MatchString(text) {
		return false
	}
	low := strings.ToLower(strings.TrimSpace(text))
	// Reject accessibility control labels aggressively. v1.3.3 once accepted
	// "RichEdit Control" as if it were a message because it only rejected the
	// exact class name. These tokens are UI metadata, not chat content.
	for _, fragment := range []string{
		"richedit", "eva_vh_listcontrol", "message input", "메시지 입력", "입력창",
	} {
		if strings.Contains(low, strings.ToLower(fragment)) {
			return false
		}
	}
	for _, exact := range []string{
		"control", "컨트롤", "button", "버튼", "pane", "scroll bar", "스크롤 막대",
		"보내기", "검색", "이모티콘", "파일 첨부", "사진 첨부",
	} {
		if strings.EqualFold(low, strings.ToLower(exact)) {
			return false
		}
	}
	runes := []rune(text)
	return len(runes) >= 1 && len(runes) <= 1200
}

func lastTargetParsedMessage(texts []string, target string) (string, bool) {
	for i := len(texts) - 1; i >= 0; i-- {
		raw := texts[i]
		if !strings.Contains(raw, "\n") && !strings.Contains(raw, "\r") && !strings.Contains(raw, "[") {
			continue
		}
		parsed := parseKakaoClipboard(raw)
		for j := len(parsed) - 1; j >= 0; j-- {
			m := parsed[j]
			if strings.EqualFold(strings.TrimSpace(m.Sender), strings.TrimSpace(target)) &&
				strings.TrimSpace(m.Body) != "" && !recentBodyKnown(m.Body) {
				return strings.TrimSpace(m.Body), true
			}
		}
	}
	// Some providers return each clipboard-formatted line as a separate node.
	joined := strings.Join(texts, "\n")
	parsed := parseKakaoClipboard(joined)
	for j := len(parsed) - 1; j >= 0; j-- {
		m := parsed[j]
		if strings.EqualFold(strings.TrimSpace(m.Sender), strings.TrimSpace(target)) &&
			strings.TrimSpace(m.Body) != "" && !recentBodyKnown(m.Body) {
			return strings.TrimSpace(m.Body), true
		}
	}
	return "", false
}

func extractIncomingFromAccessibility(texts, newTexts []string, target string) (string, bool) {
	if body, ok := lastTargetParsedMessage(texts, target); ok {
		return body, true
	}

	targetKey := normalizeA11yKey(target)
	// Best case: an accessible message item contains sender + body + timestamp.
	for i := len(texts) - 1; i >= 0; i-- {
		raw := strings.TrimSpace(texts[i])
		key := normalizeA11yKey(raw)
		if targetKey == "" || !strings.Contains(key, targetKey) {
			continue
		}
		body := cleanA11yMessageCandidate(raw, target)
		if usefulA11yBody(body, target) && !recentBodyKnown(body) {
			return body, true
		}
	}

	// Second common layout: sender, body and time are separate accessible nodes.
	for i := len(texts) - 1; i >= 0; i-- {
		if normalizeA11yKey(texts[i]) != targetKey {
			continue
		}
		for _, d := range []int{1, 2, 3, -1, -2} {
			j := i + d
			if j < 0 || j >= len(texts) {
				continue
			}
			body := cleanA11yMessageCandidate(texts[j], target)
			if usefulA11yBody(body, target) && !recentBodyKnown(body) {
				return body, true
			}
		}
	}

	// Finally use only nodes that appeared after the baseline. This is deliberately
	// conservative: pure counters/timestamps/control labels are rejected.
	for i := len(newTexts) - 1; i >= 0; i-- {
		body := cleanA11yMessageCandidate(newTexts[i], target)
		if usefulA11yBody(body, target) && !recentBodyKnown(body) {
			return body, true
		}
	}
	return "", false
}

func captureIncomingFromChatAccessibility(target uintptr) (string, string, bool) {
	if target == 0 {
		return "", "", false
	}
	list := findChildByClass(target, "EVA_VH_ListControl_Dblclk")
	if list == 0 {
		logf("chat accessibility fallback: message list not found target=%x", target)
		return "", "", false
	}
	texts, ok := chatAccessibilityTexts(target, list)
	if !ok {
		return "", "", false
	}
	newTexts, primed := chatAccessibilityDiff(texts)
	body, found := extractIncomingFromAccessibility(texts, newTexts, strings.TrimSpace(cfg.TargetChatTitle))
	if found && isPopupControlNoise(body) {
		logf("chat accessibility candidate rejected as control noise target=%x body=%q", target, abbreviate(body, 80))
		body, found = "", false
	}
	if !found {
		var sample []string
		src := newTexts
		if len(src) == 0 {
			src = texts
		}
		start := 0
		if len(src) > 6 {
			start = len(src) - 6
		}
		for _, t := range src[start:] {
			sample = append(sample, abbreviate(strings.Join(strings.Fields(t), " "), 80))
		}
		logf("chat accessibility fallback: no message extracted target=%x texts=%d new=%d primed=%v tail=%q",
			target, len(texts), len(newTexts), primed, strings.Join(sample, " || "))
		return "", "", false
	}
	sig := fmt.Sprintf("chat-a11y:%s:%d", normalizeA11yKey(body), time.Now().Unix()/3)
	return body, sig, true
}

func uiaTexts(hwnd uintptr) []string {
	if hwnd == 0 {
		return nil
	}
	// Read-only UI Automation fallback. No activation and no input injection.
	script := fmt.Sprintf(`
$ErrorActionPreference='SilentlyContinue'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]::new([Int64]%d))
if($null -eq $root){ exit }
$seen=New-Object 'System.Collections.Generic.HashSet[string]'
$out=New-Object 'System.Collections.Generic.List[string]'
function AddText([string]$s){ if(-not [string]::IsNullOrWhiteSpace($s)){ $s=$s.Trim(); if($seen.Add($s)){ [void]$out.Add($s) } } }
try { AddText $root.Current.Name } catch {}
try { AddText $root.Current.HelpText } catch {}
try {
  $els=$root.FindAll([System.Windows.Automation.TreeScope]::Subtree,[System.Windows.Automation.Condition]::TrueCondition)
  foreach($e in $els){
    if($out.Count -ge 24){ break }
    try { AddText $e.Current.Name } catch {}
    try { AddText $e.Current.HelpText } catch {}
  }
} catch {}
[Console]::Write(($out -join [Environment]::NewLine))
`, hwnd)
	ctx, cancel := context.WithTimeout(context.Background(), 1400*time.Millisecond)
	defer cancel()
	cmd := exec.CommandContext(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	out, err := cmd.Output()
	if err != nil || ctx.Err() != nil {
		return nil
	}
	var result []string
	seen := map[string]bool{}
	for _, line := range strings.Split(strings.ReplaceAll(string(out), "\r\n", "\n"), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || seen[line] {
			continue
		}
		seen[line] = true
		result = append(result, line)
		if len(result) >= 24 {
			break
		}
	}
	return result
}

// ---- Windows notification platform reader (v1.4.0) -----------------------
// Kakao's custom chat list does not expose message items through UIA/MSAA on
// current PC builds.  When Kakao publishes a standard Windows toast, however,
// Windows.UI.Notifications.Management.UserNotificationListener exposes the
// actual toast text.  These ABI calls are the same WinRT interfaces that UWP/
// Win32 notification-listener clients use; no DLL injection or input synthesis
// is involved.

var (
	iidUserNotificationListenerStatics = GUID{0xFF6123CF, 0x4386, 0x4AA3, [8]byte{0xB7, 0x3D, 0xB8, 0x04, 0xE5, 0xB6, 0x3B, 0x23}}
	iidIAsyncInfo                      = GUID{0x00000036, 0x0000, 0x0000, [8]byte{0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}}
)

func hrFailed(hr uintptr) bool { return int32(uint32(hr)) < 0 }

func comMethod(obj uintptr, slot uintptr) uintptr {
	if obj == 0 {
		return 0
	}
	vtbl := *(*uintptr)(unsafe.Pointer(obj))
	if vtbl == 0 {
		return 0
	}
	return *(*uintptr)(unsafe.Pointer(vtbl + slot*unsafe.Sizeof(uintptr(0))))
}

func comInvoke(obj uintptr, slot uintptr, args ...uintptr) uintptr {
	fn := comMethod(obj, slot)
	if fn == 0 {
		return uintptr(uint32(0x80004003)) // E_POINTER
	}
	argv := make([]uintptr, 0, len(args)+1)
	argv = append(argv, obj)
	argv = append(argv, args...)
	r1, _, _ := syscall.SyscallN(fn, argv...)
	return r1
}

func comRelease(obj uintptr) {
	if obj != 0 {
		comInvoke(obj, 2)
	}
}

func comQueryInterface(obj uintptr, iid *GUID) (uintptr, bool) {
	if obj == 0 || iid == nil {
		return 0, false
	}
	var out uintptr
	hr := comInvoke(obj, 0, uintptr(unsafe.Pointer(iid)), uintptr(unsafe.Pointer(&out)))
	return out, !hrFailed(hr) && out != 0
}

func createWinRTHString(text string) (uintptr, bool) {
	u := utf16.Encode([]rune(text))
	var h uintptr
	var p uintptr
	if len(u) > 0 {
		p = uintptr(unsafe.Pointer(&u[0]))
	}
	hr, _, _ := pWindowsCreateString.Call(p, uintptr(len(u)), uintptr(unsafe.Pointer(&h)))
	return h, !hrFailed(hr) && h != 0
}

func deleteWinRTHString(h uintptr) {
	if h != 0 {
		pWindowsDeleteString.Call(h)
	}
}

func winRTHStringToString(h uintptr) string {
	if h == 0 {
		return ""
	}
	var n uint32
	ptr, _, _ := pWindowsGetStringRawBuffer.Call(h, uintptr(unsafe.Pointer(&n)))
	if ptr == 0 || n == 0 {
		return ""
	}
	buf := unsafe.Slice((*uint16)(unsafe.Pointer(ptr)), int(n))
	return syscall.UTF16ToString(buf)
}

func comHStringProperty(obj uintptr, slot uintptr) string {
	if obj == 0 {
		return ""
	}
	var h uintptr
	hr := comInvoke(obj, slot, uintptr(unsafe.Pointer(&h)))
	if hrFailed(hr) || h == 0 {
		return ""
	}
	defer deleteWinRTHString(h)
	return strings.TrimSpace(winRTHStringToString(h))
}

func waitWinRTAsyncResult(op uintptr, timeout time.Duration) (uintptr, error) {
	if op == 0 {
		return 0, errors.New("nil async operation")
	}
	info, ok := comQueryInterface(op, &iidIAsyncInfo)
	if !ok {
		return 0, errors.New("IAsyncInfo unavailable")
	}
	defer comRelease(info)

	deadline := time.Now().Add(timeout)
	for {
		var status uint32
		hr := comInvoke(info, 7, uintptr(unsafe.Pointer(&status))) // IAsyncInfo.Status
		if hrFailed(hr) {
			return 0, fmt.Errorf("IAsyncInfo.Status hr=0x%08x", uint32(hr))
		}
		switch status {
		case 1: // Completed
			var result uintptr
			hr = comInvoke(op, 8, uintptr(unsafe.Pointer(&result))) // IAsyncOperation<T>.GetResults
			if hrFailed(hr) {
				return 0, fmt.Errorf("GetResults hr=0x%08x", uint32(hr))
			}
			return result, nil
		case 2, 3: // Canceled / Error
			var asyncErr int32
			_ = comInvoke(info, 8, uintptr(unsafe.Pointer(&asyncErr)))
			return 0, fmt.Errorf("async status=%d error=0x%08x", status, uint32(asyncErr))
		}
		if time.Now().After(deadline) {
			return 0, errors.New("async timeout")
		}
		time.Sleep(10 * time.Millisecond)
	}
}

func acquireUserNotificationListener() (uintptr, error) {
	className, ok := createWinRTHString("Windows.UI.Notifications.Management.UserNotificationListener")
	if !ok {
		return 0, errors.New("WindowsCreateString failed")
	}
	defer deleteWinRTHString(className)

	var factory uintptr
	hr, _, _ := pRoGetActivationFactory.Call(className, uintptr(unsafe.Pointer(&iidUserNotificationListenerStatics)), uintptr(unsafe.Pointer(&factory)))
	if hrFailed(hr) || factory == 0 {
		return 0, fmt.Errorf("RoGetActivationFactory hr=0x%08x", uint32(hr))
	}
	defer comRelease(factory)

	var listener uintptr
	hr = comInvoke(factory, 6, uintptr(unsafe.Pointer(&listener))) // IUserNotificationListenerStatics.Current
	if hrFailed(hr) || listener == 0 {
		return 0, fmt.Errorf("UserNotificationListener.Current hr=0x%08x", uint32(hr))
	}
	return listener, nil
}

func ensureSystemNotificationAccess() bool {
	// Main is locked to the GUI OS thread. RequestAccessAsync is intentionally
	// initiated here because Windows documents that the permission request must
	// originate from a UI thread.
	hr, _, _ := pRoInitialize.Call(0) // RO_INIT_SINGLETHREADED
	if !hrFailed(hr) {
		winRTMainInitialized = true
	} else if uint32(hr) != 0x80010106 { // RPC_E_CHANGED_MODE: already initialized differently
		logf("system notification listener: RoInitialize failed hr=0x%08x", uint32(hr))
		return false
	}

	listener, err := acquireUserNotificationListener()
	if err != nil {
		logf("system notification listener unavailable: %v", err)
		return false
	}
	defer comRelease(listener)

	var status uint32
	hr = comInvoke(listener, 7, uintptr(unsafe.Pointer(&status))) // GetAccessStatus
	if hrFailed(hr) {
		logf("system notification listener GetAccessStatus failed hr=0x%08x", uint32(hr))
		return false
	}
	if status == 1 {
		logf("system notification listener access=Allowed")
		return true
	}
	if status == 2 {
		logf("system notification listener access=Denied; Windows notification-store path disabled")
		return false
	}

	// Unspecified. Ask once through the OS permission UI. This does not activate
	// KakaoTalk or touch game input.
	var op uintptr
	hr = comInvoke(listener, 6, uintptr(unsafe.Pointer(&op))) // RequestAccessAsync
	if hrFailed(hr) || op == 0 {
		logf("system notification listener RequestAccessAsync failed hr=0x%08x", uint32(hr))
		return false
	}
	result, err := waitWinRTAsyncResult(op, 20*time.Second)
	comRelease(op)
	if err != nil {
		logf("system notification listener permission wait failed: %v", err)
		return false
	}
	status = uint32(result)
	logf("system notification listener permission result=%d", status)
	return status == 1
}

func startSystemNotificationPoller() {
	go func() {
		runtime.LockOSThread()
		defer runtime.UnlockOSThread()
		hr, _, _ := pRoInitialize.Call(1) // RO_INIT_MULTITHREADED
		initialized := !hrFailed(hr)
		if hrFailed(hr) && uint32(hr) != 0x80010106 {
			logf("system notification poller RoInitialize failed hr=0x%08x", uint32(hr))
			return
		}
		if initialized {
			defer pRoUninitialize.Call()
		}

		listener, err := acquireUserNotificationListener()
		if err != nil {
			logf("system notification poller listener failed: %v", err)
			return
		}
		defer comRelease(listener)

		seen := map[uint32]string{}
		if n, err := pollSystemNotifications(listener, seen, true); err != nil {
			logf("system notification baseline failed: %v", err)
		} else {
			logf("system notification baseline primed count=%d", n)
		}
		for {
			time.Sleep(220 * time.Millisecond)
			if _, err := pollSystemNotifications(listener, seen, false); err != nil {
				logf("system notification poll failed: %v", err)
				time.Sleep(780 * time.Millisecond)
			}
		}
	}()
}

func pollSystemNotifications(listener uintptr, seen map[uint32]string, prime bool) (int, error) {
	if listener == 0 {
		return 0, errors.New("nil listener")
	}
	var op uintptr
	hr := comInvoke(listener, 10, 1, uintptr(unsafe.Pointer(&op))) // GetNotificationsAsync(NotificationKinds.Toast)
	if hrFailed(hr) || op == 0 {
		return 0, fmt.Errorf("GetNotificationsAsync hr=0x%08x", uint32(hr))
	}
	view, err := waitWinRTAsyncResult(op, 1600*time.Millisecond)
	comRelease(op)
	if err != nil || view == 0 {
		if err == nil {
			err = errors.New("nil notification vector")
		}
		return 0, err
	}
	defer comRelease(view)

	var count uint32
	hr = comInvoke(view, 7, uintptr(unsafe.Pointer(&count))) // IVectorView.Size
	if hrFailed(hr) {
		return 0, fmt.Errorf("notification vector Size hr=0x%08x", uint32(hr))
	}
	for i := uint32(0); i < count; i++ {
		var userNotif uintptr
		hr = comInvoke(view, 6, uintptr(i), uintptr(unsafe.Pointer(&userNotif))) // GetAt
		if hrFailed(hr) || userNotif == 0 {
			continue
		}
		func() {
			defer comRelease(userNotif)
			var id uint32
			if hr2 := comInvoke(userNotif, 8, uintptr(unsafe.Pointer(&id))); hrFailed(hr2) {
				return
			}

			// A notification can be updated in place while retaining its Windows ID.
			// Compare the visible payload as well as the ID so consecutive Kakao
			// messages are not lost when Kakao updates one toast instead of creating
			// a brand-new notification object.
			appName, aumid, texts, ok := readSystemNotification(userNotif)
			if !ok {
				return
			}
			signature := normalizeA11yKey(appName + "\x1f" + aumid + "\x1f" + strings.Join(texts, "\x1f"))
			if old, existed := seen[id]; existed && old == signature {
				return
			}
			seen[id] = signature
			if prime {
				return
			}

			if !isKakaoSystemNotification(appName, aumid) {
				// Keep content private for unrelated apps, but identity-only logging makes
				// it possible to diagnose whether Windows is exposing Kakao under an
				// unexpected application name.
				logf("system toast observed id=%d app=%q aumid=%q", id, appName, aumid)
				return
			}
			joined := strings.Join(texts, " || ")
			logf("system Kakao toast id=%d app=%q aumid=%q texts=%q", id, appName, aumid, abbreviate(joined, 300))

			target := strings.TrimSpace(cfg.TargetChatTitle)
			if target == "" || !notificationTextsContainTarget(texts, target) {
				logf("system Kakao toast ignored: target %q not present id=%d", target, id)
				return
			}
			body := cleanSystemNotificationBody(texts, target, appName)
			if body == "" {
				body = "새 메시지가 도착했습니다."
			}
			noteIncomingPopupCaptured()
			removeIncomingFallbackHints()
			appendRecentMessage(body, fmt.Sprintf("winrt-toast:%d", id))
			logf("system Kakao toast captured id=%d body=%q", id, abbreviate(body, 120))

			// If requested, dismiss only this already-identified Windows toast. This
			// does not activate Kakao or alter keyboard focus.
			if cfg.HideNativeTargetNotification {
				hr2 := comInvoke(listener, 13, uintptr(id)) // RemoveNotification
				if hrFailed(hr2) {
					logf("system Kakao toast remove failed id=%d hr=0x%08x", id, uint32(hr2))
				}
			}
		}()
	}
	return int(count), nil
}

func isKakaoSystemNotification(appName, aumid string) bool {
	v := strings.ToLower(appName + " " + aumid)
	return strings.Contains(v, "kakao") || strings.Contains(v, "카카오")
}

func notificationTextsContainTarget(texts []string, target string) bool {
	t := normalizeA11yKey(target)
	if t == "" {
		return false
	}
	for _, x := range texts {
		if strings.Contains(normalizeA11yKey(x), t) {
			return true
		}
	}
	return false
}

func cleanSystemNotificationBody(texts []string, target, appName string) string {
	var out []string
	seen := map[string]bool{}
	for _, raw := range texts {
		x := strings.TrimSpace(strings.ReplaceAll(strings.ReplaceAll(raw, "\r", " "), "\n", " "))
		if x == "" {
			continue
		}
		key := normalizeA11yKey(x)
		if key == normalizeA11yKey(target) || key == normalizeA11yKey(appName) ||
			key == "카카오톡" || key == "kakaotalk" || key == "kakao talk" {
			continue
		}
		if kakaoA11yTimeRx.MatchString(x) && len([]rune(x)) <= 16 {
			continue
		}
		if !seen[key] {
			seen[key] = true
			out = append(out, x)
		}
	}
	return strings.TrimSpace(strings.Join(out, " "))
}

func readSystemNotification(userNotif uintptr) (appName, aumid string, texts []string, ok bool) {
	if userNotif == 0 {
		return "", "", nil, false
	}
	// UserNotification.AppInfo (slot 7)
	var appInfo uintptr
	if hr := comInvoke(userNotif, 7, uintptr(unsafe.Pointer(&appInfo))); !hrFailed(hr) && appInfo != 0 {
		func() {
			defer comRelease(appInfo)
			aumid = comHStringProperty(appInfo, 7) // AppUserModelId
			var display uintptr
			if hr2 := comInvoke(appInfo, 8, uintptr(unsafe.Pointer(&display))); !hrFailed(hr2) && display != 0 {
				defer comRelease(display)
				appName = comHStringProperty(display, 6) // DisplayName
			}
		}()
	}

	var notif uintptr
	if hr := comInvoke(userNotif, 6, uintptr(unsafe.Pointer(&notif))); hrFailed(hr) || notif == 0 {
		return appName, aumid, nil, false
	}
	defer comRelease(notif)

	var visual uintptr
	if hr := comInvoke(notif, 8, uintptr(unsafe.Pointer(&visual))); hrFailed(hr) || visual == 0 { // Notification.Visual
		return appName, aumid, nil, false
	}
	defer comRelease(visual)

	var bindings uintptr
	if hr := comInvoke(visual, 8, uintptr(unsafe.Pointer(&bindings))); hrFailed(hr) || bindings == 0 { // NotificationVisual.Bindings
		return appName, aumid, nil, false
	}
	defer comRelease(bindings)

	var bindingCount uint32
	if hr := comInvoke(bindings, 7, uintptr(unsafe.Pointer(&bindingCount))); hrFailed(hr) {
		return appName, aumid, nil, false
	}
	unique := map[string]bool{}
	for i := uint32(0); i < bindingCount; i++ {
		var binding uintptr
		if hr := comInvoke(bindings, 6, uintptr(i), uintptr(unsafe.Pointer(&binding))); hrFailed(hr) || binding == 0 {
			continue
		}
		func() {
			defer comRelease(binding)
			var textView uintptr
			if hr := comInvoke(binding, 11, uintptr(unsafe.Pointer(&textView))); hrFailed(hr) || textView == 0 { // GetTextElements
				return
			}
			defer comRelease(textView)
			var textCount uint32
			if hr := comInvoke(textView, 7, uintptr(unsafe.Pointer(&textCount))); hrFailed(hr) {
				return
			}
			for j := uint32(0); j < textCount; j++ {
				var textElem uintptr
				if hr := comInvoke(textView, 6, uintptr(j), uintptr(unsafe.Pointer(&textElem))); hrFailed(hr) || textElem == 0 {
					continue
				}
				text := comHStringProperty(textElem, 6) // AdaptiveNotificationText.Text
				comRelease(textElem)
				key := normalizeA11yKey(text)
				if key != "" && !unique[key] {
					unique[key] = true
					texts = append(texts, text)
				}
			}
		}()
	}
	return appName, aumid, texts, len(texts) > 0
}

func appendUniqueText(parts []string, values ...string) []string {
	for _, v := range values {
		v = strings.TrimSpace(v)
		if v == "" {
			continue
		}
		dup := false
		for _, p := range parts {
			if strings.EqualFold(strings.TrimSpace(p), v) {
				dup = true
				break
			}
		}
		if !dup {
			parts = append(parts, v)
		}
	}
	return parts
}

func popupSignature(hwnd uintptr, useUIA bool) (string, bool) {
	return popupSignatureMode(hwnd, useUIA, true)
}

func popupSignatureAnyVisibility(hwnd uintptr, useUIA bool) (string, bool) {
	return popupSignatureMode(hwnd, useUIA, false)
}

func popupSignatureMode(hwnd uintptr, useUIA bool, requireVisible bool) (string, bool) {
	if !isCompactPopupGeometryMode(hwnd, requireVisible) {
		return "", false
	}
	parts := []string{}
	if t := strings.TrimSpace(getWindowText(hwnd)); t != "" {
		parts = appendUniqueText(parts, t)
	}
	for _, t := range childTexts(hwnd) {
		parts = appendUniqueText(parts, t)
		if len(parts) >= 12 {
			break
		}
	}
	basic := strings.Join(parts, " | ")
	target := strings.ToLower(strings.TrimSpace(cfg.TargetChatTitle))
	needUIA := len(parts) <= 1 || (target != "" && !strings.Contains(strings.ToLower(basic), target))
	if useUIA && needUIA && isNotificationHostProcess(hwnd) {
		for _, t := range uiaTexts(hwnd) {
			parts = appendUniqueText(parts, t)
		}
	}
	if len(parts) == 0 {
		return "", false
	}
	return strings.Join(parts, " | "), true
}

func isPopupControlNoise(body string) bool {
	s := strings.ToLower(strings.Join(strings.Fields(strings.TrimSpace(body)), " "))
	if s == "" {
		return false
	}
	for _, exact := range []string{
		"richedit 컨트롤", "rich edit 컨트롤", "richedit control", "richedit50w",
		"메시지 입력", "입력창", "eva_vh_listcontrol_dblclk", "eva_vh_listcontrol",
	} {
		if s == strings.ToLower(exact) {
			return true
		}
	}
	// Accessibility descriptions sometimes decorate the RichEdit class name.
	return strings.Contains(s, "richedit") && (strings.Contains(s, "컨트롤") || strings.Contains(s, "control"))
}

func cleanPopupText(sig, target string) string {
	s := strings.ReplaceAll(sig, "\r", " ")
	s = strings.ReplaceAll(s, "\n", " ")
	s = strings.ReplaceAll(s, "카카오톡", "")
	if target != "" {
		s = strings.ReplaceAll(s, target, "")
	}
	s = strings.Trim(s, " |-")
	for strings.Contains(s, "  ") {
		s = strings.ReplaceAll(s, "  ", " ")
	}
	return s
}

func showToast(title, body string) {
	if toastHwnd == 0 {
		return
	}
	toastTitle = title
	toastBody = body
	positionToastWindow()
	pInvalidateRect.Call(toastHwnd, 0, 1)
	pShowWindow.Call(toastHwnd, SW_SHOWNORMAL)
	pSetWindowPos.Call(toastHwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE)
	pKillTimer.Call(controllerHwnd, TIMER_TOAST_HIDE)
	dur := cfg.NotifyDurationMS
	if dur < 1200 {
		dur = 1200
	}
	pSetTimer.Call(controllerHwnd, TIMER_TOAST_HIDE, uintptr(dur), 0)
}

func showHistoryOverlay() {
	if historyHwnd == 0 {
		return
	}
	positionHistoryWindow()
	pSetLayeredWindowAttributes.Call(historyHwnd, 0, uintptr(cfg.OverlayAlpha), LWA_ALPHA)
	pInvalidateRect.Call(historyHwnd, 0, 1)
	pShowWindow.Call(historyHwnd, SW_SHOWNORMAL)
	pSetWindowPos.Call(historyHwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE)
}

func positionHistoryWindow() {
	rc := referenceRect()
	count := cfg.RecentMessageCount
	if count < 3 {
		count = 3
	}
	if count > 10 {
		count = 10
	}
	w := int32(430)
	h := int32(52 + count*44)
	if h > 492 {
		h = 492
	}
	x := rc.Right - w - 14
	// Keep the conversation panel tight to the lower-right edge. On typical
	// 16:9 FF14 layouts it sits beside the centered reply bar rather than above it.
	y := rc.Bottom - h - 14
	if y < rc.Top+14 {
		y = rc.Top + 14
	}
	pSetWindowPos.Call(historyHwnd, HWND_TOPMOST, uintptr(x), uintptr(y), uintptr(w), uintptr(h), SWP_NOACTIVATE)
}

func positionReplyWindow() {
	rc := referenceRect()
	w, h := int32(760), int32(58)
	x := rc.Left + (rc.Right-rc.Left-w)/2
	y := rc.Bottom - h - 56
	if y < rc.Top {
		y = rc.Top
	}
	// Active foreground is sufficient; avoid the TOPMOST overlay band for the
	// keyboard-capable reply window.
	pSetWindowPos.Call(replyHwnd, 0, uintptr(x), uintptr(y), uintptr(w), uintptr(h), SWP_NOACTIVATE)
}

func positionToastWindow() {
	rc := referenceRect()
	w, h := int32(350), int32(68)
	x := rc.Right - w - 18
	y := rc.Bottom - h - 18
	pSetWindowPos.Call(toastHwnd, HWND_TOPMOST, uintptr(x), uintptr(y), uintptr(w), uintptr(h), SWP_NOACTIVATE)
}

func referenceRect() RECT {
	wins := enumTopWindows()
	for _, hwnd := range wins {
		if isFF14(hwnd) {
			var rc RECT
			if r, _, _ := pGetWindowRect.Call(hwnd, uintptr(unsafe.Pointer(&rc))); r != 0 && rc.Right > rc.Left && rc.Bottom > rc.Top {
				return rc
			}
		}
	}
	var rc RECT
	pSystemParametersInfoW.Call(SPI_GETWORKAREA, 0, uintptr(unsafe.Pointer(&rc)), 0)
	return rc
}

func centerWindow(hwnd uintptr, w, h int32) {
	rc := referenceRect()
	x := rc.Left + (rc.Right-rc.Left-w)/2
	y := rc.Top + (rc.Bottom-rc.Top-h)/2
	pSetWindowPos.Call(hwnd, 0, uintptr(x), uintptr(y), uintptr(w), uintptr(h), 0)
}

func getText(hwnd uintptr) string {
	if hwnd == 0 {
		return ""
	}
	n, _, _ := pGetWindowTextLengthW.Call(hwnd)
	buf := make([]uint16, int(n)+2)
	pGetWindowTextW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
	return syscall.UTF16ToString(buf)
}
func getWindowText(hwnd uintptr) string { return getText(hwnd) }
func setText(hwnd uintptr, s string) {
	if hwnd != 0 {
		pSetWindowTextW.Call(hwnd, uintptr(unsafe.Pointer(u16(s))))
	}
}
func pGetDlgItemHandle(parent uintptr, id uintptr) uintptr {
	r, _, _ := pGetDlgItem.Call(parent, id)
	return r
}
func getCheck(hwnd uintptr) bool {
	r, _, _ := pSendMessageW.Call(hwnd, BM_GETCHECK, 0, 0)
	return r == BST_CHECKED
}
func setCheck(hwnd uintptr, v bool) {
	x := uintptr(BST_UNCHECKED)
	if v {
		x = BST_CHECKED
	}
	pSendMessageW.Call(hwnd, BM_SETCHECK, x, 0)
}

func messageBox(title, text string) {
	pMessageBoxW.Call(settingsHwnd, uintptr(unsafe.Pointer(u16(text))), uintptr(unsafe.Pointer(u16(title))), 0x40)
}

func addTrayIcon() bool {
	if controllerHwnd == 0 {
		logf("addTrayIcon: controller hwnd is zero")
		return false
	}
	icon, _, iconErr := pLoadIconW.Call(0, 32512)
	if icon == 0 {
		logf("addTrayIcon: LoadIconW failed: %v", iconErr)
		return false
	}
	var nid NOTIFYICONDATAW
	nid.CbSize = uint32(unsafe.Sizeof(nid))
	nid.HWnd = controllerHwnd
	nid.UID = 1
	nid.UFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
	nid.UCallbackMessage = WM_APP_TRAY
	nid.HIcon = icon
	copyUTF16(nid.SzTip[:], "FF14 Kakao Bridge")
	r, _, e := pShellNotifyIconW.Call(NIM_ADD, uintptr(unsafe.Pointer(&nid)))
	if r == 0 {
		logf("Shell_NotifyIconW(NIM_ADD) failed: %v cbSize=%d hwnd=%x", e, nid.CbSize, controllerHwnd)
		return false
	}
	trayRegistered = true
	logf("tray icon registered")
	return true
}

func addTrayIconWithRetry() bool {
	if trayRegistered {
		return true
	}
	for i := 1; i <= 5; i++ {
		if addTrayIcon() {
			return true
		}
		logf("tray retry %d/5", i)
		time.Sleep(250 * time.Millisecond)
	}
	return false
}

func deleteTrayIcon() {
	if controllerHwnd == 0 {
		return
	}
	var nid NOTIFYICONDATAW
	nid.CbSize = uint32(unsafe.Sizeof(nid))
	nid.HWnd = controllerHwnd
	nid.UID = 1
	pShellNotifyIconW.Call(NIM_DELETE, uintptr(unsafe.Pointer(&nid)))
	trayRegistered = false
}

func showTrayMenu() {
	menu, _, _ := pCreatePopupMenu.Call()
	if menu == 0 {
		return
	}
	defer pDestroyMenu.Call(menu)
	pAppendMenuW.Call(menu, MF_STRING, ID_TRAY_REPLY, uintptr(unsafe.Pointer(u16("답장창 열기"))))
	pAppendMenuW.Call(menu, MF_STRING, ID_TRAY_SETTINGS, uintptr(unsafe.Pointer(u16("설정"))))
	pAppendMenuW.Call(menu, MF_STRING, ID_TRAY_EXIT, uintptr(unsafe.Pointer(u16("종료"))))
	var pt POINT
	pGetCursorPos.Call(uintptr(unsafe.Pointer(&pt)))
	pSetForegroundWindow.Call(controllerHwnd)
	cmd, _, _ := pTrackPopupMenu.Call(menu, TPM_RIGHTBUTTON|TPM_RETURNCMD, uintptr(pt.X), uintptr(pt.Y), 0, controllerHwnd, 0)
	if cmd != 0 {
		pPostMessageW.Call(controllerHwnd, WM_COMMAND, cmd, 0)
	}
}

func cleanup() {
	if controllerHwnd != 0 && shellHookMsg != 0 {
		pDeregisterShellHookWindow.Call(controllerHwnd)
	}
	if winEventHook != 0 {
		pUnhookWinEvent.Call(winEventHook)
		winEventHook = 0
	}
	if winEventA11yHook != 0 {
		pUnhookWinEvent.Call(winEventA11yHook)
		winEventA11yHook = 0
	}
	if winEventAlertHook != 0 {
		pUnhookWinEvent.Call(winEventAlertHook)
		winEventAlertHook = 0
	}
	if controllerHwnd != 0 && registeredVK != 0 {
		pUnregisterHotKey.Call(controllerHwnd, ID_HOTKEY)
		registeredVK = 0
	}
	deleteTrayIcon()
	if toastBrush != 0 {
		pDeleteObject.Call(toastBrush)
		toastBrush = 0
	}
	if historyBrush != 0 {
		pDeleteObject.Call(historyBrush)
		historyBrush = 0
	}
	if historyMineFont != 0 {
		pDeleteObject.Call(historyMineFont)
		historyMineFont = 0
	}
	if winRTMainInitialized {
		pRoUninitialize.Call()
		winRTMainInitialized = false
	}
}

func abbreviate(s string, max int) string {
	r := []rune(strings.TrimSpace(s))
	if len(r) <= max {
		return string(r)
	}
	return string(r[:max-1]) + "…"
}

func rgb(r, g, b uint32) uintptr { return uintptr(r | (g << 8) | (b << 16)) }
