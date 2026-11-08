# -*- coding: utf-8 -*-
"""Image import correctness for the standalone desktop interface.

This module is deliberately independent from Tkinter so that every image
import can be tested without launching a GUI.
"""
from pathlib import Path
from PIL import ImageOps

def normalize_imported_image(image):
    """Respect camera/phone EXIF orientation before removing metadata."""
    if image is None:
        raise ValueError("Image is missing")
    if image.width <= 0 or image.height <= 0:
        raise ValueError("Image has no visible pixels")
    return ImageOps.exif_transpose(image).convert("RGB")

def unique_image_name(name, existing_entries):
    """Avoid silently merging separate clipboard/file images with equal names."""
    candidate=str(name or "이미지")
    existing={str(item[0]) for item in existing_entries}
    if candidate not in existing:
        return candidate
    stem,suffix=Path(candidate).stem,Path(candidate).suffix
    counter=2
    while f"{stem} ({counter}){suffix}" in existing:
        counter+=1
    return f"{stem} ({counter}){suffix}"
