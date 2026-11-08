# -*- coding: utf-8 -*-
"""Find a game screenshot shown inside a desktop image viewer.

This does not OCR a JPEGView title to infer personal filenames. It inspects
pixel geometry only: a bright caption bar above dark FFXIV chat, with a
separate desktop/application region to its right. Never trims a native full-
screen FFXIV screenshot or a bright document.
"""
import numpy as np

def viewer_chat_box(image):
    if image is None or image.width<900 or image.height<330:
        return None
    a=np.asarray(image.convert("RGB"),dtype=np.uint8)
    h,w=a.shape[:2]
    y0=max(6,min(15,h//30))
    y1=min(45,max(25,h//12))
    if y1-y0<15:return None
    bar=a[y0:y1,:,:]
    # More than 70% bright RGB pixels in a 25-column neighborhood.
    bright=((bar[:,:,0]>185)&(bar[:,:,1]>185)&(bar[:,:,2]>185)).mean(axis=0)
    width=min(w-20,int(w*.83))
    smoothed=np.convolve(bright[:width],np.ones(25)/25,mode="same")
    # Caption bar must start near the left screenshot margin.
    if smoothed[32:85].mean()<.67:return None
    start=max(240,int(w*.18))
    breaks=np.flatnonzero(smoothed[start:]<.30)
    if not len(breaks):return None
    right=int(start+breaks[0])
    if right<300 or right>int(w*.78):return None
    # Require a sustained transition, not just glyphs or caption text.
    if np.mean(smoothed[right:min(width,right+35)])>.32:return None
    # Image viewer body must be dark and contain warm FFXIV text pixels.
    content=a[min(65,h-1):min(h,240),:right-3]
    if content.size==0:return None
    if float((content.mean(axis=2)<105).mean())<.48:return None
    r,g,b=[content[:,:,i].astype("int16") for i in range(3)]
    warm=(r>135)&(g>100)&(r-b>30)&(g-b>20)
    if int(warm.sum())<75:return None
    # A white caption should terminate above the dark body.
    strip=a[8:min(110,h),25:min(260,right-10)].mean(axis=(1,2))
    transitions=np.flatnonzero((strip[:-1]>155)&(strip[1:]<125))
    if not len(transitions):return None
    top=int(9+transitions[0])
    if top<27 or top>83:return None
    return (0,top,min(w,right-2),h)

def crop_viewer_chat(image):
    box=viewer_chat_box(image)
    return (image.crop(box),box) if box else (image,None)

def restore_coordinates(result,box):
    """Return analysis tuple with overlay boxes in original desktop coords."""
    if box is None:return result
    from app import merge_rows
    xoffset,yoffset=box[0],box[1]
    detected,output,hits,meta,rows,raw=result
    def shift(rect):
        x0,y0,x1,y1=rect
        return (x0+xoffset,y0+yoffset,x1+xoffset,y1+yoffset)
    shifted=[]
    for item in raw:
        copy=dict(item)
        if "box" in copy:copy["box"]=shift(copy["box"])
        shifted.append(copy)
    corrected_hits=[(shift(rect),job) for rect,job in hits]
    corrected_meta=[]
    for item in meta:
        if not isinstance(item,dict):
            corrected_meta.append(item);continue
        copy=dict(item)
        if "box" in copy:copy["box"]=shift(copy["box"])
        if "y" in copy:copy["y"]=copy["y"]+yoffset
        corrected_meta.append(copy)
    return detected,output,corrected_hits,corrected_meta,merge_rows(shifted),shifted
