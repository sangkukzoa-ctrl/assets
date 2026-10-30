# -*- coding: utf-8 -*-
"""ChatLens OCR 0.2: pixel-layout-first processing.
Detects screenshot type from pixels, segments UI elements before running OCR.
Avoids making up missing text, icons, names and world names.
"""
import re
import numpy as np
import cv2
from PIL import Image, ImageOps, ImageEnhance

_FFXIV = re.compile(r"^\s*[\[［【]\s*\d{1,2}\s*[:：]\s*\d{2}\s*[\]］】]\s*(?:[\[［【][^\]］】]{0,28}[\]］】])?\s*[<〈＜]\s*(.{1,34}?)\s*[>〉＞]\s*(.*)$")
_FFXIV_LOOSE = re.compile(r"[<〈＜]\s*([^<>〈〉＜＞]{1,32})\s*[>〉＞]\s*(.+)")
_HHMM = re.compile(r"\b(?:오전|오후)\s*\d{1,2}\s*[:：]\s*\d{2}\b")
def _runs(mask, min_length=2, gap=2):
    idx=np.flatnonzero(mask)
    if not len(idx): return []
    groups=[]; start=last=int(idx[0])
    for n in idx[1:]:
        n=int(n)
        if n-last>gap+1:
            if last-start+1>=min_length:groups.append((start,last+1))
            start=n
        last=n
    if last-start+1>=min_length:groups.append((start,last+1))
    return groups

def detect_mode(img):
    rgb=np.asarray(img.convert("RGB"))
    h,w=rgb.shape[:2]
    # KakaoTalk default desktop/mobile export theme: blue-gray background,
    # white and yellow rectangular bubbles. Pure pixel test, no OCR needed.
    sample=rgb[int(h*.1):int(h*.9):max(1,h//120),::max(1,w//120)]
    bg=np.median(sample.reshape(-1,3),axis=0)
    yellow=((rgb[:,:,0]>225)&(rgb[:,:,1]>165)&(rgb[:,:,2]<145)).sum()
    if yellow>140 and (bg[2]>bg[0]+10 or (rgb[:,:,:3].mean(axis=2)>220).mean()>.45):
        return "카카오톡"
    # FFXIV chat window: mostly black/dark with dense 1-2 px high glyphs
    # and timestamps at the first few columns.
    left=rgb[:, :min(w,65)]
    darkness=(rgb.mean(axis=2)<75).mean()
    light=((left[:,:,0]>130)&(left[:,:,1]>125)&(left[:,:,2]>70)).sum()
    if darkness>.55 and light>50: return "파판14"
    return "범용"

def _flatten_ocr(img, language="한국어", precise=True):
    # import lazily to avoid circular imports
    from app import recognize, merge_rows
    items=recognize(img,language,precise)
    rows=merge_rows(items)
    return " ".join(row["text"].strip() for row in rows if row["text"].strip()), items

def _variants(img,mode, language, precise):
    from app import recognize, merge_rows
    opts=[]
    scale=3 if img.height<55 else 2 if img.height<130 else 1.5
    scale=min(scale, max(1,2200/max(img.width,1)))
    # light/dark input, local crop avoids full-page text detection merging.
    ims=[img.convert("RGB")]
    if precise:
        base=img.convert("RGB")
        if mode=="파판14":
            # Bright foreground on almost black background; retain anti-aliasing
            a=np.asarray(base).astype(np.int16)
            gray=cv2.cvtColor(a.astype(np.uint8),cv2.COLOR_RGB2GRAY)
            boosted=np.clip((gray.astype(np.float32)-25)*1.60,0,255).astype(np.uint8)
            ims.append(Image.fromarray(cv2.cvtColor(boosted,cv2.COLOR_GRAY2RGB)))
        else:
            ims.append(ImageOps.autocontrast(base,cutoff=1))
    for candidate in ims:
        if scale>1: candidate=candidate.resize((max(1,int(candidate.width*scale)),max(1,int(candidate.height*scale))),Image.Resampling.LANCZOS)
        res=recognize(candidate, language,False)
        groups=merge_rows(res)
        content=" ".join(r["text"].strip() for r in groups if r["text"].strip())
        # Coverage + Hangul ratio + OCR confidence, no dictionary guessing.
        if not content:continue
        hangul=len(re.findall(r"[가-힣]",content))
        nonsensical=len(re.findall(r"[|©€¤@{}]",content))
        mean_conf=sum(x["score"] for x in res)/max(1,len(res))
        score=mean_conf*3 + min(1.5,len(content)*.019)+ min(1.1,hangul*.025) - nonsensical*.17
        opts.append((score,content,res))
    if not opts:return "",[],0.
    opts.sort(key=lambda x:x[0],reverse=True)
    return opts[0][1],opts[0][2],opts[0][0]

def _offset(items, x,y,scale=1):
    out=[]
    for q in items:
        b=q["box"]
        out.append({"text":q["text"],"score":q["score"],
            "box":(int(b[0]/scale+x),int(b[1]/scale+y),int(b[2]/scale+x),int(b[3]/scale+y))})
    return out

def _fixed_lines(img, color="ffxiv"):
    a=np.asarray(img.convert("RGB")).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    if color=="ffxiv":
        selected=(g>118)&(r>115)&( (r-b>25)&(g-b>14) | ((r>145)&(g>145)&(b>135)) )
    elif color=="red":
        selected=(r>80)&(r-g>35)&(r-b>34)
    else:
        selected=(b-r>16)&(g-r>10)&(b>80)
    amount=selected.sum(axis=1)
    # The projection is stable despite glyph differences and anti-aliasing.
    # Do NOT dilate the projection: in dense FFXIV chat, adjacent
    # 19px-spaced lines otherwise bridge into one huge block.
    proj=amount>=max(6,img.width//110)
    return _runs(proj, min_length=3, gap=0)

def ffxiv(img, language, precise, world, icons):
    lines=_fixed_lines(img)
    out=[]; raw=[]; metadata=[]; hits=[]
    # Crop one row, never ask recognizer to guess location inside entire chat log.
    for y0,y1 in lines:
        if y1-y0>36:continue
        top=max(0,y0-2);bottom=min(img.height,y1+2)
        crop=img.crop((0,top,img.width,bottom))
        value,items,score=_variants(crop,"파판14",language,precise)
        if not value:continue
        raw.extend(_offset(items,0,top,3 if crop.height<55 else 1))
        value=re.sub(r"\s+([:：>〉）\]])",r"\1",value)
        match=_FFXIV.match(value)
        if match is None:
            match=_FFXIV_LOOSE.search(value)
        if match:
            nickname=match.group(1).strip()
            message=match.group(2).strip()
            # RapidOCR can insert spaces between individual Hangul syllables;
            # keep actual spaces in dialogue, remove only in the header name.
            nickname=re.sub(r"\s+","",nickname)
            server=""
            if "&" in nickname:
                nickname,server=nickname.rsplit("&",1)
            elif "@" in nickname:
                nickname,server=nickname.rsplit("@",1)
            speaker=nickname+("&"+server if server and server!=world else "")
            # Job icons are not drawn in every FFXIV chat mode.
            # Only match a confirmed actual icon; never infer from nickname.
            job="직업미확인"
            icon=None; conf=0.
            try:
                found,rect,conf=icons.match(img,(0,top, min(160,img.width),bottom))
                if found:job=found;icon=rect
            except Exception:pass
            out.append(f"({job}){speaker}: {message}")
            if icon: hits.append((icon,job))
            metadata.append({"speaker":nickname,"server":server,"job":job,"ocr_score":score,"icon_score":conf,"y":top})
        elif re.search(r"스크린샷|저장했|Screenshot",value):
            out.append("[시스템] "+value)
        elif out and not re.search(r"\d{1,2}\s*[:：]\s*\d{2}",value[:12]):
            # Do not hallucinate speakers on a cropped continuation line.
            out[-1]+=" "+value
        else:
            out.append("[미분류] "+value)
    return "파판14","\n".join(out),hits,metadata,raw

def _bubble_boxes(img):
    a=np.asarray(img.convert("RGB"))
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    white=((r>=244)&(g>=244)&(b>=244))
    yellow=(r>=228)&(g>=170)&(b<=130)&(r>b+75)
    found=[]
    for name,mask in (("상대",white),("나",yellow)):
        # A 3x3 morphology closes anti-aliasing gaps and rounded corners.
        mask=cv2.morphologyEx(mask.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        count,labels,stats,centers=cv2.connectedComponentsWithStats(mask,8)
        for x,y,w,h,area in stats[1:]:
            if w<24 or h<17 or area<160 or w>img.width*.96: continue
            if name=="상대" and x<min(38,img.width*.10):continue # profile pictures
            if name=="나" and x+w<img.width*.48:continue
            # Disallow white holes in emoji stickers by rectangle fill ratio
            if area/(w*h)<.56: continue
            found.append((int(x),int(y),int(w),int(h),name))
    # one bubble per connected flat-colored surface
    return sorted(found,key=lambda v:(v[1],v[0]))

def kakao(img,language,precise):
    boxes=_bubble_boxes(img)
    results=[];raw=[];metadata=[]
    # Names appear above the first white bubble of each group. Extract from
    # fixed label ROI and vote across repetitions, rather than OCRing avatars
    # and timestamps in the same large detection image.
    candidate_names=[]
    previous_bottom=-100
    for x,y,w,h,kind in boxes:
        if kind!="상대": continue
        if y-previous_bottom>=12 and y>16:
            name_area=img.crop((max(0,x-8),max(0,y-29),min(img.width,x+95),max(0,y-5)))
            name_txt,_,_= _variants(name_area,"카카오톡",language,False)
            cleaned=re.sub(r"[^가-힣A-Za-z0-9_]","",name_txt)
            if 2<=len(cleaned)<=12 and re.search(r"[가-힣]",cleaned):
                candidate_names.append(cleaned)
        previous_bottom=y+h
    from collections import Counter
    nickname=Counter(candidate_names).most_common(1)[0][0] if candidate_names else "상대"
    for x,y,w,h,kind in boxes:
        margin=7 if w>55 else 3
        image=img.crop((x+margin,y+4,x+w-3,y+h-3))
        if image.width<5 or image.height<5:continue
        content,items,score=_variants(image,"카카오톡",language,precise)
        if not content:continue
        content=_HHMM.sub("",content).strip()
        if not content:continue
        raw.extend(_offset(items,x+margin,y+4,3 if image.height<55 else 2 if image.height<130 else 1.5))
        who="나" if kind=="나" else nickname
        results.append(f"{who}: {content}")
        metadata.append({"speaker":who,"kind":"bubble","box":(x,y,x+w,y+h),"ocr_score":score})
    if not results:
        return generic(img,language,precise)
    return "카카오톡","\n".join(results),[],metadata,raw

def generic(img, language, precise):
    # Colored support chat blocks: detect horizontal text baselines by red/blue ink.
    a=np.asarray(img.convert("RGB"))
    flat=np.median(a,axis=(0,1))
    # Text on a pale uniform background can be processed line by line.
    all_lines=[]
    if (flat>175).all():
        red=_fixed_lines(img,"red")
        blue=_fixed_lines(img,"blue")
        both=sorted(red+blue)
        for y0,y1 in both:
            if all_lines and y0<all_lines[-1][1]+5:
                old=all_lines.pop();all_lines.append((min(old[0],y0),max(old[1],y1)))
            else: all_lines.append((y0,y1))
    if len(all_lines)<3:
        from app import recognize,merge_rows
        items=recognize(img,language,precise)
        rows=merge_rows(items)
        return "범용","\n".join(v["text"] for v in rows),[],[{"confidence":v["score"]} for v in rows],items
    results=[];raw=[];meta=[]
    for y0,y1 in all_lines:
        if y1-y0>42:continue
        y=max(0,y0-4);end=min(img.height,y1+4)
        part=img.crop((0,y,img.width,end))
        content,items,score=_variants(part,"범용",language,precise)
        if content:
            results.append(content);raw.extend(_offset(items,0,y,3 if part.height<55 else 1))
            meta.append({"line_y":y,"ocr_score":score})
    return "범용","\n".join(results),[],meta,raw

def analyze(img,mode,language,precise,world,icons):
    if mode=="자동":mode=detect_mode(img)
    if mode=="파판14":
        result=ffxiv(img,language,precise,world,icons)
    elif mode=="카카오톡":
        result=kakao(img,language,precise)
    else: result=generic(img,language,precise)
    detected,output,hits,metadata,lines=result
    from app import merge_rows
    return detected,output,hits,metadata,merge_rows(lines),lines

def _test_detection():
    from PIL import Image,ImageDraw
    f=Image.new("RGB",(360,110),(10,12,15));d=ImageDraw.Draw(f);d.text((1,4),"[1:22][Party]<Example>hello",fill=(245,225,135))
    k=Image.new("RGB",(360,260),(185,205,226));d=ImageDraw.Draw(k);d.rectangle((55,30,260,90),fill="white");d.rectangle((230,110,340,160),fill="#ffe000")
    g=Image.new("RGB",(360,100),(247,225,225))
    assert detect_mode(f)=="파판14"
    assert detect_mode(k)=="카카오톡"
    assert detect_mode(g)=="범용"
    assert len(_bubble_boxes(k))==2
    return True
