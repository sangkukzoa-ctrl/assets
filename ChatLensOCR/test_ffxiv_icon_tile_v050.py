# -*- coding: utf-8 -*-
"""Synthetic and bundled-asset tests only. No screenshot samples."""
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from PIL import Image
from ffxiv_icon_tile_v050 import match_tile
from ffxiv_header_v050 import split_header, transcribe_header
from test_ffxiv_header_v050 import fixture


def patterns():
    a=np.zeros((24,24),np.uint8)
    cv2.circle(a,(12,12),8,220,2)
    cv2.line(a,(5,5),(19,19),160,2)
    b=np.zeros_like(a)
    cv2.rectangle(b,(4,4),(19,19),200,2)
    cv2.line(b,(12,4),(12,19),120,2)
    return a,b


class Tests(unittest.TestCase):
    def test_equal_size(self):
        a,b=patterns()
        self.assertEqual(match_tile(Image.fromarray(a),[("Alpha",a),("Beta",b)])[:2],
                         ("Alpha",(0,0,24,24)))
    def test_embedded_tile(self):
        a,b=patterns()
        canvas=np.zeros((26,30),np.uint8)
        canvas[1:25,3:27]=a
        job,box,_=match_tile(Image.fromarray(canvas),[("Alpha",a),("Beta",b)])
        self.assertEqual(job,"Alpha")
        self.assertTrue(0<=box[0]<box[2]<=30 and 0<=box[1]<box[3]<=26)
    def test_ambiguous_jobs(self):
        a,_=patterns()
        self.assertEqual(match_tile(Image.fromarray(a),[("Alpha",a),("Beta",a)])[:2],("",None))
    def test_same_job_duplicate(self):
        a,b=patterns()
        self.assertEqual(match_tile(Image.fromarray(a),[("Alpha",a),("Alpha",a),("Beta",b)])[0],"Alpha")
    def test_blank_and_invalid(self):
        a,_=patterns()
        for im in (Image.new("L",(24,24)),Image.new("L",(5,5)),Image.new("L",(24,100))):
            self.assertEqual(match_tile(im,[("Alpha",a)])[:2],("",None))
    def test_production_method_and_coordinates(self):
        from app import Icons
        a,b=patterns()
        icons=Icons.__new__(Icons)
        icons.icons=[("Alpha",a),("Beta",b)]
        self.assertEqual(icons.match_tile(Image.fromarray(a))[0],"Alpha")
        im=fixture();geo=split_header(im)
        self.assertIsNotNone(geo)
        source=Image.new("RGB",(im.width,im.height+14))
        source.paste(im,(0,14))
        reads={geo.name:("TestName",[],90),geo.server:("TestWorld",[],90),
               geo.body:("<Title> Lv ??",[],90),geo.party:("4",[],90)}
        with patch.object(icons,"match_tile",return_value=("Alpha",(1,1,12,12),.95)) as bounded, \
             patch.object(icons,"match",side_effect=AssertionError("legacy search used")):
            output,meta,hit=transcribe_header(im,source,14,"한국어","",icons,
                lambda _,x,y,l:reads[(x,y)],geo)
        self.assertEqual(bounded.call_count,1)
        self.assertEqual(hit[0],(geo.job[0]+1,15,geo.job[0]+12,26))
        self.assertEqual(output,"(Alpha)TestName&TestWorld: <Title> Lv ??")
        self.assertEqual(sum(r["kind"]=="job_icon" for r in meta["semantic_regions"]),1)
    def test_viewer_nested_coordinates(self):
        from ffxiv_viewer_crop_v047 import restore_coordinates
        record={"box":(1,2,3,4),"left_box":(1,2,2,4),"right_box":(3,2,4,4),
                "name_box":(5,2,9,4),"body_box":(10,2,15,4),"server_box":None,
                "semantic_regions":[{"kind":"job_icon","box":(3,4,8,9)}],"y":2}
        result=restore_coordinates(("파판14","Test",[],[record],[],[]),(11,17,100,100))
        meta=result[3][0]
        self.assertEqual(meta["left_box"],(12,19,13,21))
        self.assertEqual(meta["right_box"],(14,19,15,21))
        self.assertEqual(meta["name_box"],(16,19,20,21))
        self.assertEqual(meta["body_box"],(21,19,26,21))
        self.assertIsNone(meta["server_box"])
        self.assertEqual(meta["semantic_regions"][0]["box"],(14,21,19,26))
        self.assertEqual(meta["y"],19)
        self.assertEqual(record["semantic_regions"][0]["box"],(3,4,8,9))


def bundled_assets_test():
    from app import Icons
    icons=Icons(allow_learning=False)
    official=[(job,img) for job,img in icons.icons if id(img) in icons.official_templates]
    assert len(official)>=40, len(official)
    wanted=("무도가","나이트","소환사")
    for job in wanted:
        refs=[img for name,img in official if name==job]
        assert refs,job
        # A real packaged reference rendered as a synthetic tile, not a
        # screenshot. This verifies resource loading and the matcher contract.
        raw=refs[0]
        tile=Image.fromarray(cv2.resize(raw,(24,24),interpolation=cv2.INTER_AREA if min(raw.shape)>24 else cv2.INTER_LINEAR))
        actual,box,score=match_tile(tile,official)
        assert actual==job and box is not None,(job,actual,score)
    print("Bundled job resource self-match: 3/3")


if __name__=="__main__":
    import sys
    if "--bundled-assets" in sys.argv:
        bundled_assets_test()
        sys.argv.remove("--bundled-assets")
    unittest.main()
