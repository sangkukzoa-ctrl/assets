# -*- coding: utf-8 -*-
"""Final Fantasy XIV high-density, timestamp-free battle log OCR.

Unlike chat messages, combat events have no '<speaker>' and must never be
appended to the preceding line. A chromatic-ink row detector preserves each
event as its own line, even on dark, textured battlefield backgrounds.
"""
import re
import numpy as np
from PIL import Image

def _signals(image):
    a=np.asarray(image.convert("RGB")).astype(np.int16)
    if a.shape[1]<250 or a.shape[0]<250:return None
    if (a.mean(axis=2)<75).mean()<.43:return None
    near=a[:,:min(95,a.shape[1])]
    r,g,b=near[:,:,0],near[:,:,1],near[:,:,2]
    pink=(r>145)&(r-g>45)&(b>90)&(b-g>25)
    cyan=(b-r>30)&(b>130)&(g>110)
    if pink.sum()<180 or cyan.sum()<220:return None
    return a

def _runs(rows,gap=1):
    ids=np.flatnonzero(rows)
    if not len(ids):return []
    out=[];first=last=int(ids[0])
    for n in ids[1:]:
        n=int(n)
        if n-last>gap+1:
            out.append((first,last+1))
            first=n
        last=n
    out.append((first,last+1))
    return out

def rows(image):
    a=_signals(image)
    if a is None:return []
    near=a[:,:min(205,a.shape[1])]
    high=near.max(axis=2);low=near.min(axis=2)
    ink=(high>150)&((high-low>35)|(low>120))
    counts=ink.sum(axis=1)
    bands=[(int(y0),int(y1)) for y0,y1 in _runs(counts>=8,1)
           if 7<=y1-y0<=25]
    if len(bands)<10:return []
    gaps=np.diff([y0 for y0,_ in bands])
    if len(gaps)<8 or not (np.mean((gaps>=15)&(gaps<=32))>=.75):
        return []
    return bands

def is_combat(image):
    return len(rows(image))>=10

def analyze(image,language,precise):
    from tess_backend import read
    from app import recognize,merge_rows
    bands=rows(image)
    if not bands:return None
    output=[];metadata=[];raw=[]
    for idx,(top,bottom) in enumerate(bands):
        y0=max(0,top-2);y1=min(image.height,bottom+3)
        clip=image.crop((0,y0,image.width,y1)).convert("RGB")
        # Both Latin character names and Korean skill names can occur.
        big=clip.resize((clip.width*3,clip.height*3),Image.Resampling.LANCZOS)
        text,boxes,confidence=read(big,"파판14",language,psm=7)
        if not text or confidence<30:
            fallback=merge_rows(recognize(big,language,False))
            guess=" ".join(r["text"] for r in fallback)
            if len(guess)>len(text):text=guess
        text=" ".join(text.split())
        if not text:
            # Never silently drop a detected visual line.
            text="[문자 인식 실패]"
        output.append("[전투] "+text)
        metadata.append({"type":"battle_event","row":idx+1,"y":top,
                         "tesseract_confidence":round(confidence,1)})
        for item in boxes:
            x0,b0,x1,b1=item["box"]
            raw.append({**item,"box":(int(x0/3),int(b0/3+y0),
                                       int(x1/3),int(b1/3+y0))})
    return ("파판14","\n".join(output),[],metadata,raw)

def _synthetic():
    from PIL import ImageDraw,ImageFont
    image=Image.new("RGB",(530,380),(22,24,27))
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",13)
    colors=("#fa8ed6","#95e2fd","#f9e2a0","#f3f3f3")
    for i in range(17):
        draw.text((1,4+i*20),"Kharon 톤베리가 부활했습니다",fill=colors[i%4],font=font)
    bands=rows(image)
    assert len(bands)==17,bands
    return True
