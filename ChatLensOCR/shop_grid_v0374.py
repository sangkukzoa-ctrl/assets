# -*- coding: utf-8 -*-
"""Product-card aware OCR for catalog grids (v0.3.7.4).

The geometry detector works on pixels before text recognition, so product
names, prices and availability from neighbouring columns cannot intermingle.
It is deliberately conservative in automatic mode. No product information is
invented; text is copied only from the pixels in each detected card.
"""
import cv2
import numpy as np
from PIL import Image


def _candidates(image):
    a = np.asarray(image.convert('RGB'))
    h, w = a.shape[:2]
    gray = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    mask = cv2.morphologyEx((gray < 120).astype('uint8') * 255,
                            cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    images, buttons = [], []
    for x, y, cw, ch, area in stats[1:]:
        if y < h * .055 or cw <= 0 or ch <= 0:
            continue
        cx, cy = float(x + cw / 2), float(y + ch / 2)
        density = area / (cw * ch)
        if (cw >= max(65, w * .065) and ch >= max(23, h * .028)
                and cw <= w * .43 and ch < h * .35
                and area >= 820 and density >= .11):
            images.append((cx, cy, float(cw), float(ch)))
        elif (24 <= cw <= 90 and 13 <= ch <= 24
              and density >= .65 and y >= h * .12 and area >= 220):
            buttons.append((cx, cy, float(cw), float(ch)))
    return images, buttons


def _grid_lattice(candidates, width):
    """Find an evenly spaced grid with 2..7 product columns."""
    if len(candidates) < 2:
        return None
    xs = [p[0] for p in candidates]
    proposals = []
    # Product card pitches are generally between 9% and 44% of the viewport.
    for i, x in enumerate(xs):
        for y in xs[i + 1:]:
            distance = abs(y - x)
            for skipped in range(1, 7):
                pitch = distance / skipped
                if width * .085 <= pitch <= width * .49:
                    proposals.append(pitch)
    if not proposals:
        return None
    best = None
    for pitch in proposals:
        tolerance = max(9, pitch * .09)
        for x in xs:
            # Evaluate all candidate components against a repeating lattice.
            slots = {}
            score = 0.
            for p in candidates:
                pos = round((p[0] - x) / pitch)
                delta = abs(p[0] - (x + pos * pitch))
                if delta <= tolerance:
                    score += (1.4 if p[2] >= 60 else .65) * (1 - delta / (tolerance * 2))
                    slots[pos] = slots.get(pos, 0) + 1
            if len(slots) < 2:
                continue
            lo, hi = min(slots), max(slots)
            span = hi - lo + 1
            if span < 2 or span > 7:
                continue
            # Treat missing intermediate product columns as a weaker fit.
            score += len(slots) * 1.4 - (span - len(slots)) * 5
            score += sum(min(3, n) for n in slots.values()) * .35
            score *= len(slots) / span
            if best is None or score > best[0]:
                best = (score, pitch, x + lo * pitch, span, len(slots))
    if best is None:
        return None
    score, pitch, first, count, occupied = best
    # An isolated pair of elements is insufficient for automatic routing.
    if score < 4.7:
        return None
    left = max(0, round(first - pitch / 2))
    right = min(width, round(first + (count - .5) * pitch))
    # In card grids the first image is often offset inside its tile; use the
    # entire available right-hand tile when the gap is small.
    if width - right < pitch * .46:
        right = width
    if left < pitch * .46:
        left = 0
    cuts = [left] + [max(0, min(width, round(first + (i + .5) * pitch)))
                     for i in range(count - 1)] + [right]
    if any(b <= a for a, b in zip(cuts, cuts[1:])):
        return None
    return cuts, score, pitch, occupied


def _row_ranges(images, buttons, height, pitch, columns):
    """Detect product rows using repeated image bands or bottom buy buttons."""
    by = sorted(p[1] for p in buttons if p[2] < pitch * .5)
    groups = []
    for val in by:
        if groups and val - groups[-1][-1] < max(17, height * .04):
            groups[-1].append(val)
        else:
            groups.append([val])
    groups = [v for v in groups if len(v) >= max(2, int(columns * .52 + .5))]
    if len(groups) >= 2:
        centers = [sum(v) / len(v) for v in groups]
        # Each buy button typically marks a row's footer.
        cuts = [max(0, int(centers[0] - min(300, (centers[1] - centers[0]) * .9)))]
        for i in range(len(centers) - 1):
            cuts.append(min(height, int(centers[i] + max(14, (centers[i + 1] - centers[i]) * .06))))
        cuts.append(min(height, int(centers[-1] + max(14, height * .025))))
        return [(a, b) for a, b in zip(cuts, cuts[1:]) if b - a >= 65]
    # Product image bands are a reliable alternative for red-button stores.
    iy = sorted(p[1] for p in images)
    image_groups = []
    for y in iy:
        if image_groups and y - image_groups[-1][-1] < max(45, height * .085):
            image_groups[-1].append(y)
        else:
            image_groups.append([y])
    image_groups = [g for g in image_groups if len(g) >= 2]
    if not image_groups:
        return [(0, height)]
    mean = [sum(g) / len(g) for g in image_groups]
    if len(mean) < 2:
        return [(max(0, int(min(iy) - min(180, height * .2))), height)]
    cuts = [max(0, int(mean[0] - (mean[1] - mean[0]) * .24))]
    cuts.extend(int(y - min(85, (y - mean[i - 1]) * .18)) for i, y in enumerate(mean[1:], 1))
    cuts.append(height)
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if b - a >= 65]


def card_boxes(image, forced=False):
    """Return item crop rectangles plus geometry confidence or None."""
    w, h = image.size
    if w < 450 or h < 320:
        return None
    images, buttons = _candidates(image)
    # Strong evidence is a row of similarly sized photographic thumbnails;
    # this rejects menus, logos and text-only websites with regular buttons.
    image_bands = {}
    for part in images:
        yband = round(part[1] / max(32, h * .09))
        image_bands.setdefault(yband, []).append(part)
    repeated = any(len([p for p in group if p[2] >= 85 and p[3] >= 45]) >= 2
                   for group in image_bands.values())
    primary = _grid_lattice(images, w) if repeated else None
    grid = primary or _grid_lattice(images + buttons, w)
    if grid is None:
        return None
    xcuts, score, pitch, occupied = grid
    cols = len(xcuts) - 1
    # Without explicit mode, require several recurring components, a bright
    # background, and visible product photographs.
    a = np.asarray(image.convert('RGB'))
    bright_ratio = float((a.mean(axis=2) > 180).mean())
    if not forced and (bright_ratio < .57 or len(images) < 2
                       or occupied < 2 or score < 6
                       or (not repeated and (len(buttons) < 2 or len(images) > 2))):
        return None
    rows = _row_ranges(images, buttons, h, pitch, cols)
    boxes = [(x0 + 2, y0, x1 - 2, y1)
             for y0, y1 in rows
             for x0, x1 in zip(xcuts, xcuts[1:])
             if x1 - x0 > 70 and y1 - y0 >= 65]
    if len(boxes) < 2:
        return None
    return {'boxes': boxes, 'columns': cols, 'rows': len(rows),
            'score': round(score, 2), 'pitch': round(pitch, 1)}


def analyze(image, language='한국어', precise=True, forced=False, reader=None):
    if reader is None:
        from multicolumn_v037 import _read as reader
    if not forced:
        # A strip of alternate photographs underneath ONE large hero image
        # must not become five independently numbered products. This check
        # is only activated by the geometry of a true single-item detail.
        from product_detail_v0415 import detail_evidence
        detail=detail_evidence(image)
        if detail is not None:
            x0,y0,x1,y1=detail["detail_box"]
            content,local_boxes,confidence=reader(
                image.crop((x0,y0,x1,y1)),language,precise)
            if content.strip():
                items=[]
                for item in local_boxes:
                    a,b,c,d=item["box"]
                    items.append({**item,"box":(x0+a,y0+b,x0+c,y0+d)})
                metadata=[{"type":"product_detail","product_count":1,
                           "box":detail["detail_box"],
                           "evidence":detail["evidence"],
                           "confidence":confidence,
                           "human_verified":False}]
                # The only output text is OCR actually returned from the
                # product-details region; no name or price is synthesized.
                return "쇼핑몰",content.strip(),[],metadata,items
    geo = card_boxes(image, forced=forced)
    if geo is None:
        return None
    output, raw, metadata = [], [], []
    for index, (x0, y0, x1, y1) in enumerate(geo['boxes'], 1):
        crop = image.crop((x0, y0, x1, y1))
        content, local_boxes, confidence = reader(crop, language, precise)
        if not content.strip():
            continue
        output.append(f'[상품 {index:02d}]\n{content.strip()}')
        metadata.append({'type': 'product_card', 'index': index,
                         'box': (x0, y0, x1, y1), 'confidence': confidence,
                         'columns': geo['columns']})
        for item in local_boxes:
            a, b, c, d = item['box']
            raw.append({**item, 'box': (x0 + a, y0 + b, x0 + c, y0 + d)})
    if not output:
        return None
    return '쇼핑몰', '\n\n'.join(output), [], metadata, raw


def _synthetic():
    from PIL import ImageDraw
    im = Image.new('RGB', (1100, 660), 'white')
    d = ImageDraw.Draw(im)
    for row in range(2):
        for col in range(5):
            x = 58 + col * 210
            y = 75 + row * 280
            d.rectangle((x, y, x + 124, y + 58), fill=(33, 34, 35))
            d.rectangle((x + 50, y + 185, x + 79, y + 201), fill='black')
    guess = card_boxes(im)
    assert guess and guess['columns'] == 5 and guess['rows'] == 2, guess
    return True
