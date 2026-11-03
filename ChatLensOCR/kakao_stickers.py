# -*- coding: utf-8 -*-
"""Offline KakaoTalk sticker discovery and user-owned visual template matching.

Detect colored, non-rectangular sticker artwork outside ordinary chat balloons.
Never send images to a server; no language-model guesses about character identity.
"""
import json
import re
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def _groups(rows, gap=12):
    if not len(rows):return []
    out=[];a=last=int(rows[0])
    for v in rows[1:]:
        v=int(v)
        if v-last>gap:
            out.append((a,last));a=v
        last=v
    out.append((a,last))
    return out

def _describe(crop):
    a=np.asarray(crop.convert("RGB")).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    gold=((r>170)&(g>90)&(b<145)&((r-g)>47)&((g-b)>35)).sum()
    pale=((r>226)&(g>226)&(b>215)).sum()
    orange=((r>190)&(g>80)&(g<195)&(b<110)).sum()
    if gold>110 and pale>120:
        return "흰색의 둥근 캐릭터와 노란색 머리 부분, 작은 주황색 부분이 보이며 위에 말풍선이 있는 그림"
    if gold>110:
        return "노란색과 주황색 부분이 있는 캐릭터가 그려진 스티커"
    return "말풍선과 함께 표시된 캐릭터 그림 스티커"

def _signature(im):
    # Perceptual downsample for previously taught stickers; ignore scale.
    a=np.asarray(im.convert("RGB").resize((48,48),Image.Resampling.BILINEAR),dtype=np.float32)/255.0
    return a

def _bank_match(crop):
    try:
        from app import DATA
        folder=DATA/"sticker_samples"
        path=folder/"descriptions.jsonl"
        if not path.exists():return None
        samples={p.name:p for p in folder.glob("*.png")}
        lines=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        target=_signature(crop)
        ranked=[]
        # Maintain backwards compatibility with descriptions saved before
        # the sample filename was added to each JSONL record.
        legacy=iter(sorted(samples.values(),key=lambda x:x.stat().st_mtime))
        for item in lines:
            name=item.get("filename")
            if name in samples:src=samples[name]
            elif not name:
                src=next(legacy,None)
            else:continue
            if src is None:continue
            ref=_signature(Image.open(src))
            distance=float(np.abs(target-ref).mean())
            ranked.append((distance,item.get("description","")))
        if ranked:
            distance,caption=min(ranked)
            if distance<.125 and caption.strip():return caption
    except Exception:pass
    return None

def find_stickers(image,bubbles=()):
    arr=np.asarray(image.convert("RGB")).astype(np.int16)
    h,w=arr.shape[:2]
    if w<200 or h<100:return []
    r,g,b=arr[:,:,0],arr[:,:,1],arr[:,:,2]
    # Saturated orange hair/tail is an anchor, not a claim about which
    # character appears. The larger sticker silhouette is expanded around it.
    art=(r>170)&(g>90)&(b<145)&((r-g)>47)&((g-b)>35)
    art[:,:max(45,int(w*.14))]=False
    art[:,min(175,int(w*.53)):]=False
    # Ignore flat-color message bubbles, whose antialiased glyphs otherwise
    # resemble orange sticker pixels on yellow surfaces.
    for x,y,bw,bh,_ in bubbles:
        if bw>=20:
            art[max(0,y-2):min(h,y+bh+2),max(0,x-2):min(w,x+bw+2)]=False
    counts=art.sum(axis=1)
    output=[]
    for y0,y1 in _groups(np.flatnonzero(counts>=3)):
        region=art[y0:y1+1]
        ys,xs=np.nonzero(region)
        if len(xs)<260 or y1-y0<24:continue
        min_x=int(xs.min());max_x=int(xs.max())
        x1=max(48,min_x-24);x2=min(w-2,max_x+48)
        top=max(0,y0-54);bottom=min(h,y1+25)
        if x2-x1<45 or bottom-top<64:continue
        box=(x1,top,x2,bottom)
        crop=image.crop(box)
        description=_bank_match(crop) or _describe(crop)
        output.append({"box":box,"description":description,"y":top,"anchor_pixels":len(xs)})
    return output

def _synthetic():
    from PIL import ImageDraw
    im=Image.new("RGB",(355,270),(186,206,224))
    dr=ImageDraw.Draw(im)
    dr.ellipse((85,88,145,145),fill=(249,248,239),outline="black",width=2)
    dr.ellipse((85,81,125,119),fill=(247,165,18),outline="black",width=2)
    dr.ellipse((99,126,110,136),fill=(252,121,15))
    dr.rounded_rectangle((86,42,146,75),radius=9,fill="white",outline="black",width=2)
    dr.rounded_rectangle((215,170,345,207),radius=6,fill=(254,229,0))
    found=find_stickers(im,[(215,170,130,37,"나")])
    assert len(found)==1,found
    assert "노란색" in found[0]["description"],found
    return True
