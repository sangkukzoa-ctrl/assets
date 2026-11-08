# -*- coding: utf-8 -*-
"""Regression for conservative FFXIV mixed Latin rereading."""
from PIL import Image
from ffxiv_latin_v0422 import recover_low_confidence_latin
img=Image.new("RGB",(240,25),"black")
boxes=[
  {"text":"갈론드","score":.93,"box":(75,1,118,20)},
  {"text":"6Ｌ-15","score":.26,"box":(120,3,168,17)},
  {"text":"에","score":.92,"box":(156,2,170,20)},
  {"text":"탑승","score":.92,"box":(175,1,210,19)}]
src="현시완 님이 갈론드 6Ｌ-15에 탑승했습니다."
assert recover_low_confidence_latin(img,src,boxes,reader=lambda crop,psm:"GL-IS")=="현시완 님이 갈론드 GL-IS에 탑승했습니다."
assert recover_low_confidence_latin(img,src,boxes,reader=lambda crop,psm:"GL-IS" if psm==7 else "GL-1S")==src
assert recover_low_confidence_latin(img,src,[{**boxes[1],"score":.95}],reader=lambda crop,psm:"GL-IS")==src
assert recover_low_confidence_latin(img,"퉤",boxes,reader=lambda crop,psm:"GL-IS")=="퉤"
print("Round3 PASS: FFXIV Latin crop reread, anti-overlap, OCR disagreement gate")
