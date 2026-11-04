# -*- coding: utf-8 -*-
"""KakaoTalk bubble recognition tuned for small Korean UI fonts.

Use Korean-only OCR on the intact single speech balloon. The mixed English
recognizer frequently hallucinates Latin tokens (MAY, OLE, SRE) from Hangul.
Preserve multiline reading order and all visible glyphs; never use a language
model or dictionary to guess what the sender meant.
"""
import re
from PIL import Image

def _rate(text, confidence):
    hangul=len(re.findall(r"[가-힣]",text))
    ascii_fragments=len(re.findall(r"\b[A-Za-z]{2,}\b",text))
    junk=len(re.findall(r"[|©€¤{}]",text))
    return (confidence/100)*2.2 + min(hangul/16,1.0) - ascii_fragments*.23 - junk*.25

def read_bubble(crop,language="한국어",precise=True):
    if language!="한국어":return None
    from tess_backend import read
    height=crop.height
    # For one-line chat, 2x keeps sub-pixel anti-aliasing; multiline needs 3x.
    zoom=3 if height>=37 else 2
    im=crop.convert("RGB").resize((max(1,crop.width*zoom),max(1,crop.height*zoom)),Image.Resampling.LANCZOS)
    psm=6 if height>=37 else 7
    ko,boxes,conf=read(im,"카카오톡","한국어",psm=psm,tess_lang="kor")
    # On short conventional chat bubbles the separate Korean recognizer gives
    # cleaner words without the erroneous Latin tokens of the joint model.
    if ko:
        ko=" ".join(ko.split())
    if len(re.findall(r"[가-힣]",ko))<2 or conf<44:
        return None
    # Do not accept a transcript with an implausibly high markup ratio.
    if _rate(ko,conf)<1.18:return None
    normal=[]
    for item in boxes:
        x1,y1,x2,y2=item["box"]
        normal.append({**item,"box":(int(x1/zoom),int(y1/zoom),int(x2/zoom),int(y2/zoom))})
    return ko,normal,conf/20

def _synthetic():
    from PIL import ImageDraw,ImageFont
    from pathlib import Path
    im=Image.new("RGB",(278,37),(255,221,0))
    font_file=Path("C:/Windows/Fonts/malgun.ttf")
    if not font_file.exists():return True
    font=ImageFont.truetype(str(font_file),16)
    ImageDraw.Draw(im).text((7,7),"벌써 결론을 지어야해?",fill=(13,13,13),font=font)
    result=read_bubble(im)
    if result is None:
        from tess_backend import read
        big=im.resize((556,74),Image.Resampling.LANCZOS)
        text,_,conf=read(big,"카카오톡","한국어",psm=7,tess_lang="kor")
        raise AssertionError(f"Korean bubble rejected: native={text!r} confidence={conf:.1f}")
    assert "결론" in result[0],result
    return True
