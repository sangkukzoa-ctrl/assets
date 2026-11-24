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



def _single_pass_text_and_tsv(image, executable, tessdata, lang, psm):
    """Run Tesseract once with identical PSM for native text and TSV geometry.

    ImageToData + ImageToString used to launch two separate OCR processes for
    every candidate row. Native Tesseract supports combined 'txt tsv' outputs.
    Output is local and transient; no chat or image data is sent to a server.
    """
    import os
    import subprocess
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix="chatlens_ocr_") as work:
        source=Path(work)/"input.png"
        target=Path(work)/"result"
        image.save(source,format="PNG")
        env=os.environ.copy()
        env["TESSDATA_PREFIX"]=str(tessdata)
        flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
        run=subprocess.run(
            [str(executable),str(source),str(target),"-l",lang,
             "--psm",str(psm),"txt","tsv"],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=20,env=env,creationflags=flags,
            check=False)
        if run.returncode!=0:
            raise RuntimeError("Bundled Tesseract failed (%d): %s" %
                               (run.returncode,run.stderr.decode("utf-8","replace")[:240]))
        def read_sidecar(suffix):
            try:
                return Path(str(target)+suffix).read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                return None
        native=read_sidecar(".txt")
        tsv=read_sidecar(".tsv")
        if native is None and tsv is None:
            raise RuntimeError("Tesseract produced no readable output")
        return (native or "").strip(),tsv or ""


def read(image,mode,language,psm=None,tess_lang=None):
    """Return native text and per-word boxes from ONE Tesseract invocation."""
    try:
        import math
        from collections import defaultdict
        exe,data=resolve_tesseract_paths()
        if not exe or not data:return "",[],0.
        lang=tess_lang or ("kor+eng" if language=="한국어" else "jpn+eng" if language=="일본어" else "eng")
        if psm is None:
            psm=6 if mode=="파판14" else 7 if image.height<52 else 6
        native,tsv=_single_pass_text_and_tsv(image,exe,data,lang,psm)
        groups=defaultdict(list)
        parts=[];confs=[]
        # Native TSV is not CSV: quotes are literal OCR glyphs. Split only
        # the 11 structural separators, preserving the final text field.
        # A malformed geometry row must not discard other valid rows or
        # the independently produced native text.
        lines=tsv.replace("\r\n","\n").split("\n")
        expected="level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
        if not lines or lines[0].lstrip("\ufeff")!=expected:
            return native,[],0.
        for line in lines[1:]:
            fields=line.split("\t",11)
            if len(fields)!=12:continue
            t=fields[11].strip()
            if not t:continue
            try:
                if int(fields[0])!=5:continue
                raw_conf=float(fields[10])
                if not math.isfinite(raw_conf) or not 0<raw_conf<=100:continue
                confidence=float(int(raw_conf))
                if confidence<=0:continue
                key=tuple(int(fields[k]) for k in (1,2,3,4))
                x,y,w,h=(int(fields[k]) for k in (6,7,8,9))
                if x<0 or y<0 or w<=0 or h<=0:continue
            except (ValueError,OverflowError):
                continue
            item={"text":t,"score":confidence/100,"box":(x,y,x+w,y+h)}
            groups[key].append(item)
            parts.append(item)
            confs.append(confidence)
        # Tesseract's hierarchy encodes reading order. Global y sorting
        # interleaves separate columns and can reverse adjacent lines.
        # Native text remains authoritative; raw token order is unchanged.
        lines=[groups[key] for key in sorted(groups)]
        reconstructed="\n".join(_assemble(row) for row in lines)
        return native if native else reconstructed,parts,sum(confs)/max(1,len(confs))
    except Exception:
        return "",[],0.
