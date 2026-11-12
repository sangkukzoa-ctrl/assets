# -*- coding: utf-8 -*-
"""v0.4.15 icon inventory anti-hallucination layout regression.

Generated pixels only; no user's inventory screenshot is in the repository.
"""
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
from ocr_hallucination_guard_v0414 import (
    icon_grid_title_crop_bottom,is_repeated_icon_grid
)
from layout_v2 import generic

im=Image.new("RGB",(519,377),(160,160,160))
d=ImageDraw.Draw(im)
font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",18)
d.text((22,8),"Large Chest",font=font,fill=(22,22,22))
for x in range(22,480,54):
    d.line((x,47,x,365),fill=(42,42,42),width=3)
for y in range(47,370,54):
    d.line((22,y,500,y),fill=(42,42,42),width=3)
for i,x in enumerate(range(22,480,54)):
    for j,y in enumerate(range(47,340,54)):
        d.rectangle((x+15,y+15,x+35,y+30),
                    fill=((i*19+45)%150+45,(j*22+50)%150+45,80))

assert is_repeated_icon_grid(im)
top=icon_grid_title_crop_bottom(im)
assert top is not None and 39<=top<=47,top

captured=[]
def read_only_title(crop,language,precise):
    captured.append(crop.size)
    # Simulate RapidOCR's title result; icons would be 300 nonsense words
    # if the crop contained any pixels below the slot border.
    assert crop.height<=top
    return [{"text":"Large Chest","box":(22,10,170,32),"score":.99}]

with patch("app.recognize",side_effect=read_only_title):
    mode,output,hits,metadata,raw=generic(im,"한국어",True)
assert mode=="범용" and output=="Large Chest",output
assert len(raw)==1 and captured==[(im.width,top)],captured
assert metadata[0]["type"]=="icon_grid_title_only"
assert metadata[0]["human_verified"] is False

ordinary=Image.new("RGB",(519,377),"white")
assert icon_grid_title_crop_bottom(ordinary) is None
print("v0.4.15 inventory region filtering, exact title preservation, "
      "no OCR on icon slots, ordinary image exclusion PASS")
