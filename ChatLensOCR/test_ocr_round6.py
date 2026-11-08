# -*- coding: utf-8 -*-
"""Round 6: preserve unreadable speech and test actual native OCR availability.

All images generated in this test are synthetic; no personal benchmark data is
included in the public repository.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kakao_integrity_v044 import has_visible_text_pixels,text_or_unreadable,UNREADABLE_BUBBLE
from tess_backend import resolve_tesseract_paths,read

white=Image.new("RGB",(33,23),"white")
yellow=Image.new("RGB",(48,27),(255,218,10))
ImageDraw.Draw(white).rectangle((8,6,12,15),fill="black")
ImageDraw.Draw(white).rectangle((16,6,22,15),fill="black")
ImageDraw.Draw(yellow).rectangle((8,6,20,15),fill="black")
assert has_visible_text_pixels(white)
assert has_visible_text_pixels(yellow)
assert not has_visible_text_pixels(Image.new("RGB",(33,23),"white"))
assert text_or_unreadable(white,"")==UNREADABLE_BUBBLE
assert text_or_unreadable(yellow,None)==UNREADABLE_BUBBLE
assert text_or_unreadable(Image.new("RGB",(33,23),"white"),"") is None
assert text_or_unreadable(yellow,"오잉")=="오잉"

exe,data=resolve_tesseract_paths()
assert exe and data,(exe,data)
assert Path(exe).is_file() and (Path(data)/"kor.traineddata").is_file(),(exe,data)
fontfile=Path("C:/Windows/Fonts/malgun.ttf")
assert fontfile.exists(),"Windows Korean test font not found"
img=Image.new("RGB",(600,105),"white")
ImageDraw.Draw(img).text((20,20),"안녕하세요",fill="black",
                        font=ImageFont.truetype(str(fontfile),47))
text,boxes,confidence=read(img,"카카오톡","한국어",psm=7,tess_lang="kor")
assert "안녕" in text,(repr(text),len(boxes),confidence)
assert boxes and confidence>25,(repr(text),len(boxes),confidence)

src=(Path(__file__).resolve().parent/"layout_v2.py").read_text(encoding="utf-8")
assert "content=text_or_unreadable(crop,content)" in src
assert '"needs_review":unreadable' in src
assert "if content is None:continue" in src

print("Round6 PASS: visible-text preservation, empty-graphic safety, real Korean OCR in Windows source, TXT review metadata")
