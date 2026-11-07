#!/usr/bin/env python3
"""Diagnose why 1.20.1 client emitted FileNotFoundException RGB item models.
Author published 1.3.1F resources are baseline; never silently drop assets.
"""
import collections,json,urllib.request,zipfile,io
URLS={
 "fabric_131":"https://cdn.modrinth.com/data/A48MxLWx/versions/HsQZbhRf/RgbBlocksmod-26.1.2-1.3.1F.jar",
 "neoforge_131":"https://mediafilez.forgecdn.net/files/8426/251/RgbBlocksmod-26.1.2-1.3.1.jar"
}
for source,url in URLS.items():
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"RGB-Blocks-1.3.1-Asset-Source-Audit"}),timeout=120) as r: data=r.read()
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   paths=set(z.namelist())
   colors=json.loads(z.read("assets/rgbblocks/palette.json"))
   selected=next(c for c in colors if c["red"]>180 and c["green"]<100 and c["blue"]<100)
   base="rgb_%s_%d_%d_%d"%(selected["group"],selected["red"],selected["green"],selected["blue"])
   print("SOURCE",source,"total zip entries",len(paths),"palette count",len(colors),"base",base,flush=True)
   for prefix in ["assets/rgbblocks/items/","assets/rgbblocks/models/item/","assets/rgbblocks/models/block/","assets/rgbblocks/blockstates/","assets/rgbblocks/textures/"]:
    x=sorted(k for k in paths if k.startswith(prefix))
    print("CATEGORY",prefix,"COUNT",len(x),"SAMPLES",x[:4],"END",x[-3:],flush=True)
   for v in [base,base+"_glow",base+"_glass"]:
    for prefix in ["assets/rgbblocks/items/","assets/rgbblocks/models/item/","assets/rgbblocks/models/block/","assets/rgbblocks/blockstates/"]:
     name=prefix+v+".json"
     print("LOOKUP",name,"PRESENT",name in paths)
     if name in paths:
      print("JSON",z.read(name).decode("utf-8")[:700].replace("\n"," "),flush=True)
   for key in ["assets/rgbblocks/items/rgb_purple_191_150_214_glow.json","assets/rgbblocks/models/item/rgb_purple_191_150_214_glow.json"]:
    print("SPECIFIC",key,key in paths,"CONTENT",z.read(key).decode()[:500] if key in paths else "")
 except Exception as e:print("SOURCE_ERROR",source,repr(e),flush=True)
