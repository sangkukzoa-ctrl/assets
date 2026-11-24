"""Synthetic tests only: no private image, GT, or vocabulary."""
import unittest
from PIL import Image
from panel_grid_v0423 import _read_roi

class CacheReviewTests(unittest.TestCase):
    def reader(self, sequence):
        it=iter(sequence)
        def read(image,*args,**kw):
            value=next(it)
            return value,[{'text':value,'score':.95,'box':(1,1,5,5)}],95
        return read
    def test_equal_bytes_different_shape_label(self):
        raw=bytes([195,35,195,195]*240)
        a=Image.frombytes('L',(40,24),raw);b=Image.frombytes('L',(48,20),raw)
        cache={}
        def read(im,*args,**kw):
            val='Alpha' if im.width in (40,80,120) else 'Beta'
            return val,[],95
        self.assertEqual(_read_roi(a,'label',read,cache,'영어')[0],'Alpha')
        self.assertEqual(_read_roi(b,'label',read,cache,'영어')[0],'Beta')
        self.assertEqual(len(cache),2)
    def test_equal_bytes_different_shape_button(self):
        raw=bytes([195,35,195,195]*240)
        a=Image.frombytes('L',(40,24),raw);b=Image.frombytes('L',(48,20),raw)
        cache={}
        def read(im,*args,**kw):
            return ('Alpha' if im.width in (80,120) else 'Beta'),[],95
        self.assertEqual(_read_roi(a,'button',read,cache,'영어')[0],'Alpha')
        self.assertEqual(_read_roi(b,'button',read,cache,'영어')[0],'Beta')
    def test_identical_shape_pixels_reuse(self):
        a=Image.new('L',(40,24),195);cache={};calls=[]
        def read(im,*args,**kw):
            calls.append(im.size);return 'Alpha',[],95
        self.assertEqual(_read_roi(a,'button',read,cache,'영어'),_read_roi(a.copy(),'button',read,cache,'영어'))
        self.assertEqual(len(calls),4)
    def test_split_vote_review(self):
        r=_read_roi(Image.new('L',(40,24),195),'button',self.reader(['Alpha','Beta','Alpha','Beta']),{},'영어')
        self.assertEqual(r[0],'Alpha');self.assertFalse(r[3])
    def test_three_way_plurality_review(self):
        r=_read_roi(Image.new('L',(40,24),195),'button',self.reader(['Alpha','Beta','Gamma','Alpha']),{},'영어')
        self.assertEqual(r[0],'Alpha');self.assertFalse(r[3])
    def test_majority_unchanged(self):
        r=_read_roi(Image.new('L',(40,24),195),'button',self.reader(['Alpha','Beta','Alpha','Alpha']),{},'영어')
        self.assertEqual(r[0],'Alpha');self.assertTrue(r[3])
    def test_unanimous_unchanged(self):
        r=_read_roi(Image.new('L',(40,24),195),'button',self.reader(['Alpha']*4),{},'영어')
        self.assertEqual(r[0],'Alpha');self.assertTrue(r[3])
    def test_native_label_priority_unchanged(self):
        r=_read_roi(Image.new('L',(40,24),195),'label',self.reader(['Alpha','Alphb','Alphb','Alphb','Alphb']),{},'영어')
        self.assertEqual(r[0],'Alpha');self.assertFalse(r[3])
    def test_language_isolated(self):
        im=Image.new('L',(40,24),195);cache={}
        def read(im,mode,language,**kw):return ('Alpha' if language=='영어' else 'Beta'),[],95
        self.assertEqual(_read_roi(im,'button',read,cache,'영어')[0],'Alpha')
        self.assertEqual(_read_roi(im,'button',read,cache,'한국어')[0],'Beta')
if __name__=='__main__': unittest.main()
