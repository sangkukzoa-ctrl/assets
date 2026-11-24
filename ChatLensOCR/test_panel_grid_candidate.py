"""Synthetic candidate regressions; no private image data."""
import unittest
from PIL import Image
from panel_grid_v0423 import _read_roi

class CandidateTests(unittest.TestCase):
    def run_roi(self,seq,kind='button'):
        calls=iter(seq)
        def reader(*args,**kw):
            text,conf=next(calls)
            return text,[{'text':text,'box':(1,1,10,10)}],conf
        return _read_roi(Image.new('L',(80,30),116),kind,reader,{},'영어')
    def test_literal_pipe(self):
        self.assertEqual(self.run_roi([('|A|',95)]*4)[0],'|A|')
    def test_punctuation_only(self):
        r=self.run_roi([('...',96)]*4);self.assertEqual(r[0],'...');self.assertTrue(r[3])
    def test_symbol_only_label(self):
        self.assertEqual(self.run_roi([('→',95)]*5,'label')[0],'→')
    def test_low_conf_symbol_rejected(self):
        self.assertIsNone(self.run_roi([('|',25)]*4)[0])
    def test_none_not_string(self):
        self.assertIsNone(self.run_roi([(None,95)]*4)[0])
    def test_nonfinite_isolated(self):
        r=self.run_roi([('BAD',float('nan')),('GOOD',96),('GOOD',96),('GOOD',96)])
        self.assertEqual(r[0],'GOOD');self.assertTrue(r[3])
    def test_invalid_conf_isolated(self):
        self.assertEqual(self.run_roi([('BAD','invalid'),('GOOD',90),('GOOD',90),('GOOD',90)])[0],'GOOD')
    def test_out_of_range_conf(self):
        self.assertIsNone(self.run_roi([('BAD',101)]*4)[0])
    def test_empty_votes_count(self):
        r=self.run_roi([('OK',95),('',0),('OK',95),('',0)]);self.assertEqual(r[0],'OK');self.assertFalse(r[3])
    def test_weak_agreement_needs_review(self):
        r=self.run_roi([('OK',20)]*4);self.assertEqual(r[0],'OK');self.assertFalse(r[3])
    def test_weak_label_agreement_needs_review(self):
        r=self.run_roi([('OK',20)]*5,'label');self.assertEqual(r[0],'OK');self.assertFalse(r[3])
    def test_normal_agreement(self):
        r=self.run_roi([('APPLY 42',95)]*4);self.assertEqual(r[0],'APPLY 42');self.assertTrue(r[3])
    def test_two_distinct_labels(self):
        r=self.run_roi([('Native',80),('Other',98),('Nativf',98),('Other',98),('Other',98)],'label');self.assertEqual(r[0],'Native');self.assertFalse(r[3])
    def test_one_off_symbol_review(self):
        r=self.run_roi([('+',95),('',0),('',0),('',0)]);self.assertEqual(r[0],'+');self.assertFalse(r[3])
if __name__=='__main__':unittest.main()
