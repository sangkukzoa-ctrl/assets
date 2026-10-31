# -*- coding: utf-8 -*-
"""Offline Tesseract recognizer with pixel-distance-based word spacing.
Each recognized token retains coordinates; whitespace is reconstructed
from the original glyph geometry rather than arbitrary OCR word breaks.
"""
from collections import defaultdict
def _assemble(words):
    if not words:return ""
    words=sorted(words,key=lambda z:z["box"][0])
    # Derive glyph width only from Hangul token bounds.
    widths=[]
    for w in words:
        t=w["text"]
        if t and all("가"<=c<="힣" for c in t):
            widths.append((w["box"][2]-w["box"][0])/len(t))
    widths.sort()
    unit=widths[len(widths)//2] if widths else 15.
    pieces=[]
    prev=None
    for w in words:
        t=w["text"]
        if prev is not None:
            gap=w["box"][0]-prev["box"][2]
            both_hangul=("가"<=prev["text"][-1]<="힣" and "가"<=t[0]<="힣")
            # In Tesseract Korean a single word can fragment into syllables.
            # Join only where the gap is shorter than a visible word space.
            join=(both_hangul and gap<max(2.0,unit*.27)) or (t[0] in ".,!?;:)]}〉＞" and gap<unit*.45)
            if not join:pieces.append(" ")
        pieces.append(t)
        prev=w
    return "".join(pieces)

def read(image,mode,language,psm=None):
    try:
        import os
        import pytesseract
        from pytesseract import Output
        from app import BASE
        exe=BASE/"tesseract"/"tesseract.exe"
        data=BASE/"tesseract"/"tessdata"
        if not exe.is_file() or not data.is_dir():return "",[],0.
        pytesseract.pytesseract.tesseract_cmd=str(exe)
        os.environ["TESSDATA_PREFIX"]=str(data)
        lang="kor+eng" if language=="한국어" else "jpn+eng" if language=="일본어" else "eng"
        if psm is None:
            psm=6 if mode=="파판14" else 7 if image.height<52 else 6
        d=pytesseract.image_to_data(image,lang=lang,config=f"--psm {psm}",output_type=Output.DICT,timeout=20)
        groups=defaultdict(list)
        parts=[];confs=[]
        for i,t in enumerate(d["text"]):
            t=t.strip()
            if not t:continue
            confidence=float(d["conf"][i])
            if confidence<=0:continue
            key=(d["block_num"][i],d["par_num"][i],d["line_num"][i])
            x,y,w,h=(int(d[z][i]) for z in ("left","top","width","height"))
            item={"text":t,"score":confidence/100,"box":(x,y,x+w,y+h)}
            groups[key].append(item)
            parts.append(item)
            confs.append(confidence)
        lines=sorted(groups.values(),key=lambda a:min(t["box"][1] for t in a))
        return " ".join(_assemble(row) for row in lines),parts,sum(confs)/max(1,len(confs))
    except Exception:return "",[],0.
