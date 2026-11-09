# -*- coding: utf-8 -*-
"""Synthetic Frontline 8/9-column HUD and embedded screenshot regression.

Real screenshot pixels, usernames, chat logs and captions must NEVER be
committed to the public repository or uploaded as Actions artifacts.
"""
from PIL import Image,ImageDraw,ImageFont
from unittest.mock import patch
from pathlib import Path
from ffxiv_scoreboard_grid_v0412 import (
    header_geometry,embedded_scoreboard_box,_synthetic as geometry_synthetic
)
from ffxiv_scoreboard_v037 import row_bands,is_scoreboard
from layout_v2 import analyze

font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",14)
class Icons:
    def match(self,*args,**kwargs):return "",None,0

assert geometry_synthetic()
def scene(nine):
    # Approximate the real HUD's variable location inside an outdoor
    # background, without copying any user's image.
    im=Image.new("RGB",(979,992),(42,63,49))
    d=ImageDraw.Draw(im)
    d.rectangle((0,118,944,744),fill=(231,223,214))
    starts=([230,355,394,433,471,613,754,840,936] if nine
            else [234,359,398,437,475,627,778,940])
    for x in starts:
        d.line((x,300,x,330),fill=(36,30,27),width=2)
    for row in range(11):
        y=344+32*row
        d.text((65,y),"A테스터",font=font,fill=(77,58,34))
        d.text((277,y),"모그리",font=font,fill=(46,46,46))
        d.text((515,y),str(1585809+row),font=font,fill=(33,33,33))
    return im

for nine in (False,True):
    image=scene(nine)
    box=embedded_scoreboard_box(image)
    assert box is not None,(nine,"missing embedded HUD")
    crop=image.crop(box)
    assert is_scoreboard(crop)
    assert len(row_bands(crop))==11,(nine,row_bands(crop))
    inferred=header_geometry(crop)
    assert inferred is not None and len(inferred[0])==(9 if nine else 8),inferred
    assert inferred[0][-1]==("거점 점령 횟수" if nine else "총 회복량")
    with patch("ffxiv_scoreboard_v037._read_cell",return_value=("7",[],90)):
        d,result,hits,meta,rows,raw=analyze(
            image,"자동","한국어",False,"모그리",Icons())
    assert d=="파판14",(nine,d)
    header=result.splitlines()[1].split("\t")
    assert len(header)==(9 if nine else 8),header
    assert len([m for m in meta if m.get("type")=="scoreboard_row"])==11
    assert any(m.get("type")=="embedded_scoreboard" for m in meta)

# A warm UI card without aligned stat rows must not be treated as a game HUD.
not_hud=Image.new("RGB",(979,992),(242,222,222))
assert embedded_scoreboard_box(not_hud) is None
print("v0.4.12 embedded HUD region, dynamic 8/9-column grids, row "
      "recovery, OCR routing and synthetic false-positive checks PASS")
