# -*- coding: utf-8 -*-
"""Deterministic FFXIV damaged-chat-header regression (synthetic only).

No user images, real nicknames, original dialogue or private transcript are
included in this file. It tests parser behavior after OCR drops the '<' glyph.
"""
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image
from layout_v2 import _recover_damaged_ffxiv_chat_header, ffxiv

examples = [
    ("[0:03][서초링\"5]8테스터> 첫 번째 짧은 문장", "테스터", "첫 번째 짧은 문장"),
    ("[0:05][서초링 51<=동료> 다음 검사 문장", "동료", "다음 검사 문장"),
    ("[0:05][서초링 515동료> 마지막 검사 문장", "동료", "마지막 검사 문장"),
    ("[0:05][서초링 5]<테스터> 올바른 입력", "테스터", "올바른 입력"),
]
for text, name, message in examples:
    match = _recover_damaged_ffxiv_chat_header(text)
    assert match is not None and match.group(1) == name and match.group(2) == message, text

# Ordinary system messages and non-channel text must not turn into chat.
for text in [
    "[0:05]PvP 지역에 진입했습니다!",
    "[0:03]파티장이 임무에 참가를 신청했습니다.",
    "[0:05][시스템] 출입> 완료",
    "문서 내용> 설명",
    "[0:05] 링크> 이동",
]:
    assert _recover_damaged_ffxiv_chat_header(text) is None, text

lines = [x[0] for x in examples[:3]] + [
    "[0:05]PvP 지역에 진입했습니다!",
    "PvP 대결이 가능한 직업인 경우 전용 단축바로 전환됩니다.",
]
scene = Image.new("RGB", (500, 165), (20, 22, 25))
class NoIcons:
    def match(self, *args):
        return ("", None, 0.)

# Feed known OCR readings at the point immediately before speaker parsing.
# This isolates the classification regression from OCR model variation.
with patch("layout_v2._fixed_lines", return_value=[(i*25+3, i*25+16) for i in range(len(lines))]), \
     patch("layout_v2._variants", side_effect=[(s, [], 3.2) for s in lines]), \
     patch("layout_v2._pvp_color_read", return_value=("", [], 0.0)), \
     patch("pvp_v2.transcribe", return_value=None), \
     patch("tess_backend.read", return_value=("", [], 0.0)):
    kind, output, hits, meta, raw = ffxiv(scene, "한국어", False, "모그리", NoIcons())

parts = output.splitlines()
assert kind == "파판14", kind
assert len(parts) == 4, parts
assert parts[0] == "(직업미확인)테스터: 첫 번째 짧은 문장", parts
assert parts[1] == "(직업미확인)동료: 다음 검사 문장", parts
assert parts[2] == "(직업미확인)동료: 마지막 검사 문장", parts
assert parts[3].startswith("[시스템] [0:05]PvP 지역에 진입했습니다!"), parts
assert "전용 단축바로 전환됩니다." in parts[3], parts
assert len(meta) == 3 and len(hits) == 0
print("FFXIV damaged header parser regression: PASS; chat/system/continuations preserved")
