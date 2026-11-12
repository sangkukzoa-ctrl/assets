# -*- coding: utf-8 -*-
"""v0.4.17 synthetic-only photo-caption consensus and strict abstention.

Real transcripts and screen pixels remain on the user's private machine.
"""
from unittest.mock import patch
from PIL import Image
import numpy as np
from generic_blank_caption_v0413 import recover_empty_caption

w,h=545,363
yy,xx=np.mgrid[0:h,0:w]
v=(10+xx/w*205+yy/h*67).clip(0,240).astype("uint8")
photo=Image.fromarray(np.stack([v,v//2+19,v//2+26],axis=2),"RGB")

# A pure trailing segmentation artifact is resolved using an extra real
# pixel-processing read, NEVER by removing a syllable on semantic grounds.
base="다음 주말에 만나요"
with patch("tess_backend.read",side_effect=[
        (base,[],81),(base+" 해",[],82),
        ("다음 주마레 만나요",[],74),(base,[],86)]):
    assert recover_empty_caption(photo,"","한국어")==base

# A period and a comma are not interchangeable even when punctuation-
# stripped strings agree. Only an EXACT extra vote chooses the comma.
comma="단어 하나, 둘 셋 입니다"
with patch("tess_backend.read",side_effect=[
        (comma,[],86),("",[],0),
        ("단어 하나. 둘 셋",[],92),(comma,[],87)]):
    assert recover_empty_caption(photo,"","한국어")==comma

# Literal spacing matters. A low-confidence raw vote cannot outvote a
# corroborated, pixel-sourced word boundary.
spaced="구역도 없습니다."
with patch("tess_backend.read",side_effect=[
        ("구역도없습니다.",[],73),(spaced,[],71),
        (spaced,[],61),(spaced,[],56),(spaced,[],74)]):
    assert recover_empty_caption(photo,"","한국어")==spaced

# A single DIFFERENT internal Hangul glyph is not a license to generate
# any fourth or fifth hypothesis. This also catches unbounded OCR retries.
with patch("tess_backend.read",side_effect=[
        ("여기에서 만나요",[],89),("여기에서 마나요",[],92),
        ("여기에서 오나요",[],89)]):
    assert recover_empty_caption(photo,"","한국어")==""

assert recover_empty_caption(photo,"source already read","한국어")=="source already read"
print("v0.4.17 exact white-caption text and punctuation recovery; "
      "no grammar changes, no free fourth/fifth guesses PASS")
