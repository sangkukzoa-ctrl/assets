# -*- coding: utf-8 -*-
"""Preserve evidence of unreadable KakaoTalk text in a detected speech bubble.

Suppress empty/sticker surfaces while marking visible, genuine text for review.
This module never changes or invents recognized Korean words.
"""
import numpy as np
import cv2


def has_visible_text_pixels(image):
    if image is None or image.width < 6 or image.height < 8:
        return False
    gray=np.asarray(image.convert("L"))
    # Speech bubble is white or Kakao yellow. Corners are mostly background;
    # compare foreground with local background rather than a global threshold.
    rim=np.concatenate([gray[0,:],gray[-1,:],gray[:,0],gray[:,-1]])
    background=float(np.median(rim))
    foreground=(gray < min(155.0,background-38.0)).astype(np.uint8)
    count,_,stats,_=cv2.connectedComponentsWithStats(foreground,8)
    glyph_area=sum(int(area) for _,_,w,h,area in stats[1:]
                   if 1<=w<=image.width and 3<=h<=image.height and area>=3)
    return glyph_area>=max(8,int(image.width*image.height*.007))


UNREADABLE_BUBBLE="[글자 미인식]"


def text_or_unreadable(image,ocr_text):
    """Return explicit placeholder if visible ink was omitted by all OCR passes.

    None means no visible text: keep empty graphic shapes out of transcripts.
    """
    if ocr_text and ocr_text.strip():
        return ocr_text
    return UNREADABLE_BUBBLE if has_visible_text_pixels(image) else None
