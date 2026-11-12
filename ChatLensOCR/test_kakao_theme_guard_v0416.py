# -*- coding: utf-8 -*-
"""v0.4.16 KakaoTalk routing regression with synthetic pixel evidence.

Kakao's blue/gray flat chat background is not the same as a blue game,
even when the game has many yellow characters or flashes. No private
actual chat or full-screen game frame is embedded in this public test.
"""
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from layout_v2 import detect_mode

font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",17)
chat=Image.new("RGB",(357,945),(186,206,224))
draw=ImageDraw.Draw(chat)
for i in range(8):
    y=38+i*103
    if i%2==0:
        draw.rectangle((102,y,340,y+60),fill=(255,225,15))
        draw.text((110,y+13),"테스트 문장 123",font=font,fill=(22,22,22))
    else:
        draw.rectangle((17,y,218,y+59),fill=(255,255,255))
        draw.text((25,y+10),"다른 사람의 문장",font=font,fill=(22,22,22))
assert detect_mode(chat)=="카카오톡"

rng=np.random.default_rng(20261112)
height,width=890,1400
noise=rng.normal(0,43,(height,width,1))
pixels=np.clip(np.array([105,145,165])+noise+
               rng.normal(0,8,(height,width,3)),0,255).astype("uint8")
game=Image.fromarray(pixels,"RGB")
draw=ImageDraw.Draw(game)
for i in range(8):
    x=(i*171)%1200
    y=65+i*92
    draw.rectangle((x,y,x+115,y+23),fill=(248,214,73))
# This was exactly the old false-positive condition: blue median and yellow.
rgb=np.asarray(game.convert("RGB"))
h,w=rgb.shape[:2]
sample=rgb[int(h*.1):int(h*.9):max(1,h//120),::max(1,w//120)]
bg=np.median(sample.reshape(-1,3),axis=0)
yellow=((rgb[:,:,0]>225)&(rgb[:,:,1]>165)&(rgb[:,:,2]<145)).sum()
assert yellow>140 and bg[2]>bg[0]+12 and bg[1]>bg[0]+8 and bg[2]<245
assert detect_mode(game)=="범용","Vivid game misidentified as Kakao"

flat=Image.new("RGB",(1100,700),(186,206,224))
assert detect_mode(flat)=="범용", "Blue without speech bubbles is not a chat"
print("v0.4.16 chat background and anti-false-positive game routing PASS")
