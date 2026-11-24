"""Synthetic Tesseract TSV regression; no private screenshots or GT."""
import unittest
from unittest.mock import patch
from PIL import Image
import tess_backend as t
HEADER='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
def row(text,conf='96.7',x=10,w=15,h=20,line=1):
    return f'5\t1\t1\t1\t{line}\t1\t{x}\t5\t{w}\t{h}\t{conf}\t{text}\n'
class TSVTests(unittest.TestCase):
    def read(self,body,native=''):
        with patch.object(t,'resolve_tesseract_paths',return_value=('exe','data')),patch.object(t,'_single_pass_text_and_tsv',return_value=(native,HEADER+body)) as run:
            result=t.read(Image.new('RGB',(200,80)), '범용','영어');self.assertEqual(run.call_count,1);return result
    def test_literal_quote(self):
        s,p,c=self.read(row('"')+row('NEXT',x=35),'" NEXT');self.assertEqual([x['text'] for x in p],['"','NEXT'])
    def test_literal_opening_quote(self):
        s,p,c=self.read(row('"HELLO')+row('WORLD',x=35),'"HELLO WORLD');self.assertEqual([x['text'] for x in p],['"HELLO','WORLD'])
    def test_internal_tab(self):
        s,p,c=self.read(row('A\tB'),'A\tB');self.assertEqual(p[0]['text'],'A\tB')
    def test_bad_confidence_row(self):
        s,p,c=self.read(row('A')+row('BAD','x')+row('B',x=50),'A B');self.assertEqual(s,'A B');self.assertEqual([x['text'] for x in p],['A','B'])
    def test_nonfinite_confidence(self):
        s,p,c=self.read(row('A')+row('BAD','nan')+row('BAD','inf')+row('B',x=50),'A B');self.assertEqual([x['text'] for x in p],['A','B'])
    def test_invalid_box_row(self):
        s,p,c=self.read(row('A')+row('BAD',w=-4)+row('BAD',h=0)+row('BAD',x='bad')+row('B',x=50),'A B');self.assertEqual([x['text'] for x in p],['A','B'])
    def test_short_row(self):
        s,p,c=self.read(row('A')+'5\t1\t1\t1\t1\t1\t5\n'+row('B',x=50),'A B');self.assertEqual([x['text'] for x in p],['A','B'])
    def test_native_survives_bad_geometry(self):
        self.assertEqual(self.read(row('BAD','x'),'Native text'),('Native text',[],0.))
    def test_zero_negative_rejected(self):
        self.assertEqual(self.read(row('ZERO','0')+row('NEG','-1')),('',[],0.))
    def test_over_100_rejected(self):
        self.assertEqual(self.read(row('BAD','101')),('',[],0.))
    def test_normal_and_native_precedence(self):
        s,p,c=self.read(row('Alpha')+row('Beta',x=50),'Native text');self.assertEqual(s,'Native text');self.assertEqual(c,96.0);self.assertEqual(p[0]['box'],(10,5,25,25));self.assertEqual(p[0]['score'],.96)
    def test_reconstructed_fallback(self):
        s,p,c=self.read(row('Alpha')+row('Beta',x=50));self.assertEqual(s,'Alpha Beta')
    def test_engine_error(self):
        with patch.object(t,'resolve_tesseract_paths',return_value=('exe','data')),patch.object(t,'_single_pass_text_and_tsv',side_effect=RuntimeError('engine error')):
            self.assertEqual(t.read(Image.new('RGB',(200,80)),'범용','영어'),('',[],0.))
if __name__=='__main__':unittest.main()
