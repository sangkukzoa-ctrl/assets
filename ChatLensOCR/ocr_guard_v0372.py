# -*- coding: utf-8 -*-
"""RapidOCR input-size guard.

RapidOCR's reduce_max_side can compute a rounded resize width/height of 0
for a very long, thin crop. That caused v0.3.7.1's ResizeImgError on long
product listings. Before inference, split extreme strips and pad small
dimensions WITHOUT stretching glyphs; convert boxes back to source pixels.
All failures are recorded in the local debug log. The rest of the batch can
continue even if an individual OCR tile fails.
"""
from PIL import Image
import numpy as np
from debuglog_v0372 import note, warning, exception

MIN_SIDE = 48
MAX_STRIP = 768
STRIP_OVERLAP = 48

def regions(image):
    w,h=image.size
    if w<=0 or h<=0:return []
    if w>MAX_STRIP and h<90:
        step=MAX_STRIP-STRIP_OVERLAP
        starts=list(range(0,w,step))
        return [(image.crop((a,0,min(w,a+MAX_STRIP),h)),a,0)
                for a in starts if min(w,a+MAX_STRIP)-a>1]
    if h>MAX_STRIP and w<90:
        step=MAX_STRIP-STRIP_OVERLAP
        starts=list(range(0,h,step))
        return [(image.crop((0,a,w,min(h,a+MAX_STRIP))),0,a)
                for a in starts if min(h,a+MAX_STRIP)-a>1]
    return [(image,0,0)]

def _pad(image,minimum=MIN_SIDE):
    w,h=image.size
    if w<=0 or h<=0:return None,0,0
    # Give OCR ample room to downscale without creating a zero dimension.
    safe_min=max(minimum,int(np.ceil(max(w,h)/35.0)))
    neww=max(w,safe_min);newh=max(h,safe_min)
    if neww==w and newh==h:return image,0,0
    r,g,b=np.asarray(image.convert("RGB"))[0,0]
    pad_x=(neww-w)//2;pad_y=(newh-h)//2
    canvas=Image.new("RGB",(neww,newh),(int(r),int(g),int(b)))
    canvas.paste(image,(pad_x,pad_y))
    return canvas,pad_x,pad_y

def _flatten(result, shift_x, shift_y, pad_x, pad_y, w,h):
    output=[]
    if result is None or getattr(result,"boxes",None) is None:return output
    for pts,txt,conf in zip(result.boxes,result.txts,result.scores):
        if not txt:continue
        try:
            a=np.asarray(pts,dtype=float)
            x0=max(0.,min(float(w),float(a[:,0].min())-pad_x))
            x1=max(0.,min(float(w),float(a[:,0].max())-pad_x))
            y0=max(0.,min(float(h),float(a[:,1].min())-pad_y))
            y1=max(0.,min(float(h),float(a[:,1].max())-pad_y))
            if x1-x0>0 and y1-y0>0:
                output.append({"text":str(txt),"score":float(conf),
                               "box":(shift_x+x0,shift_y+y0,shift_x+x1,shift_y+y1)})
        except (TypeError,ValueError,IndexError):
            continue
    return output

def guarded_infer(ocr,picture):
    """Use only nonzero OCR input dimensions; return source-local boxes."""
    if picture.width<=0 or picture.height<=0:
        warning("skipped_empty_ocr_crop",width=picture.width,height=picture.height)
        return []
    output=[]
    tiled=regions(picture)
    if len(tiled)>1:
        note("long_strip_tiled",source=picture.size,tiles=len(tiled))
    for patch,x,y in tiled:
        safe=None
        try:
            safe,px,py=_pad(patch)
            if safe is None:continue
            if px or py:
                note("ocr_crop_padded",original=patch.size,
                     safe=safe.size,offset=(x,y))
            result=ocr(np.asarray(safe.convert("RGB")))
            output+=_flatten(result,x,y,px,py,patch.width,patch.height)
        except Exception as error:
            # RapidOCR sometimes rejects pathological single-line aspect
            # ratios. Retry as a larger padded canvas once.
            exception("rapidocr_tile_failed",error,original=patch.size,
                      offset=(x,y),effective=safe.size if safe else None)
            try:
                safe,px,py=_pad(patch,minimum=128)
                if safe is None:continue
                result=ocr(np.asarray(safe.convert("RGB")))
                output+=_flatten(result,x,y,px,py,patch.width,patch.height)
                note("rapidocr_tile_recovered",original=patch.size,offset=(x,y))
            except Exception as retry_error:
                exception("rapidocr_tile_skipped",retry_error,original=patch.size,
                          offset=(x,y))
                # Do not throw out other lines or other images.
                continue
    # Deduplicate overlapping strip results while keeping separate words.
    output.sort(key=lambda a:-a["score"])
    unique=[]
    for item in output:
        x0,y0,x1,y1=item["box"]
        area=max(1.,(x1-x0)*(y1-y0))
        duplicate=False
        for prev in unique:
            xx0,yy0,xx1,yy1=prev["box"]
            inter=max(0.,min(x1,xx1)-max(x0,xx0))*max(0.,min(y1,yy1)-max(y0,yy0))
            other=max(1.,(xx1-xx0)*(yy1-yy0))
            if inter>.68*min(area,other) and item["text"]==prev["text"]:
                duplicate=True
                break
        if not duplicate:unique.append(item)
    return sorted(unique,key=lambda r:(r["box"][1],r["box"][0]))

def regression():
    # Verifies that a 1px x 4000px input is padded/segmented into safely
    # nonzero dimensions and box coordinates are restored accurately.
    class Dummy:
        def __init__(self):self.shapes=[]
        def __call__(self,arr):
            self.shapes.append(arr.shape[:2])
            assert min(arr.shape[:2])>=MIN_SIDE
            class R:
                boxes=[[[8,8],[35,8],[35,28],[8,28]]]
                txts=["TEST"]
                scores=[.99]
            return R()
    for dim in ((4000,1),(1,4000),(2200,5),(1000,12),(12,1000),(1,1)):
        fake=Dummy()
        r=guarded_infer(fake,Image.new("RGB",dim,"white"))
        assert fake.shapes and all(min(h,w)>=MIN_SIDE for h,w in fake.shapes),(dim,fake.shapes)
        assert isinstance(r,list),dim
        for item in r:
            x0,y0,x1,y1=item["box"]
            assert 0<=x0<x1<=dim[0] and 0<=y0<y1<=dim[1],(dim,item)
    class AlwaysFails:
        def __call__(self,arr):raise ValueError("simulated RapidOCR ResizeImgError")
    assert guarded_infer(AlwaysFails(),Image.new("RGB",(2300,3),"white"))==[]
    return True
