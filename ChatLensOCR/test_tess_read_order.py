"""Synthetic independent reading-order and output-isolation regressions."""
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import tess_backend as t
HEADER='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
def row(text, page=1, block=1, par=1, line=1, word=1, x=10, y=10):
    return f'5\t{page}\t{block}\t{par}\t{line}\t{word}\t{x}\t{y}\t20\t15\t95\t{text}\n'
class ReadingOrder(unittest.TestCase):
    def read(self,body,native=''):
        with patch.object(t,'resolve_tesseract_paths',return_value=('exe','data')),patch.object(t,'_single_pass_text_and_tsv',return_value=(native,HEADER+body)):
            return t.read(Image.new('RGB',(800,400)),'범용','영어')
    def test_columns(self):
        body=row('Left one',y=10)+row('Left two',line=2,y=80)+row('Right one',block=2,x=400,y=20)+row('Right two',block=2,line=2,x=400,y=90)
        self.assertEqual(self.read(body)[0],'Left one\nLeft two\nRight one\nRight two')
    def test_page_order(self):
        self.assertEqual(self.read(row('Page one',y=80)+row('Page two',page=2,y=10))[0],'Page one\nPage two')
    def test_same_line_vertical_jitter(self):
        self.assertEqual(self.read(row('First',y=20)+row('Second',line=2,y=18))[0],'First\nSecond')
    def test_paragraph_order(self):
        self.assertEqual(self.read(row('First',y=60)+row('Second',par=2,y=40))[0],'First\nSecond')
    def test_shuffled_rows(self):
        self.assertEqual(self.read(row('Second',line=2,y=10)+row('First',y=10))[0],'First\nSecond')
    def test_native_priority_and_parts_unchanged(self):
        result=self.read(row('B',block=2,y=20)+row('A',y=50),'Native\nText')
        self.assertEqual(result[0],'Native\nText');self.assertEqual([p['text'] for p in result[1]],['B','A']);self.assertEqual(result[2],95)
    def test_hangul_spacing(self):
        self.assertEqual(self.read(row('한',x=10)+row('글',x=31,word=2)+row('문자',x=66,word=3))[0],'한글 문자')
    def test_unicode_line_separator_literal(self):
        self.assertEqual(self.read(row('A\u2028B'))[1][0]['text'],'A\u2028B')
    def test_crlf(self):
        self.assertEqual(self.read(row('A') .replace('\n','\r\n')+row('B',line=2,y=30).replace('\n','\r\n'))[0],'A\nB')
class OutputIsolation(unittest.TestCase):
    def run_fake(self,txt=None,tsv=None):
        def fake(args,**kwargs):
            base=Path(args[2]);
            if txt is not None: base.with_suffix('.txt').write_bytes(txt)
            if tsv is not None: base.with_suffix('.tsv').write_bytes(tsv)
            return SimpleNamespace(returncode=0,stderr=b'')
        with patch('subprocess.run',side_effect=fake) as run:
            value=t._single_pass_text_and_tsv(Image.new('RGB',(20,20)),'exe','data','eng',7)
            self.assertEqual(run.call_count,1);return value
    def test_missing_txt(self):
        self.assertEqual(self.run_fake(tsv=HEADER.encode()),('',HEADER))
    def test_missing_tsv(self):
        self.assertEqual(self.run_fake(txt=b'Native'),('Native',''))
    def test_invalid_tsv_utf8(self):
        self.assertEqual(self.run_fake(txt=b'Native',tsv=b'\xff'),('Native',''))
    def test_invalid_txt_utf8(self):
        self.assertEqual(self.run_fake(txt=b'\xff',tsv=HEADER.encode()),('',HEADER))
    def test_both_missing(self):
        with self.assertRaises(RuntimeError):self.run_fake()
    def test_both_valid(self):
        self.assertEqual(self.run_fake(txt=b'Native',tsv=HEADER.encode()),('Native',HEADER))
if __name__=='__main__':unittest.main(verbosity=2)
