# -*- coding: utf-8 -*-
"""Public-safe synthetic geometry and no-guess OCR regression."""
from PIL import Image,ImageDraw,ImageFont
from unittest.mock import patch
import sys,types
from panel_grid_v0423 import pixel_control_rows,analyze

im=Image.new('RGB',(850,570),(197,197,197))
d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20) if __import__('os').name=='nt' else ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
for i in range(8):
 y=55+i*60
 d.text((8,y+5),'Option '+str(i),fill=(30,30,30),font=font)
 d.rectangle((202,y,325,y+40),outline=(12,12,12),fill=(116,116,116),width=3)
 d.text((229,y+7),'Apply',fill=(243,243,243),font=font)
assert pixel_control_rows(im) is not None
assert sum(len(row[1]) for row in pixel_control_rows(im))==8
assert pixel_control_rows(Image.new('RGB',(850,570),'white')) is None
assert pixel_control_rows(Image.new('RGB',(850,570),(15,15,15))) is None
assert pixel_control_rows(Image.new('RGB',(850,570),(195,210,225))) is None
assert pixel_control_rows(Image.new('RGB',(350,570),(190,190,190))) is None
many_black=im.copy();drawer=ImageDraw.Draw(many_black)
drawer.rectangle((450,70,540,100),fill='black')
drawer.rectangle((450,130,540,160),fill='black')
assert pixel_control_rows(many_black) is None

fake_app=types.ModuleType('app')
fake_app.recognize=lambda image,language,precise: []
fake_app.merge_rows=lambda value:[]
fake_review=types.ModuleType('review_v046')
fake_review.UNREADABLE_MARKER='[글자 미인식]'
with patch.dict(sys.modules,{'app':fake_app,'review_v046':fake_review}):
 calls=[]
 def text_reader(image,mode,language,psm=None,tess_lang=None):
  calls.append((mode,language,psm,tess_lang,image.size))
  return ('Test', [{'text':'Test','score':.97,'box':(1,2,25,15)}],97)
 result=analyze(im,'영어',True,reader=text_reader)
 assert result is not None
 mode,output,hits,metadata,boxes=result
 assert mode=='범용' and output.count('Test')>=16,output
 assert metadata[0]['control_count']==8 and metadata[0]['row_count']==8
 assert not hits and len(boxes)>=16
 assert all(value['box'][2]>value['box'][0] for value in boxes)
 assert all(not v.get('human_verified',True) for v in metadata)
 assert all(z[3]=='eng' for z in calls)
 assert analyze(im,'영어',False,reader=text_reader) is None
print('v0.4.23 pixel UI: true rectangles only, 8 buttons, label/field OCR, no invented word dictionary PASS')