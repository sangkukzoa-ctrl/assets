# -*- coding: utf-8 -*-
"""Round-2 localized transcription regressions. Synthetic images only."""
import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import layout_v2
from kakao_korean import _choose_consensus,_preserve_lines
from shop_grid_v0374 import _synthetic
src=(ROOT/"layout_v2.py").read_text(encoding="utf-8")
assert 'return "\\n".join(lines),all_boxes,sum(sc)/max(1,len(sc))'.replace('\\\\','\\') in src

img=Image.new("RGB",(200,100),"white")
d=ImageDraw.Draw(img)
d.rectangle((8,10,80,18),fill="black")
d.rectangle((23,65,95,74),fill="black")
def fake_variants(crop,*args):
    import numpy as np
    a=np.asarray(crop.convert("L"));ys,xs=np.where(a<110)
    if len(xs)==0:return "",[],0
    return ("첫째 줄" if xs.min()<10 else "둘째 줄"),[],85
with patch("kakao_korean.read_bubble",lambda *args:None),patch.object(layout_v2,"_variants",fake_variants):
    txt,boxes,conf=layout_v2._bubble_text(img,"한국어",True)
    assert txt=="첫째 줄\n둘째 줄",repr(txt)
    assert conf>0
assert _choose_consensus([("덜뚱이가",[],91,2),("덜팽이가",[],80,3),("덜팽이가",[],86,3)])[0]=="덜팽이가"
# Without agreement, retain the first source's candidate. Never auto-map 퉤/튀.
assert _choose_consensus([("퉤",[],81,2),("튀",[],97,3),("",[],0,3)])[0]=="퉤"
assert _preserve_lines("가나다   라마\n바사 아자")=="가나다 라마\n바사 아자"
# One multiline bubble: alternative OCR must recover an omitted second line.
import types
from unittest.mock import patch as mock_patch
import kakao_korean
backend=types.ModuleType("tess_backend")
def stub_read(img,mode,lang,psm=6,tess_lang=None):
    if psm==11:
        return ("올라올거면 10일에 알바끝난 날 데리고\n가는게 미션이다.",[],75)
    return ("알바끝난 날 데리고",[],66)
backend.read=stub_read
with mock_patch.dict(sys.modules,{"tess_backend":backend}):
    rescued=kakao_korean.read_bubble(Image.new("RGB",(225,40),"white"),"한국어",True)
    assert rescued is not None and "가는게 미션이다." in rescued[0],rescued
assert _synthetic()
print("Round2 PASS: multiline preservation, disagreement safety, 5-column card segmentation")
