# -*- coding: utf-8 -*-
"""Abstain on a narrow class of isolated, uncorroborated graphic readings.

A pair of broad enclosed contours sharing a frame is not sufficient evidence
of a word. Only a solitary short low-confidence Latin token in the generic
photographic path is considered. Keep rejected evidence in review metadata.
"""
import math
import re
import cv2
import numpy as np
from PIL import ImageOps


def paired_frame(crop):
    """Detect two aligned, broad holes sharing one connected dark frame."""
    a=np.asarray(crop.convert('L'))
    h,w=a.shape
    if h<12 or w<24 or not 1.4<=w/h<=4.5:return False
    lo,hi=np.percentile(a,(10,90))
    if hi-lo<100:return False
    # Two thresholds must support the same topology, not just one noisy mask.
    def evidence(frac):
        mask=(a<lo+(hi-lo)*frac).astype('uint8')
        contours,hierarchy=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None:return False
        groups={}
        for j,c in enumerate(contours):
            parent=int(hierarchy[0,j,3])
            if parent<0:continue
            x,y,bw,bh=cv2.boundingRect(c)
            if not (.16*w<=bw<=.43*w and .24*h<=bh<=.68*h and 1.12<=bw/bh<=2.8):continue
            if cv2.contourArea(c)<.60*bw*bh:continue
            groups.setdefault(parent,[]).append((x,y,bw,bh))
        for parent,holes in groups.items():
            if len(holes)!=2:continue
            l,r=sorted(holes);x,y,bw,bh=l;u,v,rw,rh=r
            gap=u-x-bw
            if not (.02*w<=gap<=.20*w and abs(y-v)<=.12*h and
                    .75<=bw/rw<=1.33 and .75<=bh/rh<=1.33):continue
            # A visible bridge and a wide enclosing outline, not two
            # independent letter counters such as ordinary printed "oo".
            px,py,pw,ph=cv2.boundingRect(contours[parent])
            if pw<.60*w or ph>h or not (px<x and px+pw>u+rw):continue
            # Require separate small dark marks above both holes: an
            # additional graphic-layout cue, not a single shape threshold.
            above=mask[:min(y,v),:]
            if above.shape[0]<3:continue
            n,_,stats,_=cv2.connectedComponentsWithStats(above,8)
            def mark(cx):
                return any(abs((ax+aw/2)-cx)<=.15*w and
                           .045*w<=aw<=.25*w and 1<=ah<=.25*h and
                           ar>=3 and ay+ah<=above.shape[0]-1
                           for ax,ay,aw,ah,ar in stats[1:])
            if mark(x+bw/2) and mark(u+rw/2):return True
        return False
    return evidence(.17) and evidence(.27)


def reject_isolated_graphic(image,items,rows,language,reader=None):
    """Return review evidence or None. Never use a failed OCR call as proof."""
    if len(items)!=1 or len(rows)!=1:return None
    item=items[0];text=str(item.get('text','')).strip()
    if not re.fullmatch(r'[A-Za-z]{1,3}',text) or str(rows[0].get('text','')).strip()!=text:return None
    try:
        score=float(item.get('score',1))
        if not math.isfinite(score) or not 0<score<.70:return None
        x,y,u,v=map(int,item['box'])
        if not (0<=x<u<=image.width and 0<=y<v<=image.height):return None
    except (ValueError,TypeError,KeyError,OverflowError):return None
    crop=image.crop((x,y,u,v))
    if not paired_frame(crop):return None
    if reader is None:
        from tess_backend import read as reader
    # Independent recognizer veto: any exact reading preserves the original.
    # Do not run OCR over the entire image or replace it with new guesses.
    area=ImageOps.expand(crop.resize((crop.width*3,crop.height*3)),border=10,fill='white')
    try:
        alternate,boxes,confidence=reader(area,'범용',language,psm=7,tess_lang='eng')
    except Exception:return None
    # Missing engine, empty result, or failed read: preserve original.
    if not str(alternate).strip():return None
    if text.casefold() in re.findall(r'[A-Za-z]+',str(alternate).casefold()):return None
    return {'type':'isolated_graphic_candidate','box':(x,y,u,v),
            'rejected_text':text,'confidence':score,'human_verified':False,
            'needs_review':True,'evidence':'paired_connected_frame_and_ocr_disagreement'}
