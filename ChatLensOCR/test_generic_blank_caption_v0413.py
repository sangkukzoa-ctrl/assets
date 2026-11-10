# -*- coding: utf-8 -*-
"""Synthetic-only v0.4.13 blank-caption and false-positive tests.

Never commit screenshots or transcription of the private 166-image dataset.
"""
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from generic_blank_caption_v0413 import _line,recover_empty_caption

font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",25)
w,h=545,363
yy,xx=np.mgrid[0:h,0:w]
v=(15+xx/w*180+yy/h*70).clip(0,235).astype("uint8")
a=np.stack([v,v//2+22,v//2+28],axis=2)
photo=Image.fromarray(a,"RGB")
draw=ImageDraw.Draw(photo)
draw.text((66,302),"화면 아래 자막을 읽습니다",font=font,
          fill="white",stroke_width=2,stroke_fill="black")

assert _line("0\n진동기도 없고, 구역도 없고, 아무런              、") == (
    "진동기도 없고, 구역도 없고, 아무런")
word="화면 아래 자막을 읽습니다"
with patch("tess_backend.read",side_effect=[
        (word,[],.90),(word,[],.89),("",[],0)]):
    assert recover_empty_caption(photo,"","한국어")==word
# One OCR output is never sufficient to assert an invisible sentence.
with patch("tess_backend.read",side_effect=[
        (word,[],.90),("아무 관련 없는 다른 문자입니다",[],.90),
        ("못 읽었습니다",[],0)]):
    assert recover_empty_caption(photo,"","한국어")==""
# Do not treat a low-contrast flat background as a subtitle screenshot.
assert recover_empty_caption(Image.new("RGB",(545,363),"#303030"),
                             "","한국어")==""
# Existing text and the selected non-Korean OCR language are untouched.
assert recover_empty_caption(photo,"Original text","한국어")=="Original text"
assert recover_empty_caption(photo,"","영어")==""
print("v0.4.13 synthetic blank-caption rescue / disagreement / "
      "flat UI exclusion / source preservation PASS")
