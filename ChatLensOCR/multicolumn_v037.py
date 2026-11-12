# -*- coding: utf-8 -*-
"""Photographed multi-column instruction sheet OCR.

Column-local recognition prevents unrelated English and Korean text from
adjacent cards being concatenated into one sentence. No translated or
invented instructions: original visible strings only.
"""
import numpy as np
from PIL import Image

def is_multicolumn_photo(image):
    if image.width<1700 or image.height<900:return False
    a=np.asarray(image.convert("RGB"))
    if (a.mean(axis=2)>135).mean()<.52:return False
    # A mildly gray photographed background rather than a flat-white digital
    # screenshot. Applies only when the user chooses automatic/generic OCR.
    background=np.median(a.reshape(-1,3),axis=0)
    return all(115<value<241 for value in background)

def _read(region,language,precise):
    from tess_backend import read
    from app import recognize,merge_rows
    scale=2 if region.width<750 else 1
    big=region.resize((region.width*scale,region.height*scale),
                      Image.Resampling.LANCZOS) if scale>1 else region
    text,boxes,confidence=read(big,"범용",language,psm=6)
    if not text.strip():
        # A longer OCR response is NOT more accurate. In particular, item
        # icons, photographs and box borders can generate many imaginary
        # words. Preserve every nonempty Tesseract transcription instead of
        # replacing it on string-length or grammar-likelihood grounds.
        items=recognize(big,language,False)
        verified_boxes=[
            item for item in items
            if float(item.get("score",0))>=.85
            and len(str(item.get("text","")).strip())>=2
            and (item["box"][3]-item["box"][1])<max(60,big.height*.15)
        ]
        if len(verified_boxes)>=2:
            candidate="\n".join(r["text"] for r in merge_rows(verified_boxes))
            if candidate.strip():
                text=candidate
                boxes=verified_boxes
                confidence=100*sum(x["score"] for x in verified_boxes)/len(verified_boxes)
    mapped=[]
    for item in boxes:
        x0,y0,x1,y1=item["box"]
        mapped.append({**item,"box":(int(x0/scale),int(y0/scale),
                                      int(x1/scale),int(y1/scale))})
    return text.strip(),mapped,confidence

def analyze(image,language,precise):
    if not is_multicolumn_photo(image):return None
    w,h=image.size
    output=[];metadata=[];raw=[]
    header_h=round(h*.13)
    head,head_boxes,conf=_read(image.crop((0,0,w,header_h)),language,precise)
    if head:output.append(head)
    raw.extend(head_boxes)
    # Include the left tool/requirements column, then read illustrated
    # steps in page order by row, from left to right.
    col_breaks=[.0,.265,.51,.75,1.0]
    row_breaks=[.13,.535,1.0]
    for row in range(2):
        for col in range(4):
            x0=round(w*col_breaks[col])+6
            x1=round(w*col_breaks[col+1])-8
            y0=round(h*row_breaks[row])+3
            y1=round(h*row_breaks[row+1])-5
            if x1-x0<80 or y1-y0<80:continue
            area=image.crop((x0,y0,x1,y1))
            text,boxes,c=_read(area,language,precise)
            if not text:continue
            output.append("")
            output.append(text)
            metadata.append({"type":"column_section","row":row+1,
                             "column":col+1,"box":(x0,y0,x1,y1),
                             "confidence":c})
            for item in boxes:
                a,b,c,d=item["box"]
                raw.append({**item,"box":(x0+a,y0+b,x0+c,y0+d)})
    return "범용","\n".join(output),[],metadata,raw

def _synthetic():
    im=Image.new("RGB",(2100,1200),(172,173,175))
    assert is_multicolumn_photo(im)
    assert not is_multicolumn_photo(Image.new("RGB",(700,1100),"white"))
    return True
