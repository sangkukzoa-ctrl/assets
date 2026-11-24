#!/usr/bin/env python3
"""Stage the actual owner's RGB Blocks 1.3.1 sources. NO released-mod download.

Default archive is a tiny, lossless, owner-provided canonical source bundle.
Generate it once from the actual supplied Fabric TAR and NeoForge ZIP.
Original Java remains the authority; 1.20.1/1.21.1 modifications are separate.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tarfile, tempfile, zipfile, urllib.request, urllib.error

HERE=Path("rgb-blocks-compat")
OUT=HERE/"owner-source"
CANONICAL_NAME="RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst"
FABRIC_NAME="RGB-Blocks-1.3.1-Fabric-26.1.2-full-source.tar"
NEO_CORE_NAME="RGB-Blocks-1.3.1-OWNER-JAVA-and-BUILD-SOURCES.zip"
EXPECTED_BUNDLE="1aea93f67e0375ecea72c86a5a72add5488d43d87a6b058dbce93128f250d007"
EXPECTED_FABRIC="ae5fffb7b37d7376f4e579491af878b7ed74fbe386b8691751e6d1c538bcb39c"
EXPECTED_NEO_CORE="420da2011167e9dac00b6404eba29043e9a342dd61c7c1fc4d4cd85662d64607"
NEO_RAW_NAME="RGB-Blocks-1.3.1-NeoForge-26.1.2-full-source.zip"
EXPECTED_NEO_RAW="f267b09141811f3eeb64e8247fff1d08ed2e11fdbea6c5b165f52b93e31607e1"

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

# Stable hashes of high-impact original files from the user-provided
# archives. A previously written provenance JSON alone is NOT a valid cache.
SOURCE_SENTINELS={
    "fabric/com/rgbblocks/runtime/RGBRuntime.java":"06906da29ece71a9b4d80ee256b216a72f9cd3067e573e2f7586a0d1b3eff40c",
    "fabric/com/rgbblocks/client/lighting/RGBRealLightEngine.java":"65415885e0ba47617cc505f69e10733cbe8e353f60ec5fc0c8113b5327bb537d",
    "neoforge/com/rgbblocks/RgbBlocksMod.java":"ae258c25762366a2b5701e7d6689ce2873f50a80904ac82afb24455fd080ec17",
    "fabric/resources/rgbblocks.mixins.json":"d4b9458c82c81ae034be51fba7469b4caf25aeb875c91b47465c954e3c2aecc8",
    "fabric/resources/rgbblocks.client.mixins.json":"8f5a2e90836cce588e4fe1ffe4c703414ec0ae12fe80f6128413c0cf50664b8e",
    "fabric/resources/fabric.mod.json":"cd2df4c3bffc0b59c08c676d70e46c4e105ad0fc63f2497b8eadd35d3cc6c073",
    "neoforge/resources/rgbblocks.mixins.json":"e941bbf54eb1772263ee2a00ddfc6a8dc6645f0a01c19d406bbecdce45ea9ebd",
}
RESOURCE_SENTINELS={
    "shared/resources/assets/rgbblocks/palette.json":"e94c52deb1cf167c9633ae7477bc8e3e91e112531805175427dba8013c241dde",
    "shared/resources/assets/rgbblocks/lang/en_us.json":"99195086f03946134829b8d54e35a96952edf19c2f64953c50fea968f02390b3",
}
# Complete author Java manifest digests — derived from ALL 63 original
# source files, sorted by path, not just a few sample classes. This allows
# full offline verification without publishing the author's source on GitHub.
EXPECTED_JAVA_TREES={
    "fabric":(32,"ce55ca98211dedd548d5300fe42508b6480ca6f5a4a2a882d01dbc1e825608a1"),
    "neoforge":(31,"7d81b077f858fd325b30d9d57f2176b9def7c5fa6765d1c50b48babd0ac652a1"),
}
def owner_java_tree_hash(loader):
    root=OUT/loader
    files=sorted((root/"com").rglob("*.java"),
                 key=lambda p:p.relative_to(root).as_posix())
    h=hashlib.sha256()
    for file in files:
        relative=file.relative_to(root).as_posix()
        h.update((relative+"\t"+hash_file(file)+"\n").encode("utf-8"))
    return len(files),h.hexdigest()

def verify_owner_resource_samples():
    # 233k tiny files can take minutes to SHA-hash on GitHub Actions.
    # Instead, the entire original 455MB author archive is SHA-256 pinned
    # BEFORE extraction. For cache reuse, prove 42 deterministic content
    # samples from five independent resource families and both index files.
    lock=HERE/"owner-resource-sentinels.json"
    manifest=json.loads(lock.read_text(encoding="utf-8"))
    if manifest.get("source_archive_sha256")!=EXPECTED_FABRIC:
        raise RuntimeError("Resource sample list is for another author source")
    samples=manifest.get("samples")
    if not isinstance(samples,dict) or len(samples)!=42:
        raise RuntimeError("Owner resource sentinel manifest must have 42 hashes")
    root=OUT/"shared/resources"
    for relative,digest in samples.items():
        rel=Path(relative)
        if rel.is_absolute() or ".." in rel.parts or len(digest)!=64:
            raise RuntimeError("Invalid original resource sentinel: "+relative)
        file=root/rel
        if not file.is_file() or hash_file(file)!=digest:
            return False
    return True

def verified_stage_cache(code_only):
    """Provenance + exact source hashes + file counts, never JSON trust alone."""
    for relative,digest in SOURCE_SENTINELS.items():
        actual=OUT/relative
        if not actual.is_file() or hash_file(actual)!=digest:return False
    for loader,expected in EXPECTED_JAVA_TREES.items():
        if owner_java_tree_hash(loader)!=expected:return False
    if not code_only:
        for relative,digest in RESOURCE_SENTINELS.items():
            actual=OUT/relative
            if not actual.is_file() or hash_file(actual)!=digest:return False
        if sum(p.is_file() for p in (OUT/"shared/resources").rglob("*"))!=233627:
            return False
        if not verify_owner_resource_samples():
            return False
    return True

def stage(fabric,neo_core,code_only=False):
    if hash_file(fabric)!=EXPECTED_FABRIC:
        raise RuntimeError("Wrong owner Fabric 1.3.1 source TAR fingerprint")
    neo_digest=hash_file(neo_core)
    if neo_digest not in (EXPECTED_NEO_CORE,EXPECTED_NEO_RAW):
        raise RuntimeError("Wrong owner NeoForge source ZIP fingerprint")
    # Hundreds of thousands of tiny assets take much longer than hashing
    # their original compressed source. Keep a checked, resumable extraction
    # checkpoint. Never accept a tree sourced from different archive hashes.
    wanted={"owner_fabric_sha256":EXPECTED_FABRIC,
            "owner_neo_core_sha256":neo_digest}
    provenance=OUT/"source-provenance.json"
    if provenance.is_file():
        existing=json.loads(provenance.read_text(encoding="utf-8"))
        if (all(existing.get(k)==v for k,v in wanted.items())
            and existing.get("fabric_java")==32 and existing.get("neo_java")==31
            and existing.get("resources")==233629
            and (code_only or existing.get("resources_extracted"))
            and verified_stage_cache(code_only)):
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
        # Same-length corruption is real (including interrupted writes);
        # compare original bytes, never merely the length.
        if target.is_file() and target.stat().st_size==len(data) and target.read_bytes()==data:
            reused+=1
        else:
            write_file(root,rel,data)
    stat={"kind":"author-original-sources","fabric_java":0,"neo_java":0,
          "resources":0,"resources_extracted":not code_only,
          "owner_fabric_sha256":EXPECTED_FABRIC,
          "owner_neo_core_sha256":neo_digest,
          "modrinth_original_download_count":0}
    with tarfile.open(fabric) as tf:
        for member in tf:
            if not member.isfile():continue
            name=member.name
            if "/src/client/resources/" in name:
                rel=name.split("/src/client/resources/",1)[1]
                # Client mixin metadata is small and required by the
                # source-only integrity gate as well as the full build.
                put_cached(OUT/"fabric/resources",rel,tf.extractfile(member).read())
            elif "/src/main/resources/" in name:
                rel=name.split("/src/main/resources/",1)[1]
                stat["resources"]+=1
                if not code_only or rel in ("fabric.mod.json","rgbblocks.mixins.json"):
                    root=OUT/"fabric/resources" if rel in ("fabric.mod.json","rgbblocks.mixins.json") else OUT/"shared/resources"
                    put_cached(root,rel,tf.extractfile(member).read())
            elif "/src/" in name and name.endswith(".java"):
                rel=name.split("/java/",1)[1]
                put_cached(OUT/"fabric",rel,tf.extractfile(member).read())
                stat["fabric_java"]+=1
    with zipfile.ZipFile(neo_core) as z:
        stage_neo_java(z,put_cached,stat)
    if (stat["fabric_java"],stat["neo_java"],stat["resources"])!=(32,31,233629):
        raise RuntimeError("Owner source inventory mismatch "+str(stat))
    stat["owner_java_trees"]={
        loader:{"java_count":count,"sha256":digest}
        for loader,(count,digest) in EXPECTED_JAVA_TREES.items()
    }
    stat["reused_existing_files"]=reused
    if not verified_stage_cache(code_only):
        raise RuntimeError("Author-original staged file bytes or inventory failed integrity gate")
    # Write only on COMPLETE extraction. An interrupted job retains its
    # marker and resumes missing assets without discarding previous work.
    (OUT/"source-provenance.json").write_text(json.dumps(stat,indent=2),encoding="utf-8")
    marker.unlink(missing_ok=True)
    print("RGB_PORT_ORIGINAL_OWNER_SOURCE_STAGED",json.dumps(stat),flush=True)

def stage_neo_java(z,put_cached,stat):
    # Both the canonical core archive and the original full project ZIP
    # are accepted ONLY after their independent pinned binary SHA check.
    # Discover the unique original project root, not a generated build dir.
    names=z.namelist()
    suffix="src/main/java/com/rgbblocks/RgbBlocksMod.java"
    roots=[name[:-len(suffix)] for name in names
           if name.endswith(suffix) and
           (name==suffix or name[-len(suffix)-1]=="/")]
    if len(roots)!=1:
        raise RuntimeError("Expected one owner NeoForge project root")
    prefix=roots[0]
    java=prefix+"src/main/java/"
    res=prefix+"src/main/resources/"
    selected=set()
    for name in names:
        if name.startswith(java) and name.endswith(".java"):
            rel=name[len(java):]
            root=OUT/"neoforge"
            stat["neo_java"]+=1
        elif name in (res+"META-INF/neoforge.mods.toml",
                      res+"rgbblocks.mixins.json"):
            rel=name[len(res):]
            root=OUT/"neoforge/resources"
        else:
            continue
        if (root,rel) in selected:
            raise RuntimeError("Duplicate original NeoForge source entry")
        selected.add((root,rel))
        put_cached(root,rel,z.read(name))

def private_owner_source_release(archive,raw_paths=None):
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
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as response:
            release=json.load(response)
    except urllib.error.HTTPError as error:
        if error.code!=404:
            raise
        # GitHub does not always resolve unpublished draft releases through
        # GET /releases/tags/<tag>. Authenticated list-releases DOES include
        # draft releases, so locate the exact author-only tag there instead.
        release=None
        for page in range(1,6):
            lookup=("https://api.github.com/repos/"+repository+
                    "/releases?per_page=100&page="+str(page))
            with urllib.request.urlopen(urllib.request.Request(lookup,headers=headers),
                                        timeout=45) as response:
                listed=json.load(response)
            found=[item for item in listed if item.get("tag_name")==tag]
            if len(found)>1:
                raise RuntimeError("Duplicate author source release tag")
            if found:
                release=found[0]
                break
            if len(listed)<100:
                break
        if release is None:
            raise RuntimeError("Owner original source draft Release not provisioned: "+tag)
    if release.get("tag_name")!=tag:
        raise RuntimeError("Wrong author source release tag")
    if not release.get("draft"):
        raise RuntimeError("The author-source GitHub Release MUST remain a private DRAFT")
    assets=release.get("assets",[])
    def matches(name):
        return [asset for asset in assets if asset.get("name")==name]
    def download(name,destination,expected):
        files=matches(name)
        if len(files)!=1:
            raise RuntimeError("Owner source draft release missing or duplicate asset: "+name)
        url="https://api.github.com/repos/"+repository+"/releases/assets/"+str(files[0]["id"])
        binary_headers={**headers,"Accept":"application/octet-stream"}
        destination.parent.mkdir(parents=True,exist_ok=True)
        temp=destination.with_name(destination.name+".partial")
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=binary_headers),timeout=300) as response:
                with temp.open("wb") as out:
                    shutil.copyfileobj(response,out)
            if hash_file(temp)!=expected:
                raise RuntimeError("Private owner source release SHA-256 mismatch; refuse corrupted/stale data")
            os.replace(temp,destination)
        finally:
            temp.unlink(missing_ok=True)
    if matches(CANONICAL_NAME):
        download(CANONICAL_NAME,archive,EXPECTED_BUNDLE)
        print("RGB_OWNER_SOURCE_PRIVATE_GITHUB_DRAFT_VERIFIED",archive,flush=True)
        return True
    if raw_paths is None:
        raise RuntimeError("Owner source draft release missing exact canonical archive")
    # Original pair transport is equally strict, with exact original SHA
    # locks. Reject missing/duplicate pair before downloading either file.
    if any(len(matches(name))!=1 for name in (FABRIC_NAME,NEO_RAW_NAME)):
        raise RuntimeError("Owner source draft release missing exact original archive pair")
    fabric,neo=raw_paths
    download(FABRIC_NAME,fabric,EXPECTED_FABRIC)
    download(NEO_RAW_NAME,neo,EXPECTED_NEO_RAW)
    print("RGB_OWNER_SOURCE_PRIVATE_ORIGINAL_PAIR_VERIFIED",flush=True)
    return "raw_pair"

def main():
    archive=Path(os.environ.get("RGB_OWNER_SOURCE_COMPLETE",
                 str(HERE/"owner-archives"/CANONICAL_NAME)))
    code_only=os.environ.get("RGB_OWNER_CODE_ONLY")=="1"
    local_fabric=os.environ.get("RGB_OWNER_FABRIC_TAR")
    local_neo=os.environ.get("RGB_OWNER_NEOFORGE_ZIP")
    if local_fabric or local_neo:
        if not local_fabric or not local_neo:
            raise RuntimeError("Set BOTH RGB_OWNER_FABRIC_TAR and RGB_OWNER_NEOFORGE_ZIP")
        stage(Path(local_fabric),Path(local_neo),code_only=code_only)
        return
    if not archive.is_file():
        raw=(archive.parent/FABRIC_NAME,archive.parent/NEO_RAW_NAME)
        mode=private_owner_source_release(archive,raw_paths=raw)
        if mode=="raw_pair":
            stage(*raw,code_only=code_only)
            return
        if not mode:
            raise SystemExit("RGB BLOCKS AUTHOR SOURCE MISSING: "+str(archive)+
               ". Provision the private draft source or set BOTH RGB_OWNER_FABRIC_TAR "
               "and RGB_OWNER_NEOFORGE_ZIP. Public RGB Blocks JAR fallback is DISABLED.")
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
