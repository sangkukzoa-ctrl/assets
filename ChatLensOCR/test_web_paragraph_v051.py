import unittest
from PIL import Image,ImageDraw
from web_paragraph_v051 import paragraph_ink,coverage,suspect,rescue


def page():
    im=Image.new('RGB',(640,60),'white');d=ImageDraw.Draw(im)
    for y in (7,33):
        for x in range(15,605,20):
            d.rectangle((x,y,x+9,y+14),outline='black',width=2)
            d.line((x+1,y+7,x+8,y+7),fill='black',width=1)
    return im

def box(bounds,score=.99):return {'text':'test','score':score,'box':bounds}

class Tests(unittest.TestCase):
    def test_eligible(self):self.assertIsNotNone(paragraph_ink(page()))
    def test_blank(self):self.assertIsNone(paragraph_ink(Image.new('RGB',(640,60),'white')))
    def test_dark(self):self.assertIsNone(paragraph_ink(Image.new('RGB',(640,60),'black')))
    def test_border(self):
        im=page();ImageDraw.Draw(im).line((0,0,639,0),fill='black');self.assertIsNone(paragraph_ink(im))
    def test_tall(self):self.assertIsNone(paragraph_ink(page().resize((640,640))))
    def test_normal_preserved(self):
        self.assertIsNone(rescue(page(),'한국어',[box((0,0,640,60))],lambda *a,**k:self.fail('must not call OCR')))
    def test_non_korean(self):self.assertIsNone(rescue(page(),'영어',[],lambda *a,**k:self.fail('must not call OCR')))
    def test_missed_row(self):self.assertTrue(suspect(paragraph_ink(page()),[box((0,0,640,29))]))
    def test_low_confidence(self):self.assertTrue(suspect(paragraph_ink(page()),[box((0,0,640,60),.5)]))
    def test_coordinates(self):
        def read(im,*args,**kwargs):
            self.assertEqual(im.size,(1980,240));self.assertEqual(kwargs['psm'],6)
            return '검증용 문장',[box((30,30,1950,210))],95.
        out=rescue(page(),'한국어',[],read);self.assertEqual(out[0],'검증용 문장');self.assertEqual(out[1][0]['box'],(0.,0.,640,60));self.assertFalse(out[2]['human_verified'])
    def test_reject_low_confidence(self):self.assertIsNone(rescue(page(),'한국어',[],lambda *a,**k:('검증',[box((30,30,1950,210))],60.)))
    def test_reject_incomplete(self):self.assertIsNone(rescue(page(),'한국어',[],lambda *a,**k:('검증',[box((30,30,1950,100))],95.)))
    def test_reject_nan(self):self.assertIsNone(rescue(page(),'한국어',[],lambda *a,**k:('검증',[box((30,30,1950,210))],float('nan'))))
    def test_reader_failure(self):
        def fail(*a,**k):raise RuntimeError('test')
        self.assertIsNone(rescue(page(),'한국어',[],fail))
if __name__=='__main__':unittest.main()
