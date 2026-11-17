#!/usr/bin/env python3
"""Stage the actual owner's RGB Blocks 1.3.1 sources. NO released-mod download.

Default archive is a tiny, lossless, owner-provided canonical source bundle.
Generate it once from the actual supplied Fabric TAR and NeoForge ZIP.
Original Java remains the authority; 1.20.1/1.21.1 modifications are separate.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tarfile, tempfile, zipfile

HERE=Path("rgb-blocks-compat")
OUT=HERE/"owner-source"
CANONICAL_NAME="RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst"
FABRIC_NAME="RGB-Blocks-1.3.1-Fabric-26.1.2-full-source.tar"
NEO_CORE_NAME="RGB-Blocks-1.3.1-OWNER-JAVA-and-BUILD-SOURCES.zip"
EXPECTED_BUNDLE="1aea93f67e0375ecea72c86a5a72add5488d43d87a6b058dbce93128f250d007"
EXPECTED_FABRIC="ae5fffb7b37d7376f4e579491af878b7ed74fbe386b8691751e6d1c538bcb39c"
EXPECTED_NEO_CORE="420da2011167e9dac00b6404eba29043e9a342dd61c7c1fc4d4cd85662d64607"

def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):h.update(block)
    return h.hexdigest()

def write_file(root,relative,data):
    path=root/relative
    if path.is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Unexpected author source path "+relative)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)

def stage(fabric,neo_core,code_only=False):
    if hash_file(fabric)!=EXPECTED_FABRIC:
        raise RuntimeError("Wrong owner Fabric 1.3.1 source TAR fingerprint")
    if hash_file(neo_core)!=EXPECTED_NEO_CORE:
        raise RuntimeError("Wrong owner NeoForge source ZIP fingerprint")
    shutil.rmtree(OUT,ignore_errors=True)
    (OUT/"shared/resources").mkdir(parents=True)
    stat={"kind":"author-original-sources","fabric_java":0,"neo_java":0,
          "resources":0,"resources_extracted":not code_only,
          "owner_fabric_sha256":EXPECTED_FABRIC,
          "owner_neo_core_sha256":EXPECTED_NEO_CORE,
          "modrinth_original_download_count":0}
    with tarfile.open(fabric) as tf:
        for member in tf:
            if not member.isfile():continue
            name=member.name
            if "/src/main/resources/" in name:
                rel=name.split("/src/main/resources/",1)[1]
                stat["resources"]+=1
                if not code_only:
                    root=OUT/"fabric/resources" if rel in ("fabric.mod.json","rgbblocks.mixins.json") else OUT/"shared/resources"
                    write_file(root,rel,tf.extractfile(member).read())
            elif "/src/" in name and name.endswith(".java"):
                rel=name.split("/java/",1)[1]
                write_file(OUT/"fabric",rel,tf.extractfile(member).read())
                stat["fabric_java"]+=1
    with zipfile.ZipFile(neo_core) as z:
        for name in z.namelist():
            if name.startswith("neoforge/src/main/java/") and name.endswith(".java"):
                rel=name.split("neoforge/src/main/java/",1)[1]
                write_file(OUT/"neoforge",rel,z.read(name))
                stat["neo_java"]+=1
            elif name in (
                "neoforge/src/main/resources/META-INF/neoforge.mods.toml",
                "neoforge/src/main/resources/rgbblocks.mixins.json"):
                rel=name.split("neoforge/src/main/resources/",1)[1]
                write_file(OUT/"neoforge/resources",rel,z.read(name))
    if (stat["fabric_java"],stat["neo_java"],stat["resources"])!=(32,31,233629):
        raise RuntimeError("Owner source inventory mismatch "+str(stat))
    (OUT/"source-provenance.json").write_text(json.dumps(stat,indent=2),encoding="utf-8")
    print("RGB_PORT_ORIGINAL_OWNER_SOURCE_STAGED",json.dumps(stat),flush=True)

def main():
    archive=Path(os.environ.get("RGB_OWNER_SOURCE_COMPLETE",
                 str(HERE/"owner-archives"/CANONICAL_NAME)))
    if not archive.is_file():
        raise SystemExit("RGB BLOCKS AUTHOR SOURCE MISSING: "+str(archive)+
           ". Supply owner's original source bundle once. Public Modrinth JAR fallback is DISABLED.")
    if hash_file(archive)!=EXPECTED_BUNDLE:
        raise RuntimeError("Unrecognized author-supplied source archive SHA-256")
    with tempfile.TemporaryDirectory(prefix="rgb-owner-") as d:
        proc=subprocess.run(["tar","-I","zstd","-xf",str(archive.resolve()),"-C",d],
                            capture_output=True,text=True)
        if proc.returncode:
            raise RuntimeError("Cannot unpack owner source bundle: "+proc.stderr[-1500:])
        root=Path(d)
        stage(root/FABRIC_NAME,root/NEO_CORE_NAME,
              code_only=os.environ.get("RGB_OWNER_CODE_ONLY")=="1")

if __name__=="__main__":main()
