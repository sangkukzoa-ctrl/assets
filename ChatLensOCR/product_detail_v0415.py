# -*- coding: utf-8 -*-
"""Conservative pixel detector for ONE product detail with thumbnail gallery.

Never treat five photographs of a single product as five separate items.
Do not use OCR words, product model, language, price or semantics to classify
a gallery: verify geometric evidence of hero photo + right-side details +
a row of repeating thumbnails in the bottom-left area.
"""
import cv2
import numpy as np

def detail_evidence(image):
    w,h=image.size
    if not (900<=w<=2500 and 345<=h<=1500 and w/h>=1.45):
        return None
    rgb=np.asarray(image.convert("RGB"))
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    right=gray[int(h*.06):int(h*.75),int(w*.52):int(w*.99)]
    bright=float((right>222).mean())
    ink=float((right<105).mean())
    hero=gray[int(h*.04):int(h*.73),int(w*.025):int(w*.47)]
    hero_ink=float((hero<125).mean())
    hero_var=float(hero.std())
    if not (bright>.70 and .009<ink<.20
            and hero_ink>.03 and hero_var>20):
        return None
    lower=gray[int(h*.83):int(h*.99),:int(w*.52)]
    if lower.shape[0]<25:
        return None
    strokes=(cv2.Canny(lower,22,76)>0).mean(axis=0)
    xs=np.flatnonzero(strokes>.74)
    runs=[]
    for x in xs:
        x=int(x)
        if not runs or x-runs[-1][-1]>4:runs.append([x])
        else:runs[-1].append(x)
    peaks=[int(round(np.median(g))) for g in runs if 1<=len(g)<=6]
    best=0
    for i,x in enumerate(peaks):
        for y in peaks[i+1:]:
            pitch=y-x
            if 65<=pitch<=230:
                matched=sum(any(abs(p-(x+pitch*j))<=5 for p in peaks)
                            for j in range(6))
                best=max(best,matched)
    if best<5:
        return None
    return {"type":"single_product_detail",
            "gallery_border_count":best,
            "detail_box":(round(w*.50),0,w,h),
            "evidence":"hero_image_and_lower_left_thumbnail_edges"}

def is_single_product_detail(image):
    return detail_evidence(image) is not None
