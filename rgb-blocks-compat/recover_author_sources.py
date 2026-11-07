#!/usr/bin/env python3
"""Recover author-published RGB Blocks 1.3.1 class-only sources on GitHub Actions.
Generated Java is a reconstruction for API porting, NOT replacement for the author's archives.
No art, assets or other authors' nested dependencies are committed to Git.
"""
import collections
import hashlib
import json
import os
import pathlib
import subprocess
import urllib.request
import zipfile

ROOT=pathlib.Path("rgb-blocks-compat/recovered")
CACHE=pathlib.Path("source-recovery-cache")
ROOT.mkdir(parents=True,exist_ok=True)
CACHE.mkdir(exist_ok=True)
HEADERS={"User-Agent":"RGBBlocks-1.3.1-owner-porting/1.0"}

def get(url):
    print("DOWNLOAD", url,flush=True)
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=120) as r:
        return r.read()

def find_upstream():
    variants=[("neoforge","https://mediafilez.forgecdn.net/files/8426/251/RgbBlocksmod-26.1.2-1.3.1.jar")]
    try:
        versions=json.loads(get("https://api.modrinth.com/v2/project/A48MxLWx/version"))
        fabrics=[v for v in versions if "fabric" in [x.lower() for x in v.get("loaders",[])] and ("1.3.1" in v.get("version_number","") or any("1.3.1F" in x.get("filename","") for x in v.get("files",[])))]
        if not fabrics:
            raise ValueError("No upstream 1.3.1 Fabric release in Modrinth metadata")
        # Most recently published exact branch; primary file is used.
        fabrics.sort(key=lambda v:v.get("date_published",""),reverse=True)
        v=fabrics[0]
        files=sorted(v["files"],key=lambda f:not f.get("primary",False))
        variants.append(("fabric",files[0]["url"]))
        print("FABRIC version metadata",v.get("version_number"),"file",files[0]["filename"])
    except Exception as ex:
        print("FABRIC SOURCE UNAVAILABLE",str(ex))
    return variants

vfurl="https://repo.maven.apache.org/maven2/org/vineflower/vineflower/1.12.0/vineflower-1.12.0.jar"
vf=CACHE/"vineflower.jar"
vf.write_bytes(get(vfurl))

manifest={}
for loader,url in find_upstream():
    data=get(url)
    upstream=CACHE/(loader+".jar")
    upstream.write_bytes(data)
    if not zipfile.is_zipfile(upstream):
        raise ValueError(f"Not a valid upstream Jar: {loader}")
    classes=CACHE/(loader+"-classes.jar")
    with zipfile.ZipFile(upstream) as src,zipfile.ZipFile(classes,"w",compression=zipfile.ZIP_DEFLATED) as dst:
        class_names=[n for n in src.namelist() if n.endswith(".class") and not n.startswith("META-INF/")]
        tops=collections.Counter(n.split("/")[0] for n in class_names)
        print(loader,"classes",len(class_names),"top-level packages",tops.most_common(20),flush=True)
        for name in class_names:
            dst.writestr(name,src.read(name))
    target=ROOT/loader
    target.mkdir(parents=True,exist_ok=True)
    cmd=["java","-Xmx3G","-jar",str(vf),"-dgs=1","-rsy=1",str(classes),str(target)]
    cp=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=900)
    print("DECOMPILE",loader,"return code",cp.returncode,"last output:\n",cp.stdout[-5000:],flush=True)
    files=sorted(target.rglob("*.java"))
    if not files:
        raise RuntimeError(f"No Java recovered from {loader}; decompiler return={cp.returncode}")
    pathlist=[str(p.relative_to(target)) for p in files]
    manifest[loader]={
        "upstream":url, "official_jar_sha256":hashlib.sha256(data).hexdigest(),
        "class_count":len(class_names),"java_count":len(files),"packages":tops.most_common(20),
        "java_files":pathlist,"decompiler_exit_code":cp.returncode,
        "note":"Decompiled reference; compare against original owner source; not compile-verified"
    }
    print(loader,"recovered JAVA",len(files),flush=True)
(ROOT/"recovery-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("=== FINAL RECOVERY ===",json.dumps({k:{"java_count":v["java_count"],"class_count":v["class_count"],"examples":v["java_files"][:40]} for k,v in manifest.items()},indent=2),flush=True)
