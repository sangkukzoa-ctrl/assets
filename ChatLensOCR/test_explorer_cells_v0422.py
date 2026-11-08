# -*- coding: utf-8 -*-
"""Explorer column fallback must repair only independently validated missing cells."""
from unittest.mock import patch
from PIL import Image
import explorer_v1
image=Image.new("RGB",(807,560),"white")
centers=[10+i*28 for i in range(12)]
calls=[]
def measure(im): return 28,centers
def batch(im,x0,x1,found,pitch,lang="kor+eng"):
    if x0>=683: return ["" for _ in centers],[]
    if x0>=530: return ["압축(ZIP) 파일" for _ in centers],[]
    if x0>=383: return ["[날짜 미인식]" for _ in centers],[]
    return ["" for _ in centers],[]
def read(crop,lang="eng"):
    w,h=crop.size
    calls.append((w,lang))
    if w>250:return "RGBBlocks_1.2.1_actual_contour_patch.zip",[],91
    if lang=="kor":return "2026-05-18 오후 7:05",[],89
    if w<150:return "12KB",[],85
    return "",[],0
with patch.object(explorer_v1,"_measure",measure),patch.object(explorer_v1,"_batch_metadata",batch),patch.object(explorer_v1,"_ocr_single",read):
    out=explorer_v1.analyze(image)
assert out is not None
lines=out[1].splitlines()
assert len(lines)==12,len(lines)
assert "2026-05-18" in lines[0],lines[0]
assert lines[0].endswith("12KB"),lines[0]
assert "RGBBlocks_1.2.1_actual_contour_patch.zip" in lines[0],lines[0]
assert sum(1 for w,lang in calls if lang=="kor")<=6,calls
assert sum(1 for w,lang in calls if lang=="eng" and w<150)<=6,calls
print("Round3 PASS: missing Explorer date/size recovered per cell, bounded retries")
