# -*- coding: utf-8 -*-
"""Generated UI smoke tests: no user screenshots or personal chat data included."""
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).parent))
from layout_v2 import _fixed_lines,_bubble_boxes,detect_mode,analyze

font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",14)
def fill(text,im,x,y,ink):
    ImageDraw.Draw(im).text((x,y),text,font=font,fill=ink)
class NoIcons:
    def match(self,*a,**k):return "",None,0.

ff=Image.new("RGB",(625,230),(14,15,19))
for i,text in enumerate([
    "[1:22][새초링 2]<테스터>안녕하세요 오늘 전장 어때요",
    "[1:22][새초링 2]<친구>오늘은 재미있겠네요",
    "[1:23][새초링 2]<테스터>지금 출발합니다",
    "[1:23][새초링 2]<친구>좋아요"
]):fill(text,ff,1,2+i*20,(245,221,140))
det=detect_mode(ff); lines=_fixed_lines(ff)
assert det=="파판14",(det,lines)
assert len(lines)==4, lines
result=analyze(ff,"자동","한국어",False,"모그리",NoIcons())
print("FFXIV",repr(result[1])[:1500],flush=True)
assert result[0]=="파판14"

ka=Image.new("RGB",(360,320),(187,209,228)); d=ImageDraw.Draw(ka)
d.rectangle((55,32,290,73),fill="white")
d.rectangle((213,110,340,151),fill=(255,220,0))
d.rectangle((55,205,286,246),fill="white")
fill("달팽이",ka,56,9,(20,20,20))
fill("안녕하세요 반갑습니다",ka,65,39,(15,15,15))
fill("네 안녕하세요",ka,225,117,(15,15,15))
fill("달팽이",ka,56,185,(20,20,20))
fill("오늘도 잘 부탁해요",ka,65,212,(15,15,15))
assert detect_mode(ka)=="카카오톡"
bb=_bubble_boxes(ka)
assert len(bb)==3,bb
result=analyze(ka,"자동","한국어",False,"모그리",NoIcons())
print("KAKAO",repr(result[1])[:1500],flush=True)
assert result[0]=="카카오톡" and result[1].count(": ")>=2

gen=Image.new("RGB",(742,300),(255,255,255));d=ImageDraw.Draw(gen)
d.rectangle((0,0,724,130),fill=(244,225,225))
d.rectangle((80,151,741,246),fill=(216,239,249))
fill("AI 서비스 주문 상품의 생각이 있습니다",gen,16,22,(180,55,42))
fill("사진을 촬영하여 보내주시기 바랍니다",gen,16,56,(180,55,42))
fill("운송장 번호가 표시되지 않았습니다",gen,96,174,(45,107,142))
assert detect_mode(gen)=="범용"
result=analyze(gen,"자동","한국어",False,"모그리",NoIcons())
print("GENERAL",repr(result[1])[:1500],flush=True)
assert result[0]=="범용" and result[1].strip()
print("Synthetic UI tests PASSED",flush=True)
