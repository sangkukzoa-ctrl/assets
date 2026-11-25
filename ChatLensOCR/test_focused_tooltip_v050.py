# -*- coding: utf-8 -*-
"""Synthetic-only regressions for focused tooltip isolation."""
import unittest
from PIL import Image, ImageDraw
import numpy as np
from focused_tooltip_v050 import detect, prepare, analyze

def fixture(scale=1, tile=True, dividers=True, dark=True):
    img=Image.new("RGB",(280,520),(26,26,26) if dark else (240,240,240))
    d=ImageDraw.Draw(img)
    if dividers:
        for y in (65,180,300,440):
            for x in range(8,270,6):
                d.line((x,y,x+3,y),fill=(62,62,62))
    if tile:
        d.rectangle((12,90,76,154),fill=(255,255,255))
        d.rectangle((36,110,48,132),fill=(28,90,180))
    for y in (32,200,220,240,260,320,340,360,380,460,480):
        for x in range(15,190,12):
            d.rectangle((x,y,x+5,y+8),fill=(120,230,180))
    d.rectangle((130,270,155,276),fill=(37,22,14))
    if scale!=1:
        img=img.resize((round(img.width*scale),round(img.height*scale)),Image.Resampling.NEAREST)
    return img

class Tests(unittest.TestCase):
    def test_detect(self):
        self.assertIsNotNone(detect(fixture()))
    def test_scale(self):
        for factor in (1.5,2):
            self.assertIsNotNone(detect(fixture(factor)))
    def test_erased_dividers_fall_back(self):
        # Nearest-neighbor downsampling can remove 1px separators.
        self.assertIsNone(detect(fixture(.75)))
    def test_missing_icon(self):
        self.assertIsNone(detect(fixture(tile=False)))
    def test_missing_dividers(self):
        self.assertIsNone(detect(fixture(dividers=False)))
    def test_light_document(self):
        self.assertIsNone(detect(fixture(dark=False)))
    def test_blank_and_landscape(self):
        self.assertIsNone(detect(Image.new("RGB",(280,520),(26,26,26))))
        self.assertIsNone(detect(fixture().transpose(Image.Transpose.ROTATE_90)))
    def test_preserve_color_and_coordinates(self):
        im=fixture();f=detect(im);out=prepare(im,f)
        self.assertEqual(out.size,im.size)
        self.assertEqual(out.getpixel((130,270)),(26,26,26))
        self.assertEqual(out.getpixel((15,200)),im.getpixel((15,200)))
        a=np.asarray(im);b=np.asarray(out);keep=a.max(2)>f.cutoff
        self.assertTrue(np.array_equal(a[keep],b[keep]))
    def test_no_reader_for_unsupported(self):
        def bad(*args):raise AssertionError("reader invoked")
        self.assertIsNone(analyze(fixture(tile=False),"한국어",True,bad,bad))
    def test_pipeline_output_preserved(self):
        tokens=[{"text":"<Title> Lv ??","score":.9,"box":(15,200,100,210)}]
        def read(img,lang,precise):
            self.assertEqual(img.getpixel((130,270)),(26,26,26))
            self.assertEqual(lang,"한국어")
            self.assertTrue(precise)
            return tokens
        out=analyze(fixture(),"한국어",True,read,lambda x:x)
        self.assertEqual(out[1],"<Title> Lv ??")
        self.assertEqual(out[4],tokens)
        self.assertTrue(out[3][0]["needs_review"])
    def test_empty_fallback(self):
        self.assertIsNone(analyze(fixture(),"한국어",True,lambda *a:[],lambda x:x))

if __name__=="__main__":
    unittest.main()
