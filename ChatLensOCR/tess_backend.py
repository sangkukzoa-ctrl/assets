# -*- coding: utf-8 -*-
"""Bundled offline Tesseract OCR, independent of a system installation."""
import os
from pathlib import Path

def read(image, mode, language):
    try:
        import pytesseract
        from pytesseract import Output
        from app import BASE
        exe=BASE/"tesseract"/"tesseract.exe"
        data=BASE/"tesseract"/"tessdata"
        if not exe.is_file() or not data.is_dir():
            return "", [], 0.
        pytesseract.pytesseract.tesseract_cmd=str(exe)
        os.environ["TESSDATA_PREFIX"]=str(data)
        lang="kor+eng" if language=="한국어" else "jpn+eng" if language=="일본어" else "eng"
        psm=7 if mode in ("파판14","범용") or image.height<85 else 6
        d=pytesseract.image_to_data(image,lang=lang,config=f"--psm {psm}",output_type=Output.DICT,timeout=20)
        groups={}; parts=[];confs=[]
        for i,txt in enumerate(d["text"]):
            if not txt.strip():continue
            confidence=max(0.,float(d["conf"][i]))
            if confidence<=0:continue
            key=(d["block_num"][i],d["par_num"][i],d["line_num"][i])
            groups.setdefault(key,[]).append(txt.strip())
            x,y,w,h=(int(d[z][i]) for z in ("left","top","width","height"))
            parts.append({"text":txt.strip(),"score":confidence/100,"box":(x,y,x+w,y+h)})
            confs.append(confidence)
        return " ".join(" ".join(v) for v in groups.values()),parts,sum(confs)/max(1,len(confs))
    except Exception:
        return "",[],0.
