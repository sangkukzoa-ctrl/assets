#!/usr/bin/env python3
"""Create Modrinth-compatible complete test profiles for RGB Blocks 1.3.1 ports.
RGBBlocks itself is a user-owned generated JAR inside overrides/mods.
All third-party mod and shader content is obtained from official release
hosts through SHA-512 verified URL pointers. Never repack/rehost their JARs.
"""
import hashlib,json,pathlib,sys,urllib.parse,urllib.request,zipfile
PROFILE=sys.argv[1] if len(sys.argv)>1 else "fabric1211"
if PROFILE not in ("fabric1211","neoforge1211","forge1201"):raise ValueError("expected fabric1211, neoforge1211 or forge1201")
cfg={
 "fabric1211":{"mc":"1.21.1","loader":"fabric-loader","loaderver":"0.19.5",
    "build":"port-work/mc1211-fabric/build/libs",
    "mods":[("fabric-api","0.116.17+1.21.1","fabric","both"),
            ("sodium","0.6.13","fabric","client"),
            ("iris","1.8.8","fabric","client")],
    "cnb":("chisels-and-bits-fabric-21.1.40.jar","https://mediafilez.forgecdn.net/files/9455/172/chisels-and-bits-fabric-21.1.40.jar")},
 "neoforge1211":{"mc":"1.21.1","loader":"neoforge","loaderver":"21.1.265",
    "build":"port-work/mc1211-neoforge/build/libs",
    "mods":[("sodium","mc1.21.1-0.6.13-neoforge","neoforge","client"),
            ("iris","1.8.12+1.21.1-neoforge","neoforge","client")],
    "cnb":("chisels-and-bits-neoforge-21.1.32.jar","https://mediafilez.forgecdn.net/files/7405/270/chisels-and-bits-neoforge-21.1.32.jar")},
 "forge1201":{"mc":"1.20.1","loader":"forge","loaderver":"47.4.28",
    "build":"port-work/mc1201-forge/build/libs",
    "mods":[("embeddium","0.3.31","forge","client"),
            ("oculus","1.8.0","forge","client")],
    "cnb":("chisels-and-bits-forge-20.1.20.jar","https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar")},
}[PROFILE]
mc=cfg["mc"]
BUILD=pathlib.Path(cfg["build"])
JARS=[p for p in BUILD.glob("*.jar") if "-sources" not in p.name and "-dev" not in p.name]
if not JARS:raise RuntimeError("No RGB Blocks compiled JAR found in "+str(BUILD))
rgb=max(JARS,key=lambda p:p.stat().st_size)
HEAD={"User-Agent":"RGBBlocks-1.3.1-Owner-ModpackBuilder/1.0"}
def json_url(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=120) as response:return json.load(response)
def raw_url(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=220) as response:return response.read()
def pick(project,prefix,loader):
    q=urllib.parse.urlencode({"game_versions":json.dumps([mc]),"loaders":json.dumps([loader])})
    versions=json_url(f"https://api.modrinth.com/v2/project/{project}/version?{q}")
    # Modrinth uses both '0.6.13+mc1.21.1' and 'mc1.21.1-0.6.13-fabric'.
    # Match a version component, not only a leading prefix; reject 0.6.130 etc.
    import re
    token=re.compile(r"(?<![0-9])"+re.escape(prefix)+r"(?![0-9])")
    matches=[v for v in versions if token.search(v.get("version_number",""))]
    if not matches:raise RuntimeError("No exact supported "+project+" "+prefix+" for "+mc+" "+loader)
    matches.sort(key=lambda x:x.get("date_published",""),reverse=True)
    files=sorted(matches[0].get("files",[]),key=lambda f:not f.get("primary",False))
    jar=next((f for f in files if f["filename"].endswith(".jar")),None)
    if not jar:raise RuntimeError("No mod jar for "+project)
    return matches[0],jar
def hashes(data):
    return {"sha1":hashlib.sha1(data).hexdigest(),"sha512":hashlib.sha512(data).hexdigest()}
def add(filename,url,env):
    data=raw_url(url)
    expected=hashes(data)
    if filename.endswith(".jar"):
        with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
            bad=z.testzip()
            if bad:raise ValueError("Bad ZIP CRC for "+filename+" entry "+bad)
    entry={"path":filename,"hashes":expected,"downloads":[url],"fileSize":len(data),
           "env":{"client":"required" if env in ("client","both") else "unsupported",
                  "server":"required" if env=="both" else "unsupported"}}
    entries.append(entry)
    return entry
entries=[]
mods=[]
cnbname,cnburl=cfg["cnb"]
mods.append(add("mods/"+cnbname,cnburl,"both"))
for proj,prefix,loader,env in cfg["mods"]:
    version,file=pick(proj,prefix,loader)
    entry=add("mods/"+file["filename"],file["url"],env)
    if file.get("hashes",{}).get("sha512") and file["hashes"]["sha512"]!=entry["hashes"]["sha512"]:
        raise RuntimeError("Modrinth official metadata SHA-512 mismatch: "+proj)
    mods.append(entry)
# Complementary Reimagined r5.9.3 is cross-version shader, client-side only.
shader=json_url("https://api.modrinth.com/v2/version/Bqen1mJX")
assert shader["version_number"]=="r5.9.3", shader["version_number"]
shaderfile=next(f for f in shader["files"] if f["filename"].lower().endswith(".zip"))
mods.append(add("shaderpacks/"+shaderfile["filename"],shaderfile["url"],"client"))

outdir=pathlib.Path("rgb-blocks-compat/packages")
outdir.mkdir(parents=True,exist_ok=True)
name=f"RGBBlocks-1.3.1-MC{mc}-{cfg['loader']}-complete-ecosystem"
packpath=outdir/(name+".mrpack")
index={
    "formatVersion":1,"game":"minecraft","versionId":f"1.3.1+mc{mc}",
    "name":f"RGB Blocks 1.3.1 — Minecraft {mc}",
    "summary":"RGB Blocks complete compatibility test profile with Chisels & Bits, shader loader, optimized renderer and Complementary Shaders",
    "files":entries,
    "dependencies":{"minecraft":mc,cfg["loader"]:cfg["loaderver"]}
}
install=f"""RGB Blocks 1.3.1 for Minecraft {mc} / {cfg['loader']} {cfg['loaderver']}
================================================================================
The .mrpack is a Modrinth/PrismLauncher importable test profile.
1. Import this .mrpack in a modpack-compatible launcher.
2. The launcher downloads C&B, rendering mods and Complementary r5.9.3
   from their ORIGINAL creators' URLs, checking SHA-512.
3. RGB Blocks candidate mod JAR is already inside the pack.
4. Client-only rendering mods and shaders must NOT be copied to a dedicated server.
5. Complementary is INSTALLED but NOT automatically enabled.
6. DO NOT publish as a stable release until the user verifies original
   RGB colored lighting, C&B chiseling, glass transparency and multiplayer.
Source and CI tests: https://github.com/sangkukzoa-ctrl/assets/tree/rgb-blocks-legacy-compat-audit
WARNING: Minecraft 1.20.1/1.21.1 legacy ports are developer backport builds.
"""
with zipfile.ZipFile(packpath,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr("modrinth.index.json",json.dumps(index,ensure_ascii=False,indent=2))
    z.writestr("overrides/README_RGBBlocks_Port.txt",install)
    z.write(rgb,"overrides/mods/"+rgb.name)
    z.writestr("overrides/shaderpacks/README.txt",
      "Use Video Settings -> Shaders to enable Complementary Reimagined after loading the game.")
lock=outdir/(name+"-lock.json")
lock.write_text(json.dumps({"profile":PROFILE,"own_mod":rgb.name,"own_mod_sha256":hashlib.sha256(rgb.read_bytes()).hexdigest(),
                           "index":index,"source":"Owner-developed RGB Blocks 1.3.1 backport candidate",
                           "licensed_3rd_party_mods_rehosted":False},ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS built complete ecosystem",packpath,packpath.stat().st_size,"bytes",
      "mods/shaders",len(mods),"RGB",rgb.name,flush=True)
