# -*- coding: utf-8 -*-
"""Conservative Latin-token reread for low-confidence FFXIV text.
Only source pixels are used, and independent page modes must agree.
"""
import re,unicodedata
from PIL import Image
_DASHED=re.compile(r'^[A-Za-z0-9|Il!]{1,6}-[A-Za-z0-9|Il!]{1,5}$')
_CLEAN=re.compile(r'^[A-Z][A-Z0-9]{1,6}-[A-Z0-9]{1,5}$')

def recover_low_confidence_latin(image, transcript, boxes, reader=None):
    if not boxes or not transcript or image.width<50:return transcript
    if reader is None:
        import pytesseract
        def reader(region,psm):
            return pytesseract.image_to_string(region,lang='eng',config=
                f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',timeout=6).strip()
    ordered=sorted(boxes,key=lambda t:(t['box'][1]//15,t['box'][0]))
    for item in ordered:
        original=str(item.get('text',''))
        plain=unicodedata.normalize('NFKC',original)
        if '-' not in plain or not _DASHED.fullmatch(plain):continue
        if float(item.get('score',1))>=.65:continue
        if original not in transcript:continue
        x0,y0,x1,y1=map(int,item['box'])
        neighbors=[int(p['box'][0]) for p in ordered if p is not item
                   and int(p['box'][0])>x0+4 and abs(int(p['box'][1])-y0)<12]
        # An uncertain box may include the adjacent Korean suffix.
        if neighbors:x1=min(x1,min(neighbors))
        x0=max(0,x0-1);y0=max(0,y0-2);x1=min(image.width,x1);y1=min(image.height,y1+4)
        if x1-x0<15 or y1-y0<7:continue
        roi=image.crop((x0,y0,x1,y1)).resize(((x1-x0)*4,(y1-y0)*4),Image.Resampling.LANCZOS)
        try:
            first=reader(roi,7).strip().replace(' ','').upper()
            second=reader(roi,13).strip().replace(' ','').upper()
        except Exception:continue
        if first!=second or not _CLEAN.fullmatch(first):continue
        if first==plain.upper():continue
        transcript=transcript.replace(original,first,1)
    return transcript
