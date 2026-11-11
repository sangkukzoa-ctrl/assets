# -*- coding: utf-8 -*-
"""Recover white captions when generic OCR returned no text.

Independent pixel normalizations must agree. Never reconstruct words using
plot context, dialogue semantics, personal test data, or a language model.
"""
import re
import numpy as np
from PIL import Image, ImageOps

def _line(text):
    candidates=[]
    for line in str(text).splitlines():
        line=line.strip()
        if not line:continue
        m=re.search(r"[가-힣]",line)
        if m is None:continue
        line=line[m.start():]
        line=re.split(r"\s{3,}",line,maxsplit=1)[0]
        line=line.strip().strip("~ ^!“”\"·-;'|\\『』、").strip()
        korean=len(re.findall(r"[가-힣]",line))
        if korean<5:continue
        if korean/max(1,len(line))<.48:continue
        candidates.append((korean,line))
    return max(candidates,default=(0,""))[1]

def _norm(line):
    return re.sub(r"[^가-힣0-9A-Za-z]","",line)

def recover_empty_caption(image,original,language):
    """Return pixel-backed caption only when whole-image OCR was empty."""
    if original.strip() or language!="한국어":return original
    w,h=image.size
    if w<380 or h<320 or w>1800 or h>1600:return original
    from ocr_hallucination_guard_v0414 import is_repeated_icon_grid
    if is_repeated_icon_grid(image):
        # Inventory item pictures are NOT captions, even when two passes
        # confidently hallucinate the same sequence of Korean syllables.
        return original
    reduced=np.asarray(image.convert("RGB").resize(
        (min(200,w),min(200,h))),dtype=np.int16)
    brightness=reduced.mean(axis=2)
    if brightness.std()<36:return original
    sample=reduced[int(reduced.shape[0]*.68):]
    spread=sample.max(axis=2)-sample.min(axis=2)
    pale=(sample.min(axis=2)>160)&(spread<55)
    if pale.mean()<.003:return original
    y=round(h*.67)
    roi=image.crop((0,y,w,h)).convert("RGB")
    contrast=ImageOps.autocontrast(ImageOps.grayscale(roi))
    a=np.asarray(roi,dtype=np.int16)
    low=a.min(axis=2);span=a.max(axis=2)-low
    white=(low>155)&(span<58)
    white_mask=Image.fromarray(
        np.where(white,0,255).astype("uint8"),"L")
    zoom=3 if w<1300 else 2
    def enlarge(p):
        return p.resize((p.width*zoom,p.height*zoom),
                        Image.Resampling.LANCZOS)
    from tess_backend import read
    results=[]
    # Do not use inverted grayscale as an independent vote; Tesseract
    # auto-inverts many regions, so it can repeat the same recognition error.
    for variant in (contrast,white_mask,roi):
        raw,_,confidence=read(
            enlarge(variant),"범용",language,psm=6,tess_lang="kor")
        line=_line(raw)
        if line:results.append((line,confidence))
    if len(results)<2:return original
    def confident(value):
        # tess_backend supplies mean word confidence in 0..100, but
        # legacy injected tests supply 0..1. Both scales are accepted.
        normalized=value/100 if value>1 else value
        return normalized>=.65
    for i,(a,ca) in enumerate(results):
        for b,cb in results[i+1:]:
            na,nb=_norm(a),_norm(b)
            if len(na)<7 or na!=nb:continue
            # 90% matching is not sufficient: even one different Hangul
            # glyph can completely change what a speaker actually said.
            if not (confident(ca) and confident(cb)):continue
            # This is still OCR agreement, not human-confirmed ground truth.
            # Preserve the exactly recognized character sequence.
            return a if ca>=cb else b
    return original
