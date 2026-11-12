# -*- coding: utf-8 -*-
"""4/8 quality gate for general-release UI and offline input correctness.
This is deliberately GUI-free and includes no private user screenshots.
"""
from pathlib import Path
import ast
from PIL import Image
from ui_input_v042 import normalize_imported_image,unique_image_name

root=Path(__file__).resolve().parent
code=(root/"app.py").read_text(encoding="utf-8")
ast.parse(code,filename=str(root/"app.py"))
assert 'root.title("ChatLens OCR v0.4.16' in code
assert 'by 2bornot' in code
assert 'Copyright © 2026 2bornot' in code
assert 'v0.4.16  ·  오프라인 OCR' in code
assert 'file_bar=ttk.Frame(bar)' in code
assert 'options_bar=ttk.Frame(bar)' in code
assert 'button(file_bar,"🔎 현재 이미지 분석"' in code
assert '전체 이미지 일괄 분석' in code
assert 'icon_tools.pack(side="left")' in code
assert 'sticker_tools.pack(side="left")' in code
assert 'if mode.get()=="파판14"' in code
assert 'elif mode.get()=="카카오톡"' in code
assert 'if not last[0]:' in code  # forbid saving placeholder text
assert 'if sel:active[0]=entries[sel[0]][1];selection[0]=None;show()' in code
assert 'default_test_result_filename()' in code
assert 'with Image.open(f) as picture:add_image(picture,Path(f).name)' in code

assert unique_image_name("클립보드 이미지",[("클립보드 이미지",None)])=="클립보드 이미지 (2)"
assert unique_image_name("사진.png",[("사진.png",None),("사진 (2).png",None)])=="사진 (3).png"
assert unique_image_name("A.png",[])=="A.png"
assert unique_image_name("",[])=="이미지"

img=Image.new("RGB",(21,37),(255,120,50))
img.getexif()[274]=6  # 90° clockwise
fixed=normalize_imported_image(img)
assert fixed.size==(37,21),fixed.size
assert fixed.mode=="RGB"
normal=normalize_imported_image(Image.new("RGBA",(50,30),(20,30,40,128)))
assert normal.size==(50,30) and normal.mode=="RGB"

from shop_grid_v0374 import _synthetic as shop_test
assert shop_test()
print("4/8 UI and input gate PASS: responsive toolbars, specialized actions, EXIF, duplicate names, output safety, shopping grid")
