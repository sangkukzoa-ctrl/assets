# -*- coding: utf-8 -*-
"""Color-independent KakaoTalk sticker detection and registered visual matching.
The user's own descriptions win over generic color-based summaries.
No screenshots or personal sticker descriptions leave the PC.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def _runs(indices,gap=5):
    if len(indices)==0:return []
    out=[];start=last=int(indices[0])
    for value in indices[1:]:
        value=int(value)
        if value-last>gap+1:
            out.append((start,last+1));start=value
        last=value
    out.append((start,last+1))
    return out

def _iou(a,b):
    x0=max(a[0],b[0]);y0=max(a[1],b[1])
    x1=min(a[2],b[2]);y1=min(a[3],b[3])
    intersection=max(0,x1-x0)*max(0,y1-y0)
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
    return intersection/max(union,1)

def _background(image):
    a=np.asarray(image.convert("RGB"))
    h,w=a.shape[:2]
    samples=np.concatenate([
        a[max(0,h//10):max(1,h*9//10),max(0,w-18):max(1,w-7)].reshape(-1,3),
        a[max(0,h//10):max(1,h*9//10),max(0,w//2-6):max(1,w//2+4)].reshape(-1,3)
    ],axis=0)
    return np.median(samples.astype(np.float32),axis=0)

def foreground_candidates(image,bubbles=()):
    """Detect monochrome cartoon figures as well as colored ones.
    Reject low, broad, flat-colored chat bubbles using foreground ratios.
    """
    a=np.asarray(image.convert("RGB")).astype(np.float32)
    h,w=a.shape[:2]
    if w<200 or h<100:return []
    bg=_background(image)
    mask=(np.max(np.abs(a-bg),axis=2)>39).astype(np.uint8)
    mask[:,:max(40,int(.12*w))]=0
    merged=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    _,_,stats,_=cv2.connectedComponentsWithStats(merged,8)
    candidates=[]
    for x,y,cw,ch,area in stats[1:]:
        if cw<44 or ch<41 or area<600:continue
        if cw>min(w*.92,360) or ch>min(h*.58,330):continue
        if area/(cw*ch)>.90 and cw>75:continue
        region=mask[y:y+ch,x:x+cw]
        profile=region.sum(axis=1)
        groups=_runs(np.flatnonzero(profile>=max(6,round(cw*.08))),gap=5)
        if ch<=100:
            # A speech balloon and the illustrated character may be separated
            # by a few empty pixels; treat the entire short artwork as one.
            groups=[(0,ch)]
        for y0,y1 in groups:
            sub=region[y0:y1]
            yy,xx=np.where(sub)
            if len(xx)<480:continue
            x0=int(xx.min());x1=int(xx.max())+1
            sy0=int(yy.min());sy1=int(yy.max())+1
            bw=x1-x0;bh=sy1-sy0
            if bw<40 or bh<38:continue
            left=max(0,x+x0-2);top=max(0,y+sy0-2)
            right=min(w,x+x1+2);bottom=min(h,y+sy1+2)
            pixels=a[top:bottom,left:right].astype(np.int16)
            r,g,b=pixels[:,:,0],pixels[:,:,1],pixels[:,:,2]
            fg=np.max(np.abs(pixels-bg),axis=2)>39
            yellow=((r>225)&(g>160)&(b<145)).sum()/max(1,fg.sum())
            white=((r>245)&(g>245)&(b>236)).sum()/max(1,fg.sum())
            if yellow>.50 or (white>.80 and bw>bh*1.7):continue
            box=(int(left),int(top),int(right),int(bottom))
            if any(_iou(box,(bx,by,bx+bww,by+bhh))>.62
                   for bx,by,bww,bhh,_ in bubbles):continue
            candidates.append({"box":box,"source":"shape",
                               "anchor_pixels":int(len(xx)),"y":int(top)})
    cleaned=[]
    for item in sorted(candidates,key=lambda v:-
                       (v["box"][2]-v["box"][0])*(v["box"][3]-v["box"][1])):
        if not any(_iou(item["box"],keep["box"])>.35 for keep in cleaned):
            cleaned.append(item)
    return sorted(cleaned,key=lambda d:d["y"])

def _saved_records(folder):
    path=folder/"descriptions.jsonl"
    if not path.is_file():return []
    files=sorted(folder.glob("*.png"),key=lambda p:p.stat().st_mtime)
    legacy=iter(files)
    out=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row=json.loads(line)
            name=row.get("filename")
            image=folder/name if name else next(legacy,None)
            if not image or not image.is_file():continue
            caption=row.get("description","").strip()
            if caption:out.append((image,caption))
        except (ValueError,TypeError,OSError):continue
    return out

def registered_matches(image,folder=None):
    """Match user-selected sticker crops at multiple scales, not by averaging
    the entire candidate and comparing two arbitrary 48x48 rectangles."""
    if folder is None:
        from app import DATA
        folder=DATA/"sticker_samples"
    folder=Path(folder)
    if not folder.exists():return []
    gray=np.asarray(image.convert("L"))
    h,w=gray.shape
    found=[]
    for path,description in _saved_records(folder):
        try:
            template=np.asarray(Image.open(path).convert("L"))
            th,tw=template.shape
            if min(th,tw)<23 or max(th,tw)>380 or float(template.std())<18:
                continue
            matches=[]
            for scale in (.70,.80,.90,1.0,1.10,1.25,1.4):
                sw=round(tw*scale);sh=round(th*scale)
                if sw>=w-2 or sh>=h-2 or min(sw,sh)<20:continue
                scaled=cv2.resize(template,(sw,sh),
                    interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC)
                if float(scaled.std())<13:continue
                result=cv2.matchTemplate(gray,scaled,cv2.TM_CCOEFF_NORMED)
                for _ in range(5):
                    _,score,_,pos=cv2.minMaxLoc(result)
                    if score<.72:break
                    x,y=pos
                    if x>=max(23,w*.07):
                        matches.append((float(score),(int(x),int(y),int(x+sw),int(y+sh))))
                    result[max(0,y-sh//2):min(result.shape[0],y+sh//2+1),
                           max(0,x-sw//2):min(result.shape[1],x+sw//2+1)]=-1
            for score,box in sorted(matches,reverse=True):
                if any(_iou(box,entry["box"])>.18 for entry in found):continue
                found.append({"box":box,"description":description,"y":box[1],
                              "anchor_pixels":0,"source":"registered",
                              "confidence":score})
        except Exception:
            continue
    return sorted(found,key=lambda x:x["y"])

def find(image,bubbles=(),folder=None):
    known=registered_matches(image,folder)
    for candidate in foreground_candidates(image,bubbles):
        if any(
            _iou(candidate["box"],item["box"])>.13 or (
            abs((candidate["box"][1]+candidate["box"][3])//2-
                (item["box"][1]+item["box"][3])//2)<24 and
            abs((candidate["box"][0]+candidate["box"][2])//2-
                (item["box"][0]+item["box"][2])//2)<26)
            for item in known):
            continue
        known.append(candidate)
    return sorted(known,key=lambda x:x["y"])

def _synthetic():
    """Monochrome art plus a yellow ordinary bubble: exactly one sticker."""
    from PIL import ImageDraw
    image=Image.new("RGB",(355,330),(186,206,224))
    draw=ImageDraw.Draw(image)
    draw.ellipse((67,125,143,208),fill="white",outline="black",width=4)
    draw.line((77,170,134,180),fill="black",width=5)
    draw.line((100,140,116,193),fill="black",width=3)
    draw.ellipse((180,250,330,288),fill="#ffe200")
    result=find(image,[(180,250,150,38,"나")],folder="/nonexistent")
    assert len(result)==1,result
    return True
