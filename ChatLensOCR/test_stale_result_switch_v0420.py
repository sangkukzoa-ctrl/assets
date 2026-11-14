# -*- coding: utf-8 -*-
"""Public-safe regression for switching between OCR input images.

An old single-image result must not leak into a new image's TXT/JSON while
batch results remain available for images in the same batch.
"""
from pathlib import Path
from review_v046 import result_belongs_to_image

first=[{"filename":"sample.png","result":"first"}]
assert result_belongs_to_image(first,"sample.png")
assert not result_belongs_to_image(first,"other.png")
assert not result_belongs_to_image(first,"sample.png2")
assert not result_belongs_to_image(first,"")
assert not result_belongs_to_image([], "sample.png")
assert not result_belongs_to_image(None,"sample.png")
batch=[
    {"filename":"sample.png","result":"first"},
    {"filename":"other.png","result":"second"}
]
assert result_belongs_to_image(batch,"sample.png")
assert result_belongs_to_image(batch,"other.png")
selected=[{"filename":"sample.png [선택 영역]","result":"crop"}]
assert result_belongs_to_image(selected,"sample.png")
assert not result_belongs_to_image(selected,"other.png")
assert result_belongs_to_image(selected,"sample.png [선택 영역]")

source=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
handler=source.split("    def change(event=None):",1)[1].split(
    '    lb.bind("<<ListboxSelect>>",change)',1)[0]
assert "result_belongs_to_image(last[0],filename)" in handler
assert "last[0]=None" in handler
assert 'widget.delete("1.0","end")' in handler
assert "show()" in handler
print("v0.4.20 exact filename / selected ROI / batch result preservation "
      "and stale OCR output guard PASS")
