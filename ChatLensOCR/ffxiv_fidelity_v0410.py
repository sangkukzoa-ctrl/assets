# -*- coding: utf-8 -*-
"""Strict pixel-read consensus for FFXIV chat; no grammar-based correction.

Tesseract contrast/mask passes are the SAME OCR model. Their agreement is
a useful proposal, not independent human verification. Only a one-glyph
change in an existing Hangul word, agreed on by BOTH pixel passes, may be
applied. No new words, line completions, dictionary replacements, or
inference of intended meaning are allowed.
"""
import re
import numpy as np
from PIL import Image

_KOR=re.compile(r'[가-힣]')

def _body(value):
    if not value:return None
    pos=value.find('>')
    return value[pos+1:].strip() if pos>=0 else None

def merge_hypotheses(base,boost,overlay):
    """Preserve raw source unless BOTH OCR variants agree on an exact edit."""
    old=_body(base) if '>' in base else base.strip()
    first=_body(boost)
    second=_body(overlay)
    if not old or not _KOR.search(old) or not first or not second:return old
    old_words=old.split()
    one=first.split()
    two=second.split()
    # There must be no change in words, order, or line structure.
    if not (len(old_words)==len(one)==len(two)):return old
    fixed=[]
    for source,a,b in zip(old_words,one,two):
        if a==b and a!=source and len(source)==len(a) and _KOR.search(source):
            edits=sum(x!=y for x,y in zip(source,a))
            # A single directly observed Hangul-glyph disagreement is the
            # largest substitution permitted. Both readings must be EXACT.
            positions=[i for i,(x,y) in enumerate(zip(source,a)) if x!=y]
            if edits==1 and len(positions)==1:
                j=positions[0]
                if _KOR.fullmatch(source[j]) and _KOR.fullmatch(a[j]):
                    fixed.append(a)
                    continue
        fixed.append(source)
    return " ".join(fixed)

def isolate_warm_chat(crop):
    """Separate the warm green-yellow chat glyphs from the game background."""
    a=np.asarray(crop.convert('RGB')).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    ink=(r>145)&(g>150)&((r-b)>32)
    if ink.sum()<max(35,crop.width//6) or ink.sum()>ink.size*.50:
        return None
    return Image.fromarray(np.where(ink,0,255).astype('uint8'),mode='L')

def refine_ffxiv_dialogue(crop,original,speaker,language):
    """Preserve the original speaker; verify the dialogue with two pixel reads."""
    if language!='한국어' or not speaker or '>' not in original:return original
    source=original.split('>',1)[-1]
    if not _KOR.search(source) and not re.search(r'\d[A-Za-z]|[A-Za-z]\d',source):
        return original # Don't rewrite legitimate English dialogue as Korean.
    ink=isolate_warm_chat(crop)
    if ink is None:return original
    from tess_backend import read
    def enlarge(im):
        return im.resize((im.width*4,im.height*4),Image.Resampling.LANCZOS)
    gray=np.asarray(crop.convert('L')).astype(np.float32)
    boosted=Image.fromarray(np.uint8(np.clip((gray-25)*1.7,0,255)))
    alt,_,_=read(enlarge(boosted),'파판14','한국어',psm=7)
    warm,_,_=read(enlarge(ink),'파판14','한국어',psm=7)
    def valid(text):
        if not text or '>' not in text:return ''
        header=text.split('>',1)[0]
        return text if re.sub(r'\s+','',speaker) in re.sub(r'\s+','',header) else ''
    alt=valid(alt)
    warm=valid(warm)
    if not alt and not warm:return original
    result=merge_hypotheses(original,alt,warm)
    body=source.strip()
    return original.split('>',1)[0]+'>'+' '+result if result and result!=body else original
