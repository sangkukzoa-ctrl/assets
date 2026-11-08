# -*- coding: utf-8 -*-
"""Round 1 OCR behavioral tests. Uses synthetic strings, NOT private screenshots."""
import sys
import types
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parent))
from kakao_korean import _choose_consensus, _preserve_lines

assert _preserve_lines("첫째  줄\n둘째  문장") == "첫째 줄\n둘째 문장"
selected = _choose_consensus([
    ("덜뚱이가",[],92,2),("덜팽이가",[],78,3),("덜팽이가",[],80,3)
])
assert selected[0] == "덜팽이가", selected
assert _choose_consensus([("",[],0,2)]) is None

import kakao_names_v036 as nicknames
backend=types.ModuleType("tess_backend")
readings=iter([
    ("달팽이", [], 76),("팽이", [], 93),("팽이", [], 91),
    ("달공이", [], 65),("달팽이", [], 92),("달팽이", [], 88),
])
backend.read=lambda *a,**k: next(readings)
previous_backend=sys.modules.get("tess_backend")
previous_rows=nicknames.avatar_rows
try:
    sys.modules["tess_backend"]=backend
    nicknames.avatar_rows=lambda img: [(18,55),(90,127)]
    got=nicknames.resolve(Image.new("RGB",(355,220),(185,207,225)))
    assert got=="달팽이", got
finally:
    nicknames.avatar_rows=previous_rows
    if previous_backend is None:
        sys.modules.pop("tess_backend",None)
    else:
        sys.modules["tess_backend"]=previous_backend

print("round1 PASS: Korean bubble consensus, nickname ROI voting, multiline preservation")
