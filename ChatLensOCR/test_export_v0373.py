# -*- coding: utf-8 -*-
"""Naming helper for ChatLens OCR's user-requested test-result export.

The existing TXT Save action and Test Result Export share the exact same
text payload and UTF-8 encoding; only the suggested filename differs.
"""
from datetime import date

VERSION = "0.4.2"

def default_test_result_filename(on_date=None):
    """Return version-test result-local calendar date.txt.

    The system's local date is intentional: the saved screenshot results
    correspond to the user's current Windows date, not the GitHub build date.
    """
    if on_date is None:
        on_date = date.today()
    return f"ChatLensOCR_v{VERSION}-테스트결과-{on_date:%Y-%m-%d}.txt"

def export_payload(text_widget):
    """Use the same content boundaries as the legacy TXT Save button."""
    return text_widget.get("1.0", "end-1c")
