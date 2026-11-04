# -*- coding: utf-8 -*-
"""FFXIV Frontline results scoreboard OCR.

Scoreboard is a table of characters and numeric statistics, NOT KakaoTalk
speech bubbles. Detect its beige HUD and read row-aligned cells separately.
"""
import re
import numpy as np
from PIL import Image

HEADERS=("캐릭터","서버","K","D","A","총 공격량","총 피해량","총 회복량","총 확보 시간")
COLUMNS=((50,228),(229,354),(354,394),(394,433),(433,472),
         (472,611),(611,752),(752,839),(839,930))

def is_scoreboard(image):
    if image.width<700 or image.height<440:return False
    a=np.asarray(image.convert("RGB")).astype(np.int16)
    h,w=a.shape[:2]
    mid=a[int(h*.33):int(h*.88)]
    beige=(mid[:,:,0]>195)&(mid[:,:,1]>175)&(mid[:,:,2]>155)&(mid[:,:,0]<245)
    if beige.mean()<.70:return False
    return len(row_bands(image))>=7

def row_bands(image):
    a=np.asarray(image.convert("RGB")).astype(np.int16)
    h,w=a.shape[:2]
    if w<700:return []
    col=a[:,round(w*50/938):round(w*229/938)]
    high=col.max(axis=2);low=col.min(axis=2)
    ink=(high<150)&(low<145) | ((high-low>55)&(low<145))
    count=ink.sum(axis=1)
    valid=(count>=8)&(np.arange(h)>=int(h*.35))&(np.arange(h)<int(h*.90))
    coords=np.flatnonzero(valid)
    if not len(coords):return []
    runs=[];start=last=int(coords[0])
    for y in coords[1:]:
        y=int(y)
        if y-last>3:
            if 7<=last-start+1<=22:runs.append((start,last+1))
            start=y
        last=y
    if 7<=last-start+1<=22:runs.append((start,last+1))
    if len(runs)<7:return []
    # Overlap/duplicate headings don't create extra score rows.
    return runs

def _read_cell(image,bounds,lang,zoom=3):
    from tess_backend import read
    x0,y0,x1,y1=bounds
    if x1-x0<4 or y1-y0<4:return "",[],0.
    roi=image.crop((x0,y0,x1,y1))
    up=roi.resize((roi.width*zoom,roi.height*zoom),Image.Resampling.LANCZOS)
    raw,boxes,conf=read(up,"범용",lang,psm=7,
        tess_lang="eng" if lang=="영어" else None)
    content=" ".join(raw.split()).strip()
    normalized=[]
    for entry in boxes:
        x,y,xx,yy=entry["box"]
        normalized.append({**entry,
          "box":(int(x/zoom+x0),int(y/zoom+y0),
                 int(xx/zoom+x0),int(yy/zoom+y0))})
    return content,normalized,conf

def analyze(image,language="한국어"):
    if not is_scoreboard(image):return None
    bands=row_bands(image)
    w,h=image.size
    sx=w/938.
    head,_items,_=_read_cell(image,(round(215*sx),0,round(735*sx),
                                  max(36,round(.07*h))),language)
    # Character name and server world are two separate columns. Numeric
    # values are read with English-digits OCR to preserve their exact format.
    output=["[전장 스코어보드] "+(head or "경기 결과"),
            "\t".join(HEADERS)]
    metadata=[];raw=[]
    for idx,(first,last) in enumerate(bands):
        center=(first+last)/2
        y0=max(0,round(center-12));y1=min(h,round(center+12))
        values=[]
        for ci,(a,b) in enumerate(COLUMNS):
            x0=max(0,round(a*sx));x1=min(w,round(b*sx))
            text,boxes,confidence=_read_cell(image,(x0,y0,x1,y1),
                                            language if ci<2 else "영어")
            # Short stat fields are digits or mm:ss, not Korean prose.
            if ci>=2:
                text=re.sub(r"[^\d:]","",text)
            if ci==0:
                # The alliance marker (A/B/C) appears before the character
                # and is retained when OCR successfully recognizes it.
                text=text.strip()
            values.append(text if text else "[미인식]")
            raw.extend(boxes)
        output.append("\t".join(values))
        metadata.append({"type":"scoreboard_row","index":idx+1,
                         "y":round(center),"cells":values})
    return "파판14","\n".join(output),[],metadata,raw

def _synthetic():
    from PIL import ImageDraw,ImageFont
    im=Image.new("RGB",(938,659),(230,222,213))
    d=ImageDraw.Draw(im)
    font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",15)
    for i in range(11):
        y=239+i*32.5
        d.text((51,int(y)),"A현시완",font=font,fill=(66,85,33))
        d.text((244,int(y)),"모그리",font=font,fill=(44,44,44))
    bands=row_bands(im)
    assert len(bands)==11,bands
    assert is_scoreboard(im)
    return True
