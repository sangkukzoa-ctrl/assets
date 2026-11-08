# -*- coding: utf-8 -*-
"""Loss-minimizing text representation for locally recognized speech.
No dictionary substitutions: do not turn one Hangul syllable into another.
"""
import re

def normalize_visible_punctuation(text):
    """Write OCR's Unicode ellipsis as ASCII triple-dot in exported transcripts.

    OCR may return '.…?' for three visible dot glyphs, whereas the chat
    screenshot contains three dot positions. A preceding single/double dot
    plus ellipsis is not intended to become four or five periods.
    """
    if not text:
        return text
    return re.sub(r"\\.{1,3}…", "...", text).replace("…", "...")

def one_syllable_agreement(readings, min_confidence=72):
    """Accept a 1-Hangul-character bubble only when two independent passes agree.

    readings: (text, boxes, confidence_0_to_100, zoom).
    The source screenshot is the only authority; disagreement returns None.
    """
    from collections import defaultdict
    candidates=defaultdict(list)
    for text,boxes,confidence,zoom in readings:
        cleaned=(text or "").strip()
        if re.fullmatch(r"[가-힣]",cleaned) and confidence>=min_confidence:
            candidates[cleaned].append((cleaned,boxes,confidence,zoom))
    for syllable,items in candidates.items():
        # At least two observations, with a consensus among all usable glyphs.
        if len(items)>=2 and len(items)>sum(len(v) for k,v in candidates.items() if k!=syllable):
            return max(items,key=lambda x:x[2])[0:]
    return None
