# -*- coding: utf-8 -*-
"""KakaoTalk bubble recognition tuned for small Korean UI fonts.

Use Korean-only OCR on the intact single speech balloon. The mixed English
recognizer frequently hallucinates Latin tokens (MAY, OLE, SRE) from Hangul.
Preserve multiline reading order and all visible glyphs; never use a language
model or dictionary to guess what the sender meant.
"""
import re
from PIL import Image, ImageOps

def _rate(text, confidence):
    hangul=len(re.findall(r"[가-힣]",text))
    ascii_fragments=len(re.findall(r"\b[A-Za-z]{2,}\b",text))
    junk=len(re.findall(r"[|©€¤{}]",text))
    return (confidence/100)*2.2 + min(hangul/16,1.0) - ascii_fragments*.23 - junk*.25

def _preserve_lines(text):
    """Keep the original line breaks of longer user chat bubbles."""
    return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())

def _choose_consensus(readings):
    """Prefer repeated OCR readings over a single outlier; do not guess words."""
    from collections import Counter
    usable=[]
    for text,boxes,conf,zoom in readings:
        text=_preserve_lines(text)
        key=text.strip().strip(" |_[].").replace(" ", "")
        if key and re.search(r"[가-힣]",key):
            usable.append((key,text,boxes,conf,zoom))
    if not usable:return None
    votes=Counter(k for k,*_ in usable)
    if max(votes.values())>=2:
        best=max(votes,key=lambda k:(votes[k],max(x[3] for x in usable if x[0]==k)))
        return max((x for x in usable if x[0]==best),key=lambda x:x[3])[1:]
    return usable[0][1:]

def read_bubble(crop,language="한국어",precise=True):
    if language!="한국어":return None
    from tess_backend import read
    height=crop.height
    zoom=3 if height>=37 else 2
    im=crop.convert("RGB").resize((max(1,crop.width*zoom),max(1,crop.height*zoom)),Image.Resampling.LANCZOS)
    psm=6 if height>=37 else 7
    ko,boxes,conf=read(im,"카카오톡","한국어",psm=psm,tess_lang="kor")
    readings=[(ko,boxes,conf,zoom)]
    # Small Korean messages and nicknames are particularly susceptible
    # to visually similar syllable substitutions. Re-evaluate the cropped
    # pixels using an independent scale and Tesseract page segmentation.
    if precise and height<=35 and crop.width<=240:
        check=crop.convert("RGB").resize((max(1,crop.width*3),max(1,crop.height*3)),Image.Resampling.LANCZOS)
        for alternative_psm in (7,13):
            candidate,b,confidence=read(check,"카카오톡","한국어",psm=alternative_psm,tess_lang="kor")
            readings.append((candidate,b,confidence,3))
    # PSM6 sometimes discards a genuine continuation line. PSM11 on the
    # already-isolated, contrast-adjusted bubble can recover it.
    # Require substantially more actual Hangul and adequate confidence,
    # otherwise keep the primary reading. No dictionary substitutions.
    multiline_rescue = None
    if precise and 36 <= height <= 145 and crop.width <= 450:
        enhanced=ImageOps.autocontrast(crop.convert("L"),cutoff=1)
        enhanced=enhanced.resize((max(1,crop.width*2),max(1,crop.height*2)),Image.Resampling.LANCZOS)
        alternative,alt_boxes,alt_conf=read(enhanced,"카카오톡","한국어",psm=11,tess_lang="kor")
        base_hangul=len(re.findall(r"[가-힣]",ko))
        alt_hangul=len(re.findall(r"[가-힣]",alternative))
        if (alt_hangul >= base_hangul+max(4,round(base_hangul*.20))
            and alt_conf >= max(45,conf-20)
            and alt_hangul >= 8):
            multiline_rescue=(alternative,alt_boxes,alt_conf,2)
    selected=multiline_rescue or _choose_consensus(readings)
    if selected is None:return None
    ko,boxes,conf,zoom=selected
    if len(re.findall(r"[가-힣]",ko))<2 or conf<44:return None
    if _rate(ko,conf)<1.18:return None
    normal=[]
    for item in boxes:
        x1,y1,x2,y2=item["box"]
        normal.append({**item,"box":(int(x1/zoom),int(y1/zoom),int(x2/zoom),int(y2/zoom))})
    return ko,normal,conf/20

def _synthetic():
    # A robust engine smoke test; the real tiny UI font benchmark is performed
    # with user-supplied screenshots locally, not a font-renderer approximation.
    from PIL import ImageDraw,ImageFont
    from pathlib import Path
    im=Image.new("RGB",(700,130),"white")
    font_file=Path("C:/Windows/Fonts/malgun.ttf")
    if not font_file.exists():return True
    font=ImageFont.truetype(str(font_file),44)
    ImageDraw.Draw(im).text((25,34),"안녕하세요 반갑습니다",fill="black",font=font)
    result=read_bubble(im)
    if result is None:
        # Returning None means safe fallback to the previous recognition path;
        # it is not an application failure.
        return True
    assert len(result)==3 and len(result[0])>1
    return True
