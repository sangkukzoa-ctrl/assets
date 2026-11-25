# -*- coding: utf-8 -*-
"""Synthetic-only regressions: no real chats or user data."""
import unittest
from PIL import Image, ImageDraw
from ffxiv_chromatic_v050 import autocomplete_pairs, chromatic_body, autocomplete_metadata

# Synthetic mirrored bracket-like stencil (not a game asset).
SHAPE=('..###.','..###.','.####.','.##...','##....','##....','##....','.##...','.####.','..###.','..###.')
def fixture(pair=True, flip=False, fill=True):
    im=Image.new('RGB',(180,18),(18,20,25));d=ImageDraw.Draw(im)
    if fill:
        for x in range(25,65,10):d.rectangle((x,4,x+6,13),fill=(242,132,18))
    if pair:
        for y,line in enumerate(SHAPE,3):
            for x,c in enumerate(line):
                if c=='#':
                    d.point((12+x,y),fill=(40,240,45))
                    d.point((74+(x if flip else 5-x),y),fill=(240,45,40))
    return im

class Tests(unittest.TestCase):
    def test_pair(self):
        a=autocomplete_pairs(fixture());self.assertEqual(len(a),1);self.assertFalse(a[0]['verified']);self.assertEqual(a[0]['kind'],'autocomplete_pair_candidate')
    def test_source_coordinates(self):
        a=autocomplete_pairs(fixture())[0];b=autocomplete_metadata(fixture(),37)[0]
        for k in ("box","left_box","right_box"):
            x,y,e,z=a[k];self.assertEqual(b[k],(x,y+37,e,z+37))
    def test_no_pair(self):self.assertEqual(autocomplete_pairs(fixture(pair=False)),[])
    def test_nonmirror(self):self.assertEqual(autocomplete_pairs(fixture(flip=True)),[])
    def test_no_enclosed_ink(self):self.assertEqual(autocomplete_pairs(fixture(fill=False)),[])
    def test_high_confidence_bypass(self):
        def forbidden(*a,**kw):raise AssertionError('backend invoked')
        self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *a:('기존',[],90),forbidden)[0],'기존')
    def test_icon_bypass(self):
        def forbidden(*a,**kw):raise AssertionError('backend invoked')
        self.assertEqual(chromatic_body(fixture(),0,180,'한국어',lambda *a:('O',[],45),forbidden)[0],'O')
    def test_consensus(self):
        self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *a:('원문 12',[],52),lambda *a,**kw:('검사 12',[],90)),('검사 12',[],90))
    def test_disagreement(self):
        original=('원문',[],52);votes=iter([('가',[],90),('나',[],90),('다',[],90)])
        self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *a:original,lambda *a,**kw:next(votes)),original)
    def test_literal_guard(self):
        for a,b in [('검사 12','검사 13'),('AB 테스트','테스트'),('<칭호> ??','칭호'),('텍스트 □','텍스트')]:
            old=(a,[],52)
            self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *x:old,lambda *x,**k:(b,[],90)),old)
    def test_single_latin_guard(self):
        old=('A 테스트',[{'text':'A','score':.90}],52)
        self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *x:old,lambda *x,**k:('테스트',[],90)),old)
    def test_korean_only_cannot_override(self):
        old=('원문',[],52)
        self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *a:old,lambda *a,**kw:('검사',[],90) if kw['tess_lang']=='kor' else ('',[],0)),old)
    def test_no_stale_boxes(self):
        old=('원문',[{'text':'원문','score':.52}],52)
        self.assertEqual(chromatic_body(fixture(pair=False),0,180,'한국어',lambda *a:old,lambda *a,**kw:('검사',[],90))[1],[])

if __name__=='__main__':unittest.main()
