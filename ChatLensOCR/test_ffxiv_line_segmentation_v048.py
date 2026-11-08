# -*- coding: utf-8 -*-
"""Synthetic real-layout regression: FFXIV rows against bright game scenery.

Private screenshots and real messages are not stored in the repository.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw
from layout_v2 import _fixed_lines

scene=Image.new("RGB",(453,180),(22,24,28))
draw=ImageDraw.Draw(scene)
expected_y=[10,32,54,76,98,120]
for y in expected_y:
    draw.rectangle((4,y,164,y+9),fill=(240,215,120))
# Synthetic bright road/path overlaps and bridges 4 chat lines on the right.
draw.rectangle((350,31,452,111),fill=(196,190,135))
rows=_fixed_lines(scene)
assert len(rows)==len(expected_y),rows
assert [a for a,b in rows]==expected_y,rows
assert all(8<=b-a<=14 for a,b in rows),rows
# On a clean chat window the existing behavior is unchanged.
clean=Image.new("RGB",(453,180),(22,24,28))
p=ImageDraw.Draw(clean)
for y in expected_y:p.rectangle((4,y,164,y+9),fill=(240,215,120))
assert _fixed_lines(clean)==rows,(_fixed_lines(clean),rows)
print("FFXIV bright-background row segmentation: PASS; six rows preserved")
