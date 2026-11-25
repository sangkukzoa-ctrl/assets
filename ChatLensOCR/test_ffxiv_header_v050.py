# -*- coding: utf-8 -*-
"""Synthetic-only tests for adaptive colored chat header geometry."""
import unittest
from PIL import Image, ImageDraw
from ffxiv_header_v050 import split_header, transcribe_header

def fixture(length=4, flower=True, scale=1):
    w,h=380,18
    im=Image.new("RGB",(w,h),(17,24,27))
    d=ImageDraw.Draw(im)
    for x in range(3,45,7):
        d.rectangle((x,4,x+3,14),fill=(220,220,220))
    def parens(x):
        d.rectangle((x,3,x+2,15),fill=(240,130,20))
        d.rectangle((x+6,3,x+8,15),fill=(240,130,20))
    parens(48)
    d.rectangle((60,3,70,14),fill=(220,75,100))
    d.rectangle((75,3,86,15),fill=(190,110,35))
    x=95
    for _ in range(length):
        d.rectangle((x,4,x+8,14),fill=(235,92,120))
        x+=13
    if flower:
        d.rectangle((x+1,3,x+10,15),fill=(140,90,240))
        x+=15
        for _ in range(3):
            d.rectangle((x,4,x+8,14),fill=(235,92,120))
            x+=13
    parens(x)
    for xx in range(x+17,min(w-6,x+115),13):
        d.rectangle((xx,3,xx+7,15),fill=(240,130,20))
    if scale!=1:
        im=im.resize((w*scale,h*scale),Image.Resampling.NEAREST)
    return im

class NoIcons:
    def match(self,*args):return "",None,0.

class Tests(unittest.TestCase):
    def test_variable_width(self):
        a=split_header(fixture(2));b=split_header(fixture(8))
        self.assertIsNotNone(a);self.assertIsNotNone(b)
        self.assertGreater(b.body[0],a.body[0]+60)
        self.assertEqual(a.name[0],b.name[0])
    def test_long_header_beyond_legacy_limit(self):
        g=split_header(fixture(10))
        self.assertIsNotNone(g);self.assertGreater(g.body[0],205)
    def test_no_separator(self):
        g=split_header(fixture(flower=False))
        self.assertIsNotNone(g);self.assertIsNone(g.server)
        self.assertIsNone(g.flower)
    def test_separator_not_text(self):
        g=split_header(fixture())
        self.assertIsNotNone(g.flower)
        self.assertLessEqual(g.name[1],g.flower[0])
        self.assertLessEqual(g.flower[1],g.server[0])
    def test_blank(self):
        self.assertIsNone(split_header(Image.new("RGB",(380,18),(20,20,20))))
    def test_body_only(self):
        im=Image.new("RGB",(380,18),(20,20,20))
        d=ImageDraw.Draw(im)
        for x in range(20,320,15):d.rectangle((x,3,x+7,15),fill=(240,130,20))
        self.assertIsNone(split_header(im))
    def test_missing_timestamp(self):
        im=fixture();ImageDraw.Draw(im).rectangle((0,0,45,17),fill=(20,20,20))
        self.assertIsNone(split_header(im))
    def test_semantics_literal_body(self):
        im=fixture();g=split_header(im)
        self.assertIsNotNone(g)
        reads={g.name:("Tester9",[],90),g.server:("SampleWorld",[],92),
               g.body:("<Title> Lv ?? ﾊ,,ﾊ",[],94),g.party:("4",[],85)}
        def read(im,x0,x1,lang):return reads[(x0,x1)]
        class Icon:
            def match(self,im,box):return "테스트직업",(1,1,im.width-1,im.height-1),.92
        text,meta,hit=transcribe_header(im,im,0,"한국어","Other",Icon(),read,g)
        self.assertEqual(text,"(테스트직업)Tester9&SampleWorld: <Title> Lv ?? ﾊ,,ﾊ")
        self.assertEqual(meta["party_marker"],"4")
        self.assertEqual(len(meta["semantic_regions"]),3)
        self.assertEqual(sum(x["kind"]=="job_icon" for x in meta["semantic_regions"]),1)
        self.assertEqual(meta["semantic_regions"][2]["value"],None)
        self.assertEqual(hit[0][0],g.job[0]+1)
    def test_app_entrypoint_adaptive_and_fallback(self):
        from unittest.mock import patch
        import pvp_v2
        im=fixture(8);g=split_header(im)
        reads={g.name:("Tester8",[],90),g.server:("World",[],92),
               g.body:("??",[],94),g.party:("C",[],85)}
        with patch.object(pvp_v2,"_read_zone",side_effect=lambda _,x0,x1,l:reads[(x0,x1)]), \
             patch.object(pvp_v2,"is_pvp_row",side_effect=AssertionError("fixed split used")):
            out=pvp_v2.transcribe(im,im,0,"한국어","",NoIcons())
            self.assertEqual(out[0],"(직업미확인)Tester8&World: ??")
        with patch.object(pvp_v2,"_read_zone",return_value=("Tester",[],1)), \
             patch.object(pvp_v2,"is_pvp_row",side_effect=AssertionError("fixed split used")):
            self.assertIsNone(pvp_v2.transcribe(im,im,0,"한국어","",NoIcons()))
        with patch.object(pvp_v2,"is_pvp_row",return_value=False) as old:
            self.assertIsNone(pvp_v2.transcribe(Image.new("RGB",(380,18)),im,0,"한국어","",NoIcons()))
            old.assert_called_once()
    def test_low_confidence_no_invention(self):
        im=fixture();g=split_header(im)
        self.assertIsNone(transcribe_header(im,im,0,"한국어","",NoIcons(),lambda *a:("Tester",[],1),g))
    def test_no_flower_does_not_guess_server(self):
        im=fixture(flower=False);g=split_header(im)
        reads={g.name:("Mixed Name9",[],90),g.body:("??",[],90),g.party:("?",[],90)}
        text,meta,hit=transcribe_header(im,im,0,"한국어","",NoIcons(),lambda _,x0,x1,l:reads[(x0,x1)],g)
        self.assertEqual(text,"(직업미확인)Mixed Name9: ??")
        self.assertEqual(meta["server"],"")
        self.assertIsNone(meta["party_marker"])
        self.assertIsNone(hit)

if __name__=="__main__":
    unittest.main()
