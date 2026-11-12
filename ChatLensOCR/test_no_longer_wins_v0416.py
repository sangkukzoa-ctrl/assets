# -*- coding: utf-8 -*-
"""v0.4.16 no-longer-wins fallback regression for all text extraction paths.

Simulated OCR candidates show why longer text and natural language should not
outvote the original pixels. Does not contain any private screenshots.
"""
from unittest.mock import patch
from PIL import Image
from multicolumn_v037 import _read as multi_read
from ffxiv_combat_v037 import analyze as battle_analyze

page=Image.new("RGB",(950,400),"white")
original="PRODUCT TITLE\nPRICE $45.00"
with patch("tess_backend.read",return_value=(original,[],13)),patch(
        "app.recognize",side_effect=AssertionError(
        "Must not replace nonempty text with longer OCR guess")):
    text,boxes,confidence=multi_read(page,"한국어",True)
assert text==original and confidence==13 and boxes==[]

with patch("tess_backend.read",return_value=("",[],0)),patch(
        "app.recognize",return_value=[
            {"text":"icon-as-word","box":(4,5,120,35),"score":.98}]):
    text,boxes,confidence=multi_read(page,"한국어",True)
assert text=="" and not boxes, "A single icon must not turn into text"

with patch("tess_backend.read",return_value=("",[],0)),patch(
        "app.recognize",return_value=[
            {"text":"PRODUCT TITLE","box":(4,5,185,28),"score":.94},
            {"text":"PRICE $45.00","box":(4,43,175,67),"score":.92}]):
    text,boxes,confidence=multi_read(page,"한국어",True)
assert "PRODUCT TITLE" in text and "PRICE $45.00" in text
assert len(boxes)==2 and confidence>=90

screen=Image.new("RGB",(530,380),(24,24,27))
bands=[(10+i*22,23+i*22) for i in range(10)]
with patch("ffxiv_combat_v037.rows",return_value=bands),patch(
        "tess_backend.read",return_value=("이미 판독된 문자",[],20)),patch(
        "app.recognize",side_effect=AssertionError(
        "Do not discard short existing combat text for a longer guess")):
    kind,body,hits,meta,raw=battle_analyze(screen,"한국어",True)
assert kind=="파판14"
assert all(line=="[전투] 이미 판독된 문자" for line in body.splitlines())
assert len(meta)==10 and all(v["ocr_source"]=="tesseract" for v in meta)

with patch("ffxiv_combat_v037.rows",return_value=bands),patch(
        "tess_backend.read",return_value=("",[],0)),patch(
        "app.recognize",return_value=[
            {"text":"아이콘 그림 없음","score":.2,"box":(3,3,90,29)}]):
    kind,body,hits,meta,raw=battle_analyze(screen,"한국어",True)
assert all(line=="[전투] [문자 인식 실패]" for line in body.splitlines())
assert all(v["needs_review"] for v in meta)
print("v0.4.16 never-trust-longer-output fallback, source and "
      "confidence provenance, no icon-to-word creation PASS")
