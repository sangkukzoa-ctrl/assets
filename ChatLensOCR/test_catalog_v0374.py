# -*- coding: utf-8 -*-
"""Deterministic shopping grid/card regression tests (synthetic assets only).

Never uploads the user's real 34 screenshot corpus into the public repository.
"""
import ast
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
import catalog_v0374 as catalog

assert catalog._synthetic(), "Periodic 4-column product listing not detected"
assert catalog.PRICE_RE.search("판매가: 450,000원")
assert catalog.PRICE_RE.search("1,200,00021")
assert not catalog.PRICE_RE.search("System7 42GBB")
gibberish="ㅋ＞＜×_{"*65
assert not catalog._clean_lines(gibberish), "Long punctuation-heavy OCR noise must be filtered"
assert catalog._clean_lines("KSC ModelName 450,000원") == ["KSC ModelName 450,000원"]

w,h=1020,610
picture=Image.new("RGB",(w,h),"white")
draw=ImageDraw.Draw(picture)
try:font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",16)
except OSError:font=ImageFont.load_default()
for row in range(2):
    for col in range(4):
        x=col*250+10;y=row*300+8
        draw.rectangle((x+18,y+20,x+190,y+160),outline=(75,75,75),width=2)
        draw.text((x+14,y+180),f"MODEL_{row}_{col}",fill="black",font=font)
        draw.text((x+14,y+207),"450,000원",fill=(13,95,215),font=font)
        draw.text((x+14,y+235),"SOLD OUT",fill=(188,48,48),font=font)
cols,conf=catalog._grid(picture)
assert len(cols)==4,(cols,conf)
saved_prices=catalog._price_anchors
saved_reader=catalog._text_blocks
try:
    catalog._price_anchors=lambda im,columns:[218,518]
    spans,_=catalog._row_spans(picture,cols)
    assert len(spans)==2,spans
    def fake_read(clip,lang="한국어",psm=6):
        return "MODEL_0_0\n450,000원\nSOLD OUT",[
            {"text":"MODEL_0_0","score":.97,"box":(10,8,100,26)},
            {"text":"450,000원","score":.99,"box":(10,40,103,59)}],92.
    catalog._text_blocks=fake_read
    out=catalog.analyze(picture)
    assert out is not None,"A 4x2 synthetic catalog must be recognized"
    mode,content,hits,meta,boxes=out
    assert mode=="범용"
    assert len(meta)==8,(len(meta),meta)
    assert "[상품 1 / 1행 1열]" in content
    assert "[상품 8 / 2행 4열]" in content
    assert all(b["box"][0]>=0 for b in boxes)
finally:
    catalog._price_anchors=saved_prices
    catalog._text_blocks=saved_reader

# Plain nonshopping pages must not trigger the product listing recognizer.
ordinary=Image.new("RGB",(700,800),"white")
draw=ImageDraw.Draw(ordinary)
for i in range(30):
    draw.text((40,12+i*24),"Plain document paragraph without prices",
              font=font,fill="black")
assert catalog.analyze(ordinary) is None

for file in ("app.py","layout_v2.py","explorer_v1.py","catalog_v0374.py"):
    ast.parse((Path(__file__).resolve().parent/file).read_text(encoding="utf-8"))
print("v0.3.7.4 4x2 shopping cards, noise gate and nonshopping controls PASSED",flush=True)
