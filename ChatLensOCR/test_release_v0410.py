# -*- coding: utf-8 -*-
"""Offline prerelease integrity regression. Does not include user screenshots."""
from pathlib import Path
import ast
from datetime import date
from PIL import Image,ImageDraw
from shop_grid_v0374 import card_boxes, analyze as analyze_shop

d=Path(__file__).resolve().parent
app=(d/"app.py").read_text(encoding="utf-8")
version=(d/"test_export_v0373.py").read_text(encoding="utf-8")
meta=(d/"version_info.txt").read_text(encoding="utf-8")
for file in d.glob("*.py"):
    ast.parse(file.read_text(encoding="utf-8"),filename=str(file))
for expected in ("ChatLens OCR v0.4.12", "2bornot", "Copyright © 2026 2bornot", "MIT"):
    assert expected in app or expected in meta,expected
assert 'VERSION = "0.4.12"' in version
from test_export_v0373 import default_test_result_filename
assert default_test_result_filename(date(2026,11,7))=="ChatLensOCR_v0.4.12-테스트결과-2026-11-07.txt"
assert 'Copyright (c) 2026 2bornot' in (d/"LICENSE").read_text(encoding="utf-8")
assert 'SignPath Foundation' in (d/"CODE_SIGNING_POLICY.md").read_text(encoding="utf-8")
assert 'ChatLensOCR_v0.4.12.exe' in meta

blank=Image.new("RGB",(1100,660),"white")
assert card_boxes(blank) is None
img=Image.new("RGB",(1100,660),"white");draw=ImageDraw.Draw(img)
for row in range(2):
    for col in range(5):
        x=58+col*210;y=75+row*280
        draw.rectangle((x,y,x+124,y+58),fill=(33,34,35))
        draw.rectangle((x+50,y+185,x+79,y+201),fill=(0,0,0))
seen=[]
def mock_reader(crop,language,precise):
    seen.append(crop.size)
    return "상품 테스트", [{"text":"상품 테스트","score":1,"box":(2,3,40,17)}],99
result=analyze_shop(img,reader=mock_reader)
assert result is not None and len(seen)==10
assert len(result[3])==10 and len(result[4])==10
print("v0.4.12 metadata, developer copyright, export name, code syntax and product grid PASSED")
