# -*- coding: utf-8 -*-
"""Offline product-list screenshot OCR: keep each product's text in its own card.

Detects periodic shopping-grid columns from image geometry, using no domain,
product database, AI captioning or site-specific IDs. Price glyphs supply
independent confirmation and vertical separators. Never guesses model names
or associates a price from another column.
"""
import re
import numpy as np
import cv2
from PIL import Image

PRICE_RE = re.compile(r"\d{1,3}\s*[,\.]\s*\d{3}")
GIBBERISH_RE = re.compile(r"[<>★☆|\\{}_^×“”\[\]]")

def _gray(image):
    return cv2.cvtColor(np.asarray(image.convert("RGB")),cv2.COLOR_RGB2GRAY)

def _grid(image):
    """Return the occupied equal-width columns and periodicity confidence."""
    w,h=image.size
    if w<450 or h<310:return [],0.
    gray=_gray(image)
    if float((gray>205).mean())<.55:return [],0.
    projection=(gray[round(h*.25):round(h*.97)]<190).sum(axis=0).astype("float32")
    smooth=cv2.GaussianBlur(projection.reshape(1,-1),(0,0),8).reshape(-1)
    centered=smooth-smooth.mean()
    candidates=[]
    for period in range(135,min(325,w//2)):
        a=centered[:-period];b=centered[period:]
        denom=(float(np.linalg.norm(a))*float(np.linalg.norm(b))+1e-5)
        candidates.append((float(a.dot(b))/denom,period))
    if not candidates:return [],0.
    conf,step=max(candidates)
    if conf<.42:return [],conf
    # Certain compact mobile catalogues alternate their card graphics,
    # so the strongest autocorrelation appears at twice the card pitch.
    if step>285 and w<950:step=int(round(step/2))
    phases=[]
    for phase in range(step):
        cuts=[x for x in range(phase,w-35,step) if x>step*.7]
        if cuts:
            val=float(np.mean([np.min(smooth[max(0,x-7):min(w,x+8)])
                               for x in cuts]))
            phases.append((val,phase))
    if not phases:return [],conf
    _,phase=min(phases)
    borders=[0]+[x for x in range(phase,w-35,step) if x>step*.7]+[w]
    columns=[]
    for left,right in zip(borders,borders[1:]):
        if right-left<65:continue
        inset=min(6,(right-left)//5)
        section=gray[:,left+inset:right-inset]
        if section.size and float((section<190).mean())>=.013:
            columns.append((int(left),int(right)))
    if not 2<=len(columns)<=8:return [],conf
    return columns,conf

def _text_blocks(image,lang="한국어",psm=6):
    """Canonical Tesseract text and token bounds; RapidOCR is backup only."""
    from tess_backend import read
    text,parts,conf=read(image,"범용",lang,psm=psm)
    if text.strip():return text,parts,conf
    from app import recognize,merge_rows
    items=recognize(image,lang,False)
    lines=merge_rows(items)
    content="\n".join(r["text"] for r in lines if r["text"].strip())
    return content,items,0.

def _price_anchors(image,columns):
    anchors=[]
    # Two independent columns are enough to locate sale prices. OCR numeric
    # tokens, not decorative logos or colored UI borders.
    for x0,x1 in columns[:min(3,len(columns))]:
        excerpt=image.crop((x0+4,0,x1-4,image.height))
        _text,parts,_=_text_blocks(excerpt)
        for item in parts:
            text=item.get("text","")
            if PRICE_RE.search(text):
                y=item["box"][1]
                if 40<y<image.height-10:anchors.append(y)
    return sorted(set(anchors))

def _blank_gaps(image):
    gray=_gray(image)
    h,w=gray.shape
    counts=(gray<185).sum(axis=1)
    ids=np.flatnonzero(counts<=max(5,w*.014))
    if not len(ids):return []
    groups=[];begin=last=int(ids[0])
    for value in ids[1:]:
        value=int(value)
        if value!=last+1:
            groups.append((begin,last+1))
            begin=value
        last=value
    groups.append((begin,last+1))
    return [(a,b) for a,b in groups
            if b-a>=25 and a>90 and a<h*.89]

def _row_spans(image,columns):
    h=image.height
    prices=_price_anchors(image,columns)
    gaps=_blank_gaps(image)
    separators=[]
    last=0
    for a,b in gaps:
        if a-last<160:continue
        # The preceding item must actually show a price before the blank
        # spacer. This prevents mistaking the gap INSIDE a photograph for
        # the gap BETWEEN two product cards.
        price_before=any(last+75<=p<a-14 and a-p<=170 for p in prices)
        if price_before:
            center=(a+b)//2
            separators.append(center)
            last=center
    start=0
    if not separators and prices:
        # Pages with a filter/search header before the first product row.
        early=[(a,b) for a,b in gaps
               if a>h*.30 and a<h*.70 and b-a>=45
               and prices[0]-b>90]
        if early:
            start=max(early,key=lambda ab:ab[0])[1]
    borders=[start]+[y for y in separators if y>start+100]+[h]
    return [(a,b) for a,b in zip(borders,borders[1:]) if b-a>=90],prices

def _clean_lines(text):
    out=[]
    for row in text.splitlines():
        row=" ".join(row.split()).strip()
        if not row:continue
        valid=sum(ch.isalnum() or ("가"<=ch<="힣") for ch in row)
        if len(row)>=75 and (valid/max(1,len(row))<.52 or
                             len(GIBBERISH_RE.findall(row))>len(row)*.32):
            continue
        if len(row)>170:continue
        if valid<2:continue
        out.append(row)
    return out

def is_catalog(image):
    columns,confidence=_grid(image)
    if not columns:return False
    # Currency tokens are required. Periodic columns alone appear in Word,
    # calendars and multi-column photographed manuals.
    prices=_price_anchors(image,columns)
    return len(prices)>=2 and confidence>=.42

def analyze(image,language="한국어",precise=True):
    columns,conf=_grid(image)
    if not columns:return None
    rows,prices=_row_spans(image,columns)
    if len(prices)<2 or not rows:return None
    output=[f"[상품 목록 / {len(columns)}열 / 상품별 분리 인식]"]
    raw=[];meta=[];count=0
    for row_no,(top,bottom) in enumerate(rows,1):
        for col_no,(left,right) in enumerate(columns,1):
            width=right-left;height=bottom-top
            # Product artwork occupies the first 20-30% of a card; OCR the
            # title/price/stock text below it, not the large brand watermark.
            y0=min(bottom-12,top+int(height*.24))
            x0=max(0,left+4);x1=min(image.width,right-5)
            if x1<=x0 or bottom-y0<14:continue
            clip=image.crop((x0,y0,x1,bottom-3))
            ink=float((_gray(clip)<185).mean())
            if ink<.007:continue
            text,boxes,confidence=_text_blocks(clip,language,psm=6)
            contents=_clean_lines(text)
            if not contents:continue
            count+=1
            output.append(f"\n[상품 {count} / {row_no}행 {col_no}열]")
            output.extend(contents)
            meta.append({"type":"product_card","number":count,"row":row_no,
                         "column":col_no,"box":(x0,y0,x1,bottom),
                         "ocr_confidence":float(confidence),
                         "has_visible_price":bool(any(PRICE_RE.search(x)
                                                      for x in contents))})
            for item in boxes:
                a,b,c,d=item["box"]
                raw.append({**item,"box":(x0+a,y0+b,x0+c,y0+d)})
    if count<2:return None
    return "범용","\n".join(output),[],meta,raw

def _synthetic():
    from PIL import ImageDraw,ImageFont
    w,h=1020,610
    img=Image.new("RGB",(w,h),"white")
    d=ImageDraw.Draw(img)
    try:font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",16)
    except OSError:font=ImageFont.load_default()
    for row in range(2):
        for col in range(4):
            x=col*250+10;y=row*300+8
            d.rectangle((x+18,y+20,x+190,y+160),outline=(80,80,80),width=2)
            d.text((x+14,y+180),f"MODEL_{row}_{col} Shop",fill="black",font=font)
            d.text((x+14,y+207),f"123,000",fill=(15,105,215),font=font)
            d.text((x+14,y+235),"SOLD OUT",fill=(190,60,60),font=font)
    cols,score=_grid(img)
    assert len(cols)==4,(cols,score)
    assert score>=.42,score
    return True
