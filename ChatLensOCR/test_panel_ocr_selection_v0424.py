# -*- coding: utf-8 -*-
"""Public synthetic PSM7 label evidence and pixel ROI overflow regression."""
from PIL import Image,ImageDraw
from unittest.mock import patch
import sys,types
import panel_grid_v0423 as panel

roi=Image.new('L',(100,30),'white')
def glyph_reader(image,mode,language,psm=None,tess_lang=None):
    scale=image.width//100
    word='Bright Letter' if (scale,psm)==(1,7) else 'Bright Letfer'
    return word,[{'text':word,'box':(1,1,20,15),'score':.85}],90
r=panel._read_roi(roi,'label',glyph_reader,{},'영어')
assert r[0]=='Bright Letter' and r[3] is False,r

def enlarged_reader(image,mode,language,psm=None,tess_lang=None):
    word='Clear Text' if (image.width,psm)==(300,7) else 'Clerra Text'
    confidence=50 if word=='Clear Text' else 90
    return word,[{'text':word,'box':(1,1,20,15),'score':.9}],confidence
r=panel._read_roi(roi,'label',enlarged_reader,{},'영어')
assert r[0]=='Clear Text' and r[3] is False,r

def stable_reader(image,mode,language,psm=None,tess_lang=None):
    word='Stable Label' if psm==7 else 'Wrong'
    return word,[{'text':word,'box':(1,1,20,15),'score':.9}],80
r=panel._read_roi(roi,'label',stable_reader,{},'영어')
assert r[0]=='Stable Label' and r[3] is True,r

# Preserve PSM8-only evidence if PSM7 cannot decode a label.
def isolated_reader(image,mode,language,psm=None,tess_lang=None):
    if psm==7:return '',[],0
    return 'Fallback Token',[{'text':'Fallback Token','box':(1,1,25,18),'score':.91}],93
r=panel._read_roi(roi,'label',isolated_reader,{},'영어')
assert r[0]=='Fallback Token' and r[3] is False,r

def button_reader(image,mode,language,psm=None,tess_lang=None):
    word='Apply' if (psm==8 or image.width==200) else 'Applx'
    return word,[{'text':word,'box':(1,1,20,15),'score':.9}],93
r=panel._read_roi(Image.new('RGB',(100,30),(110,110,110)),
                  'button',button_reader,{},'영어')
assert r[0]=='Apply' and r[3] is True,r

# Eight synthetic controls; only row five has visible label ink at the edge.
im=Image.new('RGB',(850,570),(198,198,198));d=ImageDraw.Draw(im)
rows=[]
for i in range(8):
    y=8+i*62
    d.rectangle((18,y+12,46,y+18),fill=(12,12,12))
    if i==4:d.rectangle((182,y+12,183,y+20),fill=(12,12,12))
    rows.append([y+20,[(185,y,125,40)]])
def reader(image,mode,language,psm=None,tess_lang=None):
    return 'Evidence',[{'text':'Evidence','box':(1,2,20,15),'score':.98}],97
fake_app=types.ModuleType('app')
fake_app.recognize=lambda image,language,precise:[]
fake_app.merge_rows=lambda entries:[]
fake_review=types.ModuleType('review_v046')
fake_review.UNREADABLE_MARKER='[글자 미인식]'
with patch.object(panel,'pixel_control_rows',return_value=rows),patch.dict(
        sys.modules,{'app':fake_app,'review_v046':fake_review}):
    out=panel.analyze(im,'영어',True,reader=reader)
assert out is not None
labels=[m['box'] for m in out[3] if m.get('type')=='pixel_ui_label']
assert len(labels)==8
assert all(b[2]==185 for i,b in enumerate(labels) if i!=4),labels
assert labels[4][2]==189,labels
assert all(m.get('human_verified') is False for m in out[3])
print('v0.4.24 synthetic pixel-label PSM7, PSM8 override guard, button OCR and edge crop PASS')
