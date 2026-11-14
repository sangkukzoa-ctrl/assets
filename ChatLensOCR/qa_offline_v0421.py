# -*- coding: utf-8 -*-
"""Private/offline real-image audit for the packaged ChatLens OCR executable.

The original images and OCR transcripts NEVER leave the user's computer.
An audit is a genuine run of layout_v2.analyze, not a synthetic CI score.
Outputs: append-only JSONL evidence and numeric-only summary; optional CER
scoring uses a user-supplied private human reference CSV.
"""
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

EXTENSIONS={".png",".jpg",".jpeg",".webp",".bmp",".tif",".tiff"}

def _image_files(folder):
    root=Path(folder).resolve()
    if not root.is_dir():
        raise ValueError("Audit folder is not a directory: "+str(root))
    return sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS),
        key=lambda p:p.relative_to(root).as_posix().casefold()
    )

def _load_evidence(path):
    observed={}
    if not Path(path).exists(): return observed
    with Path(path).open(encoding="utf-8-sig") as stream:
        for num,line in enumerate(stream,1):
            if not line.strip():continue
            try:row=json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError("Corrupt audit JSONL line %s: %s"%(num,error))
            if not isinstance(row,dict) or "filename" not in row:
                raise ValueError("Invalid audit record on line %s"%num)
            observed[row["filename"]]=row
    return observed

def audit_folder(folder,output_jsonl,*,resume=False,analyzer=None,icons=None,
                 mode="자동",language="한국어",precise=True,world="모그리"):
    from PIL import Image
    from ui_input_v042 import normalize_imported_image
    from test_export_v0373 import VERSION
    if analyzer is None:
        from layout_v2 import analyze as analyzer
    if icons is None:
        from app import Icons
        icons=Icons()
    folder=Path(folder).resolve()
    files=_image_files(folder)
    if not files:raise ValueError("No supported screenshot image found")
    out=Path(output_jsonl).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.is_dir():raise ValueError("Audit output must be a JSONL file")
    prior=_load_evidence(out) if resume else {}
    # Do not overwrite previous OCR evidence by default; resume keeps an
    # append-only audit trail and reruns only changed image bytes.
    if out.exists() and not resume:
        raise FileExistsError("Audit file already exists; use --audit-resume: "+str(out))
    if out.exists() and out.stat().st_size and resume:
        old_mode={tuple(r.get("settings",[])) for r in prior.values()}
        current=(mode,language,bool(precise),world,VERSION)
        if old_mode!={current}:
            raise ValueError("Audit settings or OCR version changed; choose a fresh JSONL")
    results=dict(prior)
    processed=0
    with out.open("a" if resume else "x",encoding="utf-8",newline="\n") as stream:
        for source in files:
            relative=source.relative_to(folder).as_posix()
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            if (relative in results
                    and results[relative].get("sha256")==digest
                    and not results[relative].get("failed")):
                continue
            began=time.monotonic()
            item={"filename":relative,"sha256":digest,
                  "settings":[mode,language,bool(precise),world,VERSION],
                  "failed":False}
            try:
                with Image.open(source) as opened:
                    img=normalize_imported_image(opened)
                    item["image_size"]=list(img.size)
                    detected,output,hits,metadata,rows,raw=analyzer(
                        img,mode,language,precise,world,icons)
                item.update({"mode":detected,"result":output,
                             "ocr_lines":raw,"messages":metadata,
                             "icons":hits})
            except Exception as error:
                item.update({"failed":True,"error_type":type(error).__name__,
                             "error":str(error)})
            item["elapsed_seconds"]=round(time.monotonic()-began,3)
            stream.write(json.dumps(item,ensure_ascii=False,default=str)+"\n")
            stream.flush()
            results[relative]=item
            processed+=1
    active={name:results[name] for name in (
        p.relative_to(folder).as_posix() for p in files)}
    from collections import Counter
    summary={"version":VERSION,"image_count":len(files),
             "processed_this_run":processed,
             "completed":sum(not r.get("failed") for r in active.values()),
             "failed":sum(bool(r.get("failed")) for r in active.values()),
             "detected_modes":dict(Counter(r.get("mode","오류") for r in active.values())),
             "output_jsonl":str(out),"private_local_only":True}
    Path(str(out)+".summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    return summary

def _distance(a,b):
    if len(a)>len(b):a,b=b,a
    previous=list(range(len(a)+1))
    for i,bchar in enumerate(b,1):
        current=[i]
        for j,achar in enumerate(a,1):
            current.append(min(current[-1]+1,previous[j]+1,
                               previous[j-1]+(achar!=bchar)))
        previous=current
    return previous[-1]

def score_human_truth(audit_jsonl,reference_csv,output_json):
    """Score literal CER, exact matches and empty-image hallucinations.

    A manually verified *blank* screenshot is a valid negative GT; treating
    its empty reference as missing would hide fabricated OCR strings.
    """
    evidence=_load_evidence(audit_jsonl)
    by_basename={}
    for filename,row in evidence.items():
        by_basename.setdefault(Path(filename).name,[]).append(row)
    exact=0;total_edits=0;total_chars=0;positives=0;blank_total=0;blank_false=0
    missing=[];duplicates=[];rows=[]
    with Path(reference_csv).open(encoding="utf-8-sig",newline="") as f:
        for gt in csv.DictReader(f):
            if gt.get("fully_human_transcribed","").strip()!="예":continue
            name=gt.get("filename","")
            matched=by_basename.get(name,[])
            if len(matched)>1:
                duplicates.append(name);continue
            if not matched or matched[0].get("failed"):
                missing.append(name);continue
            original=(gt.get("human_ground_truth_full") or "").replace("\r\n","\n").strip()
            guessed=(matched[0].get("result") or "").replace("\r\n","\n").strip()
            if original:
                positives+=1
                edits=_distance(original,guessed)
                total_edits+=edits;total_chars+=len(original)
                if edits==0:exact+=1
                rows.append({"filename":name,"reference_chars":len(original),
                             "predicted_chars":len(guessed),
                             "errors":edits,"exact":edits==0})
            else:
                blank_total+=1
                if guessed:blank_false+=1
                rows.append({"filename":name,"reference_chars":0,
                             "predicted_chars":len(guessed),
                             "false_positive":bool(guessed)})
    summary={"labeled_positive_images":positives,
             "labeled_blank_images":blank_total,
             "exact_matches":exact,
             "weighted_literal_cer":round(total_edits/total_chars,6)
                 if total_chars else None,
             "reference_characters":total_chars,
             "character_edits":total_edits,
             "blank_image_false_positives":blank_false,
             "missing_or_failed":missing,
             "duplicate_basename":duplicates,
             "private_local_only":True,
             "per_image":rows}
    Path(output_json).write_text(json.dumps(summary,ensure_ascii=False,indent=2),
                                 encoding="utf-8")
    return summary

def cli(arguments=None):
    args=list(sys.argv[1:] if arguments is None else arguments)
    if len(args)==3 and args[0] in ("--audit-folder","--audit-resume"):
        result=audit_folder(args[1],args[2],resume=args[0]=="--audit-resume")
        return 0 if not result["failed"] else 2
    if len(args)==4 and args[0]=="--audit-score":
        summary=score_human_truth(args[1],args[2],args[3])
        return 0 if not summary["missing_or_failed"] and not summary["duplicate_basename"] else 2
    return 2
