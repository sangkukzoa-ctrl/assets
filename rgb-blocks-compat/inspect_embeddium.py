#!/usr/bin/env python3
"""Read exact 1.20.1 Embeddium 0.3.31 rendering runtime class APIs.
No external mod JAR rehost; inspect official binary in short-lived CI only.
"""
import json,pathlib,subprocess,urllib.request,zipfile
h={"User-Agent":"RGBBlocksOwner-MC1201-Embeddium-API-Audit/1.0"}
url="https://api.modrinth.com/v2/version/UTbfe5d1"
with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=120) as r:
    metadata=json.load(r)
files=sorted(metadata["files"],key=lambda x:not x.get("primary",False))
f=next(x for x in files if x["filename"].endswith(".jar"))
p=pathlib.Path("embeddium-0.3.31-mc1201-temp.jar")
with urllib.request.urlopen(urllib.request.Request(f["url"],headers=h),timeout=200) as r:
    p.write_bytes(r.read())
print("Official Modrinth file",f["filename"],p.stat().st_size,"bytes",flush=True)
with zipfile.ZipFile(p) as z:
    names=[n for n in z.namelist() if n.endswith(".class")]
    targets=[n for n in names if any(key in n for key in (
        "/BlockRenderer.class","/ChunkBuilderMeshingTask.class","/MutableQuadViewImpl.class",
        "/AbstractBlockRenderContext.class","/QuadViewImpl.class","/VertexConsumerMixin.class"))]
    print("ALL MATCHED TARGETS",json.dumps(targets,indent=2))
    pkg=[x.split("/")[0] for x in names]
    print("ROOT NAMES",json.dumps({name:pkg.count(name) for name in set(pkg)},indent=2))
for classpath in targets:
    cls=classpath[:-6].replace("/",".")
    cp=subprocess.run(["javap","-classpath",str(p),"-p","-s",cls],text=True,capture_output=True)
    print("\n======= "+cls+" =======\n"+(cp.stdout or cp.stderr)[:20000],flush=True)
