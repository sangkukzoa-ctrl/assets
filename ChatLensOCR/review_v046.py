# -*- coding: utf-8 -*-
"""Review and lossless TXT/JSON export helpers for ChatLens OCR.

The original recognized text is never silently rewritten. A user may edit
the visible TXT transcript before export; the JSON preserves the raw OCR
records and, when edited, stores the full user-corrected TXT separately.
"""
import json

UNREADABLE_MARKER = "[글자 미인식]"


def result_belongs_to_image(records, filename):
    """An OCR result from A must not be displayed as if it belongs to B.

    A manually selected crop keeps the original filename with the explicit
    selection suffix. Exact equality prevents prefix collisions between files.
    Batch OCR remains valid while any item from that batch is selected.
    """
    if not records or not filename:
        return False
    return any(
        isinstance(item,dict) and
        item.get("filename") in (filename, filename+" [선택 영역]")
        for item in records
    )

def format_batch_txt(records):
    return "\n\n".join(
        "--- " + str(row["filename"]) + " [" + str(row["mode"]) + "] ---\n"
        + str(row["result"])
        for row in records
    )

def review_positions(text):
    if not text:
        return []
    positions = []
    cursor = 0
    while True:
        pos = text.find(UNREADABLE_MARKER, cursor)
        if pos < 0:
            break
        positions.append((pos, pos + len(UNREADABLE_MARKER)))
        cursor = pos + len(UNREADABLE_MARKER)
    return positions

def next_review_position(text, cursor=0):
    positions = review_positions(text)
    if not positions:
        return None
    for start, end in positions:
        if start > cursor:
            return (start, end)
    return positions[0]

def make_json_export(records, visible_txt):
    """Retain the original list schema and original OCR evidence.

    The full edited TXT goes in a separate field on the first result only,
    allowing existing JSON consumers to continue reading the same list.
    """
    result = [dict(item) for item in records]
    if result and visible_txt != format_batch_txt(records):
        result[0]["user_edited_full_txt"] = visible_txt
        result[0]["user_edited_note"] = (
            "The user corrected the displayed TXT after OCR. "
            "Raw OCR fields remain unchanged."
        )
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)
