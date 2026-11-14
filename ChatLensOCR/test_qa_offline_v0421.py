# -*- coding: utf-8 -*-
"""Synthetic-only private-folder audit/continuation and CER regression."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from qa_offline_v0421 import audit_folder,score_human_truth,_load_evidence
from test_export_v0373 import VERSION

with TemporaryDirectory(prefix="chatlens_qa_") as tmp:
    root=Path(tmp);folder=root/"images";folder.mkdir()
    Image.new("RGB",(400,100),"white").save(folder/"demo_a.png")
    Image.new("RGB",(500,100),"black").save(folder/"demo_b.png")
    output=root/"private.jsonl"
    calls=[]
    class Icons:pass
    def analyzer(img,mode,language,precise,world,icons):
        assert (mode,language,precise,world)==("자동","한국어",True,"모그리")
        calls.append(img.size)
        result="정확한 글자" if img.width==400 else ""
        return "범용",result,[],[],[],[]
    first=audit_folder(folder,output,icons=Icons(),analyzer=analyzer)
    assert (first["image_count"],first["completed"],first["failed"])==(2,2,0)
    assert first["processed_this_run"]==2
    assert first["version"]==VERSION
    assert len(_load_evidence(output))==2
    assert Path(str(output)+".summary.json").exists()
    assert all(len(r["sha256"])==64 for r in _load_evidence(output).values())

    second=audit_folder(folder,output,resume=True,icons=Icons(),analyzer=analyzer)
    assert second["processed_this_run"]==0 and len(calls)==2
    try:
        audit_folder(folder,output,icons=Icons(),analyzer=analyzer)
    except FileExistsError:pass
    else:raise AssertionError("Audit must never overwrite previous local output")

    truth=root/"human.csv"
    with truth.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=[
            "filename","fully_human_transcribed","human_ground_truth_full"])
        writer.writeheader()
        writer.writerow({"filename":"demo_a.png","fully_human_transcribed":"예",
                         "human_ground_truth_full":"정확한 글자"})
        writer.writerow({"filename":"demo_b.png","fully_human_transcribed":"예",
                         "human_ground_truth_full":""})
    score=score_human_truth(output,truth,root/"score.json")
    assert score["labeled_positive_images"]==1
    assert score["labeled_blank_images"]==1
    assert score["exact_matches"]==1 and score["weighted_literal_cer"]==0.
    assert score["blank_image_false_positives"]==0

    # Blank GT is NOT an absent label: hallucinated text must be counted.
    extra=_load_evidence(output)["demo_b.png"]
    extra["result"]="invented"
    with output.open("a",encoding="utf-8") as f:
        f.write(json.dumps(extra,ensure_ascii=False)+"\n")
    hallucinated=score_human_truth(output,truth,root/"score_2.json")
    assert hallucinated["blank_image_false_positives"]==1

    # When the image has changed, resume must reread rather than silently
    # attributing stale pixels to the same filename.
    Image.new("RGB",(400,100),(220,200,190)).save(folder/"demo_a.png")
    third=audit_folder(folder,output,resume=True,icons=Icons(),analyzer=analyzer)
    assert third["processed_this_run"]==1 and len(calls)==3

source=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
assert 'sys.argv[1] in (' in source and '"--audit-score"' in source
assert "qa_offline_v0421 import cli" in source
print("v0.4.21 offline image audit, resume, blank human GT hallucination,"
      " exact literal CER and packaged entrypoint PASS")
