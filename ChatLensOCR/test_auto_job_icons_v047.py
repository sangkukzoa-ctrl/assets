# -*- coding: utf-8 -*-
"""Offline FFXIV job icon auto-learning regression, no private screenshots."""
import tempfile
from pathlib import Path
from PIL import Image,ImageDraw
from auto_job_samples_v047 import learn_verified_icon,MIN_SCORE,MIN_MARGIN,MAX_PER_JOB

with tempfile.TemporaryDirectory() as dirname:
    root=Path(dirname)
    im=Image.new("RGB",(72,72),(21,21,24))
    d=ImageDraw.Draw(im)
    d.ellipse((14,14,46,46),outline=(249,231,204),width=4)
    d.line((16,19,42,44),fill=(236,228,216),width=4)
    d.line((42,19,16,44),fill=(236,228,216),width=4)
    rect=(12,12,48,48)
    allowed={"현자","나이트"}
    assert learn_verified_icon(im,rect,"현자",.72,.31,root,allowed) is None
    assert learn_verified_icon(im,rect,"현자",.97,.08,root,allowed) is None
    assert learn_verified_icon(im,rect,"알수없는직업",.98,.35,root,allowed) is None
    assert learn_verified_icon(im,(12,12,52,25),"현자",.99,.31,root,allowed) is None
    learned=learn_verified_icon(im,rect,"현자",.98,.26,root,allowed)
    assert learned and learned.exists(),learned
    assert "auto" in learned.parts and learned.name.startswith("현자__")
    assert Image.open(learned).size==(32,32)
    # Same icon with the same pixels is not silently multiplied.
    assert learn_verified_icon(im,rect,"현자",.98,.26,root,allowed) is None
    assert len(list((root/"job_samples"/"auto").glob("*.png")))==1

    # A fully flat rectangle is not a useful training sample.
    blank=Image.new("RGB",(60,60),"white")
    assert learn_verified_icon(blank,(10,10,43,43),"현자",.99,.22,root,allowed) is None

source=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
assert 'self.official_templates=set()' in source
assert 'DATA/"job_samples"/"auto"' in source
assert 'if self.allow_learning and is_official and score>=.90 and score-runner>=.12:' in source
assert 'self.allow_learning=allow_learning' in source
assert 'icons=Icons(allow_learning=False)' in (
    Path(__file__).resolve().parent/"qa_offline_v0421.py"
).read_text(encoding="utf-8")
assert 'learn_verified_icon(image,rect,job,score,score-runner,DATA' in source
assert 'button(icon_tools,"직업 아이콘 직접 등록 (선택)"' in source

# The original KakaoTalk sticker detector, source-matched descriptions,
# and manual description editor remain available.
assert 'def teach_sticker():' in source
from kakao_stickers import _synthetic as sticker_test
assert sticker_test()
print("Auto FFXIV icons PASS: trusted reference only, on-device cache, quality gate, Unicode sample names, stickers retained")
