# -*- coding: utf-8 -*-
"""Synthetic release CI tests; no personal screenshots or private chat data."""
from PIL import Image, ImageDraw
from shop_grid_v0374 import _synthetic,card_boxes,analyze
assert _synthetic()
canvas=Image.new('RGB',(1100,660),'white')
d=ImageDraw.Draw(canvas)
for row in range(2):
    for col in range(5):
        x=58+col*210;y=75+row*280
        d.rectangle((x,y,x+124,y+58),fill='#222222')
        d.rectangle((x+50,y+185,x+79,y+201),fill='#000000')
seen=[]
def fake_reader(crop,lang,precise):
    seen.append(crop.size)
    return 'TEST ITEM', [{'text':'TEST ITEM','score':1.,'box':(4,8,60,22)}], 88
result=analyze(canvas,'한국어',True,reader=fake_reader)
assert result is not None
mode,text,hits,meta,raw=result
assert mode=='쇼핑몰' and len(seen)==10 and text.count('[상품 ')==10
assert len(meta)==10 and len(raw)==10
assert all(0<=box['box'][0]<1100 and 0<=box['box'][1]<660 for box in raw)
assert card_boxes(Image.new('RGB',(1100,660),'white')) is None
print('Shop grid: 5 columns × 2 rows, isolated card OCR, offset boxes PASSED')
