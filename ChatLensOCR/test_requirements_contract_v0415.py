# -*- coding: utf-8 -*-
"""v0.4.17 originally requested features / historical regression contract.

Contains literal UI and code surface checks only; no customer screenshots.
If any of these features disappears, Windows CI must stop before release.
"""
from pathlib import Path
import ast

root=Path(__file__).resolve().parent
source=(root/"app.py").read_text(encoding="utf-8")
layout=(root/"layout_v2.py").read_text(encoding="utf-8")
shop=(root/"shop_grid_v0374.py").read_text(encoding="utf-8")
guard=(root/"ocr_hallucination_guard_v0414.py").read_text(encoding="utf-8")
version=(root/"test_export_v0373.py").read_text(encoding="utf-8")
for file in root.glob("*.py"):
    # A broken Python file must never ship even if an optional module is
    # normally imported only on a rare user input.
    ast.parse(file.read_text(encoding="utf-8"),filename=str(file))
features={
    "desktop standalone GUI": 'root.title("ChatLens OCR v0.4.17',
    "author and public copyright": "Copyright © 2026 2bornot",
    "offline input from local files": "filedialog.askopenfilenames",
    "clipboard image import": "ImageGrab.grabclipboard()",
    "single picture analysis": "🔎 현재 이미지 분석",
    "multi-image batch analysis": "전체 이미지 일괄 분석",
    "general OCR mode": '"범용"',
    "FFXIV mode": '"파판14"',
    "KakaoTalk mode": '"카카오톡"',
    "catalog mode": '"쇼핑몰 목록"',
    "file explorer mode": '"파일 탐색기"',
    "manual text edit and export": "직접 수정 후 TXT 저장 가능",
    "plain-text export": 'button(actions,"TXT 저장"',
    "JSON export": 'button(actions,"JSON 저장"',
    "shareable debug log UI": 'button(actions,"🐞 디버그 로그"',
    "debug log copy": 'button(actions_log,"로그 복사",copy_log)',
    "debug log save": 'button(actions_log,"로그 TXT 저장",save_log)',
    "automatic dated test result filename": 'default_test_result_filename()',
    "separate test result export button": 'button(actions,"📄 테스트결과 내보내기"',
    "OCR unreadable review button": 'button(actions,"🔎 미인식 찾기"',
    "imported EXIF orientation": "normalize_imported_image(im)",
    "prevents stale output on new image": 'field.delete("1.0","end")',
    "selftest for packaged exe": 'sys.argv[1]=="--self-test"',
}
missing=[name for name,token in features.items() if token not in source]
assert not missing,missing
assert source.index('button(actions,"🐞 디버그 로그"') < source.index(
    'button(actions,"📄 테스트결과 내보내기"')
for text in ("restore_white_subtitle","recover_empty_caption",
             "icon_grid_title_crop_bottom","embedded_scoreboard_box",
             "detect_mode(img)"):
    assert text in layout,text
assert "detail_evidence(image)" in shop
assert "icon_grid_title_crop_bottom" in guard
assert 'VERSION = "0.4.17"' in version
print("v0.4.17 requirements contract: %d UI/storage/review/offline "
      "features and six general/specialized guards PASS" % len(features))
