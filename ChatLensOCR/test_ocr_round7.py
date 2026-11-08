# -*- coding: utf-8 -*-
"""Round 7 image-local transcription safeguards.
Synthetic images only. The 34 private benchmark images are not committed.
"""
import sys,types
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kakao_tail_rescue_v045 import _one_safe_tail_edit,rescue_korean_tail
from kakao_korean import read_bubble

before="12시라고잡아야1시에오켓지"
after="12시라고잡아야1시에오겠지"
assert _one_safe_tail_edit(before,after)
assert not _one_safe_tail_edit("올라오는거 근데 하지말라면서","돌라오는거 근데 하지말라면서")
assert not _one_safe_tail_edit("안올라오면 일야네집 12시?1시?","안돌라오면 일야네집 12시?1시?")
assert not _one_safe_tail_edit("핑핑이에게바로바로대답해달란마리야","핑핑이에게바로바로대답해달란마리아")
assert not _one_safe_tail_edit(before,"12시라고잡아야1시에오겠죠")
assert not _one_safe_tail_edit("오잉","으잉")
assert not _one_safe_tail_edit("abcd\n한글많은문장입니다","abcd\n한글많은문장이니다")

crop=Image.new("RGB",(165,22),(255,255,255))
readings=[]
def agree(img,mode,language,psm=None,tess_lang=None):
    readings.append(img.size)
    return after,[],88
got,modified=rescue_korean_tail(crop,before,reader=agree)
assert modified and got==after and len(readings)==2,(got,modified,readings)
assert readings[0] == (165*4+32,22*4+32),readings
got,modified=rescue_korean_tail(crop,before,reader=lambda *a,**k:(after,[],40))
assert got==before and not modified
n=[0]
def split(img,mode,language,psm=None,tess_lang=None):
    n[0]+=1
    return (after if n[0]==1 else before),[],89
got,modified=rescue_korean_tail(crop,before,reader=split)
assert got==before and not modified

backend=types.ModuleType("tess_backend")
def stub_read(img,mode,language,psm=7,tess_lang=None):
    if img.width>=165*4+32:return after,[],87
    if psm==7:return before,[],94
    return "",[],0
backend.read=stub_read
with patch.dict(sys.modules,{"tess_backend":backend}):
    result=read_bubble(crop,"한국어",True)
    assert result and result[0]==after,result

print("Round7 PASS: image-local OCR consensus, no word-final false positives, guard against disagreement")
