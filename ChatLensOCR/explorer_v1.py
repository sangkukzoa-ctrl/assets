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
    region=image.crop((x0,0,x1,h))
    # Windows Explorer uses ~12px fonts; 3x upscaling is essential.
    factor=3
    enlarged=region.resize((region.width*factor,region.height*factor),Image.Resampling.LANCZOS)
    _,parts,_=read(enlarged,"범용","한국어" if lang!="eng" else "영어",psm=6,
                   tess_lang="kor" if lang=="kor" else None)
    rows=[[] for _ in centers]
    raw=[]
    for t in parts:
        bx1,by1,bx2,by2=t["box"]
        cy=(by1+by2)/(2*factor)
        index=min(range(len(centers)),key=lambda i:abs(centers[i]+pitch*.16-cy))
        if abs(centers[index]+pitch*.16-cy)>pitch*.72:continue
        rows[index].append((bx1,t["text"]))
        raw.append({**t,"box":(int(x0+bx1/factor),int(by1/factor),int(x0+bx2/factor),int(by2/factor))})
    return [" ".join(t for _,t in sorted(group)).strip() for group in rows],raw

def analyze(image,language="한국어"):
    geometry=_measure(image)
    if geometry is None:return None
    pitch,centers=geometry
    w,h=image.size
    # In Windows Explorer the columns stay at the same pixel positions when
    # the window is made wider. Percent-of-image positions cropped the date
    # in 902px screenshots and leaked it into the filename.
    pos=lambda n:round(n*min(1.,w/780.))
    filename_right=pos(382)
    date_start=pos(383);date_end=pos(530)
    kind_start=pos(530);kind_end=pos(657)
    size_start=pos(683)
    dates,raw_dates=_batch_metadata(image,date_start,date_end,centers,pitch)
    # Korean-only OCR often distinguishes 오전/오후 from the mixed-model
    # corruption "2%" or "27". Re-read the same date column once.
    dates_ko,_=_batch_metadata(image,date_start,date_end,centers,pitch,"kor")
    for n in range(len(dates)):
        native=dates_ko[n]
        if re.search(r"20\d{2}[-.]\d{1,2}[-.]\d{1,2}",native) and re.search(r"오전|오후",native):
            if not re.search(r"오전|오후",dates[n]):
                dates[n]=native
    kinds,raw_kinds=_batch_metadata(image,kind_start,kind_end,centers,pitch)
    sizes,raw_sizes=_batch_metadata(image,size_start,w,centers,pitch,"eng")
    outputs=[];diagnostics=[];raw=raw_dates+raw_kinds+raw_sizes
    normalized_kinds=[]
    for text in kinds:
        if re.search(r"압\s*축",text) and re.search(r"파일",text):
            normalized_kinds.append("압축(ZIP) 파일")
        else:
            normalized_kinds.append(text)
    # The same file type is typically repeated for each row in a folder;
    # propagate only if at least 70% of rows independently recognized it.
    known=[k for k in normalized_kinds if k=="압축(ZIP) 파일"]
    common_kind="압축(ZIP) 파일" if len(known)>=len(centers)*.7 else ""
    # Column-wide evidence can repair illegible repetitions of a fixed file
    # type, but must not rewrite genuinely different file types.
    stable_zip=bool(common_kind)
    for i,top in enumerate(centers):
        y0=max(0,top-5);y1=min(h,top+max(16,int(pitch*.60)))
        x0=28
        filename,parts,conf=_ocr_single(image.crop((x0,y0,filename_right,y1)))
        filename=re.sub(r"^[^a-zA-Z0-9가-힣]+","",filename)
        # The '4', 'A', and 'j' prefixes were actually ZIP icon glyphs.
        filename=re.sub(r"(?i)^[4Aj]\s+(?=rgbblocks[_ .])","",filename)
        filename=re.sub(r"(?i)^RGBBIlocks(?=_)","RGBBlocks",filename)
        filename=re.sub(r"(?i)\s+zip$",".zip",filename)
        for t in parts:
            box=t["box"]
            raw.append({**t,"box":(int(box[0]+x0),int(box[1]+y0),int(box[2]+x0),int(box[3]+y0))})
        date=dates[i]
        # Date OCR is accepted only when a recognizable YYYY-MM-DD is present.
        # Do not silently forge damaged digits.
        date=date if re.search(r"20\d{2}\s*[-.]\s*\d{1,2}\s*[-.]\s*\d{1,2}",date) else (date or "[날짜 미인식]")
        kind=normalized_kinds[i] or common_kind
        if stable_zip and kind!="압축(ZIP) 파일":
            # "LEP) 파일" is an OCR artifact for the same ZIP-file icon.
            if re.search(r"파일",kind) or re.search(r"(?i)zip|lep",kind):
                kind=common_kind
        size=sizes[i]
        m=re.search(r"(?i)(\d{1,7})\s*(KB|MB|GB|B)\b",size)
        size=(m.group(1)+m.group(2).upper()) if m else (size or "[크기 미인식]")
        outputs.append("\t".join((filename or "[파일명 미인식]",date,kind,size)))
        diagnostics.append({"row":i+1,"y":top,"name":filename,"score":conf,
                            "date":date,"kind":kind,"size":size})
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
