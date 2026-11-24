#!/usr/bin/env python3
"""Owner-only unpublished draft handoff. Never publish a release or upload binaries to public Actions artifacts."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,zipfile,urllib.parse
mode,target=sys.argv[1:]
assert mode in ("stage","download","verified") and target in ("forge1201","neoforge1211")
repo=os.environ["GITHUB_REPOSITORY"]
assert repo=="sangkukzoa-ctrl/assets"
run=os.environ["GITHUB_RUN_ID"];attempt=os.environ["GITHUB_RUN_ATTEMPT"];commit=os.environ["GITHUB_SHA"]
tag=f"rgbblocks-131-native-handoff-{target}-{run}-{attempt}"
api=f"https://api.github.com/repos/{repo}"
token=os.environ["GH_TOKEN"]
def curl(url,*args):
    # Do not echo the token; curl does not forward Authorization to redirect hosts.
    result=subprocess.run(["curl","--fail","--silent","--show-error","--location",
      "--header","Authorization: Bearer "+token,"--header","X-GitHub-Api-Version: 2022-11-28",
      *args,url],check=True,stdout=subprocess.PIPE)
    return result.stdout
def sha(path):
    with path.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def lookup():
    matches=[]
    for page in range(1,31):
        releases=json.loads(curl(api+f"/releases?per_page=100&page={page}"))
        assert isinstance(releases,list)
        matches.extend(r for r in releases if r["tag_name"]==tag)
        if len(releases)<100:break
    assert len(matches)==1,("exact unpublished handoff draft required",tag,len(matches))
    r=matches[0]
    assert r["draft"] is True and r["published_at"] is None and r["target_commitish"]==commit
    return r
def upload(path):
    r=lookup()
    assert not any(a["name"]==path.name for a in r["assets"]),("refuse duplicate handoff asset",path.name)
    url=r["upload_url"].split("{",1)[0]+"?"+urllib.parse.urlencode({"name":path.name})
    assert url.startswith("https://uploads.github.com/repos/"+repo+"/releases/")
    asset=json.loads(curl(url,"--request","POST","--header","Content-Type: application/octet-stream",
        "--data-binary","@"+str(path.resolve())))
    assert asset["name"]==path.name and asset["size"]==path.stat().st_size and asset["state"]=="uploaded"
    if asset.get("digest"):assert asset["digest"]=="sha256:"+sha(path)
    print("PRIVATE_DRAFT_ASSET",path.name,asset["size"],sha(path),flush=True)
def download(name,dest):
    r=lookup()
    items=[a for a in r["assets"] if a["name"]==name and a["state"]=="uploaded"]
    assert len(items)==1,(tag,name)
    dest.parent.mkdir(parents=True,exist_ok=True)
    curl(api+"/releases/assets/"+str(items[0]["id"]),
        "--header","Accept: application/octet-stream","--output",str(dest))
    assert dest.stat().st_size==items[0]["size"],name
    if items[0].get("digest"):assert items[0]["digest"]=="sha256:"+sha(dest)
if mode=="stage":
    stage=Path("release-stage")/target
    manifest=json.loads((stage/"MANIFEST.json").read_text())
    assert manifest["source_commit"]==commit and str(manifest["build_actions_run"])==run
    for name,digest in manifest["release_files_sha256"].items():assert sha(stage/name)==digest
    candidate=Path(f"RGBBlocks-1.3.1-{target}-JAR-SOURCE-MRPACK.zip")
    with zipfile.ZipFile(candidate,"w",zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
        for p in sorted(stage.iterdir()):
            assert p.is_file()
            z.write(p,p.name)
    with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
    servers=list(Path("windows-ready").glob("*WINDOWS-READY-SERVER.zip"))
    assert len(servers)==1
    server=servers[0]
    sums=Path(f"HANDOFF-{target}-SHA256SUMS.txt")
    sums.write_text(f"{sha(candidate)}  {candidate.name}\n{sha(server)}  {server.name}\n",encoding="ascii")
    body={"tag_name":tag,"target_commitish":commit,"name":"UNPUBLISHED RGB Blocks 1.3.1 "+target+" owner handoff "+run,
          "draft":True,"prerelease":True,
          "body":"Private-to-repository-write-access draft. NOT a published release. Windows verification is pending until WINDOWS-VERIFIED.json is attached. Source commit: "+commit}
    created=json.loads(curl(api+"/releases","--request","POST","--header","Content-Type: application/json","--data-binary",json.dumps(body)))
    assert created["draft"] is True and created["published_at"] is None
    for p in (candidate,server,sums):upload(p)
    print("PRIVATE_HANDOFF_DRAFT",created["html_url"],flush=True)
elif mode=="download":
    folder=Path("input")/target
    sums=folder/f"HANDOFF-{target}-SHA256SUMS.txt"
    download(sums.name,sums)
    entries=[line.split("  ",1) for line in sums.read_text().splitlines()]
    assert len(entries)==2
    selected=[(digest,name) for digest,name in entries if name.endswith("-WINDOWS-READY-SERVER.zip")]
    assert len(selected)==1
    digest,name=selected[0]
    assert Path(name).name==name and len(digest)==64
    dest=folder/name
    download(name,dest)
    assert sha(dest)==digest
    with open(os.environ["GITHUB_ENV"],"a",encoding="utf-8") as f:f.write("RGB_EXPECTED_WINDOWS_SHA256="+digest+"\n")
    print("PRIVATE_WINDOWS_DOWNLOAD_SHA_PASS",name,digest,flush=True)
else:
    result=Path("windows-smoke")/target/"result.json"
    r=json.loads(result.read_text())
    assert all(r[k] for k in ("first_start","rgb_palette","rgb_commands","normal_glow_glass_block_created","same_world_reopen","persistent_blocks"))
    assert r["source_commit"]==commit and r["server_zip_sha256"]==os.environ["RGB_EXPECTED_WINDOWS_SHA256"]
    r["windows_verified_actions_run"]=run
    r["draft_only"]=True
    proof=Path("WINDOWS-VERIFIED.json")
    proof.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    upload(proof)
    print("PRIVATE_HANDOFF_WINDOWS_VERIFIED",lookup()["html_url"],flush=True)
