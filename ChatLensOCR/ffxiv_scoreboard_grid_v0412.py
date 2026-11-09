# -*- coding: utf-8 -*-
"""Pixel-only geometry for embedded FFXIV Frontline scoreboards.

Do not classify a screenshot as a scoreboard from beige alone. Both a warm
HUD rectangle and aligned character/stat rows must exist. Original private
user screenshots are never bundled or uploaded with this module.
"""
import numpy as np

HEADERS8=("캐릭터","서버","K","D","A","총 공격량","총 피해량","총 회복량")
HEADERS9=HEADERS8+("거점 점령 횟수",)

def header_geometry(image):
    """Read column border positions from the image; 8 and 9 columns differ."""
    if image.width<700 or image.height<440:return None
    a=np.asarray(image.convert("L"),dtype=np.float32)
    scan=a[round(image.height*.304):round(image.height*.349),:]
    if scan.shape[0]<8:return None
    grad=np.mean(np.abs(np.diff(scan,axis=1)),axis=0)
    smoothed=np.convolve(grad,[.0625,.25,.375,.25,.0625],mode="same")
    def peak(expected,slack=13,minimum=22):
        low=max(0,round(expected-slack))
        high=min(len(smoothed),round(expected+slack+1))
        if high<=low:return None
        pos=low+int(np.argmax(smoothed[low:high]))
        return pos if smoothed[pos]>=minimum else None
    left=max(195,int(image.width*.21))
    right=min(image.width-120,300)
    if left>=right:return None
    start=left+int(np.argmax(smoothed[left:right]))
    if smoothed[start]<28:return None
    # The nine-column version has a second internal border between the
    # healing value and the capture counter. In the eight-column version
    # that pixel location lies *inside* one long healing value.
    nine=peak(start+610,slack=10,minimum=43) is not None
    offsets=(125,164,203,242,383,524,610,706) if nine else (
        125,164,203,242,393,544,704)
    boundaries=[start-185,start]
    for offset in offsets:
        target=start+offset
        found=peak(target)
        boundaries.append(found if found is not None else target)
    if boundaries[0]<0 or boundaries[-1]>image.width:return None
    widths=np.diff(boundaries)
    if (widths<22).any() or (widths>205).any():return None
    cols=list(zip(boundaries[:-1],boundaries[1:]))
    return (HEADERS9 if nine else HEADERS8),cols

def embedded_scoreboard_box(image):
    """Return screenshot-space rectangle for a verified embedded HUD."""
    w,h=image.size
    if not (850<=w<=1200 and 650<=h<=1500):return None
    a=np.asarray(image.convert("RGB"),dtype=np.int16)
    region=a[:,int(w*.06):int(w*.90)]
    r,g,b=region[:,:,0],region[:,:,1],region[:,:,2]
    warm=(r>190)&(g>170)&(b>150)&(r<249)&((g-b)>4)&((r-g)>1)
    pixels=np.flatnonzero(warm.mean(axis=1)>.50)
    if len(pixels)<350 or not 485<=pixels[-1]-pixels[0]<=755:return None
    top=max(0,int(pixels[0])-16)
    bottom=min(h,int(pixels[-1])+16)
    box=(0,top,w,bottom)
    # Require the existing scoreboard's real eleven-row text signal too.
    from ffxiv_scoreboard_v037 import is_scoreboard
    if not is_scoreboard(image.crop(box)):return None
    return box

def _synthetic():
    """No private input required to validate 8/9-column geometry."""
    from PIL import Image,ImageDraw
    def layout(nine):
        width=979
        im=Image.new("RGB",(width,658),(231,223,214))
        d=ImageDraw.Draw(im)
        starts=([234,359,398,437,475,627,778,940] if not nine
                else [230,355,394,433,471,613,754,840,936])
        for x in starts:
            d.line((x,200,x,228),fill=(32,25,23),width=2)
        return im
    g8=header_geometry(layout(False))
    g9=header_geometry(layout(True))
    assert g8 is not None and len(g8[0])==8,g8
    assert g9 is not None and len(g9[0])==9,g9
    return True
