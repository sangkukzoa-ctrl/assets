# -*- coding: utf-8 -*-
"""Progress regression; generated scenes only, no private screenshots."""
import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from layout_v2 import ffxiv
from batch_v0372 import analyze_batch

img=Image.new("RGB",(400,90),(18,20,24))
progress=[]
with patch("layout_v2._fixed_lines",return_value=[(4,15),(30,41)]), \
     patch("pvp_v2.transcribe",return_value=("(직업미확인)테스터: 안녕",{"speaker":"테스터"},None)):
    mode,text,hits,meta,raw=ffxiv(img,"한국어",True,"모그리",object(),
                               progress=lambda stage,index,total:progress.append((stage,index,total)))
assert mode=="파판14" and text.count("테스터")==2
assert progress==[("line",0,2),("line",1,2),("line",2,2)],progress

events=[]
def stub(image,mode,language,precise,world,icons,progress=None):
    progress("line",0,2)
    progress("line",1,2)
    progress("line",2,2)
    return "파판14","ok",[],[],[],[]
result=analyze_batch([("synthetic.png",img)],("자동","한국어",True,"모그리"),
                     object(),analyzer=stub,progress=lambda *args:events.append(args))
assert len(result)==1 and not result[0]["failed"]
assert events==[("file_start",1,1,0,0),("line",1,1,0,2),
               ("line",1,1,1,2),("line",1,1,2,2),
               ("file_done",1,1,0,0)],events

# Keep the status heartbeat alive while a worker is busy.
source=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
assert 'events.put(("progress",stamp,' in source
assert 'analysis_detail[0]' in source
assert 'elif kind=="ok":' in source
print("FFXIV row progress: PASS; one-job and per-image progress delivered, privacy preserved")
