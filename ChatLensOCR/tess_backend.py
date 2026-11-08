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

def resolve_tesseract_paths(base=None):
    """Locate the bundled OCR executable first; use an installed copy only
    in source/development mode. Does not download or run third-party code.
    """
    import os,sys,shutil
    from pathlib import Path
    if base is None:
        from app import BASE
        base=BASE
    embedded=Path(base)/"tesseract"/"tesseract.exe"
    installed=[]
    if not getattr(sys,"frozen",False):
        for env_var in ("ProgramFiles","ProgramW6432"):
            folder=os.environ.get(env_var)
            if folder:installed.append(Path(folder)/"Tesseract-OCR"/"tesseract.exe")
        found=shutil.which("tesseract")
        if found:installed.append(Path(found))
    for exe in [embedded]+installed:
        if not exe.is_file():continue
        datas=[exe.parent/"tessdata"]
        prefix=os.environ.get("TESSDATA_PREFIX","")
        if prefix:datas.append(Path(prefix))
        # Linux local QA can use the system language packs as well.
        if not getattr(sys,"frozen",False) and os.name!="nt":
            datas.extend(Path("/usr/share/tesseract-ocr").glob("*/tessdata"))
        for data in datas:
            if data.is_dir() and (data/"eng.traineddata").is_file():
                return str(exe),str(data)
    return None,None


def read(image,mode,language,psm=None,tess_lang=None):
    try:
        import os
        import pytesseract
        from pytesseract import Output
        exe,data=resolve_tesseract_paths()
        if not exe or not data:return "",[],0.
        pytesseract.pytesseract.tesseract_cmd=exe
        os.environ["TESSDATA_PREFIX"]=data
        lang=tess_lang or ("kor+eng" if language=="한국어" else "jpn+eng" if language=="일본어" else "eng")
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
        # Tesseract's text renderer has already reconstructed Korean word
        # boundaries at OCR time. Reassembling TSV tokens by box distance
        # repeatedly introduced arbitrary syllable spaces (e.g. 꼬이 는군).
        # Use native text as canonical transcription. Keep TSV for geometry.
        native=pytesseract.image_to_string(
            image,lang=lang,config=f"--psm {psm}",timeout=20).strip()
        reconstructed="\n".join(_assemble(row) for row in lines)
        transcript=native if native else reconstructed
        return transcript,parts,sum(confs)/max(1,len(confs))
    except Exception:return "",[],0.
