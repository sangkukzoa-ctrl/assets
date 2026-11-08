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

def _novice_chat(value,world):
    """FFXIV novice-network messages use 'name WORLD: message', not <name>."""
    m=re.search(r"[\[［【]\s*초보자\s*[\]］】]\s*(.*)$",value)
    if not m:return None
    tail=m.group(1)
    m2=re.search(r"(.{2,64}?)[:：]\s*(.+)$",tail)
    if not m2:return None
    pre=m2.group(1).strip()
    msg=m2.group(2).strip()
    pieces=re.findall(r"[가-힣A-Za-z]{2,20}",pre)
    if not pieces or not msg:return None
    if len(pieces)>=2:
        name,server=pieces[-2:]
        return "(직업미확인)"+name+("&"+server if server!=world else "")+": "+msg
    return "(직업미확인)"+pieces[-1]+": "+msg

def _looks_system_message(value):
    if re.search(r"투쟁심\s*상승|쌍사당|흑와단|불멸대|순결한\s*땅|알라그\s*석판|무효\s*상태|보유\s*한도|스크린샷|저장했",value):
        return True
    return bool(re.match(r"^\s*[［\[\(]?\s*\d{1,2}\s*[:：]\s*\d{2}\s*[\]］\)]",value))

def _recover_damaged_ffxiv_chat_header(value):
    """Recover a speaker only when an OCR-damaged channel header precedes name>.

    Restrict recovery to timestamp + bracketed chat-channel evidence. Native
    system notices and unstructured prose must not become invented speakers.
    Returns a match with groups (speaker, message), as the normal parser does.
    """
    timestamp=re.match(r"^\s*[\[［【]\s*\d{1,2}\s*[:：]\s*\d{2}\s*[\]］】]",value)
    if not timestamp:return None
    tail=value[timestamp.end():].lstrip()
    if not tail.startswith(("[","［","【")):return None
    if re.match(r"^[\[［【]\s*(?:시스템|전투|공지|알림|임무)\b",tail):
        return None
    # OCR may turn '[채널 5]<동료>' into '[채널 515동료>'
    # or '[채널 51<=동료>'. Only recover the intact name> suffix.
    candidate=re.search(
        r"(?<![가-힣A-Za-z])([가-힣]{2,16}(?:[&＠@][가-힣A-Za-z]{2,16})?)\s*[>〉＞]\s*(\S.*)$",
        tail)
    if not candidate or candidate.start(1)>65:return None
    return candidate

def detect_mode(img):
    rgb=np.asarray(img.convert("RGB"))
    h,w=rgb.shape[:2]
    # Specialized game formats take precedence over Kakao yellow pixels.
    from ffxiv_scoreboard_v037 import is_scoreboard
    from ffxiv_combat_v037 import is_combat
    if is_scoreboard(img) or is_combat(img):return "파판14"
    # KakaoTalk default desktop/mobile export theme: blue-gray background,
    # white and yellow rectangular bubbles. Pure pixel test, no OCR needed.
    sample=rgb[int(h*.1):int(h*.9):max(1,h//120),::max(1,w//120)]
    bg=np.median(sample.reshape(-1,3),axis=0)
    yellow=((rgb[:,:,0]>225)&(rgb[:,:,1]>165)&(rgb[:,:,2]<145)).sum()
    if yellow>140 and bg[2]>bg[0]+12 and bg[1]>bg[0]+8 and bg[2]<245:
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

def _prefer_korean_ffxiv_message(mixed, korean, confidence):
    """Protect the existing nickname, substitute only a better Hangul dialogue.

    FF14 overlays place <speaker> and prose on the same row. Korean-only
    Tesseract may improve the prose but damage the speaker name; preserving
    the original header prevents that regression.
    """
    if confidence<55:return mixed
    if ">" not in mixed or ">" not in korean:return mixed
    head,body=mixed.split(">",1)
    _,candidate=korean.split(">",1)
    if not re.search(r"[가-힣]{2,}",head):return mixed
    current_hangul=len(re.findall(r"[가-힣]",body))
    better_hangul=len(re.findall(r"[가-힣]",candidate))
    alien=re.findall(r"(?<![<.])[A-Za-z]{3,}",body)
    if not alien or better_hangul<current_hangul+2:return mixed
    if len(candidate.strip())<len(body.strip())*.55:return mixed
    return head+">"+candidate

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
        if mode=="파판14" and language=="한국어" and tt:
            korean,_,kc=tesseract_read(candidate,mode,language,psm=6,tess_lang="kor")
            tt=_prefer_korean_ffxiv_message(tt,korean,kc)
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
    # Do not dilate the projection: dense FFXIV rows are only ~20px apart.
    # A bright game-world surface behind the right side can connect multiple
    # chat lines into a single 80px+ slab. The old code skipped that whole slab.
    proj=amount>=max(6,img.width//110)
    full_lines=_runs(proj,min_length=3,gap=0)
    if img.width>=320 and any(y1-y0>36 for y0,y1 in full_lines):
        # Chat timestamps and channel headers are left-anchored; use only
        # their area to find row boundaries, while OCR still reads full width.
        anchor_width=min(img.width,max(190,min(300,int(img.width*.55))))
        anchor_amount=selected[:,:anchor_width].sum(axis=1)
        anchor=_runs(anchor_amount>=max(6,anchor_width//110),min_length=3,gap=0)
        if len(anchor)>len(full_lines) and not any(b-a>36 for a,b in anchor):
            return anchor
    return full_lines

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

def _accept_korean_dialogue(original,candidate,confidence):
    """Replace only suspicious dialogue, never the speaker/header.
    A common failure is RapidOCR reading Hangul as 'BEES' or 'AES'.
    Genuine English messages must survive untouched.
    """
    if confidence<56:return False
    old_h=len(re.findall(r"[가-힣]",original))
    new_h=len(re.findall(r"[가-힣]",candidate))
    old_latin=len(re.findall(r"[A-Za-z]{3,}",original))
    new_latin=len(re.findall(r"[A-Za-z]{3,}",candidate))
    if old_h<4 or old_latin==0 or new_latin>=old_latin:return False
    if new_h<old_h+2:return False
    if not candidate.strip() or len(candidate)<len(original)*.70:return False
    return True

def _recheck_ffxiv_dialogue(crop,original,language):
    if language!="한국어":return original
    if len(re.findall(r"[가-힣]",original))<4:return original
    if not re.search(r"[A-Za-z]{3,}",original):return original
    from tess_backend import read
    big=crop.resize((crop.width*3,crop.height*3),Image.Resampling.LANCZOS)
    native,_,conf=read(big,"파판14","한국어",psm=7,tess_lang="kor")
    p=re.search(r"[>〉＞]",native)
    if not p:return original
    candidate=native[p.end():].strip()
    if _accept_korean_dialogue(original,candidate,conf):
        return candidate
    return original

def ffxiv(img, language, precise, world, icons, progress=None):
    lines=_fixed_lines(img)
    out=[]; raw=[]; metadata=[]; hits=[]
    # Progress reports contain counts only, never private chat content.
    if progress:progress("line",0,len(lines))
    # Crop one row, never ask recognizer to guess location inside entire chat log.
    for row_index,(y0,y1) in enumerate(lines,1):
        if progress:progress("line",row_index,len(lines))
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
        # Re-read low-confidence mixed Latin/digit names from their own pixels.
        # This is not a dictionary replacement, and needs PSM7/13 agreement.
        if precise and items and language=="한국어":
            from ffxiv_latin_v0422 import recover_low_confidence_latin
            value=recover_low_confidence_latin(crop,value,items)
        raw.extend(_offset(items,0,top))
        value=re.sub(r"\s+([:：>〉）\]])",r"\1",value)
        novice=_novice_chat(value,world)
        if novice:
            out.append(novice)
            metadata.append({"type":"novice_chat","y":top})
            continue
        match=_FFXIV.match(value)
        # An intact <Hangul name> is stronger evidence of a chat speaker than
        # the timestamp, whose closing bracket OCR often turns into "1".
        if match is None:
            candidate=re.search(r"[<〈＜]\s*([가-힣A-Za-z0-9_＆&＠@ ]{2,32})\s*[>〉＞]\s*(.*)",value)
            if candidate:
                nick=candidate.group(1).strip()
                if re.search(r"[가-힣]",nick) and not re.search(r"(?i)^se[.．]?\d",nick):
                    match=candidate
        if match is None:
            match=_recover_damaged_ffxiv_chat_header(value)
        if match:
            nickname=match.group(1).strip()
            message=match.group(2).strip()
            message=_recheck_ffxiv_dialogue(crop,message,language)
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
        elif _looks_system_message(value):
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
            if area/(w*h)<.76: continue
            found.append((int(x),int(y),int(w),int(h),name))
    # one bubble per connected flat-colored surface
    return sorted(found,key=lambda v:(v[1],v[0]))

def _bubble_text(image,language,precise):
    """Prefer Korean-only OCR of the entire speech bubble; fall back to row OCR."""
    from kakao_korean import read_bubble
    result=read_bubble(image,language,precise)
    if result is not None:return result
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
    return "\n".join(lines),all_boxes,sum(sc)/max(1,len(sc))

def kakao(img,language,precise):
    from collections import Counter
    from kakao_stickers import find_stickers
    boxes=_bubble_boxes(img)
    stickers=find_stickers(img,boxes)
    results=[];raw=[];metadata=[];events=[]
    candidate_names=[]
    # Read labels above actual text bubbles, not profile images.
    previous_bottom=-100
    for x,y,w,h,kind in boxes:
        if kind!="상대":continue
        if y-previous_bottom>=12 and y>16:
            name_area=img.crop((max(0,x-8),max(0,y-30),min(img.width,x+95),max(1,y-5)))
            name_txt,_,_= _variants(name_area,"카카오톡",language,False)
            cleaned=re.sub(r"[^가-힣A-Za-z0-9_]","",name_txt)
            if 2<=len(cleaned)<=10 and re.search(r"[가-힣]{2,}",cleaned):
                candidate_names.append(cleaned)
        previous_bottom=y+h
    # Sticker messages can be the first visible message: the sender label
    # is usually directly ABOVE the drawn character (not in a white bubble).
    from tess_backend import read as tesseract_read
    for sticker in stickers:
        x0,y0,x1,y1=sticker["box"]
        if y0>=15:
            roi=img.crop((52,max(0,y0-38),min(img.width,165),max(1,y0-3)))
            roi=roi.resize((roi.width*3,roi.height*3),Image.Resampling.LANCZOS)
            label,_,conf=tesseract_read(roi,"카카오톡",language,psm=7)
            clean=re.sub(r"[^가-힣A-Za-z0-9_]","",label)
            if 2<=len(clean)<=8 and re.fullmatch(r"[가-힣]{2,8}",clean) and conf>=35:
                candidate_names.extend([clean,clean])
    nickname=Counter(candidate_names).most_common(1)[0][0] if candidate_names else "상대"
    # Repeated avatar/name labels are independent of OCR bubble geometry.
    from kakao_names_v036 import resolve as resolve_sender
    nickname=resolve_sender(img,nickname)
    for x,y,w,h,kind in boxes:
        # Ignore an ordinary bubble intersecting sticker artwork.
        if any(
            max(0,min(x+w,z["box"][2])-max(x,z["box"][0]))*
            max(0,min(y+h,z["box"][3])-max(y,z["box"][1])) > (w*h)*.35
            for z in stickers
        ):continue
        margin=7 if w>55 else 3
        crop=img.crop((x+margin,y+4,x+w-3,y+h-3))
        if crop.width<5 or crop.height<5:continue
        content,items,score=_bubble_text(crop,language,precise)
        from kakao_integrity_v044 import text_or_unreadable,UNREADABLE_BUBBLE
        content=text_or_unreadable(crop,content)
        if content is None:continue
        unreadable=(content==UNREADABLE_BUBBLE)
        if unreadable:score=0
        # Preserve OCR wording, but convert equivalent ellipsis glyphs to
        # ASCII triplets for faithful plain TXT exports (e.g. '.…?' -> '...?').
        from kakao_fidelity_v043 import normalize_visible_punctuation
        content=normalize_visible_punctuation(_HHMM.sub("",content)).strip()
        if not content:continue
        raw.extend(_offset(items,x+margin,y+4))
        who="나" if kind=="나" else nickname
        events.append((y, f"{who}: {content}",
                       {"speaker":who,"kind":"bubble","box":(x,y,x+w,y+h),"ocr_score":score,"needs_review":unreadable}))
    for sticker in stickers:
        box=sticker["box"]
        label=sticker["description"]
        if sticker.get("speech"):
            label+=f' / 말풍선 글씨: {sticker["speech"]}'
        events.append((sticker["y"],f'{nickname}: [이모티콘: {label}]',
                       {"speaker":nickname,"kind":"sticker","box":box,"anchor_pixels":sticker["anchor_pixels"],
                        "speech":sticker.get("speech","")}))
    for _,content,details in sorted(events,key=lambda x:x[0]):
        results.append(content)
        metadata.append(details)
    if not results:return generic(img,language,precise)
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


def analyze(img,mode,language,precise,world,icons,progress=None):
    # Screenshot of a viewer displaying the game: isolate the actual game
    # pixels before any OCR. This prevents titlebar/neighboring app text from
    # contaminating the same FFXIV chat rows; overlay coordinates are restored.
    if mode in ("자동","파판14"):
        from ffxiv_viewer_crop_v047 import crop_viewer_chat,restore_coordinates
        game_view,source_box=crop_viewer_chat(img)
        if source_box:
            return restore_coordinates(
                analyze(game_view,"파판14",language,precise,world,icons,progress=progress),
                source_box)
    if mode in ("자동","파판14"):
        from ffxiv_scoreboard_v037 import analyze as scoreboard_read
        from ffxiv_combat_v037 import analyze as combat_read
        special=scoreboard_read(img,language)
        if special is None:special=combat_read(img,language,precise)
        if special is not None:
            d,output,hits,meta,items=special
            from app import merge_rows
            return d,output,hits,meta,merge_rows(items),items

    # Catalog cards must be segmented *before* generic OCR row grouping.
    if mode in ("자동","범용","쇼핑몰 목록"):
        from shop_grid_v0374 import analyze as shop_analyze
        catalog = shop_analyze(img,language,precise,forced=(mode=="쇼핑몰 목록"))
        if catalog is not None:
            d,output,hits,meta,items=catalog
            from app import merge_rows
            return d,output,hits,meta,merge_rows(items),items
        if mode=="쇼핑몰 목록":
            mode="범용"

    if mode in ("자동","범용"):
        from multicolumn_v037 import analyze as multicolumn_read
        photo=multicolumn_read(img,language,precise)
        if photo is not None:
            d,output,hits,meta,items=photo
            from app import merge_rows
            return d,output,hits,meta,merge_rows(items),items
    if mode in ("자동","파일 탐색기"):
        from explorer_v1 import analyze as explorer_analyze
        result=explorer_analyze(img,language)
        if result is not None:
            detected,output,hits,metadata,lines=result
            from app import merge_rows
            return detected,output,hits,metadata,merge_rows(lines),lines
        if mode=="파일 탐색기":
            mode="범용"
    if mode in ("자동","범용"):
        from colored_page import analyze as colored_analyze
        result=colored_analyze(img,language,precise)
        if result is not None:
            detected,output,hits,metadata,lines=result
            from app import merge_rows
            return detected,output,hits,metadata,merge_rows(lines),lines
    if mode=="자동":mode=detect_mode(img)
    if mode=="파판14":
        result=ffxiv(img,language,precise,world,icons,progress=progress)
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
    bright=Image.new("RGB",(450,260),(240,239,239))
    ImageDraw.Draw(bright).rectangle((120,40,260,60),fill=(251,200,30))
    assert detect_mode(bright)=="범용", "Bright document with yellow text is not Kakao"
    assert len(_bubble_boxes(k))==2
    return True
