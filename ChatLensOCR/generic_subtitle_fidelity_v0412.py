# -*- coding: utf-8 -*-
"""Conservative, pixel-backed recovery of missing lines in white subtitles.

Only adds a missing subtitle line when the *existing* OCR output already
contains another line from the same visible region AND two independent
Tesseract language passes agree. No contextual reconstruction or guesses.
"""
import difflib
import re
import numpy as np
from PIL import Image

def _normal(value):
    return re.sub(r"[^가-힣A-Za-z0-9]","",value)

def _lines(value):
    return [v.strip() for v in value.splitlines()
            if len(_normal(v.strip()))>=4]

def restore_white_subtitle(image,original,language):
    if language!="한국어" or not original or len(re.findall("[가-힣]",original))<4:return original
    w,h=image.size
    if not (380<=w<=1600 and 250<=h<=1050):return original
    rgb=np.asarray(image.convert("RGB"),dtype=np.int16)
    # Photographic material has spatial contrast: a flat UI or document is
    # not a reason to add new text from the bottom of the screenshot.
    gray=np.asarray(image.convert("L"),dtype=np.uint8)
    if float(gray.std())<38:return original
    top=round(h*.67)
    r,g,b=[rgb[top:,:,i] for i in range(3)]
    spread=np.maximum(np.maximum(r,g),b)-np.minimum(np.minimum(r,g),b)
    ink=(r>165)&(g>165)&(b>165)&(spread<40)
    fraction=float(ink.mean())
    if not (.004<fraction<.18):return original
    mask=Image.fromarray(np.where(ink,0,255).astype("uint8"),mode="L")
    mask=mask.resize((mask.width*3,mask.height*3),Image.Resampling.LANCZOS)
    from tess_backend import read
    korean,_,ck=read(mask,"범용",language,psm=6,tess_lang="kor")
    mixed,_,cm=read(mask,"범용",language,psm=6,tess_lang="kor+eng")
    k_lines=_lines(korean)
    m_lines=_lines(mixed)
    if len(k_lines)<2 or len(m_lines)<2:return original
    base=_normal(original)
    # A surviving line anchors the new candidate to the existing output.
    def anchored(lines):
        return any(_normal(line) in base
                   for line in lines if len(_normal(line))>=6)
    if not anchored(k_lines) or not anchored(m_lines):return original
    result=[]
    for line in k_lines:
        normalized=_normal(line)
        if normalized in base:continue
        if len(re.findall("[가-힣]",line))<4:continue
        # An already-recognized second line must not corroborate an
        # unrelated *new* first line merely through common Hangul suffixes.
        if not any(difflib.SequenceMatcher(
                None,normalized,_normal(other)).ratio()>=.78
                for other in m_lines if _normal(other) not in base):continue
        result.append(line)
    if not result:return original
    # Preserve the existing exact recognized text, including punctuation.
    return "\n".join(result+[original])
