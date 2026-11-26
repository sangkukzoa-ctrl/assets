# -*- coding: utf-8 -*-
"""Bounded job-icon matching for an independently detected icon tile.

Unlike the legacy name-anchor search, equal-size tiles can be compared.
No samples are learned here. An uncertain or ambiguous match stays unknown.
"""
import cv2
import numpy as np


def match_tile(image, templates):
    w,h=image.size
    limit=min(w,h,64)
    if limit<8 or max(w,h)>96 or max(w,h)>2*limit:
        return "",None,0.
    patch=np.asarray(image.convert("L"))
    if patch.std()<8:
        return "",None,0.
    patch=cv2.equalizeHist(patch)
    sizes=sorted({max(8,round(limit*f)) for f in (.60,.70,.80,.90,1.0)})
    ranked={}
    for job,raw in templates:
        if not job or raw is None or raw.ndim!=2 or min(raw.shape)<8:
            continue
        for size in sizes:
            if size>limit:
                continue
            t=cv2.resize(raw,(size,size),interpolation=cv2.INTER_AREA if size<min(raw.shape) else cv2.INTER_LINEAR)
            if t.std()<5:
                continue
            t=cv2.equalizeHist(t)
            scores=cv2.matchTemplate(patch,t,cv2.TM_CCOEFF_NORMED)
            # Prefer the center of the detected tile, without searching
            # outside the evidenced region or rewarding a tiny unrelated mark.
            yy,xx=np.indices(scores.shape)
            drift=(abs(xx+size/2-w/2)+abs(yy+size/2-h/2))/limit
            adjusted=scores-.08*drift-.035*(1-size/limit)
            _,score,_,xy=cv2.minMaxLoc(adjusted.astype("float32"))
            if not np.isfinite(score):
                continue
            x,y=xy
            if job not in ranked or score>ranked[job][0]:
                ranked[job]=(float(score),(x,y,x+size,y+size))
    if not ranked:
        return "",None,0.
    order=sorted(ranked.items(),key=lambda item:-item[1][0])
    job,(score,box)=order[0]
    runner=order[1][1][0] if len(order)>1 else 0.
    if score<.76 or score-runner<.045:
        return "",None,score
    return job,box,score
