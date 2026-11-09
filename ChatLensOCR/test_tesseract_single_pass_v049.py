# -*- coding: utf-8 -*-
"""Compare v0.4.9 one-process Tesseract with previous two-process outputs.

Generated pixels only: no screenshots, names, chat records, or user materials.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pytesseract
from pytesseract import Output
from PIL import Image, ImageDraw, ImageFont
from tess_backend import read, resolve_tesseract_paths

exe,data=resolve_tesseract_paths()
assert exe and data,(exe,data)
pytesseract.pytesseract.tesseract_cmd=exe
import os
os.environ["TESSDATA_PREFIX"]=data
font_path=Path("C:/Windows/Fonts/malgun.ttf")
font=ImageFont.truetype(str(font_path),26) if font_path.is_file() else ImageFont.load_default()

cases=[
    ("한국어",6,"[0:03][채널 5]<테스터> 한글 문장 인식 테스트"),
    ("한국어",7,"[0:04] 개인정보가 없는 실험용 시스템 메시지"),
    ("영어",6,"ChatLens OCR 2026 - image recognition sample"),
]
for language,psm,sentence in cases:
    im=Image.new("RGB",(900,72),"white")
    ImageDraw.Draw(im).text((12,20),sentence,fill="black",font=font)
    lang="kor+eng" if language=="한국어" else "eng"
    old_text=pytesseract.image_to_string(im,lang=lang,config=f"--psm {psm}",timeout=20).strip()
    previous=pytesseract.image_to_data(im,lang=lang,config=f"--psm {psm}",output_type=Output.DICT,timeout=20)
    expected=[]
    for i,word in enumerate(previous["text"]):
        if not word.strip() or float(previous["conf"][i])<=0:continue
        x,y,w,h=(int(previous[k][i]) for k in ("left","top","width","height"))
        expected.append({"text":word.strip(),"score":float(previous["conf"][i])/100,
                         "box":(x,y,x+w,y+h)})
    text,boxes,confidence=read(im,"파판14",language,psm=psm)
    assert text==old_text,(language,psm,"text changed",old_text,text)
    assert boxes==expected,(language,psm,"TSV geometry changed",expected,boxes)
    if expected:
        mean=sum(x["score"]*100 for x in expected)/len(expected)
        assert abs(confidence-mean)<0.001,(language,psm,confidence,mean)

blank=Image.new("RGB",(320,50),"white")
assert isinstance(read(blank,"범용","한국어",psm=7),tuple)
print("v0.4.9 single-pass Tesseract: TXT, TSV, confidence and blank-input compatibility PASS")
