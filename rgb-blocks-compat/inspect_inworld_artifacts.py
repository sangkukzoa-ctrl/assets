#!/usr/bin/env python3
"""Inspect prior RGB Blocks in-world game log artifact archives."""
import os,urllib.request,zipfile,io
ids=[13565815748,13565551521]
url="https://api.github.com/repos/sangkukzoa-ctrl/assets/actions/artifacts"
headers={"Accept":"application/vnd.github+json","Authorization":"Bearer "+os.environ.get("GITHUB_TOKEN",""),"User-Agent":"RGBBlocks-Owner-InWorld-ProtocolDebug"}
for aid in ids:
 try:
  req=urllib.request.Request(f"{url}/{aid}/zip",headers=headers)
  with urllib.request.urlopen(req,timeout=150) as res:dat=res.read()
  print("===ARCHIVE",aid,len(dat),flush=True)
  with zipfile.ZipFile(io.BytesIO(dat)) as z:
   for filename in z.namelist():
    print("FILE",filename,z.getinfo(filename).file_size)
    if not filename.endswith(".log"):continue
    s=z.read(filename).decode("utf-8","replace")
    lines=s.splitlines()
    pats=("error","exception","failed","disconnect","connecting","join","packet","payload","mixin","unsupported","invalid","crash","openal","server thread")
    matched=[(i,line) for i,line in enumerate(lines) if any(k in line.lower() for k in pats)]
    print("====MATCHES",filename,"lines",len(lines),"matches",len(matched))
    for i,line in matched[-85:]:print("L",i,line[:950])
    print("====LAST 65")
    for line in lines[-65:]:print(line[:850])
 except Exception as exc:print("ARCHIVE_ERROR",aid,type(exc).__name__,str(exc))
