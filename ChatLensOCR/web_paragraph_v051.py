# -*- coding: utf-8 -*-
"""Experimental, pixel-gated paragraph rescue. No reference text or web lookup."""
import math
import numpy as np
from PIL import Image, ImageOps


def paragraph_ink(image):
    w,h=image.size
    if not (320<=w<=2400 and 16<=h<=300 and w>=3*h):return None
    a=np.asarray(image.convert('RGB')).astype(np.int16)
    white=(a.min(2)>=235)
    if white.mean()<.72:return None
    ink=a.max(2)<180
    if not .015<=ink.mean()<=.22:return None
    if (ink.sum(1)>.85*w).any() or (ink.sum(0)>.85*h).any():return None
    # Exclude large colored regions; small subpixel font fringes are valid.
    colorful=(a.max(2)-a.min(2)>65)&(a.min(2)<170)
    if colorful.mean()>.22:return None
    yy=np.flatnonzero(ink.sum(1)>=max(3,int(w*.006)))
    bands=[g for g in np.split(yy,np.where(np.diff(yy)>4)[0]+1) if len(g)>=4]
    if not 1<=len(bands)<=8:return None
    heights=[int(g[-1]-g[0]+1) for g in bands]
    if min(heights)<7 or max(heights)>38:return None
    if max(heights)>1.85*min(heights):return None
    if len(bands)>2:
        pitch=np.diff([g[0] for g in bands]);med=float(np.median(pitch))
        if max(abs(pitch-med))>max(5,.30*med):return None
    return ink


def coverage(ink,boxes):
    h,w=ink.shape;mask=np.zeros_like(ink)
    for item in boxes:
        try:
            l,t,r,b=map(float,item['box'])
            if not all(map(math.isfinite,(l,t,r,b))) or l>=r or t>=b:continue
            l=max(0,math.floor(l));t=max(0,math.floor(t));r=min(w,math.ceil(r));b=min(h,math.ceil(b))
            if l<r and t<b:mask[t:b,l:r]=True
        except (KeyError,TypeError,ValueError,OverflowError):continue
    return float((ink&mask).sum()/max(1,ink.sum()))


def suspect(ink,items):
    if not items:return True
    if coverage(ink,items)<.85:return True
    return any(float(x.get('score',0))<.85 for x in items)


def candidate_ok(ink,items,text,boxes,confidence):
    if not text.strip() or not boxes or not math.isfinite(confidence) or confidence<85:return False
    # Pixel coverage from both engines is on the same source coordinate system.
    c=coverage(ink,boxes); prior=coverage(ink,items)
    return c>=.85 and c>=prior-.12


def rescue(image,language,items,reader=None):
    if language!='한국어':return None
    ink=paragraph_ink(image)
    if ink is None or not suspect(ink,items):return None
    if reader is None:
        from tess_backend import read as reader
    scale=3;pad=30
    picture=ImageOps.expand(image.convert('RGB').resize((image.width*scale,image.height*scale),Image.Resampling.LANCZOS),border=pad,fill='white')
    try:
        text,boxes,conf=reader(picture,'범용',language,psm=6,tess_lang='kor+eng')
        source=[]
        for x in boxes:
            l,t,r,b=x['box'];a=max(0,(l-pad)/scale);c=min(image.width,(r-pad)/scale);d=max(0,(t-pad)/scale);e=min(image.height,(b-pad)/scale)
            if a<c and d<e:source.append(dict(x,box=(a,d,c,e)))
        if candidate_ok(ink,items,text,source,float(conf)):
            return text,source,{'type':'paragraph_pixel_rescue','human_verified':False,'needs_review':True,'confidence':float(conf)/100,'box':(0,0,image.width,image.height)}
    except (TypeError,ValueError,KeyError,OverflowError,RuntimeError):pass
    return None
