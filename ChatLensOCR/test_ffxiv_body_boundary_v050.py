import unittest
from PIL import Image,ImageDraw
from ffxiv_body_boundary_v050 import boundary_offsets,guarded_body_reread


def row(fringe=True,adjacent=False,wide=False,foreign=False):
    im=Image.new('RGB',(160,20),(15,15,15));d=ImageDraw.Draw(im)
    d.rectangle((37,4,39,15),fill=(220,135,0))
    if fringe:d.rectangle((40,5,41 if wide else 40,14),fill=(120,55,0))
    d.rectangle((41 if adjacent else 48,4,55,15),fill=(230,140,0))
    if foreign:d.rectangle((42,5,43,14),fill=(30,220,30))
    return im

class Tests(unittest.TestCase):
    def test_fringe(self): self.assertEqual(boundary_offsets(row(),40,160),(2,3))
    def test_no_fringe(self): self.assertEqual(boundary_offsets(row(False),40,160),())
    def test_no_gap(self): self.assertEqual(boundary_offsets(row(adjacent=True),40,160),())
    def test_other_color_gap(self): self.assertEqual(boundary_offsets(row(foreign=True),40,160),())
    def test_two_column_fringe(self): self.assertEqual(boundary_offsets(row(wide=True),40,160),(3,4))
    def test_consensus(self):
        old=('AAA 테스트 문장입니다.<12.',[{'text':'AAA','score':.56}],88)
        got=guarded_body_reread(row(),40,160,'한국어',lambda *a:('새로운 테스트 문장입니다.<12.',[],92),old)
        self.assertEqual(got[0],'새로운 테스트 문장입니다.<12.')
    def test_preserve_latin(self):
        old=('ABC 갑니다',[{'text':'ABC','score':.95}],86)
        self.assertEqual(guarded_body_reread(row(),40,160,'한국어',lambda *a:('안녕 갑니다',[],95),old),old)
    def test_preserve_markup(self):
        old=('갑니다<se.11>',[],71)
        self.assertEqual(guarded_body_reread(row(),40,160,'한국어',lambda *a:('갑니다<se.15>',[],95),old),old)
    def test_no_agreement(self):
        old=('ABC 가요',[{'text':'ABC','score':.3}],70)
        def reader(im,x,*a):return ('안녕 가요' if x==42 else '다시 가요',[],95)
        self.assertEqual(guarded_body_reread(row(),40,160,'한국어',reader,old),old)
    def test_no_evidence(self):
        old=('ABC 가요',[],70)
        self.assertEqual(guarded_body_reread(row(),40,160,'한국어',lambda *a:('안녕 가요',[],95),old),old)
    def test_punctuation_only(self):
        old=('. 안녕 가요',[],80)
        self.assertEqual(guarded_body_reread(row(),40,160,'한국어',lambda *a:('안녕 가요',[],94),old)[0],'안녕 가요')
    def test_empty_original(self):
        old=('',[],0)
        self.assertEqual(guarded_body_reread(row(),40,160,'한국어',lambda *a:('안녕',[],94),old),old)
if __name__=='__main__':unittest.main()
