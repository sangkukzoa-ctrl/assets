# -*- coding: utf-8 -*-
"""Synthetic geometry and preservation gates; no private pixels."""
import unittest
from PIL import Image,ImageDraw,ImageFont
from isolated_graphic_v050 import paired_frame,reject_isolated_graphic


def fixture(bridge=True,marks=True):
    im=Image.new('RGB',(90,44),(242,242,242));d=ImageDraw.Draw(im)
    for x in (12,45):
        d.rounded_rectangle((x,15,x+27,34),radius=5,outline=(30,30,30),width=3)
        if marks:d.rectangle((x+8,8,x+18,10),fill=(25,25,25))
    if bridge:d.line((39,19,45,19),fill=(30,30,30),width=3)
    return im


class Tests(unittest.TestCase):
    def call(self,im=None,text='oo',score=.55,alt='graphic',reader=None,items=None,rows=None):
        im=im if im is not None else fixture()
        items=items if items is not None else [{'text':text,'score':score,'box':(0,0,im.width,im.height)}]
        rows=rows if rows is not None else [{'text':text,'score':score}]
        reader=reader if reader is not None else lambda *a,**k:(alt,[],40.)
        return reject_isolated_graphic(im,items,rows,'한국어',reader)
    def test_graphic(self):
        result=self.call();self.assertIsNotNone(result)
        self.assertEqual(result['rejected_text'],'oo');self.assertTrue(result['needs_review'])
        self.assertFalse(result['human_verified'])
    def test_unconnected_and_unmarked(self):
        for im in (fixture(bridge=False),fixture(marks=False)):
            self.assertFalse(paired_frame(im));self.assertIsNone(self.call(im))
    def test_printed_words_preserved(self):
        for text in ('oo','ee','ab','X','OK','WWW'):
            im=Image.new('RGB',(90,44),'white');d=ImageDraw.Draw(im)
            # Use platform-local default PIL font; no external font resource.
            d.text((6,4),text,fill='black',font=ImageFont.load_default(size=28))
            self.assertIsNone(self.call(im,text=text))
    def test_literal_punctuation_and_numbers_preserved(self):
        for text in ('??','1','<>','O!','가','ABCD','ﾊ'):
            self.assertIsNone(self.call(text=text))
    def test_high_confidence(self):
        self.assertIsNone(self.call(score=.91))
    def test_confirmed_reading(self):
        for alt in ('OO','oo.','word oo here'):
            self.assertIsNone(self.call(alt=alt))
    def test_unavailable_reader(self):
        self.assertIsNone(self.call(alt=''))
        def fail(*a,**k):raise RuntimeError('unavailable')
        self.assertIsNone(self.call(reader=fail))
    def test_multiple_items_preserved(self):
        items=[{'text':'oo','score':.55,'box':(0,0,90,44)}]*2
        self.assertIsNone(self.call(items=items))
    def test_invalid_geometry_and_confidence(self):
        for score in (float('nan'),float('inf'),-1,0):self.assertIsNone(self.call(score=score))
        self.assertIsNone(self.call(items=[{'text':'oo','score':.55,'box':(-1,0,90,44)}]))
    def test_reader_not_invoked_on_normal_text(self):
        def fail(*a,**k):self.fail('unnecessary OCR')
        self.assertIsNone(self.call(text='long text',reader=fail))

if __name__=='__main__':unittest.main()
