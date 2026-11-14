# -*- coding: utf-8 -*-
"""Locate unreadable pale-gold outlined captions using pixel geometry only.

This is a REVIEW trigger, not an OCR engine: it never generates or guesses
dialogue. A caption missed by OCR can be marked for human correction.
False positives are deliberately constrained by line count, repeated
letter-like horizontal transitions, lower-screen position, and spacing.
"""
import cv2
import numpy as np


def outlined_caption_box(image):
    w,h=image.size
    if not (380<=w<=1800 and 320<=h<=1400):
        return None
    a=np.asarray(image.convert("RGB"),dtype=np.int16)
    # The rescue is intended for photo/video captions, not dense game logs
    # or specification tables whose repeated yellow labels resemble subtitles.
    upper=cv2.cvtColor(a[:int(h*.52)].astype(np.uint8),
                       cv2.COLOR_RGB2GRAY)
    if np.percentile(upper,5)>=80:
        return None
    if float((cv2.Canny(upper,80,180)>0).mean())>.024:
        return None
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    yellow=((r>125)&(g>105)&(r-b>28)&(g-b>20)&
            (r-g<95)&(g>=r*.56)&(b<205))
    # Only lower-screen glyphs; golden banners far above are not subtitles.
    begin=int(h*.52)
    mask=yellow[begin:]
    transitions=np.count_nonzero(
        mask[:,1:]!=mask[:,:-1],axis=1).astype(np.float32)
    # Smooth naturally irregular antialiased edges without making up glyphs.
    score=cv2.GaussianBlur(transitions.reshape(-1,1),(1,9),0).reshape(-1)
    minimum=max(28.,w*.052)
    candidates=[]
    for i in range(3,len(score)-3):
        if score[i]<minimum or score[i]<score[i-1] or score[i]<score[i+1]:
            continue
        before=score[max(0,i-15):i]
        after=score[i+1:min(len(score),i+16)]
        if not len(before) or not len(after):
            continue
        if score[i]-min(float(before.min()),float(after.min()))<9:
            continue
        candidates.append((i+begin,float(score[i])))
    # Nonmaximum suppression picks one strong glyph row per printed line.
    keep=[]
    separation=max(21,min(40,int(h*.05)))
    for y,value in sorted(candidates,key=lambda t:-t[1]):
        if all(abs(y-other)>=separation for other,_ in keep):
            keep.append((y,value))
    keep.sort()
    runs=[]
    for i,first in enumerate(keep):
        group=[first]
        for peak in keep[i+1:]:
            gap=peak[0]-group[-1][0]
            if 25<=gap<=65:
                group.append(peak)
            elif gap>65:
                break
        if len(group)>=4:
            runs.append(group)
    if not runs:
        return None
    best=max(runs,key=lambda x:(len(x),sum(v for _,v in x)))
    if best[-1][0]<int(h*.83):
        return None
    return (0,max(0,best[0][0]-29),w,min(h,best[-1][0]+27))
