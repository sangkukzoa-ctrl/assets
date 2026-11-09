# -*- coding: utf-8 -*-
"""v0.4.11 public-safe pixel-layout regressions.

Use generated pixels only. The private 166-image validation set must NOT
be included in GitHub source, Actions artifacts, or public release.
"""
from PIL import Image, ImageDraw, ImageFont
from layout_v2 import detect_mode
from ffxiv_scoreboard_v037 import is_scoreboard, _synthetic as scoreboard_synthetic

font_path = "C:/Windows/Fonts/malgun.ttf"
font = ImageFont.truetype(font_path, 14)

# The prior scoreboard hue threshold misinterpreted pink/cyan customer
# support messages as an FFXIV results table.
pink = Image.new("RGB", (938, 659), (242, 222, 222))
draw = ImageDraw.Draw(pink)
for i in range(11):
    draw.text((55, 237+i*32), "배송 진행 문의와 답변", font=font, fill=(130, 45, 56))
assert not is_scoreboard(pink), "Pink text page became an FFXIV scoreboard"
assert detect_mode(pink) == "범용"
assert scoreboard_synthetic(), "Genuine beige FFXIV scoreboards must remain recognized"

# Neutral inspector pane: many pale glyphs on charcoal, no game chat.
editor = Image.new("RGB", (334, 1100), (39, 40, 42))
draw = ImageDraw.Draw(editor)
for i in range(43):
    draw.text((5, i*24+4), "Game Object    Variable Name", font=font, fill=(173, 177, 182))
assert detect_mode(editor) == "범용", "Dark Unity-style inspector misclassified"

# A neon green ASCII screen contains rules instead of chat message rows.
neon = Image.new("RGB", (337, 196), (12, 13, 16))
draw = ImageDraw.Draw(neon)
for y in (20, 51, 90, 132):
    draw.line((5, y, 331, y), fill=(120, 219, 82), width=2)
draw.text((10, 65), "Do you want Wipe?", font=font, fill=(123, 221, 96))
assert detect_mode(neon) == "범용", "ASCII panel misclassified"

# Real chat retains the earlier synthetic text layout and single-line support.
chat = Image.new("RGB", (625, 230), (14, 15, 19))
draw = ImageDraw.Draw(chat)
for i in range(4):
    draw.text((1, 2+i*20), "[1:22][Party]<Tester> hello FFXIV", font=font, fill=(245, 221, 140))
assert detect_mode(chat) == "파판14", "Top-aligned FFXIV chat lost"
short = Image.new("RGB", (360, 110), (10, 12, 15))
ImageDraw.Draw(short).text((1, 4), "[1:22][Party]<Tester>Hello", font=font, fill=(245, 225, 135))
assert detect_mode(short) == "파판14", "One-line chat lost"

# High aspect-ratio dark game item descriptions belong to generic text
# extraction, not the FFXIV speaker parser.
item = Image.new("RGB", (289, 610), (17, 19, 23))
d = ImageDraw.Draw(item)
for i in range(20):
    color = (70, 205, 179) if i % 3 else (250, 190, 90)
    d.text((9, 20+i*25), "Option: +125%%", font=font, fill=color)
assert detect_mode(item) == "범용"
print("v0.4.11 synthetic screen classification: pastel support / HUD / "
      "dark editor / neon panel / FFXIV chat / long item PASS")
