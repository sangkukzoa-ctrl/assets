# -*- coding: utf-8 -*-
"""Synthetic-only regression: OCR worker result is stale after image switching.

The currently selected image object is authoritative, not a filename prefix,
identical pixels, or the selection that existed when the worker started.
"""
from pathlib import Path
from review_v046 import completed_result_matches_active

A=object()
B=object()
C=object()
entries=[("first.png",A),("second.png",B)]
single=[{"filename":"first.png","result":"OLD"}]
assert completed_result_matches_active(single,entries,A)
assert not completed_result_matches_active(single,entries,B)
assert not completed_result_matches_active(single,entries,C)
assert not completed_result_matches_active(single,[],A)
assert not completed_result_matches_active(None,entries,A)
assert not completed_result_matches_active(single,entries,None)

# A completed batch can be shown for every member without losing text.
batch=[{"filename":"first.png","result":"ONE"},
       {"filename":"second.png","result":"TWO"}]
assert completed_result_matches_active(batch,entries,A)
assert completed_result_matches_active(batch,entries,B)

# Cropped images remain owned by the source image, without prefix mistakes.
selected=[{"filename":"first.png [선택 영역]","result":"ROI"}]
assert completed_result_matches_active(selected,entries,A)
assert not completed_result_matches_active(selected,entries,B)
assert not completed_result_matches_active(
    [{"filename":"first.png2","result":"DIFFERENT"}],entries,A)

# Even if identical pixels are loaded twice, object identity prevents
# a result from being attributed to the wrong file.
same_pixels_different_object=object()
assert not completed_result_matches_active(
    single,[("first.png",same_pixels_different_object)],A)

app=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
poll=app.split("    def poll():",1)[1].split("\n    root.after(120,poll)\n",1)[0]
assert "completed_result_matches_active(info,entries,active[0])" in poll
assert "last[0]=None" in poll
assert "field.delete(\"1.0\",\"end\")" in poll
assert "root.after(120,poll)" in app
assert "last[0]=info" in app
print("v0.4.23 background OCR completion / active screenshot identity / "
      "same-pixel different file / ROI / batch preservation PASS")
