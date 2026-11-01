# -*- coding: utf-8 -*-
"""Color/layout based Final Fantasy XIV PvP chat reader.
Reads speaker and message separately; normal prose OCR must not swallow job icons.
"""
import re
import cv2
import numpy as np
from PIL import Image

def is_pvp_row(img):
    a=np.asarray(img.convert("RGB")).astype("int16")
    if a.shape[1]<280:return False
    near=a[:,90:min(205,a.shape[1])]
    far=a[:,195:]
    r,g,b=near[:,:,0],near[:,:,1],near[:,:,2]
    name=((b>r+30)&(b>150)) | ((g>r+22)&(g>b+8)&(g>130)) | ((r>b+50)&(r>150))
    r,g,b=far[:,:,0],far[:,:,1],far[:,:,2]
    orange=(r>140)&(g>65)&(b<150)&(r>g+20)&(g>b+8)
    return int(name.sum())>=35 and int(orange.sum())>=35

def _read_zone(img,x0,x1,language,scale=4):
    from tess_backend import read
    end=min(img.width,x1)
    if end<=x0:return "",[],0.
    area=img.crop((x0,0,end,img.height))
    area=area.resize((area.width*scale,area.height*scale),Image.Resampling.LANCZOS)
    raw,boxes,confidence=read(area,"파판14",language,psm=7)
    return raw.strip(),boxes,confidence

def transcribe(img,source,top,language,world,icons):
    """Return (message, metadata, icon hit) or None for unrecognized colored chat."""
    if not is_pvp_row(img):return None
    # The HUD role badge occupies x=65..80 and the job icon x=78..100
    # in this chat UI scale; the speaker name follows at x~100.
    name_text,_,name_conf=_read_zone(img,97,205,language)
    msg_text,_,msg_conf=_read_zone(img,203,img.width,language)
    # Do not invent a name/server if a colored name fails to read.
    groups=re.findall(r"[가-힣]{2,}",name_text)
    if not groups or not msg_text:return None
    nickname=groups[0]
    # The world follows the floral cross-world separator, if readable.
    server=groups[1] if len(groups)>1 else ""
    prefix=nickname+("&"+server if server and server!=world else "")
    message=re.sub(r"^[\s\)\]»〉＞]+","",msg_text)
    if not message:return None
    job="직업미확인";rect=None;ic_conf=0.
    try:
        j,rect,ic_conf=icons.match(source,(100,top,125,top+img.height))
        if j:job=j
    except Exception:pass
    formatted=f"({job}){prefix}: {message}"
    meta={"speaker":nickname,"server":server,"job":job,
          "confidence":round((name_conf+msg_conf)/200,3),
          "icon_confidence":ic_conf,"pvp_color":True,"raw_header":name_text}
    return formatted,meta,(rect,job) if rect is not None and job!="직업미확인" else None
