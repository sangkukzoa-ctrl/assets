# -*- coding: utf-8 -*-
"""Conservative colored chat body recovery and paired glyph evidence."""
import re
import numpy as np
from PIL import Image, ImageOps


def _runs(mask):
    xs=np.flatnonzero(mask)
    return [(int(g[0]),int(g[-1])+1) for g in np.split(xs,np.where(np.diff(xs)>2)[0]+1) if len(g)]


def autocomplete_pairs(image):
    """Return only geometrically paired green/red bracket candidates.

    The enclosed literal text remains untouched. No icon ID is inferred.
    Coordinates are half-open and local to the source row.
    """
    w,h=image.size
    if not 8<=h<=65 or w<20:return []
    a=np.asarray(image.convert('RGB')).astype(np.int16)
    r,g,b=a.transpose(2,0,1)
    green=(g>150)&(g>r+40)&(g>b+40)
    red=(r>150)&(r>g+60)&(r>b+40)&(g<115)
    orange=(r>140)&(g>65)&(b<150)&(r>g+20)&(g>b+8)
    def components(mask):
        out=[]
        for x,e in _runs(mask.sum(0)>=max(2,h//9)):
            ys=np.flatnonzero(mask[:,x:e].any(1))
            if not len(ys):continue
            y,z=int(ys[0]),int(ys[-1]+1)
            if not (h*.15<=e-x<=h*.65 and h*.5<=z-y<=h*.95):continue
            m=mask[y:z,x:e]
            if m.mean()<.25 or m.mean()>.86:continue
            out.append(((x,y,e,z),m))
        return out
    result=[];used=set()
    for l,lm in components(green):
        candidates=[]
        for rr,rm in components(red):
            if rr in used or not h*.3<=rr[0]-l[2]<=h*18:continue
            if abs(l[1]-rr[1])>max(1,h*.12) or abs(l[3]-rr[3])>max(1,h*.12):continue
            if lm.shape!=rm.shape:continue
            mirror=rm[:,::-1]
            union=np.logical_or(lm,mirror).sum()
            if not union or np.logical_and(lm,mirror).sum()/union<.70:continue
            if orange[:,l[2]:rr[0]].sum()<h:continue
            candidates.append(rr)
        if len(candidates)==1:
            rr=candidates[0];used.add(rr)
            result.append({'kind':'autocomplete_pair_candidate','left_box':l,'right_box':rr,
                           'box':(l[0],min(l[1],rr[1]),rr[2],max(l[3],rr[3])),
                           'verified':False})
    return result


def autocomplete_row_bounds(image, bands, index):
    """Recover a clipped paired glyph without crossing adjacent OCR rows.

    The regular luminance projection can see only part of a saturated
    green/red glyph. Widen a short interior row only when a complete,
    mirrored pair overlaps that row and is clipped by the original crop.
    """
    y0,y1=bands[index]
    top,bottom=max(0,y0-2),min(image.height,y1+2)
    if index==0 or index+1>=len(bands) or y1-y0>8:
        return top,bottom
    if autocomplete_pairs(image.crop((0,top,image.width,bottom))):
        return top,bottom
    lo=max(0,bands[index-1][1]+2,y0-16)
    hi=min(image.height,bands[index+1][0]-2,y1+16)
    if not (lo<=top<bottom<=hi and 8<=hi-lo<=36):
        return top,bottom
    pairs=autocomplete_pairs(image.crop((0,lo,image.width,hi)))
    if len(pairs)!=1:
        return top,bottom
    x,a,e,b=pairs[0]['box']
    a+=lo;b+=lo
    if min(y1,b)<=max(y0,a) or (a>=top and b<=bottom):
        return top,bottom
    new_top=max(lo,min(top,a-2))
    new_bottom=min(hi,max(bottom,b+2))
    # Verify the same pair still exists in the final crop. Do not change
    # ordinary row bounds based on a single loosely matching color blob.
    final=autocomplete_pairs(image.crop((0,new_top,image.width,new_bottom)))
    if len(final)!=1:
        return top,bottom
    xx,aa,ee,bb=final[0]['box']
    if (xx,aa+new_top,ee,bb+new_top)!=(x,a,e,b):
        return top,bottom
    return new_top,new_bottom


def chromatic_body(image,x0,x1,language,primary,backend=None):
    """Two independent preprocessing readings must agree before replacement.

    The original high-confidence reading, mixed-script words, numeric tokens,
    and protected punctuation are not discarded. A paired icon is left on the
    normal path until its separate glyph-removal behavior is validated.
    """
    original=primary(image,x0,x1,language)
    text,boxes,conf=original
    if language!='한국어' or conf>=80 or x1-x0<20 or not text.strip():return original
    crop=image.crop((x0,0,x1,image.height)).convert('RGB')
    if autocomplete_pairs(crop):return original
    a=np.asarray(crop).astype(np.int16);r,g,b=a.transpose(2,0,1)
    ink=((r>110)&(r>g+30)&(r>b+15))|((b>110)&(b>r+30)&(b>g+15))|((g>105)&(g>r+25)&(g>b+15))
    orange=(r>140)&(g>65)&(b<150)&(r>g+20)&(g>b+8)
    neutral=(np.minimum.reduce([r,g,b])>150)&(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<35)
    if ink.sum()<20 or (orange&ink).sum()<ink.sum()*.70 or neutral.sum()>ink.sum()*.12:return original
    if backend is None:
        from tess_backend import read as backend
    mask=Image.fromarray(np.where(ink,0,255).astype('uint8'))
    votes={}
    # Mixed model retains Latin; Korean-only vote cannot override independently.
    for scale,lang in ((4,'kor+eng'),(6,'kor+eng'),(4,'kor')):
        area=ImageOps.expand(mask.resize((mask.width*scale,mask.height*scale),Image.Resampling.NEAREST),border=8,fill=255)
        try:
            candidate,_,score=backend(area,'파판14',language,psm=7,tess_lang=lang)
            candidate=candidate.strip();score=float(score)
        except Exception:continue
        if not candidate or score<65:continue
        votes.setdefault(candidate,[]).append((scale,lang,score))
    eligible=[]
    for candidate,readings in votes.items():
        if len({s for s,_,_ in readings})<2 or not any(l=='kor+eng' for _,l,_ in readings):continue
        score=sum(c for _,_,c in readings)/len(readings)
        if score<max(70,conf+7):continue
        if re.findall(r'\d+',candidate)!=re.findall(r'\d+',text):continue
        if re.findall(r'[A-Za-z]{2,}',candidate)!=re.findall(r'[A-Za-z]{2,}',text):continue
        # A high-confidence single Latin glyph is also literal evidence.
        protected=[str(b.get('text','')) for b in boxes if float(b.get('score',0))>=.80 and re.fullmatch(r'[A-Za-z]',str(b.get('text','')))]
        if any(candidate.count(c)<text.count(c) for c in protected):continue
        if re.findall(r'[<>?□×「」『』]',candidate)!=re.findall(r'[<>?□×「」『』]',text):continue
        eligible.append((candidate,score))
    if len(eligible)!=1:return original
    # The original OCR boxes do not describe the replacement text. Preserve
    # truthful provenance rather than returning stale per-character geometry.
    candidate,score=eligible[0]
    return candidate,[],score


def autocomplete_metadata(image, top):
    result=[]
    for pair in autocomplete_pairs(image):
        record=dict(pair)
        for key in ('box','left_box','right_box'):
            x,y,e,z=record[key];record[key]=(x,y+top,e,z+top)
        record.update(type='ffxiv_autocomplete_candidate',human_verified=False,needs_review=True)
        result.append(record)
    return result
