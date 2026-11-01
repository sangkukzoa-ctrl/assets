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
    from tess_backend import read as tesseract_read
    opts=[]
    scale=3 if img.height<55 else 2 if img.height<130 else 1.5
    scale=min(scale,max(1.,2200/max(img.width,1)))
    ims=[img.convert("RGB")]
    if precise:
        base=img.convert("RGB")
        if mode=="파판14":
            gray=cv2.cvtColor(np.asarray(base),cv2.COLOR_RGB2GRAY)
            boosted=np.clip((gray.astype(np.float32)-25)*1.60,0,255).astype(np.uint8)
            ims.append(Image.fromarray(cv2.cvtColor(boosted,cv2.COLOR_GRAY2RGB)))
        else:
            ims.append(ImageOps.autocontrast(base,cutoff=1))
    for candidate in ims:
        if scale>1:
            candidate=candidate.resize(
                (max(1,round(candidate.width*scale)),max(1,round(candidate.height*scale))),
                Image.Resampling.LANCZOS)
        # Both engines return coordinates in the enlarged candidate.
        # Normalize immediately to the original cropped image's pixel grid.
        tt,tboxes,tconf=tesseract_read(candidate,mode,language)
        tboxes=_offset(tboxes,0,0,scale)
        if tt and tconf>=78 and (language!="한국어" or len(re.findall(r"[가-힣]",tt))>=2):
            return tt,tboxes,tconf/20
        if tt:
            opts.append((tconf/28+min(1,len(tt)*.018),tt,tboxes))
        res=recognize(candidate,language,False)
        groups=merge_rows(res)
        content=" ".join(r["text"].strip() for r in groups if r["text"].strip())
        if not content:continue
        hangul=len(re.findall(r"[가-힣]",content))
        nonsensical=len(re.findall(r"[|©€¤@{}]",content))
        mean_conf=sum(x["score"] for x in res)/max(1,len(res))
        score=mean_conf*3+min(1.5,len(content)*.019)+min(1.1,hangul*.025)-nonsensical*.17
        opts.append((score,content,_offset(res,0,0,scale)))
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
        selected=(r<160)&(b-r>20)&(g-r>14)&(b>80)
    amount=selected.sum(axis=1)
    # The projection is stable despite glyph differences and anti-aliasing.
    # Do NOT dilate the projection: in dense FFXIV chat, adjacent
    # 19px-spaced lines otherwise bridge into one huge block.
    proj=amount>=max(6,img.width//110)
    return _runs(proj, min_length=3, gap=0)

def _pvp_color_read(crop,language):
    """Extract saturated PvP name and chat colors from the dark game scene.
    System notices and the underlying environment are suppressed.
    """
    from tess_backend import read as _read
    a=np.asarray(crop.convert("RGB")).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    blue=(b-r>48)&(b>145)&(g>85)
    red=(r-g>42)&(r-b>55)&(r>140)
    green=(g-r>38)&(g-b>25)&(g>110)
    if (blue|red|green).sum()<20:return "",[],0.
    vmax=a.max(axis=2);vmin=a.min(axis=2)
    mask=(vmax-vmin>66)&(vmax>130)
    white=np.where(mask,0,255).astype(np.uint8)
    prep=Image.fromarray(white).resize((crop.width*3,crop.height*3),Image.Resampling.LANCZOS)
    text,boxes,conf=_read(prep,"파판14",language,psm=6)
    return text,_offset(boxes,0,0,3),conf

def ffxiv(img, language, precise, world, icons):
    lines=_fixed_lines(img)
    out=[]; raw=[]; metadata=[]; hits=[]
    # Crop one row, never ask recognizer to guess location inside entire chat log.
    for y0,y1 in lines:
        if y1-y0>36:continue
        top=max(0,y0-2);bottom=min(img.height,y1+2)
        crop=img.crop((0,top,img.width,bottom))
        # PvP role/job badge, colored nickname and orange message are
        # independently recognized before any ordinary chat-header parser.
        from pvp_v2 import transcribe as transcribe_pvp
        pvp=transcribe_pvp(crop,img,top,language,world,icons)
        if pvp is not None:
            line,meta,hit=pvp
            out.append(line)
            metadata.append(meta)
            if hit:hits.append(hit)
            continue
        value,items,score=_variants(crop,"파판14",language,precise)
        if not value:continue
        masked,mask_boxes,mask_conf=_pvp_color_read(crop,language)
        if masked and mask_conf>=38:
            # Prefer the PvP color-isolated transcription only when it
            # recovers an otherwise missing double-parenthesis speaker.
            if ("))" in masked or ") )" in masked) and not ("))" in value or ") )" in value):
                value=masked;items=mask_boxes;score=mask_conf/20
        # The FF14 channel is rendered in a dense monospaced overlay.
        # When a Korean line is fragmented, compare a full-row PSM6 read.
        from tess_backend import read as _read_tess
        alt,alt_boxes,alt_conf=_read_tess(crop.resize((crop.width*3,crop.height*3),Image.Resampling.LANCZOS),
                                         "파판14",language,psm=6)
        if alt and alt_conf>=66:
            import re as _re
            def fragmentation(t):
                return len(_re.findall(r"(?<=[가-힣]) (?=[가-힣])",t))
            if (fragmentation(alt)<fragmentation(value)
                or (value.count("<")<alt.count("<") and alt_conf>78)):
                value=alt
                items=_offset(alt_boxes,0,0,3)
                score=alt_conf/20
        raw.extend(_offset(items,0,top))
        value=re.sub(r"\s+([:：>〉）\]])",r"\1",value)
        match=_FFXIV.match(value)
        if match is None and re.match(r"^\\s*[\\[［【]\\s*\\d{1,2}\\s*[:：]\\s*\\d{2}",value):
            candidate=_FFXIV_LOOSE.search(value)
            if candidate and not re.fullmatch(r"(?i)se[.．]?[0-9]{1,3}",candidate.group(1).strip()):
                match=candidate
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
                # In PvP chat the job icon precedes the character name near x=100.
                found,rect,conf=icons.match(img,(min(112,img.width-1),top, min(200,img.width),bottom))
                if found:job=found;icon=rect
            except Exception:pass
            out.append(f"({job}){speaker}: {message}")
            if icon: hits.append((icon,job))
            metadata.append({"speaker":nickname,"server":server,"job":job,"ocr_score":score,"icon_score":conf,"y":top})
        elif re.search(r"\(\s*\(?[^)]{3,65}\)\s*\)",value):
            # PvP message format: ((party marker + job icon + NAME + WORLD))
            # It is NOT the <name> chat header format.
            block=re.search(r"\(\s*\(?([^)]{3,65})\)\s*\)\s*(.*)",value)
            if block:
                words=re.findall(r"[가-힣]{2,}",block.group(1))
                if len(words)>=2:
                    name,server=words[-2:]
                    talk=block.group(2).strip()
                    job,icon,conf=icons.match(img,(min(112,img.width-1),top,min(200,img.width),bottom))
                    speaker=name+("&"+server if server!=world else "")
                    out.append(f"({job or '직업미확인'}){speaker}: {talk}")
                    metadata.append({"speaker":name,"server":server,"job":job or "직업미확인","icon_score":conf})
                    if icon:hits.append((icon,job))
                else:out.append("[원문] "+value)
            else:out.append("[원문] "+value)
        elif re.match(r"^\s*[\[［【]\s*\d{1,2}\s*[:：]\s*\d{2}",value):
            out.append("[시스템] "+value)
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

def _bubble_text(image,language,precise):
    """Segment long chat balloons by actual dark-ink rows before OCR."""
    a=np.asarray(image.convert("RGB"))
    gray=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
    ink=(gray<155)
    density=ink.sum(axis=1)
    bands=_runs(density>=max(3,image.width//160),min_length=3,gap=1)
    if len(bands)<2:
        return _variants(image,"카카오톡",language,precise)
    lines=[];all_boxes=[];sc=[]
    for y0,y1 in bands:
        if y1-y0<3:continue
        y=max(0,y0-3);end=min(image.height,y1+3)
        content,items,score=_variants(image.crop((0,y,image.width,end)),"카카오톡",language,precise)
        if content:
            lines.append(content)
            all_boxes.extend(_offset(items,0,y))
            sc.append(score)
    return " ".join(lines),all_boxes,sum(sc)/max(1,len(sc))

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
        content,items,score=_bubble_text(image,language,precise)
        if not content:continue
        content=_HHMM.sub("",content).strip()
        if not content:continue
        raw.extend(_offset(items,x+margin,y+4))
        who="나" if kind=="나" else nickname
        results.append(f"{who}: {content}")
        metadata.append({"speaker":who,"kind":"bubble","box":(x,y,x+w,y+h),"ocr_score":score})
    if not results:
        return generic(img,language,precise)
    return "카카오톡","\n".join(results),[],metadata,raw

def generic(img,language,precise):
    """Text-page OCR: recover visible lines and paragraph gaps before recognition.
    This avoids whole-page OCR dropping bold numbered headings and bullets.
    """
    a=np.asarray(img.convert("RGB"))
    med=np.median(a.reshape(-1,3),axis=0)
    if (med>184).all():
        ink=(a[:,:,0]<180)&(a[:,:,1]<180)&(a[:,:,2]<180)
        amount=ink.sum(axis=1)
        bands=_runs(amount>=max(5,img.width//135),min_length=4,gap=0)
        if len(bands)>=5:
            out=[];raw=[];meta=[];prev_bottom=-1
            for y0,y1 in bands:
                if y1-y0>42:continue
                y=max(0,y0-4);stop=min(img.height,y1+4)
                text,items,score=_variants(img.crop((0,y,img.width,stop)),"범용",language,precise)
                if not text.strip() or (len(text.strip())<2 and not text.strip().isdigit()):continue
                if prev_bottom>=0 and y0-prev_bottom>29:out.append("")
                out.append(text.strip())
                raw.extend(_offset(items,0,y))
                meta.append({"y":y0,"ocr_score":score})
                prev_bottom=y1
            if out:return "범용","\n".join(out),[],meta,raw
    # Dark or photographic layouts: preserve OCR's original spatial ordering.
    from app import recognize,merge_rows
    items=recognize(img,language,precise)
    rows=merge_rows(items)
    return "범용","\n".join(v["text"] for v in rows),[],[{"confidence":v["score"]} for v in rows],items


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
