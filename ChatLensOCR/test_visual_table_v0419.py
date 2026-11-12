# -*- coding: utf-8 -*-
"""Public synthetic table detector and false-structure regression.

No real purchase history, personal screenshots, or OCR ground truth here.
"""
from unittest.mock import patch
from PIL import Image,ImageDraw,ImageFont
from table_v0419 import table_geometry,analyze,_repeated_leading_square

im=Image.new("RGB",(1084,650),"white")
d=ImageDraw.Draw(im)
font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",16)
xs=[35,210,365,555,743,920]
words=["ITEM-100","READY","2026/01/01","CARD","$500","VIEW"]
for y in [100,140,200,260,320,380,440,500,560]:
    d.line((23,y,1040,y),fill=(239,239,239),width=1)
for j,name in enumerate(["Number","State","Date","Pay","Total","Details"]):
    d.text((xs[j],112),name,font=font,fill="black")
for i,y in enumerate(range(140,560,60)):
    if i%2:d.rectangle((24,y+1,1039,y+59),fill=(249,249,249))
    for j,value in enumerate(words):
        if j!=5:d.text((xs[j],y+13),value,font=font,fill=(25,25,25))
    d.rectangle((35,y+37,93,y+56),fill=(36,128,196))
    d.text((42,y+38),"RETRY",font=font,fill="white")
    d.rectangle((905,y+12,918,y+26),outline=(35,35,35),width=2)
    d.line((907,y+16,916,y+16),fill=(35,35,35),width=2)
    d.text((922,y+12),"VIEW",font=font,fill=(25,25,25))

geo=table_geometry(im)
assert geo is not None
assert len(geo["row_lines"])==8,geo
assert len(geo["column_edges"])==7,geo
last_left=max(geo["column_edges"][-2],geo["column_bands"][-1][0]-5)
assert _repeated_leading_square(im,geo["row_lines"],last_left,
                                geo["column_edges"][-1])>last_left

calls=[]
def fake_read(image,mode,language,psm=6):
    if psm==7:return "RETRY",[],99
    calls.append(image.size)
    if len(calls)==1:return "",[],0
    index=len(calls)-2
    items=[{"text":words[index],"score":.99,"box":(7,30+k*120,90,58+k*120)}
           for k in range(7)]
    return "\n".join([words[index]]*7),items,99

with patch("app.recognize",return_value=[
    {"text":"DEMO TABLE","score":.99,"box":(10,10,150,35)}]):
    mode,output,_,meta,boxes=analyze(im,"영어",True,reader=fake_read)
assert mode=="범용"
lines=[line for line in output.splitlines() if "ITEM-100" in line]
assert len(lines)==7,output
assert output.count("RETRY")==7,output
assert all(line.count("\t")==5 for line in lines),output
table_meta=[item for item in meta if item.get("type")=="visual_table_column"]
assert len(table_meta)==6
assert table_meta[-1]["icon_crop"] is True
assert all(not item.get("human_verified",True) for item in table_meta)
assert table_geometry(Image.new("RGB",(1084,650),"white")) is None
assert table_geometry(Image.new("RGB",(1084,650),(16,16,16))) is None
print("v0.4.19 pixel table routing, seven rows / six columns, "
      "repeated-icon exclusion, blue glyph rescue and abstention PASS")
