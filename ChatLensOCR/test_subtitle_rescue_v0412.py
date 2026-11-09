# -*- coding: utf-8 -*-
"""Public-safe two-pass subtitle regression without private video frames."""
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from generic_subtitle_fidelity_v0412 import restore_white_subtitle

w,h=545,363
yy,xx=np.mgrid[0:h,0:w]
v=(28+(xx/w)*105+(yy/h)*35).clip(0,150).astype(np.uint8)
scene=Image.fromarray(np.stack([v,v//2+17,v//2+25],axis=2),"RGB")
d=ImageDraw.Draw(scene)
font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",23)
d.text((82,262),"첫 번째 안내문입니다",font=font,fill="white",
       stroke_width=2,stroke_fill="black")
d.text((82,302),"두 번째 안내문입니다",font=font,fill="white",
       stroke_width=2,stroke_fill="black")
base="두 번째 안내문입니다"
readable="첫 번째 안내문입니다\n두 번째 안내문입니다"
with patch("tess_backend.read",side_effect=[
       (readable,[],91),(readable,[],90)]):
    fixed=restore_white_subtitle(scene,base,"한국어")
assert fixed=="첫 번째 안내문입니다\n"+base,fixed
# Do not hallucinate from context when two pixel reads disagree.
with patch("tess_backend.read",side_effect=[
       (readable,[],90),("전혀 다른 안내문입니다\n두 번째 안내문입니다",[],89)]):
    unchanged=restore_white_subtitle(scene,base,"한국어")
assert unchanged==base,unchanged
assert restore_white_subtitle(scene,"","한국어")==""
assert restore_white_subtitle(scene,base,"영어")==base
print("v0.4.12 photo subtitle missing-first-line pixel agreement PASS")
