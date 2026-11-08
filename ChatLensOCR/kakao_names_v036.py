# -*- coding: utf-8 -*-
"""Read KakaoTalk sender labels from avatar positions, not arbitrary chat bubbles.

KakaoTalk's repeated avatar/name pairs give independent observations of the
same sender; use majority vote, without inventing a personal name.
"""
import re
from collections import Counter
import numpy as np
from PIL import Image

def avatar_rows(img):
    rgb=np.asarray(img.convert("RGB")).astype(np.int16)
    h,w=rgb.shape[:2]
    if h<70 or w<150:return []
    c=np.concatenate([
        rgb[max(0,h//10):max(1,h*9//10),max(0,w//2):max(1,w//2+4)].reshape(-1,3),
        rgb[max(0,h//10):max(1,h*9//10),max(0,w-8):max(1,w-4)].reshape(-1,3)
    ],axis=0)
    if len(c)==0:return []
    bg=np.median(c,axis=0)
    mask=(np.max(np.abs(rgb[:,:min(w,43)]-bg),axis=2)>45)
    sums=mask.sum(axis=1)
    indices=np.flatnonzero(sums>=8)
    if not len(indices):return []
    runs=[];start=last=int(indices[0])
    for idx in indices[1:]:
        idx=int(idx)
        if idx-last>3:
            if 20<=last-start+1<=60:runs.append((start,last+1))
            start=idx
        last=idx
    if 20<=last-start+1<=60:runs.append((start,last+1))
    return runs

def _clean_name(text):
    # Avoid treating nearby timestamps and message text as a name.
    parts=re.findall(r"[가-힣]{2,9}",text)
    # The nickname is usually the rightmost Hangul group beside the avatar.
    return parts[-1] if parts else ""

def resolve(img, fallback="상대"):
    from tess_backend import read
    # Collect multiple OCR observations for the same Kakao sender label.
    # Wide regions can contain the avatar; narrow regions can clip the first
    # syllable. Compare both rather than blindly trusting one reading.
    names=[]
    rows=avatar_rows(img)
    if len(rows)>4:
        rows=[rows[0],rows[len(rows)//2],rows[-1]]
    for top,bottom in rows:
        for x0,x1,topoff in ((43,145,-3),(53,133,-1),(58,119,-1)):
            y0=max(0,top+topoff)
            y1=min(img.height,top+25)
            if y1-y0<12 or x0>=img.width:continue
            crop=img.crop((x0,y0,min(img.width,x1),y1))
            if crop.width<10:continue
            zoom=3
            crop=crop.resize((crop.width*zoom,crop.height*zoom),Image.Resampling.LANCZOS)
            content,boxes,conf=read(crop,"카카오톡","한국어",psm=7,tess_lang="kor")
            name=_clean_name(content)
            if name and conf>=35:names.append((name,conf))
    if not names:return fallback
    all_names={name for name,_ in names}
    resolved=[]
    for name,conf in names:
        # If a tight region has clipped the start of the name, count that
        # observation toward the uniquely matching full-length reading.
        expansions=[longer for longer in all_names if len(longer)>len(name) and longer.endswith(name)]
        if len(expansions)==1:name=expansions[0]
        resolved.append((name,conf))
    counts=Counter(n for n,_ in resolved)
    winning=max(counts,key=lambda n:(counts[n],sum(c for name,c in resolved if name==n),len(n)))
    if counts[winning]==1 and len(resolved)>1:
        return fallback if fallback!="상대" else winning
    return winning

def _synthetic():
    from PIL import ImageDraw
    a=Image.new("RGB",(355,280),(186,206,224))
    d=ImageDraw.Draw(a)
    for y in (20,130):
        d.ellipse((6,y,42,y+37),fill="white",outline=(10,10,10),width=2)
        d.ellipse((15,y+6,29,y+25),fill=(235,159,16))
    rows=avatar_rows(a)
    assert len(rows)==2,rows
    return True
