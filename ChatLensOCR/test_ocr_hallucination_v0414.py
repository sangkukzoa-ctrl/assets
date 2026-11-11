# -*- coding: utf-8 -*-
"""Synthetic v0.4.14 OCR anti-hallucination release gate.

Pixel-derived OCR candidates are never human-confirmed transcriptions.
Tesseract rereads use one recognizer; matching predictions do not prove truth.
These tests assert abstention on repetitive icons, guessed text, semantic
rewrites, uncorroborated words and one-glyph caption disagreements.
No private benchmark screenshots, names or chat logs are included.
"""
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from ffxiv_fidelity_v0410 import merge_hypotheses
from generic_blank_caption_v0413 import recover_empty_caption
from ocr_hallucination_guard_v0414 import is_repeated_icon_grid
from generic_subtitle_fidelity_v0412 import restore_white_subtitle

font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",22)

# A visually regular chest containing only colorful icons can cause
# Tesseract to repeat entirely nonexistent characters over 40 cells.
grid=Image.new("RGB",(519,377),(160,160,160))
drawer=ImageDraw.Draw(grid)
for x in range(22,480,54):
    drawer.line((x,47,x,365),fill=(42,42,42),width=3)
for y in range(47,370,54):
    drawer.line((22,y,500,y),fill=(42,42,42),width=3)
for i,x in enumerate(range(22,480,54)):
    for j,y in enumerate(range(47,340,54)):
        drawer.rectangle((x+15,y+15,x+35,y+30),
                         fill=((i*19+45)%150+45,(j*22+50)%150+45,80))
drawer.text((22,5),"Large Chest",font=font,fill=(18,18,18))
assert is_repeated_icon_grid(grid)
with patch("tess_backend.read",side_effect=AssertionError(
        "No OCR should run inside an inventory-art grid")):
    assert recover_empty_caption(grid,"","한국어")==""

# Real photo-like pixels with only one caption line: text proposals must
# have identical characters; shared grammar and 90% similarity are insufficient.
h,w=363,545
yy,xx=np.mgrid[0:h,0:w]
v=(10+(xx/w)*210+(yy/h)*75).clip(0,240).astype(np.uint8)
photo=Image.fromarray(np.stack([v,v//2+22,v//2+25],axis=2),"RGB")
ImageDraw.Draw(photo).text((70,302),"문자 단위 근거 확인",font=font,
                          fill="white",stroke_width=2,stroke_fill="black")
assert not is_repeated_icon_grid(photo)

correct="영상 아래 안내문입니다"
wrong="영상 아래 안내문이니다"
assert correct!=wrong
with patch("tess_backend.read",side_effect=[
        (correct,[],91),(wrong,[],89),("",[],0)]):
    assert recover_empty_caption(photo,"","한국어")==""
# Even the same candidate is not accepted when quality evidence is weak.
with patch("tess_backend.read",side_effect=[
        (correct,[],41),(correct,[],42),("",[],0)]):
    assert recover_empty_caption(photo,"","한국어")==""
with patch("tess_backend.read",side_effect=[
        (correct,[],89),(correct,[],92),("",[],0)]):
    assert recover_empty_caption(photo,"","한국어")==correct

# Two passes of the same model are NOT permission to complete missing
# words, change subject, expand abbreviated text, or normalize slang.
assert merge_hypotheses("x> ㅁㄴㅇ","x> 정말 감사합니다","x> 정말 감사합니다")=="ㅁㄴㅇ"
assert merge_hypotheses("x> 두문장","x> 아주 자연스러운 두 문장","x> 아주 자연스러운 두 문장")=="두문장"
assert merge_hypotheses("x> 대마판","x> 대만판","x> 대마판")=="대마판"
assert merge_hypotheses("x> 대마판","x> 대만판","x> 대만판")=="대만판"
assert merge_hypotheses("x> 한정파 주문했어","x> 한정판 주문했어",
                        "x> 한정판 주문했어")=="한정판 주문했어"
assert merge_hypotheses("x> 영어만","x> 한글 단어를 마음대로 더한다",
                        "x> 한글 단어를 마음대로 더한다")=="영어만"
assert merge_hypotheses("x> TEST","x> 한글입니다","x> 한글입니다")=="TEST"
assert merge_hypotheses("x> 축하합니다","x> 축하해요","x> 축하해요")=="축하합니다"

# No additional near-match caption line: the old partial recognized
# line is the anchor; new content must be identical in both pixel reads.
base="두 번째 자막은 여기 있습니다"
read1="첫 번째 자막은 여기 있습니다\n"+base
read2="첫 번째 자막은 거기 있습니다\n"+base
with patch("tess_backend.read",side_effect=[
        (read1,[],88),(read2,[],90)]):
    assert restore_white_subtitle(photo,base,"한국어")==base

print("v0.4.14 hallucination gate PASS: pixel grid vs text, "
      "disagreeing glyph, low OCR evidence, no semantic paraphrase, "
      "no invented words and no near-match subtitle")
