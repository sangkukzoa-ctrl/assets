# -*- coding: utf-8 -*-
"""v0.4.15 synthetic-only single-item detail vs catalog layout regression.

No private photograph, product name, price, chat text or user identifier
is included in this public test.
"""
from PIL import Image,ImageDraw,ImageFont
from product_detail_v0415 import detail_evidence,is_single_product_detail
from shop_grid_v0374 import analyze,_synthetic as catalog_synthetic

font=ImageFont.truetype("C:/Windows/Fonts/malgun.ttf",24)
im=Image.new("RGB",(1353,546),"white")
d=ImageDraw.Draw(im)
d.rectangle((0,30,600,400),fill=(236,236,236))
d.rectangle((30,165,570,220),fill=(55,60,67))
for i in range(5):
    x=3+i*133
    d.rectangle((x,458,x+123,540),outline=(190,190,190),width=2)
    d.rectangle((x+24,490,x+105,510),fill=(53,56,65))
    d.rectangle((x+60,500,x+85,535),fill=(22,29,32))
for y,word in ((33,"PRODUCT TITLE"),(116,"Item description"),
               (197,"PRICE 45.00"),(284,"Options"),
               (380,"Add to cart")):
    d.text((700,y),word,font=font,fill=(44,44,44))

evidence=detail_evidence(im)
assert evidence is not None,evidence
assert evidence["gallery_border_count"]>=5
observations=[]
def sample_reader(crop,language,precise):
    observations.append(crop.size)
    return "PRODUCT TITLE\nPRICE $45.00",[
       {"text":"PRODUCT TITLE","box":(10,20,180,45),"score":.95},
       {"text":"PRICE $45.00","box":(10,200,170,226),"score":.97}
    ],.96

result=analyze(im,reader=sample_reader)
assert result is not None
mode,output,unused,meta,items=result
assert mode=="쇼핑몰" and output=="PRODUCT TITLE\nPRICE $45.00"
assert "[상품 02]" not in output
assert meta[0]["type"]=="product_detail" and meta[0]["product_count"]==1
assert meta[0]["human_verified"] is False
assert len(items)==2 and items[0]["box"][0]>im.width//2
assert observations and observations[0][0]<im.width*.52,observations

# Product-detail OCR may be completely blank: pixel geometry must still
# prevent the five gallery thumbnails from becoming five fake products.
# The catalog fallback is forbidden once the single-product layout is known.
from unittest.mock import patch
with patch("shop_grid_v0374.card_boxes",
           side_effect=AssertionError("gallery incorrectly parsed as catalog")):
    blank=analyze(im,reader=lambda *args:("",[],0))
assert blank is not None
blank_mode,blank_text,_,blank_meta,blank_items=blank
assert blank_mode=="쇼핑몰" and blank_text=="" and blank_items==[]
assert blank_meta[0]["product_count"]==1
assert blank_meta[0]["needs_review"] is True
assert blank_meta[0]["reason"]=="detail_text_unreadable"

# OCR cannot fabricate a product count if the evidence is insufficient.
no_gallery=im.crop((0,0,im.width,455))
assert not is_single_product_detail(no_gallery)
assert analyze(no_gallery,reader=lambda *args:("",[],0)) is None
# Switching to explicitly forced catalog mode must remain functional.
assert catalog_synthetic()
print("v0.4.15 single product detail/gallery vs catalog; "
      "exact price/text, layout metadata and region offset PASS")
