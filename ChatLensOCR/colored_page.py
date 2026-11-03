# -*- coding: utf-8 -*-
"""Color-aware OCR for shopping/checkout webpages with long red text blocks.

Foreground ink is isolated by RGB chroma, not generic dark-text threshold.
A separate top-region OCR preserves navigation and checkout labels.
"""
import numpy as np
from PIL import Image

def _redmask(image):
    a=np.asarray(image.convert("RGB")).astype("int16")
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    return (r>138)&(r-g>65)&(r-b>65)

def _ranges(ids,gap=3):
    if len(ids)==0:return []
    groups=[];s=last=int(ids[0])
    for v in ids[1:]:
        v=int(v)
        if v-last>gap:
            groups.append((s,last+1));s=v
        last=v
    groups.append((s,last+1))
    return groups

def is_colored_page(image):
    if image.width<950 or image.height<350:return False
    mask=_redmask(image)
    lower=mask[int(image.height*.52):]
    counts=lower.sum(axis=1)
    groups=[(y0,y1) for y0,y1 in _ranges(np.flatnonzero(counts>12))
            if y1-y0>=6]
    return len(groups)>=4

def analyze(image,language,precise):
    if not is_colored_page(image):return None
    from app import recognize,merge_rows
    from tess_backend import read
    mask=_redmask(image)
    counts=mask.sum(axis=1)
    ranges=[(y0,y1) for y0,y1 in _ranges(np.flatnonzero(counts>12),gap=3)
            if y1-y0>=6 and y0>image.height*.4]
    if not ranges:return None
    top=int(ranges[0][0])
    head=image.crop((0,0,image.width,max(1,top-13)))
    head_ocr=recognize(head,language,precise)
    header_rows=merge_rows(head_ocr)
    header=[" ".join(q["text"].split()) for q in header_rows if q["text"].strip()]
    raw=list(head_ocr)
    meta=[{"zone":"header","y":r["box"][1],"confidence":r["score"]} for r in header_rows]
    # Sparse OCR catches some top navigation labels that standard text detection
    # may miss against black backgrounds. Merge only lines not already present.
    sparse,sboxes,sconf=read(head,"범용",language,psm=11)
    if sparse:
        for t in sparse.splitlines():
            t=" ".join(t.split())
            if len(t)>=3 and not any(t in h or h in t for h in header if len(h)>2):
                header.append(t)
    body=[]
    previous_bottom=top
    for y0,y1 in ranges:
        if y0-previous_bottom>15 and body:
            body.append("")
        y=max(0,y0-3);stop=min(image.height,y1+3)
        # Red foreground -> black glyphs on white, no gray page noise.
        sub=mask[y:stop]
        ys,xs=np.where(sub)
        if len(xs)<12:continue
        x0=max(0,int(xs.min())-5);x1=min(image.width,int(xs.max())+6)
        foreground=np.where(sub[:,x0:x1],0,255).astype("uint8")
        roi=Image.fromarray(foreground).convert("RGB")
        factor=2
        roi=roi.resize((roi.width*factor,roi.height*factor),Image.Resampling.LANCZOS)
        text,parts,confidence=read(roi,"범용",language,psm=7)
        if text:
            body.append(" ".join(text.split()))
            meta.append({"zone":"red-text","y":y0,"confidence":confidence/100})
            for item in parts:
                a,b,c,d=item["box"]
                raw.append({**item,"box":(int(a/factor+x0),int(b/factor+y),int(c/factor+x0),int(d/factor+y))})
        previous_bottom=y1
    if not body:return None
    return "범용","\n".join(header+[""]+body),[],meta,raw

def _synthetic():
    from PIL import ImageDraw,ImageFont
    img=Image.new("RGB",(1200,490),(245,245,245))
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",15)
    d.rectangle((0,0,1199,50),fill="black")
    d.text((100,10),"브랜드 모든 상품 부품 영역",fill="white",font=font)
    for i in range(5):
        d.text((20,260+32*i),f"배송 정보 및 통관 처리 안내 문장 {i+1}",fill=(255,70,60),font=font)
    assert is_colored_page(img)
    return True
