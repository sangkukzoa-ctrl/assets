# -*- coding: utf-8 -*-
"""Opt-in precise OCR for bright grayscale pixel-font control grids.

Control outlines and reading order come from pixels, not screenshots,
application-specific labels, dictionaries or GT. Unsupported layouts fall
back to the existing generic OCR. Black value-cell screens are deliberately
left to the existing path until an independent value recognizer is verified.
"""
from collections import Counter
import hashlib
import math
import unicodedata
import cv2
import numpy as np
from PIL import Image


def pixel_control_rows(image):
    w,h=image.size
    if not (680<=w<=1250 and 380<=h<=850):return None
    arr=np.asarray(image.convert('RGB'))
    gray=cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY)
    if float((arr.max(axis=2)-arr.min(axis=2)<8).mean())<.985:return None
    if float(((gray>155)&(gray<220)).mean())<.68:return None
    mask=(gray<70).astype('uint8')*255
    contours,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    found=[]
    for contour in contours:
        x,y,bw,bh=cv2.boundingRect(contour)
        if not (65<=bw<=245 and 33<=bh<=48):continue
        region=gray[y:y+bh,x:x+bw]
        border=np.concatenate((region[0],region[-1],region[:,0],region[:,-1]))
        inside=region[3:-3,3:-3]
        if float((border<80).mean())<.72:continue
        if float(((inside>65)&(inside<175)).mean())<.65:continue
        found.append((x,y,bw,bh))
    # Dark solid numeric values use a different glyph/contrast treatment;
    # do not route them through the gray-button path or invent digits.
    _,_,stats,_=cv2.connectedComponentsWithStats((gray<48).astype('uint8'),8)
    black_values=0
    for x,y,bw,bh,area in stats[1:]:
        if 65<=bw<=240 and 25<=bh<=50 and area>=bw*bh*.80:
            black_values+=1
    if black_values>=2:return None
    found.sort(key=lambda a:-a[2]*a[3])
    unique=[]
    for x,y,bw,bh in found:
        area=bw*bh
        if any(max(0,min(x+bw,c+cw)-max(x,c))*
               max(0,min(y+bh,d+ch)-max(y,d))>.72*area
               for c,d,cw,ch in unique):continue
        unique.append((x,y,bw,bh))
    if len(unique)<8 or len(unique)>30:return None
    rows=[]
    for box in sorted(unique,key=lambda a:(a[1]+a[3]/2,a[0])):
        center=box[1]+box[3]/2
        group=next((r for r in rows if abs(r[0]-center)<=11),None)
        if group:
            group[1].append(box)
            group[0]=(group[0]+center)/2
        else:rows.append([center,[box]])
    if len(rows)<5:return None
    if not all(len(row[1])<=3 for row in rows):return None
    for _,controls in rows:controls.sort(key=lambda a:a[0])
    return rows


def _remove_border_pipe(text, items, size):
    """Drop only a separately localized full-height edge stroke.

    A literal pipe inside a control, or a standalone symbol, is retained.
    Do not infer any replacement text from labels or dictionaries.
    """
    if not isinstance(items,(list,tuple)) or not any(c.isalnum() for c in text):
        return text,items
    w,h=size
    rejected=set(); left=False; right=False
    for i,item in enumerate(items):
        try:
            if item.get('text')!='|':continue
            a,b,c,d=map(float,item['box'])
            if not all(math.isfinite(v) for v in (a,b,c,d)):continue
            if d-b<h*.90 or c-a>max(2,w*.08):continue
            if b>h*.05 or d<h*.95:continue
            if a<=w*.03 and c<=w*.10 and text.startswith('| '):
                left=True;rejected.add(i)
            elif c>=w*.97 and a>=w*.90 and text.endswith(' |'):
                right=True;rejected.add(i)
        except (TypeError,ValueError,KeyError,AttributeError):continue
    if left:text=text[2:]
    if right:text=text[:-2]
    return text,[item for i,item in enumerate(items) if i not in rejected]


def _read_roi(roi,kind,reader,cache,language):
    if roi.width<20 or roi.height<12:return None,[],0.,False,1
    if kind=='button':
        arr=np.asarray(roi.convert('RGB'))
        pale=arr.min(axis=2)>170
        glyph=Image.fromarray(np.where(pale,0,255).astype('uint8'),'L')
        variants=[(2,7),(2,8),(3,7),(3,8)]
    else:
        glyph=roi.convert('L')
        variants=[(1,7),(1,8),(3,7),(3,8),(2,8)]
    # Raw bytes alone do not encode image dimensions: differently shaped
    # ROIs can have identical byte streams but distinct glyph geometry.
    cache_key=(kind,glyph.size,hashlib.sha256(glyph.tobytes()).hexdigest(),language)
    if cache_key in cache:return cache[cache_key]
    candidates=[]
    for factor,psm in variants:
        target=(glyph.resize((glyph.width*factor,glyph.height*factor),
                            Image.Resampling.NEAREST) if factor>1 else glyph)
        try:
            text,items,confidence=reader(target,'범용',language,psm=psm,tess_lang='eng')
        except Exception:
            # An isolated backend failure is a missing vote, not a reason
            # to discard other scales or the whole screen.
            continue
        # Literal punctuation belongs to the OCR result; a pipe is not a
        # structural delimiter here. Reject invalid backend values per variant.
        if not isinstance(text,str):continue
        text=' '.join(text.split())
        if not text:continue
        text,items=_remove_border_pipe(text,items,target.size)
        if not text:continue
        try:confidence=float(confidence)
        except (TypeError,ValueError,OverflowError):continue
        if not math.isfinite(confidence) or not 0<confidence<=100:continue
        # Symbol-only controls exist, but weak one-off artifacts are not text.
        if not any(c.isalnum() for c in text):
            if confidence<80 or not all(unicodedata.category(c)[0] in 'PS' or c.isspace() for c in text):continue
        candidates.append((text,items,confidence,factor,psm))
    if not candidates:
        result=(None,[],0.,False,1)
    elif kind=='label':
        # PSM 7 is the OCR mode for an actual single text row. Repeated
        # PSM 8 readings must not outweigh the native pixel font.
        native=next((v for v in candidates if v[3]==1 and v[4]==7),None)
        enlarged=next((v for v in candidates if v[3]==3 and v[4]==7),None)
        if native and enlarged:
            if native[0]==enlarged[0]:
                chosen=max((native,enlarged),key=lambda v:v[2]);agreed=min(native[2],enlarged[2])>=40
            elif (len(native[0])==len(enlarged[0]) and
                  sum(a!=b for a,b in zip(native[0],enlarged[0]))==1 and
                  native[2]>=35):
                # Preserve the native literal glyph for a one-character
                # enlargement mismatch; do not insert guessed spellings.
                chosen=native;agreed=False
            else:
                chosen=enlarged if enlarged[2]>=40 else None
                agreed=False
        else:
            chosen=native or enlarged
            if chosen is not None and chosen[2]<40:
                chosen=None
            if chosen is None:
                # Keep PSM8-only text if PSM7 produces none.
                counts=Counter(v[0] for v in candidates)
                count=max(counts.values())
                if count>=2:
                    chosen=next(v for v in candidates if counts[v[0]]==count)
                else:
                    trusted=[v for v in candidates if v[2]>=80]
                    chosen=max(trusted,key=lambda v:v[2]) if trusted else None
            agreed=False
        result=((chosen[0],chosen[1],chosen[2],agreed,chosen[3]) if chosen
                else (None,[],0.,False,1))
    else:
        scores=Counter(value for value,_,_,_,_ in candidates)
        count=max(scores.values())
        if count>=2:
            # Preserve the earliest literal OCR candidate on a tie;
            # alphabetical order is NOT a quality measure.
            chosen=next(x for x in candidates if scores[x[0]]==count)
            # Keep the existing literal candidate, but a split vote is not
            # agreement. Mark it for review unless a strict majority agrees.
            result=(chosen[0],chosen[1],chosen[2],count*2>len(variants) and chosen[2]>=40,chosen[3])
        else:
            # Never insert low-confidence novel letters from an unmatched
            # one-off read. A human can review the original box instead.
            trusted=[x for x in candidates if x[2]>=80]
            if trusted:
                chosen=max(trusted,key=lambda x:x[2])
                result=(chosen[0],chosen[1],chosen[2],False,chosen[3])
            else:result=(None,[],0.,False,1)
    cache[cache_key]=result
    return result



def _project_parts(parts, roi_box, factor):
    """Project half-open OCR boxes back into the source ROI.

    Round the start down and end up so a narrow glyph never collapses.
    Invalid boxes do not invalidate the independently recognized text.
    Return a review flag when geometry is incomplete or clipped.
    """
    if not isinstance(parts,(list,tuple)) or not parts:
        return [],True
    x,y,right,bottom=roi_box
    out=[];needs_review=False
    for item in parts:
        try:
            a,b,c,d=map(float,item['box'])
            if not all(math.isfinite(v) for v in (a,b,c,d)) or c<=a or d<=b:
                raise ValueError('invalid OCR box')
            original=(x+math.floor(a/factor),y+math.floor(b/factor),
                      x+math.ceil(c/factor),y+math.ceil(d/factor))
            clipped=(max(x,original[0]),max(y,original[1]),
                     min(right,original[2]),min(bottom,original[3]))
            if clipped[2]<=clipped[0] or clipped[3]<=clipped[1]:
                raise ValueError('OCR box outside ROI')
            out.append({**item,'box':clipped})
            needs_review |= clipped!=original
        except (TypeError,ValueError,KeyError,OverflowError):
            needs_review=True
    return out,needs_review


def analyze(image,language='한국어',precise=True,reader=None):
    if not precise or language not in ('한국어','영어'):return None
    rows=pixel_control_rows(image)
    if rows is None:return None
    if reader is None:
        from tess_backend import read as reader
    from review_v046 import UNREADABLE_MARKER
    from app import recognize,merge_rows
    header=[];raw=[];metadata=[]
    top=min(box[1] for _,group in rows for box in group)
    if top>46:
        glyphs=recognize(image.crop((0,0,image.width,top-5)),'영어',False)
        header=[x['text'] for x in merge_rows(glyphs) if x['text'].strip()]
        raw.extend(glyphs)
    cache={};results=[];confirmed=0;failed=0
    for center,controls in rows:
        pieces=[];left=0
        for x,y,w,h in controls:
            top=max(0,int(center)-19);bottom=min(image.height,int(center)+19)
            if x-left>45:
                # Only extend a label into the 4-pixel button border when
                # its original right edge contains visible glyph pixels.
                # Expanding every label can corrupt already readable text.
                label_box=(left,top,x,bottom)
                roi=image.crop(label_box)
                edge=np.asarray(roi.convert('L'))<100
                if (x+4<=image.width and edge.shape[1]>=4 and
                    int(edge[:,-4:].sum())>=10):
                    label_box=(left,top,x+4,bottom)
                    roi=image.crop(label_box)
                ink=np.asarray(roi.convert('L'))<105
                if ink.sum()>=max(6,roi.width*roi.height*.004):
                    value,parts,confidence,agreed,factor=_read_roi(
                        roi,'label',reader,cache,language)
                    pieces.append(value if value else UNREADABLE_MARKER)
                    projected,geometry_review=_project_parts(parts,label_box,factor)
                    raw.extend(projected)
                    confirmed+=int(bool(value));failed+=int(not value)
                    metadata.append({'type':'pixel_ui_label','box':label_box,
                                     'confidence':confidence/100,
                                     'needs_review':not agreed or geometry_review,
                                     'human_verified':False})
            button_box=(x+4,y+4,x+w-4,y+h-4)
            value,parts,confidence,agreed,factor=_read_roi(
                image.crop(button_box),'button',reader,cache,language)
            pieces.append(value if value else UNREADABLE_MARKER)
            projected,geometry_review=_project_parts(parts,button_box,factor)
            raw.extend(projected)
            confirmed+=int(bool(value));failed+=int(not value)
            metadata.append({'type':'pixel_ui_button','box':button_box,
                             'confidence':confidence/100,
                             'needs_review':not agreed or geometry_review,
                             'human_verified':False})
            left=x+w
        if pieces:results.append('\t'.join(pieces))
    # Gate by pixel-backed recognized coverage, not length or semantic text.
    # The original generic engine remains authoritative for a sparse failure.
    if not results or confirmed<max(8,failed*2):return None
    metadata.insert(0,{'type':'pixel_ui_grid','control_count':sum(len(x[1]) for x in rows),
                       'row_count':len(rows),'human_verified':False,
                       'evidence':'grayscale_rectangular_buttons'})
    return ('범용','\n'.join(header+results),[],metadata,raw)