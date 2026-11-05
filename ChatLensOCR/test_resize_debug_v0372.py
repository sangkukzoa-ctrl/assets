# -*- coding: utf-8 -*-
"""Regression for the shopping catalogue crash and copyable debug tracing."""
import ast
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from ocr_guard_v0372 import regression as guard_regression
from batch_v0372 import regression as batch_regression
from debuglog_v0372 import recent_text

assert guard_regression(),"Zero-size and high-aspect image padding failed"
assert batch_regression(),"Batch must continue after failing image"
log=recent_text()
assert "synthetic per-image crash" in log and "two.png" in log,"Missing copyable detailed traceback"
assert "rapidocr_tile_skipped" in log,"Missing OCR tile diagnostics"
for name in ("app.py","ocr_guard_v0372.py","batch_v0372.py","debuglog_v0372.py"):
    ast.parse((ROOT/name).read_text(encoding="utf-8"))
source=(ROOT/"app.py").read_text(encoding="utf-8")
assert "def show_debug_log():" in source
assert "로그 복사" in source and "디버그 로그" in source

# Full recognizer must safely consume 1–12px-high strips; these are produced
# by the old generic OCR when a shopping catalog's product-card lines are cut.
from app import recognize
for w,h in ((2200,3),(2000,6),(1600,12),(6,1800),(4,4)):
    image=Image.new("RGB",(w,h),"white")
    records=recognize(image,"한국어",False)
    assert isinstance(records,list),(w,h)
    print("RapidOCR thin-crop",w,h,"pass, records",len(records),flush=True)

# A real-size white e-commerce screenshot should not fail wholesale when
# generic text-row extraction submits a long cropped horizontal band.
from layout_v2 import analyze
class NoIcons:
    def match(self,*args,**kwargs):return "",None,0.
picture=Image.new("RGB",(1444,1044),"white")
d=ImageDraw.Draw(picture)
font_path=Path("C:/Windows/Fonts/malgun.ttf")
font=ImageFont.truetype(str(font_path),17) if font_path.exists() else ImageFont.load_default()
for row in range(9):
    y=18+row*110
    for col in range(5):
        x=8+col*285
        d.text((x,y),"KSC M93R II System7",font=font,fill=(35,35,35))
        d.text((x,y+25),"판매가: 530,000원",font=font,fill=(0,120,200))
        d.text((x,y+50),"품절",font=font,fill=(0,0,0))
mode,text,icons,meta,rows,raw=analyze(picture,"자동","한국어",False,"모그리",NoIcons())
assert mode=="범용",(mode,text[:150])
print("Catalog screenshot 1444x1044 analyzed safely, lines:",len(text.splitlines()),flush=True)
print("Resize and debug regression PASSED",flush=True)
