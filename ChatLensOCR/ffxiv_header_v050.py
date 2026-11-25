# -*- coding: utf-8 -*-
"""Pixel-supported split for colored double-parenthesis chat.

Coordinates derive from paired orange delimiters, not a fixed name width.
The split is deliberately conservative; unsupported rows use the prior path.
"""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Header:
    party: tuple
    job: tuple
    name: tuple
    server: tuple | None
    flower: tuple | None
    body: tuple

def _runs(mask, gap=1):
    xs=np.flatnonzero(mask)
    return [(int(g[0]),int(g[-1])+1)
            for g in np.split(xs,np.where(np.diff(xs)>gap+1)[0]+1) if len(g)]

def split_header(image):
    w,h=image.size
    if w<120 or not 8<=h<=65:
        return None
    a=np.asarray(image.convert("RGB")).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    orange=(r>140)&(g>65)&(b<150)&(r>g+20)&(g>b+8)
    name=((r>150)&(r>g+40)&(r>b+20))|((b>150)&(b>r+40)&(b>g+20))|((g>130)&(g>r+30)&(g>b+20))
    pale=(r>150)&(g>150)&(b>150)&(np.maximum(np.maximum(r,g),b)-np.minimum(np.minimum(r,g),b)<40)
    threshold=max(2,h//9)
    runs=_runs(orange.sum(0)>=threshold,2)
    pairs=[]
    for (x,e),(u,v) in zip(runs,runs[1:]):
        pitch=u-x
        if (max(e-x,v-u)<=max(3,h*.40) and
            max(3,h*.18)<=pitch<=h*.65 and
            abs((e-x)-(v-u))<=max(2,h*.15)):
            pairs.append((x,v,pitch))
    for x,end,pitch in pairs:
        if not w*.04<=x<=min(w*.40,h*6) or pale[:,:x].sum()<h*2:
            continue
        party_start=end+1
        job_start=round(x+4*pitch)
        name_start=round(x+7.5*pitch)
        if job_start<=party_start or name_start<=job_start:continue
        for cx,ce,cp in pairs:
            if cx<name_start+h*.8 or abs(cp-pitch)>max(2,pitch*.35):
                continue
            region=name[:,name_start:cx]
            if region.sum()<max(18,h*2) or orange[:,ce:].sum()<max(18,h*2):
                continue
            # Colored header, not a pair of ordinary punctuation marks in prose.
            if orange[:,name_start:cx].sum()>max(5,region.sum()*.16):
                continue
            # Violet/white separators have a compact violet core. Only split
            # when colored text exists on both sides; no dictionary guessing.
            violet=(b>155)&(b>g+40)&(b>r+10)&(r>70)
            floral=_runs(violet[:,name_start:cx].sum(0)>=threshold,2)
            flowers=[]
            for l,u in floral:
                l+=name_start;u+=name_start
                if not h*.22<=u-l<=h*1.25:continue
                left=max(name_start,l-2);right=min(cx,u+2)
                if name[:,name_start:left].sum()<h or name[:,right:cx].sum()<h:continue
                flowers.append((left,right))
            # Multiple candidate separators are ambiguous, so leave the whole
            # header to the old path rather than creating a wrong server.
            if len(flowers)>1:return None
            flower=flowers[0] if flowers else None
            if flower:
                nbox=(name_start,flower[0]);sbox=(flower[1],cx)
            else:
                nbox=(name_start,cx);sbox=None
            return Header((party_start,job_start),(job_start,name_start),
                          nbox,sbox,flower,(ce,w))
    return None

def _valid_name(value):
    value=value.strip()
    return (0<len(value)<=64 and any(c.isalnum() for c in value)
            and all(c.isalnum() or c in " _-'." for c in value))

def transcribe_header(image, source, top, language, world, icons, reader, geometry, body_reader=None):
    """Read each evidenced region once; unknown geometry/readings fall back."""
    def read_zone(box):
        raw, _, conf=reader(image,box[0],box[1],language)
        return raw.strip(),float(conf)

    nickname,nconf=read_zone(geometry.name)
    if not _valid_name(nickname) or nconf<35:
        return None
    if body_reader is None:
        message,mconf=read_zone(geometry.body)
    else:
        message,_,mconf=body_reader(image,*geometry.body,language)
        message=message.strip();mconf=float(mconf)
    if not message or mconf<30:
        return None
    server="";sconf=None
    if geometry.server is not None:
        server,sconf=read_zone(geometry.server)
        if not _valid_name(server) or sconf<35:
            return None

    party,pconf=read_zone(geometry.party)
    if party not in ("A","B","C","1","2","3","4","5","6","7","8") or pconf<45:
        party=None
    job="직업미확인";rect=None;ic_conf=0.
    x0,x1=geometry.job
    try:
        # The legacy matcher searches to the left of the supplied anchor.
        # Give it only the evidenced job tile, not the party/name pixels.
        tile=source.crop((x0,top,x1,top+image.height))
        j,local,ic_conf=icons.match(tile,(tile.width-1,0,tile.width,tile.height))
        if j and local and 0<=local[0]<local[2]<=tile.width and 0<=local[1]<local[3]<=tile.height:
            job=j
            rect=(x0+local[0],top+local[1],x0+local[2],top+local[3])
    except Exception:
        pass
    speaker=nickname+("&"+server if server and server!=world else "")
    def absolute(box):
        return (box[0],top,box[1],top+image.height)
    semantic=[{"kind":"party_marker","value":party,"box":absolute(geometry.party),
               "verified":False},
              {"kind":"job_icon","value":job if rect else None,
               "box":rect or absolute(geometry.job),"verified":False}]
    if geometry.flower is not None:
        semantic.append({"kind":"cross_world_separator_candidate","value":None,
                         "box":absolute(geometry.flower),"verified":False})
    scores=[nconf,mconf]+([sconf] if sconf is not None else [])
    meta={"speaker":nickname,"server":server,"job":job,
          "confidence":round(sum(scores)/(100*len(scores)),3),
          "icon_confidence":ic_conf,"pvp_color":True,"y":top,
          "header_split":"paired_color_delimiters",
          "party_marker":party,"semantic_regions":semantic,
          "raw_header":nickname+("&"+server if server else ""),
          "name_box":absolute(geometry.name),"body_box":absolute(geometry.body),
          "human_verified":False,"needs_review":True}
    if geometry.server is not None:
        meta["server_box"]=absolute(geometry.server)
    return f"({job}){speaker}: {message}",meta,(rect,job) if rect else None
