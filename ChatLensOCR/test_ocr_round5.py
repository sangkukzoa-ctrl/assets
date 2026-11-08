# -*- coding: utf-8 -*-
"""Round 5: no hard-coded Korean correction, robust single-character safety.
The real 34-image corpus stays private, and its gold audit is performed off CI.
"""
import sys, types
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kakao_fidelity_v043 import normalize_visible_punctuation,one_syllable_agreement
from kakao_korean import read_bubble

assert normalize_visible_punctuation("어잉.…?")=="어잉...?"
assert normalize_visible_punctuation("오잉")=="오잉"
assert normalize_visible_punctuation("기다려…")=="기다려..."
assert normalize_visible_punctuation("마지막...")=="마지막..."
assert normalize_visible_punctuation("…?")=="...?"
assert normalize_visible_punctuation("")==""

samples=[("퉤",[],86,2),("퉤",[],91,3),("퉤",[],83,4)]
assert one_syllable_agreement(samples)[0]=="퉤"
assert one_syllable_agreement([("튀",[],89,2),("퉤",[],90,3),("터",[],94,4)]) is None
assert one_syllable_agreement([("튀",[],24,2),("튀",[],26,3)]) is None

def stub_agree(image,mode,lang,psm=7,tess_lang=None):
    if psm==10:return "퉤",[{"box":(6,6,35,35),"score":.85}],85
    if psm==13:return "퉤",[{"box":(4,5,27,30),"score":.82}],82
    return "퉤",[{"box":(3,4,21,25),"score":.86}],86
backend=types.ModuleType("tess_backend");backend.read=stub_agree
with patch.dict(sys.modules,{"tess_backend":backend}):
    returned=read_bubble(Image.new("RGB",(38,21),"white"),"한국어",True)
    assert returned is not None and returned[0]=="퉤",returned
    assert 0<returned[2]<10

def stub_disagree(image,mode,lang,psm=7,tess_lang=None):
    if psm==10:return "터",[],85
    if psm==13:return "퉤",[],85
    return "튀",[],85
backend.read=stub_disagree
with patch.dict(sys.modules,{"tess_backend":backend}):
    assert read_bubble(Image.new("RGB",(38,21),"white"),"한국어",True) is None

src=(Path(__file__).resolve().parent/"layout_v2.py").read_text(encoding="utf-8")
assert "normalize_visible_punctuation(_HHMM.sub" in src
assert 'content=normalize_visible_punctuation(' in src
print("Round5 PASS: ellipsis, one-character independent agreement, uncertainty fallback and transcript wiring")
