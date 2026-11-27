# -*- coding: utf-8 -*-
"""Experimental: recover colored chat body after a confirmed closing delimiter.
No text substitutions or fixed pixel locations. Only a weak orange fringe
adjacent to the confirmed delimiter and a verified blank gap allow rereads.
Keep original results unless two shifted views independently agree.
"""
import re
import unicodedata
import numpy as np


def boundary_offsets(image, x0, x1):
    w,h=image.size
    if not 8<=h<=65 or not 2<=x0<x1<=w or x1-x0<20:
        return ()
    # At most 1/10 of glyph height of residual anti-aliased delimiter.
    max_fringe=max(1,min(3,h//10))
    if x0+max_fringe+4>=x1:return ()
    a=np.asarray(image.crop((x0-2,0,x0+max_fringe+4,h)).convert('RGB')).astype(np.int16)
    r,g,b=a.transpose(2,0,1)
    strong=(r>140)&(g>65)&(b<150)&(r>g+20)&(g>b+8)
    weak=(r>70)&(g>25)&(r>g+12)&(g>b+4)
    if strong[:,1].sum()<max(2,h//9):return ()
    # The adjacent fringe is weaker than the delimiter detector's column
    # threshold and must connect vertically to the strong preceding column.
    n=0
    while n<max_fringe:
        k=2+n
        if not weak[:,k].any():break
        if strong[:,k].sum()>=max(2,h//9):return ()
        prev=weak[:,k-1]
        near=prev.copy();near[1:]|=prev[:-1];near[:-1]|=prev[1:]
        if np.count_nonzero(weak[:,k]&near)<max(1,int(weak[:,k].sum()*.7)):return ()
        n+=1
    if not n:return ()
    # A real gap must not contain a visible glyph of another color, a pale
    # glyph, or any weak orange. Never remove tightly adjacent punctuation.
    pale=np.minimum.reduce([r,g,b])>115
    sat=(np.maximum.reduce([r,g,b])>105)&(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])>35)
    ink=weak|pale|sat
    if ink[:,2+n:2+n+3].any():return ()
    return n+1,n+2


def _norm(t):
    return ' '.join(unicodedata.normalize('NFC',t).split())


def _protected(text):
    # Preserve digit runs, explicit markup (including truncated opening
    # tags), and symbols whose disappearance would corrupt chat semantics.
    return (re.findall(r'\d+',text),re.findall(r'<[^\s<]*>?',text),
            re.findall(r'[<>?□×「」『』]',text))


def guarded_body_reread(image,x0,x1,language,reader,original=None):
    if original is None:original=reader(image,x0,x1,language)
    text,boxes,score=original
    if language!='한국어' or not text.strip():return original
    offsets=boundary_offsets(image,x0,x1)
    if not offsets:return original
    # Do not reread stable high-confidence fully Korean content unnecessarily.
    if score>=90 and not re.search(r'[A-Za-z]|^[.,;:_\'"`]',text):return original
    # If the upstream result replaced text and no longer has native boxes,
    # only permit a pure leading-punctuation correction (no word mutation).
    try: votes=[reader(image,x0+s,x1,language) for s in offsets]
    except Exception:return original
    a,b=votes
    if not _norm(a[0]) or _norm(a[0])!=_norm(b[0]):return original
    candidate=_norm(a[0]);min_conf=min(float(a[2]),float(b[2]))
    if candidate==_norm(text) or min_conf<80 or min_conf<float(score)+3:return original
    if _protected(text)!=_protected(candidate):return original
    if not any('가'<=ch<='힣' for ch in candidate):return original
    # A changed Latin run must be traceable to a low-confidence native OCR
    # token. Without that evidence, preserve the original literal content.
    for run in re.findall(r'[A-Za-z]+',text):
        if candidate.count(run)>=text.count(run):continue
        hits=[box for box in boxes if run in str(box.get('text',''))]
        if not hits or any(float(box.get('score',0))>=.65 for box in hits):return original
    if not boxes and _norm(text).lstrip('.,;:_\'"` ')!=candidate:return original
    # Do not return word geometry from a differently positioned crop.
    return candidate,[],min_conf
