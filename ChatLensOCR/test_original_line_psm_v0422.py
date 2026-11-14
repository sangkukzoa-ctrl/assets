# -*- coding: utf-8 -*-
"""v0.4.22: do not turn a single source glyph row into a paragraph via resize.

Synthetic geometry only; no private user text, screenshots or GT.
"""
from unittest.mock import patch
from PIL import Image
from layout_v2 import _variants

seen=[]
def fake_tesseract(image,mode,language,psm=None,tess_lang=None):
    seen.append((image.size,mode,psm,tess_lang))
    return ("안녕하세요" if language=="한국어" else "Hello OCR"),[],86

def exercise(width,height,mode,language="한국어",expected_psm=7):
    seen.clear()
    with patch("tess_backend.read",side_effect=fake_tesseract),\
         patch("app.recognize",return_value=[]):
        recognized,boxes,quality=_variants(
            Image.new("RGB",(width,height),"white"),
            mode,language,False)
    assert recognized and quality>0
    assert seen and seen[0][2]==expected_psm,(width,height,mode,seen)
    return seen[0][0]

# The output bitmap is larger after the resize, but the PSM still remembers
# the ORIGINAL row's pixel geometry, including dark/light dense documents.
size=exercise(900,28,"범용")
assert size[1]>52,size
exercise(1100,52,"범용")
# Long blocks remain auto/paragraph; false promotion of a page is forbidden.
exercise(800,130,"범용",expected_psm=None)
exercise(900,53,"범용",expected_psm=None)
exercise(120,28,"범용",expected_psm=None)
# FFXIV uses its specialized dialog context; PSM is not changed.
exercise(900,28,"파판14","영어",expected_psm=None)
# A tiny crop of icons or a 1px stripe is never eligible.
exercise(2200,2,"범용",expected_psm=None)
print("v0.4.22 single-line OCR PSM determined before resize: "
      "general rows PASS, multiline, FF14 and tiny crops unchanged")
