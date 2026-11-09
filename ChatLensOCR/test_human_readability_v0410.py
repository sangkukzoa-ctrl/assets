# -*- coding: utf-8 -*-
"""Ground-truth readability and anti-hallucination regression.

All text and pixels are generated for this test. The user's real screenshots,
chat messages and identifying names are never committed to GitHub.
"""
import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont

sys.path.insert(0,str(Path(__file__).resolve().parent))
from ffxiv_fidelity_v0410 import (
    merge_hypotheses,isolate_warm_chat,refine_ffxiv_dialogue
)
from tess_backend import read

# Context alone must not turn one plausible meaning into another.
assert merge_hypotheses("t> 대만판","t> 대만판","t> 대마판")=="대만판"
assert merge_hypotheses("t> 대마판","t> 대마판","t> 대만판")=="대마판"

# A damaged word is corrected ONLY when other actual OCR pixel readings
# independently contain the replacement; keep uncorroborated words.
source="t> 새상품 한정파 주문했어"
boost="t> 새상품 한정판 주문했어"
isolated="t> 새상품 한정판 주문했어"
assert merge_hypotheses(source,boost,isolated)=="새상품 한정판 주문했어"
assert merge_hypotheses(source,"","")=="새상품 한정파 주문했어"

# Anti-regression: do not concatenate unrelated words just because OCR
# produced the same number of tokens.
raw="t> 초록빛 비슷한글"
broken="t> 초록빛비슷한글 _"
assert merge_hypotheses(raw,broken,"")=="초록빛 비슷한글"

fontpath=Path("C:/Windows/Fonts/malgun.ttf")
font=ImageFont.truetype(str(fontpath),32) if fontpath.exists() else ImageFont.load_default()
# These visually distinguishable but semantically different words must both
# be recognized, not normalized to whichever happens to sound more natural.
for phrase in ("대만판","대마판","한정판"):
    image=Image.new("RGB",(580,100),"white")
    ImageDraw.Draw(image).text((20,15),phrase,fill="black",font=font)
    text,boxes,confidence=read(image,"범용","한국어",psm=7)
    assert phrase in "".join(text.split()),(phrase,repr(text))
    assert isinstance(boxes,list)

scene=Image.new("RGB",(560,38),(18,19,22))
draw=ImageDraw.Draw(scene)
gamefont=ImageFont.truetype(str(fontpath),18) if fontpath.exists() else ImageFont.load_default()
draw.text((3,5),"[0:10][링크 5]<테스터> 새상품 대만판",font=gamefont,fill=(229,231,132))
assert isolate_warm_chat(scene) is not None
# Two independent rereads agree on the word '대만판'. The unchanged nickname
# and channel must remain intact. This tests the complete refinement gate.
original="[0:10][링크 5]<테스터> 새상품 대마판"
same="[0:10][링크 5]<테스터> 새상품 대만판"
with patch("tess_backend.read",side_effect=[(same,[],90),(same,[],90)]):
    fixed=refine_ffxiv_dialogue(scene,original,"테스터","한국어")
assert fixed=="[0:10][링크 5]<테스터> 새상품 대만판",fixed
with patch("tess_backend.read",side_effect=[(same,[],90),(same,[],90)]):
    unchanged=refine_ffxiv_dialogue(scene,original,"다른사람","한국어")
assert unchanged==original,unchanged
assert refine_ffxiv_dialogue(scene,original,"테스터","영어")==original

# Human readable output is judged against the expected text, not against the
# prior OCR version's mistaken transcription.
def distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]+[0]*len(b)
        for j,y in enumerate(b,1):
            current[j]=min(current[j-1]+1,previous[j]+1,
                           previous[j-1]+(x!=y))
        previous=current
    return previous[-1]
gold="새상품 한정판 주문했어"
assert distance(merge_hypotheses(source,boost,isolated),gold)==0
assert distance(source.split(">",1)[-1].strip(),gold)>0
print("v0.4.10 readability: exact Korean target words, pixel-supported fixes, preserved names, hallucination guard PASS")
