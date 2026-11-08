# -*- coding: utf-8 -*-
"""Conservative local self-learning for confirmed FINAL FANTASY XIV job icons.

An existing official/reference template must make a high-confidence match
before this module records its cropped icon. No screenshot, chat text or
personally identifying content is stored; only a very small job-icon crop.
A wrong/ambiguous match is never used as a training label.
"""
import hashlib
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

MAX_PER_JOB = 12
MIN_SCORE = 0.90
MIN_MARGIN = 0.12

def learn_verified_icon(image, rect, job, score, margin, data_root,
                        allowed_jobs=None):
    """Save an image-local reference crop, or return None when not reliable."""
    if (image is None or not isinstance(job, str)
            or not (re.fullmatch(r"[가-힣]{2,12}",job))
            or (allowed_jobs is not None and job not in allowed_jobs)
            or score < MIN_SCORE or margin < MIN_MARGIN):
        return None
    try:
        x0,y0,x1,y1 = (int(v) for v in rect)
        w,h = x1-x0,y1-y0
        if (w<12 or h<12 or w>64 or h>64
                or max(w,h)/min(w,h)>1.45 or
                x0<0 or y0<0 or x1>image.width or y1>image.height):
            return None
        crop=np.asarray(image.convert("L").crop((x0,y0,x1,y1)))
        if float(crop.std()) < 17:
            return None
        shape=cv2.resize(crop,(32,32),interpolation=cv2.INTER_AREA)
        shape=cv2.equalizeHist(shape)
        edges=cv2.Canny(shape,50,110)
        if not (0.025 <= float((edges>0).mean()) <= 0.68):
            return None
        # Hash the quantized thumbnail: same source in small contrast/scale
        # variants does not fill the bank with duplicates.
        signature=cv2.resize(shape,(16,16),interpolation=cv2.INTER_AREA)
        signature=(signature//24).astype(np.uint8)
        digest=hashlib.sha256(signature.tobytes()).hexdigest()[:14]
        directory=Path(data_root)/"job_samples"/"auto"
        directory.mkdir(parents=True,exist_ok=True)
        path=directory/(job+"__"+digest+".png")
        if path.exists():
            return None
        if len(list(directory.glob(job+"__*.png")))>=MAX_PER_JOB:
            return None
        Image.fromarray(shape).save(path,format="PNG")
        return path
    except (ValueError,TypeError,OverflowError,OSError,cv2.error):
        return None
