# -*- coding: utf-8 -*-
"""Conservative focus isolation for dimmed, full-panel tooltip captures.

This detector uses geometry and luminance only. It is not a game-name,
filename, reference-transcript or fixed-resolution classifier.
Unsupported images stay on their original OCR path.
"""
from dataclasses import dataclass
import numpy as np
import cv2
from PIL import Image

@dataclass(frozen=True)
class Focus:
    background: int
    cutoff: int
    separators: tuple
    icon_box: tuple

def detect(image):
    w,h=image.size
    if w<120 or h<180 or not 1.25<=h/w<=4.5:
        return None
    a=np.asarray(image.convert("RGB"))
    hi=a.max(axis=2).astype(np.int16)
    lo=a.min(axis=2).astype(np.int16)
    hist=np.bincount(hi.ravel(),minlength=256)
    bg=int(hist[:64].argmax())
    if not 8<=bg<=55 or hist[bg]/hi.size<.55:
        return None
    if (hi<=bg+22).mean()<.78 or not .025<=(hi>=100).mean()<=.22:
        return None
    # Repeated pale, narrow dividers with similar horizontal coverage.
    neutral=(hi>=bg+10)&(hi<=bg+95)&(hi-lo<=8)
    row=neutral.sum(axis=1)
    ys=np.flatnonzero(row>=w*.40)
    groups=np.split(ys,np.where(np.diff(ys)>1)[0]+1)
    div=[]
    for g in groups:
        if not len(g) or len(g)>max(3,round(w*.012)):
            continue
        y=int(g[len(g)//2])
        xs=np.flatnonzero(neutral[y])
        if len(xs) and xs[-1]-xs[0]>=w*.75:
            div.append(y)
    if len(div)<3 or div[-1]-div[0]<h*.35:
        return None
    # Bright, approximately square item tile near the upper left, bracketed
    # by dividers. A plain dark document or chat log does not satisfy this.
    white=(lo>=225).astype("uint8")
    _,_,stats,_=cv2.connectedComponentsWithStats(white,8)
    tiles=[]
    for x,y,tw,th,area in stats[1:]:
        if not (w*.12<=tw<=w*.35 and .8<=tw/max(1,th)<=1.25
                and x<=w*.18 and h*.08<=y<=h*.50
                and area>=tw*th*.45):
            continue
        if any(d<y for d in div) and any(d>y+th for d in div):
            tiles.append((int(x),int(y),int(x+tw),int(y+th)))
    if len(tiles)!=1:
        return None
    return Focus(bg,bg+18,tuple(div),tiles[0])

def prepare(image, focus):
    """Suppress dim background without resizing or deleting text regions."""
    a=np.array(image.convert("RGB"))
    dark=a.max(axis=2)<=focus.cutoff
    a[dark]=focus.background
    return Image.fromarray(a)

def analyze(image, language, precise, reader=None, merger=None):
    focus=detect(image)
    if focus is None:
        return None
    if reader is None or merger is None:
        from app import recognize, merge_rows
        reader=reader or recognize
        merger=merger or merge_rows
    filtered=prepare(image,focus)
    items=reader(filtered,language,precise)
    rows=merger(items)
    # No output means the ordinary recognition path must be allowed to run.
    text="\n".join(str(r["text"]) for r in rows)
    if not text.strip():
        return None
    return ("범용",text,[],[{
        "type":"focused_tooltip", "box":(0,0,image.width,image.height),
        "background_level":focus.background,"cutoff":focus.cutoff,
        "human_verified":False,"needs_review":True,
        "evidence":"dark_panel_geometry_and_foreground_contrast"
    }],items)
