# -*- coding: utf-8 -*-
"""Round 8 final RC: no-loss review, manual edits, general UI, JSON compatibility."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from review_v046 import (
    UNREADABLE_MARKER,format_batch_txt,review_positions,
    next_review_position,make_json_export
)
from kakao_fidelity_v043 import normalize_visible_punctuation,one_syllable_agreement
from kakao_tail_rescue_v045 import _one_safe_tail_edit
from kakao_integrity_v044 import text_or_unreadable
from PIL import Image

raw=[
    {"filename":"일반.png","mode":"범용","result":"오잉\n퉤","messages":[],"failed":False},
    {"filename":"카톡.png","mode":"카카오톡","result":"벨이: [글자 미인식]\n나: 안녕하세요\n벨이: [글자 미인식]",
     "messages":[{"speaker":"벨이","needs_review":True}],"failed":False},
]
expected="--- 일반.png [범용] ---\n오잉\n퉤\n\n--- 카톡.png [카카오톡] ---\n벨이: [글자 미인식]\n나: 안녕하세요\n벨이: [글자 미인식]"
assert format_batch_txt(raw)==expected
positions=review_positions(expected)
assert len(positions)==2
assert expected[slice(*positions[0])]==UNREADABLE_MARKER
assert next_review_position(expected,positions[0][0])==positions[1]
assert next_review_position(expected,positions[1][0])==positions[0]
assert next_review_position(expected,0)==positions[0]
assert next_review_position("완전히 인식됨")==None
assert review_positions("")==[]

clean=json.loads(make_json_export(raw,expected))
assert len(clean)==2
assert clean[0]["result"]=="오잉\n퉤"
assert "user_edited_full_txt" not in clean[0]
assert clean[1]["messages"][0]["needs_review"] is True
edited=expected.replace("벨이: [글자 미인식]","벨이: 퉤",1)
saved=json.loads(make_json_export(raw,edited))
assert saved[0]["user_edited_full_txt"]==edited
assert saved[0]["result"]=="오잉\n퉤"  # original evidence preserved
assert saved[1]["result"]==raw[1]["result"]
assert "user_edited_full_txt" not in raw[0]  # no mutation
assert "user_edited_full_txt" not in saved[1]
assert json.loads(make_json_export([], "manual"))==[]

# Do not convert ambiguous handwritten/low-resolution text using a dictionary.
assert not _one_safe_tail_edit("오잉","으잉")
assert one_syllable_agreement([("튀",[],86,2),("돼",[],91,3)]) is None
assert text_or_unreadable(Image.new("RGB",(22,22),"white"),"") is None
assert normalize_visible_punctuation("안녕하세요...")=="안녕하세요..."

app=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
assert 'root.title("ChatLens OCR v0.4.20' in app
assert 'by 2bornot' in app and 'Copyright © 2026 2bornot' in app
assert 'v0.4.20  ·  오프라인 OCR' in app
assert '🔎 미인식 찾기' in app
assert 'def go_unreadable():' in app
assert 'view.tag_add("sel",' in app
assert 'root.bind("<Control-g>"' in app
assert 'make_json_export(last[0] or [],fields[0].get(' in app
assert 'setfield(fields[0],format_batch_txt(info))' in app
assert '직접 수정 후 TXT 저장 가능' in app
assert '검증 8/8  ·  오프라인 OCR' not in app
print("Round8 PASS: editable TXT, unreadable jump, original JSON compatibility, corrected TXT preservation, no guessed Korean glyphs")
