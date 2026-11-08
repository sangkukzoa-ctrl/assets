# -*- coding: utf-8 -*-
"""Conservative, image-only reread of ambiguous short-height Korean chat lines.

Keep the base OCR text unless two separately preprocessed crops support the
same single-Hangul substitution near the end of a long line.
"""
import re
from PIL import Image, ImageOps
import cv2
import numpy as np

def _one_safe_tail_edit(original, alternative):
    if not original or not alternative or original == alternative:
        return False
    if "\n" in original or "\n" in alternative:
        return False
    if len(original) < 12 or len(original) != len(alternative):
        return False
    if len(re.findall(r"[가-힣]", original)) < 9:
        return False
    changed = [i for i, (a, b) in enumerate(zip(original, alternative)) if a != b]
    if len(changed) != 1:
        return False
    i = changed[0]
    # Keep final syllables unchanged: edge/crop artifacts at word endings
    # produced a false positive elsewhere in the full 57-bubble audit.
    if i < len(original) - max(3, len(original) // 5) or i >= len(original) - 1:
        return False
    a, b = original[i], alternative[i]
    return "가" <= a <= "힣" and "가" <= b <= "힣"

def rescue_korean_tail(crop, original, reader=None):
    """Return (transcript, improved); preserve the input on disagreement."""
    if not original or "\n" in original or crop is None:
        return original, False
    if crop.height > 35 or crop.width < 130 or crop.width > 580:
        return original, False
    if len(original) < 12 or len(re.findall(r"[가-힣]", original)) < 9:
        return original, False
    if reader is None:
        from tess_backend import read
        reader = read
    gray = np.asarray(crop.convert("L"))
    variants = (gray, cv2.fastNlMeansDenoising(gray, None, h=5))
    outcomes = []
    for variant in variants:
        image = Image.fromarray(variant).resize(
            (crop.width * 4, crop.height * 4), Image.Resampling.LANCZOS
        )
        image = ImageOps.expand(image, border=16, fill=255)
        text, boxes, confidence = reader(
            image, "카카오톡", "한국어", psm=7, tess_lang="kor"
        )
        text = (text or "").strip()
        if confidence < 65 or not _one_safe_tail_edit(original, text):
            return original, False
        outcomes.append(text)
    if outcomes[0] != outcomes[1]:
        return original, False
    return outcomes[0], True
