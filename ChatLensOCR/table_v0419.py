# -*- coding: utf-8 -*-
"""Pixel-backed segmentation for bright multi-column tables.

No customer text, order-ID format, dictionary substitution, or semantic
correction. When grid evidence is absent, ordinary OCR is left untouched.
"""
import hashlib
import cv2
import numpy as np
from PIL import Image

def _runs(values, gap=2):
    groups=[]
    for value in values:
        y=int(value)
        if not groups or y>groups[-1][-1]+gap:groups.append([y])
        else:groups[-1].append(y)
    return [int(np.median(g)) for g in groups]

def table_geometry(image):
    w,h=image.size
    if not (700<=w<=2600 and 370<=h<=1800):return None
    rgb=np.asarray(image.convert("RGB"),dtype=np.uint8)
    if float((rgb.min(axis=2)>215).mean())<.65:return None
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    dark=(gray<244).astype(np.uint8)
    horizontal=cv2.morphologyEx(
        dark,cv2.MORPH_OPEN,np.ones((1,max(100,round(w*.48))),np.uint8))
    coverage=horizontal[:,int(w*.02):int(w*.98)].mean(axis=1)
    centers=_runs(np.flatnonzero(coverage>.74))
    best=[]
    for i,start in enumerate(centers):
        for next_y in centers[i+1:]:
            pitch=next_y-start
            if not 38<=pitch<=115:continue
            chain=[start,next_y]
            for y in centers:
                if y>chain[-1] and abs(y-chain[-1]-pitch)<=3:
                    chain.append(y)
            if len(chain)>len(best):best=chain
    if len(best)<6:return None
    xs=np.flatnonzero(horizontal[best,:].mean(axis=0)>.8)
    if not len(xs):return None
    x0,x1=int(xs.min()),int(xs.max()+1)
    if x1-x0<w*.70:return None
    y0,y1=best[0],best[-1]
    yy=np.arange(y0+4,y1-3)
    keep=np.ones(len(yy),dtype=bool)
    for y in best:keep&=np.abs(yy-y)>4
    ink=(gray[y0+4:y1-3,x0+3:x1-3][keep]<138)
    if not len(ink):return None
    strong=(ink.sum(axis=0)>max(6,round(len(ink)*.016))).astype(np.uint8)
    active=cv2.dilate(strong,np.ones((1,13),np.uint8))>0
    clusters=[]
    for xx in np.flatnonzero(active):
        xx=int(xx)
        if not clusters or xx>clusters[-1][-1]+1:clusters.append([xx])
        else:clusters[-1].append(xx)
    bands=[(g[0]+x0+3,g[-1]+x0+4)
           for g in clusters if g[-1]-g[0]>=5]
    joined=[]
    for a,b in bands:
        if joined and a-joined[-1][1]<=21:
            joined[-1]=(joined[-1][0],b)
        else:joined.append((a,b))
    if not 4<=len(joined)<=12:return None
    mid=[round((joined[i][1]+joined[i+1][0])/2)
         for i in range(len(joined)-1)]
    edges=[x0+2]+mid+[x1-2]
    if any(edges[i+1]-edges[i]<30 for i in range(len(edges)-1)):
        return None
    top=next((y for y in reversed(centers) if 20<=y0-y<=65),y0)
    return {"row_lines":best,"column_edges":edges,"column_bands":joined,
            "header_top":top,"table_bounds":(x0,top,x1,y1)}

def _repeated_leading_square(image,lines,left,right):
    """Exclude a repeated rectangular icon, not the adjacent label."""
    if len(lines)<7 or right-left<65:return left
    gray=np.asarray(image.convert("L"))
    guesses=[]
    for y0,y1 in zip(lines[:-1],lines[1:]):
        region=gray[y0+5:y1-5,left:min(right,left+46)]<150
        if region.shape[0]<15:continue
        found=False
        for x in range(min(29,max(0,region.shape[1]-10))):
            for side in range(10,16):
                if x+side>=region.shape[1]:continue
                if min(region[:,[x,x+side]].sum(axis=0))<10:continue
                ys=np.flatnonzero(region[:,x] & region[:,x+side])
                if len(ys)<9:continue
                first,last=int(ys.min()),int(ys.max())
                if not 11<=last-first+1<=22:continue
                if region[first,x:x+side+1].mean()<.72:continue
                if region[last,x:x+side+1].mean()<.72:continue
                guesses.append(left+x+side+1)
                found=True
                break
            if found:break
    if len(guesses)<max(6,(len(lines)-1)*.60):return left
    cutoff=int(round(np.median(guesses)))
    if max(abs(v-cutoff) for v in guesses)>2:return left
    return min(cutoff,right-35)

def _colored_button_text(image,lines,edges,reader,language):
    """OCR literal light glyphs inside dark-blue geometric buttons."""
    rgb=np.asarray(image.convert("RGB"),dtype=np.int16)
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    blue=((b-r>35)&(b-g>15)&(b>115)&(r<175)&(g<200)).astype(np.uint8)
    _,_,stats,_=cv2.connectedComponentsWithStats(blue,8)
    cache={};out=[]
    for x,y,w,h,area in stats[1:]:
        x,y,w,h,area=map(int,(x,y,w,h,area))
        if not (35<=w<=150 and 14<=h<=42 and area>=w*h*.46):
            continue
        row=int(np.searchsorted(lines,y+h/2,side="right")-1)
        col=int(np.searchsorted(edges,x+w/2,side="right")-1)
        if not (0<=row<len(lines)-1 and 0<=col<len(edges)-1):
            continue
        region=rgb[y:y+h,x:x+w]
        if not region.size:continue
        pale=region.min(axis=2)>165
        binary=np.where(pale,0,255).astype(np.uint8)
        key=hashlib.sha256(binary.tobytes()+f"{w}x{h}".encode()).hexdigest()
        if key not in cache:
            bitmap=Image.fromarray(binary,"L").resize(
                (w*3,h*3),Image.Resampling.LANCZOS)
            value,_,confidence=reader(bitmap,"범용",language,psm=7)
            value=" ".join(str(value).split())
            cache[key]=value if confidence>=55 and len(value)>=2 else ""
        if cache[key]:out.append((row,col,cache[key],(x,y,x+w,y+h)))
    return out

def analyze(image,language="한국어",precise=True,reader=None):
    geo=table_geometry(image)
    if geo is None:return None
    from tess_backend import read
    from app import recognize,merge_rows
    if reader is None:reader=read
    lines=geo["row_lines"];edges=geo["column_edges"]
    top=geo["header_top"]
    title=[];raw=[];meta=[]
    if top>20:
        first=recognize(image.crop((0,0,image.width,top)),language,precise)
        title=[v["text"] for v in merge_rows(first) if v["text"].strip()]
        raw.extend(first)
    headings=[""]*(len(edges)-1)
    if top<lines[0]-10:
        header=image.crop((edges[0],top,edges[-1],lines[0]))
        scale=3 if header.height<52 else 2
        big=header.resize((header.width*scale,header.height*scale),
                          Image.Resampling.LANCZOS)
        _,parts,_=reader(big,"범용",language,psm=6)
        groups=[[] for _ in headings]
        for item in parts:
            a,b,c,d=item["box"]
            mapped={**item,"box":(a//scale+edges[0],b//scale+top,
                                  c//scale+edges[0],d//scale+top)}
            raw.append(mapped)
            center=(mapped["box"][0]+mapped["box"][2])/2
            col=int(np.searchsorted(edges,center,side="right")-1)
            if 0<=col<len(groups):groups[col].append(mapped)
        for col,items in enumerate(groups):
            if items:
                headings[col]=" ".join(v["text"].strip()
                    for v in merge_rows(items) if v["text"].strip())
    contents=[[""]*(len(edges)-1) for _ in range(len(lines)-1)]
    for col,(xa,xb) in enumerate(zip(edges[:-1],edges[1:])):
        start=xa
        if col==len(edges)-2:
            start=max(xa,_repeated_leading_square(
                image,lines,max(xa,geo["column_bands"][col][0]-5),xb))
        region=image.crop((start,lines[0]+2,xb,lines[-1]-2))
        scale=2
        big=region.resize((region.width*scale,region.height*scale),
                          Image.Resampling.LANCZOS)
        native,parts,confidence=reader(big,"범용",language,psm=6)
        buckets=[[] for _ in range(len(lines)-1)]
        for item in parts:
            a,b,c,d=item["box"]
            mapped={**item,"box":(int(a/scale)+start,int(b/scale)+lines[0]+2,
                                  int(c/scale)+start,int(d/scale)+lines[0]+2)}
            cy=(mapped["box"][1]+mapped["box"][3])/2
            row=int(np.searchsorted(lines,cy,side="right")-1)
            if 0<=row<len(buckets):
                buckets[row].append(mapped);raw.append(mapped)
        for row,items in enumerate(buckets):
            if items:
                contents[row][col]=" / ".join(
                    v["text"].strip() for v in merge_rows(items)
                    if v["text"].strip())
        # Native and TSV come from the same single OCR process. Preserve
        # native spaces only if the literal glyph sequence is identical.
        native_rows=[s.strip() for s in native.splitlines() if s.strip()]
        if len(native_rows)==len(buckets):
            def glyphs(t):
                return "".join(c for c in t if c.isalnum())
            for row,value in enumerate(native_rows):
                if contents[row][col] and glyphs(value)==glyphs(contents[row][col]):
                    contents[row][col]=value
        meta.append({"type":"visual_table_column","column":col+1,
                     "box":(start,lines[0],xb,lines[-1]),
                     "confidence":confidence,"human_verified":False,
                     "needs_review":True,"icon_crop":start>xa})
    for row,col,label,box in _colored_button_text(
            image,lines,edges,reader,language):
        contents[row][col]=(contents[row][col]+" / "+label).strip(" /")
        meta.append({"type":"colored_button_text","box":box,
                     "human_verified":False,"needs_review":True})
    if not any(any(c.strip() for c in row) for row in contents):
        return None
    body=["\t".join(row) for row in contents]
    if any(headings):title.append("\t".join(headings))
    return "범용","\n".join(title+body),[],meta,raw
