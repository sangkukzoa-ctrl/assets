"""Synthetic image -> control geometry -> reader -> overlay regression."""
import math,sys,types,unittest
from unittest.mock import patch
from PIL import Image,ImageDraw
from panel_grid_v0423 import analyze, pixel_control_rows

MARK='[글자 미인식]'
def image():
    im=Image.new('RGB',(850,570),(197,197,197));d=ImageDraw.Draw(im)
    for i in range(8):
        y=55+i*60
        d.rectangle((202,y,325,y+40),outline=(12,12,12),fill=(116,116,116),width=3)
        d.rectangle((230,y+13,254,y+24),fill=(243,243,243))
    return im

def run(reader):
    app=types.ModuleType('app');app.recognize=lambda *a:[];app.merge_rows=lambda a:[]
    review=types.ModuleType('review_v046');review.UNREADABLE_MARKER=MARK
    with patch.dict(sys.modules,{'app':app,'review_v046':review}):
        return analyze(image(),'영어',True,reader=reader)

class Integration(unittest.TestCase):
    def test_geometry(self):
        self.assertEqual(len(pixel_control_rows(image())),8)
    def test_normal(self):
        r=run(lambda *a,**k:('APPLY',[{'text':'APPLY','score':.9,'box':(12,12,40,24)}],90))
        self.assertEqual(r[1].splitlines(),['APPLY']*8)
        self.assertEqual(len(r[4]),8)
        self.assertTrue(all(not x['needs_review'] for x in r[3][1:]))
    def test_subpixel_box(self):
        r=run(lambda *a,**k:('I',[{'text':'I','score':.9,'box':(2,2,3,3)}],90))
        self.assertTrue(all(b['box'][2]>b['box'][0] and b['box'][3]>b['box'][1] for b in r[4]))
    def test_clip(self):
        r=run(lambda im,*a,**k:('A',[{'text':'A','box':(-8,-8,im.width+20,im.height+20)}],90))
        self.assertEqual([x['box'] for x in r[4]],[x['box'] for x in r[3][1:]])
    def test_invalid_geometry(self):
        items=[{'text':'BAD','box':(9,9,3,3)}, {'text':'BAD','box':(float('nan'),0,3,3)}, {'text':'BAD'}, {'text':'BAD','box':(10000,0,10004,4)}, {'text':'OK','box':(2,2,12,12)}]
        r=run(lambda *a,**k:('OK',items,95))
        self.assertEqual(len(r[4]),8)
        self.assertTrue(all(x['text']=='OK' for x in r[4]))
        self.assertTrue(all(x['needs_review'] for x in r[3][1:]))
    def test_missing_boxes(self):
        r=run(lambda *a,**k:('TEXT',None,95))
        self.assertEqual(r[1].splitlines(),['TEXT']*8)
        self.assertEqual(r[4],[])
        self.assertTrue(all(x['needs_review'] for x in r[3][1:]))
    def test_variant_exception(self):
        def reader(im,*a,**kw):
            if kw['psm']==7 and im.width<300:raise RuntimeError('failed variant')
            return 'OK',[{'text':'OK','box':(2,2,10,10)}],95
        r=run(reader);self.assertEqual(r[1].splitlines(),['OK']*8)
    def test_all_variants_fail_fallback(self):
        def reader(*a,**kw):raise RuntimeError('backend unavailable')
        self.assertIsNone(run(reader))
    def test_text_with_empty_boxes_review(self):
        r=run(lambda *a,**k:('TEXT',[],90));self.assertTrue(all(x['needs_review'] for x in r[3][1:]))
    def test_unsupported(self):
        self.assertIsNone(analyze(Image.new('RGB',(850,570),'white'),'영어',True))
if __name__=='__main__':unittest.main()
