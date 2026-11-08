# -*- coding: utf-8 -*-
"""Regression for embedded game screenshot inside a desktop JPEGView window.

Synthetic only: test rectangles/colors resemble the viewer layout and contain
no private user's chat, filenames, screenshots or OCR transcripts.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ffxiv_viewer_crop_v047 import viewer_chat_box,crop_viewer_chat,restore_coordinates

scene=Image.new("RGB",(1400,630),(23,33,44))
d=ImageDraw.Draw(scene)
# Viewer caption bar from x0..548, y9..52; dark game pixels below.
d.rectangle((0,10,550,53),fill=(241,243,248))
d.rectangle((0,54,550,629),fill=(20,22,26))
for i in range(24):
    y=63+21*i
    d.text((8,y),"[1:20][Party]<Name> TEST 123 ABC",(245,213,140))
# A completely separate application/result pane.
d.rectangle((800,53,1399,629),fill=(34,43,55))
for i in range(24):
    d.text((820,66+19*i),"Other application text 012345",(240,242,243))
box=viewer_chat_box(scene)
assert box is not None,box
x0,y0,x1,y1=box
assert x0==0 and 510<x1<565 and 45<y0<60 and y1==630,box
cropped,coords=crop_viewer_chat(scene)
assert coords==box and cropped.width<565 and cropped.height<590,coords
assert cropped.getpixel((10,10))[0]<80
assert viewer_chat_box(cropped) is None
# Do not erroneously crop a full-screen FF14 screenshot or a regular document.
native=scene.crop((0,54,550,630))
assert viewer_chat_box(native) is None
document=Image.new("RGB",(1400,630),"white")
assert viewer_chat_box(document) is None

record=("파판14","(직업미확인)테스터: 대화",[((10,12,28,29),"현자")],
        [{"y":12,"box":(10,12,28,29),"speaker":"테스터"}],
        [],[{"box":(10,12,28,29),"score":.80,"text":"테스터"}])
fixed=restore_coordinates(record,box)
assert fixed[2][0][0]==(10,12+y0,28,29+y0)
assert fixed[3][0]["y"]==12+y0
assert fixed[5][0]["box"]==(10,12+y0,28,29+y0)

# Pre-existing sticker and automatic FFXIV job icon source remain included.
from auto_job_samples_v047 import learn_verified_icon
from kakao_stickers import _synthetic as sticker_test
assert callable(learn_verified_icon) and sticker_test()
print("Embedded JPEGView FFXIV crop: PASS; titlebar and adjacent OCR removed, coordinates preserved")
