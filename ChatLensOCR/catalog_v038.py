# -*- coding: utf-8 -*-
"""Offline OCR for repeated e-commerce product grids.

Detect the horizontal product-card pitch from repeated blue price labels,
then recognize one card at a time so product names, prices, and stock labels
cannot be interleaved with neighboring cards. Does not identify products
from photos or invent unrecognized text. Other types keep their old reader.
"""
import numpy as np
from PIL import Image

def _blue(image):
    a=np.asarray(image.convert("RGB")).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    return (b>140)&(b>r+36)&(b>g+13)&(r<150)

def detect(image):
    w,h=image.size
    if w<450 or h<380:return None
    a=np.asarray(image.convert("RGB"))
    white=float((a.min(axis=2)>226).mean())
    if white<.50:return None
    blue=_blue(image)
    if int(blue.sum())<300:return None
    peaks=[]
    for start in (.2,.52):
        col=blue[round(h*start):].sum(axis=0).astype(np.float64)
        col-=col.mean()
        if float(np.linalg.norm(col))<1:return None
        for width in range(135,min(310,w//2)+1):
            x,y=col[:-width],col[width:]
            corr=float(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y)+1.e-8))
            peaks.append((corr,width))
    score,pitch=max(peaks)
    n=w//pitch
    if score<.27 or n<2 or n>8:return None
    active=0
    for i in range(n):
        if int(blue[h//2:,i*pitch:min(w,(i+1)*pitch)].sum())>100:
            active+=1
    if active<2:return None
    return {"pitch":pitch,"columns":n,"score":round(score,3),
            "white_fraction":round(white,3)}

def _row_boundaries(image,blue):
    w,h=image.size
    a=np.asarray(image.convert("RGB")).astype(np.int16)
    dark=(a.min(axis=2)<220).sum(axis=1)
    whitespace=dark<max(7,w*.004)
    ids=np.flatnonzero(whitespace)
    spans=[]
    if len(ids):
        first=last=int(ids[0])
        for y in ids[1:]:
            y=int(y)
            if y-last>1:
                if last-first+1>=30:spans.append((first,last+1))
                first=y
            last=y
        if last-first+1>=30:spans.append((first,last+1))
    line_ink=blue.sum(axis=1)
    boundaries=[]
    for start,end in spans:
        if start<130 or end>h-12:continue
        if int(line_ink[max(0,start-105):start].sum())<200:continue
        middle=(start+end)//2
        if middle<150 or h-middle<155:continue
        if not boundaries or middle-boundaries[-1]>=160:
            boundaries.append(middle)
    return [0]+boundaries+[h]

def _card_ocr(image,language,precise):
    from tess_backend import read
    from app import recognize,merge_rows
    factor=3 if image.width<300 else 2
    enlarged=image.resize((image.width*factor,image.height*factor),
                          Image.Resampling.LANCZOS)
    transcript,parts,confidence=read(enlarged,"범용",language,psm=6)
    if (not transcript.strip() or confidence<25) and precise:
        guesses=merge_rows(recognize(enlarged,language,False))
        better="\n".join(v["text"] for v in guesses)
        if len(better.strip())>len(transcript.strip()):
            transcript=better
    transformed=[]
    for item in parts:
        x0,y0,x1,y1=item["box"]
        transformed.append({**item,"box":(x0/factor,y0/factor,x1/factor,y1/factor)})
    return transcript.strip(),transformed,confidence

def analyze(image,language="한국어",precise=True):
    geometry=detect(image)
    if geometry is None:return None
    from debuglog_v0372 import note
    w,h=image.size
    pitch=geometry["pitch"]
    cols=geometry["columns"]
    blue=_blue(image)
    boundaries=_row_boundaries(image,blue)
    note("product_grid_detected",size=image.size,pitch=pitch,
         columns=cols,rows=len(boundaries)-1,confidence=geometry["score"])
    output=[];metadata=[];raw=[];index=0
    for row,(top,bottom) in enumerate(zip(boundaries,boundaries[1:]),start=1):
        counts=blue[top:bottom].sum(axis=1)
        eligible=np.flatnonzero(counts>=max(4,round(w*.008)))
        if not len(eligible):continue
        lastblue=int(top+np.percentile(eligible,98))
        y0=max(top,lastblue-185)
        y1=min(bottom,lastblue+65)
        # A navigation header is not a product row even when blue links
        # happen to repeat horizontally; product prices occur below photos.
        per_column=[
            int(blue[y0:y1,i*pitch:min(w,(i+1)*pitch)].sum())
            for i in range(cols)]
        if row==1 and len(boundaries)>2 and sum(per_column)/cols<230:
            note("product_grid_header_skipped",row=row,ink=per_column)
            continue
        for col,ink in enumerate(per_column):
            if ink<70:continue
            left=max(0,col*pitch+4)
            right=min(w,(col+1)*pitch-7)
            if right-left<65 or y1-y0<35:continue
            crop=image.crop((left,y0,right,y1))
            try:
                content,parts,conf=_card_ocr(crop,language,precise)
            except Exception as err:
                from debuglog_v0372 import exception
                exception("catalog_card_ocr_failed",err,row=row,column=col+1,
                          bounds=(left,y0,right,y1))
                continue
            if not content or len(content.strip())<7:continue
            index+=1
            output.append(f"[상품 {index:02d} | {row}행 {col+1}열]")
            output.append(content)
            output.append("")
            metadata.append({"type":"product_card","index":index,"row":row,
                             "column":col+1,"bounds":(left,y0,right,y1),
                             "ocr_confidence":conf,"color_pixels":ink})
            for part in parts:
                a,b,c,d=part["box"]
                raw.append({**part,"box":(left+a,y0+b,left+c,y0+d)})
    if index<2:return None
    note("product_grid_completed",items=index)
    return "범용","\n".join(output).strip(),[],metadata,raw

def regression():
    from PIL import ImageDraw,ImageFont
    img=Image.new("RGB",(1140,820),"white")
    draw=ImageDraw.Draw(img)
    font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",16)
    for r in range(2):
        for c in range(5):
            x=7+c*224; y=15+r*400
            draw.rectangle((x+5,y+5,x+165,y+155),fill=(120,125,130))
            draw.text((x+10,y+195),"KSC Sample System7",font=font,fill=(30,30,30))
            draw.text((x+10,y+242),"판매가: 530,000원",font=font,fill=(10,100,220))
    found=detect(img)
    assert found and found["columns"]==5 and abs(found["pitch"]-224)<=3,found
    assert detect(Image.new("RGB",(800,600),"white")) is None
    return True
