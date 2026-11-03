# -*- coding: utf-8 -*-
"""Windows Explorer details-view OCR, preserving the row/column layout.

The blue archive icons are visual metadata, NEVER part of a filename.
No dictionary spell-correction: punctuation, underscores, capitalization,
version numbers and ellipsis are copied as read.
"""
import re
import numpy as np
from PIL import Image

def _measure(image):
    a=np.asarray(image.convert("RGB"))
    h,w=a.shape[:2]
    left=a[:,:min(27,w)]
    blue=(left[:,:,2].astype("int16")>left[:,:,0].astype("int16")+25)&(left[:,:,2].astype("int16")>left[:,:,1].astype("int16")+12)&(left[:,:,2]>100)
    white=np.mean(np.min(a,axis=2)>220)
    if h<450 or w<570 or white<.79 or int(blue.sum())<1100:
        return None
    x1=min(w-1,max(45,int(w*.44)))
    sample=a[:,30:x1]
    density=(np.max(sample,axis=2)<160).sum(axis=1).astype(float)
    if density.max()<10:return None
    # Find the 28px row rhythm, but allow different Windows scaling.
    scores=[]
    for period in range(23,35):
        corr=np.dot(density[:-period],density[period:])/(1+np.dot(density,density))
        scores.append((corr,period))
    pitch=max(scores)[1]
    if max(scores)[0]<.25:return None
    candidates=[]
    for phase in range(pitch):
        strength=sum(density[y:y+max(8,int(pitch*.48))].sum()
                     for y in range(phase,h-max(8,int(pitch*.48)),pitch))
        candidates.append(strength)
    phase=int(np.argmax(candidates))
    # A complete displayed file row has visible dark text in the name column.
    centers=[]
    for y in range(phase,h-7,pitch):
        start=max(0,y-4);end=min(h,y+max(15,int(pitch*.65)))
        if np.max(density[start:end])>=8:
            centers.append(y)
    if len(centers)<15:return None
    return pitch,centers

def is_explorer(image):
    return _measure(image) is not None

def _ocr_single(crop,lang="eng"):
    from tess_backend import read
    w,h=crop.size
    if w<3 or h<3:return "",[],0.
    factor=2
    big=crop.resize((w*factor,h*factor),Image.Resampling.LANCZOS)
    txt,boxes,conf=read(big,"범용","영어" if lang=="eng" else "한국어",psm=7)
    items=[]
    for v in boxes:
        x1,y1,x2,y2=v["box"]
        items.append({**v,"box":(x1/factor,y1/factor,x2/factor,y2/factor)})
    return " ".join(txt.split()),items,conf

def _batch_metadata(image,x0,x1,centers,pitch,lang="kor+eng"):
    from tess_backend import read
    w,h=image.size
    if x1-x0<5:return [""]*len(centers),[]
    # Scan an entire aligned column once to avoid hundreds of OCR subprocesses.
    region=image.crop((x0,0,x1,h))
    text,parts,conf=read(region,"범용","한국어" if lang!="eng" else "영어",psm=6)
    rows=[[] for _ in centers]
    raw=[]
    for t in parts:
        x1b,y1b,x2b,y2b=t["box"]
        cy=(y1b+y2b)*.5
        index=min(range(len(centers)),key=lambda i:abs(centers[i]+pitch*.16-cy))
        if abs(centers[index]+pitch*.16-cy)>pitch*.65:continue
        rows[index].append((x1b,t["text"]))
        raw.append({**t,"box":(x0+x1b,y1b,x0+x2b,y2b)})
    return [" ".join(t for _,t in sorted(group)).strip() for group in rows],raw

def analyze(image,language="한국어"):
    geometry=_measure(image)
    if geometry is None:return None
    pitch,centers=geometry
    w,h=image.size
    name_end=int(w*.478)
    dates,raw_dates=_batch_metadata(image,int(w*.48),int(w*.666),centers,pitch)
    kinds,raw_kinds=_batch_metadata(image,int(w*.66),int(w*.868),centers,pitch)
    sizes,raw_sizes=_batch_metadata(image,int(w*.865),w,centers,pitch,"eng")
    outputs=[];diagnostics=[];raw=raw_dates+raw_kinds+raw_sizes
    for i,top in enumerate(centers):
        y0=max(0,top-5);y1=min(h,top+max(16,int(pitch*.60)))
        x0=29
        filename,parts,conf=_ocr_single(image.crop((x0,y0,name_end,y1)))
        # Preserve all detected rows, including low-confidence ones.
        for t in parts:
            b=t["box"];raw.append({**t,"box":(int(b[0]+x0),int(b[1]+y0),int(b[2]+x0),int(b[3]+y0))})
        outputs.append("\t".join((filename or "[파일명 인식 실패]",dates[i],kinds[i],sizes[i])))
        diagnostics.append({"row":i+1,"y":top,"name":filename,"score":conf,
                            "date":dates[i],"kind":kinds[i],"size":sizes[i]})
    return "범용","\n".join(outputs),[],diagnostics,raw

def _synthetic():
    from PIL import ImageDraw,ImageFont
    w,h=807,28*40+10
    im=Image.new("RGB",(w,h),"white")
    d=ImageDraw.Draw(im)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",12)
    for i in range(40):
        y=8+i*28
        d.rectangle((7,y,21,y+12),fill=(0,100,215))
        d.text((30,y),f"RGBBlocks_1.2.4_patch_{i:02d}.zip",font=font,fill="black")
        d.text((390,y),"2026-05-18 7:05",font=font,fill=(75,75,75))
        d.text((540,y),"ZIP File",font=font,fill=(70,70,70))
        d.text((705,y),"12KB",font=font,fill=(70,70,70))
    geo=_measure(im)
    assert geo and len(geo[1])==40,geo
    return True
