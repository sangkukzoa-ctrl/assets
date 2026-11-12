# -*- coding: utf-8 -*-
"""Geometry-only OCR abstention for repetitive UI graphics.

A chest or inventory is visually regular: many image-only item slots have
long dark boundaries at constant x/y increments. OCR of those icons can emit
confident invented Korean/Latin words; agreement between two Tesseract passes
is *not* independent visual ground truth. This detector never reads text or
infers its meaning, and is used ONLY to disable empty-caption restoration.
"""
import numpy as np

def is_repeated_icon_grid(image):
    w,h=image.size
    if w<300 or h<260:return False
    mono=np.asarray(image.convert("L"),dtype=np.uint8)
    dark=mono<100
    vertical=dark.mean(axis=0)>.54
    horizontal=dark.mean(axis=1)>.39

    def short_strokes(signal):
        pixels=np.flatnonzero(signal)
        if not len(pixels):return []
        strokes=[];start=last=int(pixels[0])
        for pixel in pixels[1:]:
            pixel=int(pixel)
            if pixel-last>1:
                if last-start<=7:strokes.append((start+last)//2)
                start=pixel
            last=pixel
        if last-start<=7:strokes.append((start+last)//2)
        return strokes

    xs=[x for x in short_strokes(vertical) if 8<x<w-8]
    ys=[y for y in short_strokes(horizontal) if 12<y<h-8]
    if len(xs)<6 or len(ys)<4:return False

    def has_regular_spacing(positions,minimum):
        gaps=np.diff(positions)
        for pitch in gaps:
            if 18<=pitch<=160:
                tolerance=max(2,pitch*.07)
                if sum(abs(delta-pitch)<=tolerance for delta in gaps)>=minimum:
                    return True
        return False

    return (has_regular_spacing(xs,5) and
            has_regular_spacing(ys,3))


def icon_grid_title_crop_bottom(image):
    """Find first true horizontal slot border, preserving a separate title.

    The icon grid must already pass the strict repeated x/y border test.
    Text in the grid region is not promoted to OCR evidence when the only
    visible item marks are images rather than letters.
    """
    if not is_repeated_icon_grid(image):
        return None
    mono=np.asarray(image.convert("L"),dtype=np.uint8)
    h,w=mono.shape
    coverage=(mono[:,int(w*.05):int(w*.94)]<120).mean(axis=1)
    hits=np.flatnonzero((coverage>.80)&
                        (np.arange(h)>=int(h*.09))&
                        (np.arange(h)<int(h*.46)))
    starts=[]
    last=-5
    for y in hits:
        y=int(y)
        if y-last>4:starts.append(y)
        last=y
    if len(starts)<3:return None
    # At least three parallel borders at an identical row pitch, not
    # coincidental ink-heavy text rows or unrelated decorative lines.
    pitch=starts[1]-starts[0]
    if not (28<=pitch<=115 and abs(starts[2]-starts[1]-pitch)<=3):
        return None
    return max(8,starts[0]-2)
