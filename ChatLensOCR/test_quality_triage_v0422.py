# -*- coding: utf-8 -*-
"""v0.4.22 synthetic-only quality triage; no real user's screenshots/GT."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from qa_offline_v0421 import _breakdown_by,score_human_truth,cli

items=[
    {"filename":"a.png","detected_mode":"범용",
     "recorded_screen_type":"문서","reference_chars":100,
     "predicted_chars":120,"errors":20,"exact":False,
     "needs_review":True,"review_reason":"literal_mismatch"},
    {"filename":"b.png","detected_mode":"범용",
     "recorded_screen_type":"자막","reference_chars":10,
     "predicted_chars":0,"errors":10,"exact":False,
     "needs_review":True,"review_reason":"empty_ocr"},
    {"filename":"c.png","detected_mode":"쇼핑몰",
     "recorded_screen_type":"아이콘격자","reference_chars":0,
     "predicted_chars":4,"false_positive":True,
     "needs_review":True,"review_reason":"hallucinated_text"},
]
g=_breakdown_by(items,"detected_mode")
assert g["범용"]["labeled_images"]==2
assert g["범용"]["reference_chars"]==110
assert g["범용"]["character_edits"]==30
assert g["범용"]["weighted_literal_cer"]==round(30/110,6)
assert g["쇼핑몰"]["labeled_images"]==1
assert g["쇼핑몰"]["blank_false_positives"]==1
assert g["쇼핑몰"]["weighted_literal_cer"] is None
assert _breakdown_by(items,"recorded_screen_type")["문서"]["weighted_literal_cer"]==.2

with TemporaryDirectory(prefix="chatlens_quality_") as tmp:
    d=Path(tmp)
    jsonl=d/"audit.jsonl"
    evidence=[
        {"filename":"a.png","mode":"범용","result":"abcdef",
         "failed":False},
        {"filename":"b.png","mode":"쇼핑몰","result":"",
         "failed":False},
    ]
    jsonl.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n"
                             for x in evidence),encoding="utf-8")
    gt=d/"gt.csv"
    header=["filename","fully_human_transcribed","human_ground_truth_full",
            "actual_screen_type_previous_classification",
            "v0419_corrected_screen_type"]
    with gt.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=header)
        writer.writeheader()
        writer.writerows([
            dict(zip(header,["a.png","예","abcdefghij","범용/기타","문서 정확"])),
            dict(zip(header,["b.png","예","","카카오톡","무문자 그림"])),
        ])
    report=score_human_truth(jsonl,gt,d/"score.json")
    assert report["labeled_positive_images"]==1
    assert report["labeled_blank_images"]==1
    assert report["character_edits"]==4
    assert report["weighted_literal_cer"]==.4
    assert report["by_detected_mode"]["범용"]["weighted_literal_cer"]==.4
    assert report["by_recorded_screen_type"]["문서 정확"]["text_images"]==1
    assert report["by_recorded_screen_type"]["무문자 그림"]["blank_images"]==1
    assert report["review_queue"][0]["filename"]=="a.png"
    assert not report["duplicate_gt_entries"]
    # Duplicate *GT rows* cannot double-count success or silently lower CER.
    with gt.open("a",encoding="utf-8") as f:
        csv.writer(f).writerow(["a.png","예","abcdefghij","범용/기타","문서 정확"])
    repeated=score_human_truth(jsonl,gt,d/"with_duplicate.json")
    assert repeated["duplicate_gt_entries"]==["a.png"]
    assert repeated["labeled_positive_images"]==1
    assert cli(["--audit-score",str(jsonl),str(gt),str(d/"cli.json")])==2

print("v0.4.22 quality triage PASS: weighted CER, false-positive blank,"
      " mode/type breakdown, worst-error review and duplicate GT refusal")
