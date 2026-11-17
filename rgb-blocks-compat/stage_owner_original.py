#!/usr/bin/env python3
"""Stage the actual owner's RGB Blocks 1.3.1 sources. NO released-mod download.

Default archive is a tiny, lossless, owner-provided canonical source bundle.
Generate it once from the actual supplied Fabric TAR and NeoForge ZIP.
Original Java remains the authority; 1.20.1/1.21.1 modifications are separate.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tarfile, tempfile, zipfile, urllib.request

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
    # Hundreds of thousands of tiny assets take much longer than hashing
    # their original compressed source. Keep a checked, resumable extraction
    # checkpoint. Never accept a tree sourced from different archive hashes.
    wanted={"owner_fabric_sha256":EXPECTED_FABRIC,
            "owner_neo_core_sha256":EXPECTED_NEO_CORE}
    provenance=OUT/"source-provenance.json"
    if provenance.is_file():
        existing=json.loads(provenance.read_text(encoding="utf-8"))
        if (all(existing.get(k)==v for k,v in wanted.items())
            and existing.get("fabric_java")==32 and existing.get("neo_java")==31
            and existing.get("resources")==233629
            and (code_only or existing.get("resources_extracted"))):
            print("RGB_PORT_ORIGINAL_OWNER_SOURCE_CACHE_HIT",str(provenance),flush=True)
            return
    marker=OUT/".source-stage-in-progress.json"
    if marker.is_file() and json.loads(marker.read_text(encoding="utf-8"))==wanted:
        print("RGB_PORT_ORIGINAL_OWNER_SOURCE_RESUME",str(OUT),flush=True)
    else:
        shutil.rmtree(OUT,ignore_errors=True)
    (OUT/"shared/resources").mkdir(parents=True,exist_ok=True)
    marker.write_text(json.dumps(wanted,indent=2),encoding="utf-8")
    reused=0
    def put_cached(root,rel,data):
        nonlocal reused
        target=root/rel
        # The original archive SHA was validated and the marker binds this
        # interrupted tree to these EXACT two original author archives.
        if target.is_file() and target.stat().st_size==len(data):
            reused+=1
        else:
            write_file(root,rel,data)
    stat={"kind":"author-original-sources","fabric_java":0,"neo_java":0,
          "resources":0,"resources_extracted":not code_only,
          "owner_fabric_sha256":EXPECTED_FABRIC,
          "owner_neo_core_sha256":EXPECTED_NEO_CORE,
          "modrinth_original_download_count":0}
    with tarfile.open(fabric) as tf:
        for member in tf:
            if not member.isfile():continue
            name=member.name
            if "/src/client/resources/" in name:
                rel=name.split("/src/client/resources/",1)[1]
                if not code_only:
                    put_cached(OUT/"fabric/resources",rel,tf.extractfile(member).read())
            elif "/src/main/resources/" in name:
                rel=name.split("/src/main/resources/",1)[1]
                stat["resources"]+=1
                if not code_only:
                    root=OUT/"fabric/resources" if rel in ("fabric.mod.json","rgbblocks.mixins.json") else OUT/"shared/resources"
                    put_cached(root,rel,tf.extractfile(member).read())
            elif "/src/" in name and name.endswith(".java"):
                rel=name.split("/java/",1)[1]
                put_cached(OUT/"fabric",rel,tf.extractfile(member).read())
                stat["fabric_java"]+=1
    with zipfile.ZipFile(neo_core) as z:
        for name in z.namelist():
            if name.startswith("neoforge/src/main/java/") and name.endswith(".java"):
                rel=name.split("neoforge/src/main/java/",1)[1]
                put_cached(OUT/"neoforge",rel,z.read(name))
                stat["neo_java"]+=1
            elif name in (
                "neoforge/src/main/resources/META-INF/neoforge.mods.toml",
                "neoforge/src/main/resources/rgbblocks.mixins.json"):
                rel=name.split("neoforge/src/main/resources/",1)[1]
                put_cached(OUT/"neoforge/resources",rel,z.read(name))
    if (stat["fabric_java"],stat["neo_java"],stat["resources"])!=(32,31,233629):
        raise RuntimeError("Owner source inventory mismatch "+str(stat))
    stat["reused_existing_files"]=reused
    # Write only on COMPLETE extraction. An interrupted job retains its
    # marker and resumes missing assets without discarding previous work.
    (OUT/"source-provenance.json").write_text(json.dumps(stat,indent=2),encoding="utf-8")
    marker.unlink(missing_ok=True)
    print("RGB_PORT_ORIGINAL_OWNER_SOURCE_STAGED",json.dumps(stat),flush=True)

def private_owner_source_release(archive):
    """Optional private draft GitHub Release storage for owner's input JAR-free source.

    Runs ONLY when owner explicitly provisioned a draft release, AND a
    readable repo token was injected. Public Modrinth/CurseForge is never
    accessed. A SHA-256 mismatch aborts instead of trying public fallback.
    """
    tag=os.environ.get("RGB_OWNER_SOURCE_RELEASE_TAG","").strip()
    if not tag:
        return False
    token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Author source release configured but GitHub token not passed")
    from urllib.parse import quote
    repository=os.environ.get("GITHUB_REPOSITORY","sangkukzoa-ctrl/assets")
    if repository!="sangkukzoa-ctrl/assets":
        raise RuntimeError("Refusing owner archive from unexpected GitHub repository")
    headers={"Authorization":"Bearer "+token,
             "Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28",
             "User-Agent":"RGBBlocks-original-source-131-private-CI"}
    url=("https://api.github.com/repos/"+repository+"/releases/tags/"+quote(tag,safe=""))
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as response:
        release=json.load(response)
    if not release.get("draft"):
        raise RuntimeError("The author-source GitHub Release MUST remain a private DRAFT")
    files=[asset for asset in release.get("assets",[]) if asset.get("name")==CANONICAL_NAME]
    if len(files)!=1:
        raise RuntimeError("Owner source draft release missing exact canonical archive")
    url="https://api.github.com/repos/"+repository+"/releases/assets/"+str(files[0]["id"])
    binary_headers={**headers,"Accept":"application/octet-stream"}
    archive.parent.mkdir(parents=True,exist_ok=True)
    temp=archive.with_name(archive.name+".partial")
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=binary_headers),timeout=120) as response:
            with temp.open("wb") as out:
                shutil.copyfileobj(response,out)
        if hash_file(temp)!=EXPECTED_BUNDLE:
            raise RuntimeError("Private owner source release SHA-256 mismatch; refuse corrupted/stale data")
        os.replace(temp,archive)
    finally:
        temp.unlink(missing_ok=True)
    print("RGB_OWNER_SOURCE_PRIVATE_GITHUB_DRAFT_VERIFIED",archive,flush=True)
    return True

def main():
    archive=Path(os.environ.get("RGB_OWNER_SOURCE_COMPLETE",
                 str(HERE/"owner-archives"/CANONICAL_NAME)))
    if not archive.is_file() and not private_owner_source_release(archive):
        raise SystemExit("RGB BLOCKS AUTHOR SOURCE MISSING: "+str(archive)+
           ". Provision the author's private draft GitHub Release or pass "
           "RGB_OWNER_SOURCE_COMPLETE. Public RGB Blocks JAR fallback is DISABLED.")
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
