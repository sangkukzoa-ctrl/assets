# -*- coding: utf-8 -*-
"""Synthetic-only four-line pale-gold subtitle review regression.

No real user's screenshots or transcript are embedded in this test.
"""
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from outlined_caption_v0420 import outlined_caption_box
from layout_v2 import generic
from review_v046 import UNREADABLE_MARKER,review_positions

w,h=697,536
im=Image.new("RGB",(w,h),(23,27,33))
draw=ImageDraw.Draw(im)
font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",27)
lines=["이것은 시험용 문자열입니다!",
       "네번째 줄을 알아봅시다",
       "여전히 원문만을 보존합니다",
       "실제로 보이는 것만 판독"]
for k,text in enumerate(lines):
    draw.text((8,367+k*39),text,font=font,
              fill=(249,231,139),stroke_width=2,stroke_fill=(7,7,5))
box=outlined_caption_box(im)
assert box is not None and box[1]>300,box

def no_original(img,language,precise):
    return []
with patch("app.recognize",side_effect=no_original),\
     patch("generic_subtitle_fidelity_v0412.restore_white_subtitle",
           side_effect=lambda image,text,lang:text),\
     patch("generic_blank_caption_v0413.recover_empty_caption",
           side_effect=lambda image,text,lang:text):
    mode,output,hits,meta,raw=generic(im,"한국어",True)
assert mode=="범용" and output==UNREADABLE_MARKER,output
assert review_positions(output)==[(0,len(UNREADABLE_MARKER))]
assert len([v for v in meta if v.get("type")=="unreadable_outlined_caption"])==1
assert meta[-1]["needs_review"] and not meta[-1]["human_verified"]
assert not hits and not raw

# A blank photo or an icon must not become an invented sentence or review.
blank=Image.new("RGB",(w,h),(23,27,33))
assert outlined_caption_box(blank) is None
mono=Image.new("RGB",(w,h),(255,255,255))
ImageDraw.Draw(mono).text((50,400),"NO CAPTION",font=font,fill=(0,0,0))
assert outlined_caption_box(mono) is None
assert outlined_caption_box(Image.new("RGB",(240,200),"yellow")) is None
# Dense horizontal gridlines distinguish specification tables from video
# footage even when bottom rows contain yellow labels.
gridded=im.copy()
grid_draw=ImageDraw.Draw(gridded)
for yy in range(15,275,24):
    grid_draw.line((0,yy,w-1,yy),fill=(210,210,210),width=2)
assert outlined_caption_box(gridded) is None


# If OCR already found text, it must survive byte-for-byte unchanged.
with patch("app.recognize",return_value=[
        {"text":"VISIBLE OCR", "score":.95,
         "box":(30,400,220,435)}]),\
     patch("generic_subtitle_fidelity_v0412.restore_white_subtitle",
           side_effect=lambda image,text,lang:text):
    result=generic(im,"한국어",True)
assert result[1]=="VISIBLE OCR",result[1]
print("v0.4.20 outlined caption pixel detector and unreadable review marker "
      "without invented text PASS")
