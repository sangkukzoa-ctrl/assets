#!/usr/bin/env python3
"""Real production-mapped Minecraft 1.20.1 Forge client smoke.
Unlike ForgeGradle runClient, this launches a normal installed Forge loader
so original third-party Embeddium/Oculus SRG refmaps resolve against real
production obfuscated game classes. Not a visual correctness acceptance test.
"""
from pathlib import Path
import hashlib, json, os, signal, shutil, subprocess, tarfile, threading, time, urllib.parse, urllib.request, zipfile

OUT=Path("mc1201-forge-production-client-test")
OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path("mc1201-forge-production-client")
GAME=ROOT/"game";MODS=GAME/"mods";MODS.mkdir(parents=True,exist_ok=True)
HEAD={"User-Agent":"RGBBlocks-Owner-Forge-1201-Production-Client-Smoke/1.0"}
def fetch(url,dst,timeout=240):
    req=urllib.request.Request(url,headers=HEAD)
    with urllib.request.urlopen(req,timeout=timeout) as response:data=response.read()
    dst.write_bytes(data)
    print("DOWNLOADED",dst,len(data),flush=True)
    return data
def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=120) as response:
        return json.load(response)
def get_mod(project,version):
    query=urllib.parse.urlencode({"game_versions":json.dumps(["1.20.1"]),"loaders":json.dumps(["forge"])})
    vs=get_json(f"https://api.modrinth.com/v2/project/{project}/version?{query}")
    selected=[v for v in vs if version in v.get("version_number","")]
    if not selected:raise RuntimeError(f"Missing production release {project} {version}")
    selected.sort(key=lambda x:x.get("date_published",""),reverse=True)
    f=next(f for f in sorted(selected[0]["files"],key=lambda z:not z.get("primary",False)) if f["filename"].endswith(".jar"))
    buf=fetch(f["url"],MODS/f["filename"])
    if f.get("hashes",{}).get("sha512") and hashlib.sha512(buf).hexdigest()!=f["hashes"]["sha512"]:
        raise AssertionError(project+" official Modrinth SHA512 mismatch")
    with zipfile.ZipFile(MODS/f["filename"]) as z:
        assert z.testzip() is None,project+" CRC"
    return selected[0]["version_number"]

jars=[f for f in Path("port-work/mc1201-forge/build/libs").glob("*.jar")
      if "-sources" not in f.name and "-dev" not in f.name]
if not jars:raise RuntimeError("No compiled RGB Blocks Forge production JAR")
own=max(jars,key=lambda p:p.stat().st_size)
shutil.copy2(own,MODS/own.name)
print("RGB PORT",own,own.stat().st_size,flush=True)
fetch("https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",
      MODS/"chisels-and-bits-forge-20.1.20.jar")
embeddium=get_mod("embeddium","0.3.31")
oculus=get_mod("oculus","1.8.0")
(GAME/"options.txt").write_text("fullscreen:false\nrenderDistance:2\nsimulationDistance:2\nmaxFps:20\nmipmapLevels:0\nenableVsync:false\n",encoding="utf-8")

# The following is a standalone, public, upstream Linux launcher executable,
# not a ForgeGradle dev launcher; it installs Forge with production namespace.
URL="https://github.com/theorzr/portablemc/releases/download/v5.0.6/portablemc-5.0.6-linux-x86_64-gnu.tar.gz"
archive=ROOT/"portablemc.tar.gz"
archive.parent.mkdir(parents=True,exist_ok=True)
fetch(URL,archive)
launcher=ROOT/"portablemc"
with tarfile.open(archive,"r:gz") as tar:
    members=[m for m in tar.getmembers() if m.isfile() and Path(m.name).name=="portablemc"]
    if not members:raise RuntimeError("Standalone PortableMC executable absent from release tarball")
    with tar.extractfile(members[0]) as f:launcher.write_bytes(f.read())
launcher.chmod(0o755)

cmd=["xvfb-run","-a","-s","-screen 0 1280x720x24",str(launcher.resolve()),
     "--main-dir",str((ROOT/"launcher-data").resolve()),
     "start","forge::1.20.1-47.4.28","--mc-dir",str(GAME.resolve()),
     "-u","RGBPortTester","--resolution","1280x720"]
env=os.environ.copy()
env.update({"LIBGL_ALWAYS_SOFTWARE":"1","GALLIUM_DRIVER":"llvmpipe",
            "MESA_GL_VERSION_OVERRIDE":"4.5","MESA_GLSL_VERSION_OVERRIDE":"450",
            "JAVA_HOME":os.environ.get("JAVA_HOME","")})
print("START PRODUCTION CLIENT",cmd,flush=True)
p=subprocess.Popen(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                   start_new_session=True,env=env,bufsize=1)
lines=[]
def read():
    for line in p.stdout:
        lines.append(line)
        if len(lines)%10==0 or any(x in line.lower() for x in ("error","exception","render thread","fatal","launched")):
            print("PROD",line.rstrip(),flush=True)
reader=threading.Thread(target=read,daemon=True);reader.start()
start=time.monotonic()
timeout=520
while time.monotonic()-start<timeout and p.poll() is None:
    time.sleep(1)
    # Never abort because the old client emits a large number of model warnings;
    # log volume must be evaluated as a FAILURE rather than mistaken for success.
    if len(lines)>750000:break
if p.poll() is None:
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
reader.join(timeout=15)
log="".join(lines)
(OUT/"launcher-console.log").write_text(log,encoding="utf-8")
gamefile=GAME/"logs/latest.log"
game=gamefile.read_text(encoding="utf-8",errors="replace") if gamefile.exists() else ""
if game:shutil.copy2(gamefile,OUT/"minecraft-latest.log")
crashfiles=list((GAME/"crash-reports").glob("*.txt")) if (GAME/"crash-reports").exists() else []
for file in crashfiles:shutil.copy2(file,OUT/file.name)
both=log+"\n"+game
bad=[s for s in ["MixinApplyError","MixinInitialisationError","NoClassDefFoundError",
                 "ExceptionInInitializerError","NoSuchMethodError","Crash report saved"]
     if s.lower() in both.lower()]
signs={key:key.lower() in both.lower() for key in
       ["Render thread","OpenAL initialized","Backend library: LWJGL version",
        "Created:","Sound engine started","Iris","Oculus","Embeddium","rgbblocks"]}
rgb_missing_models=[line for line in game.splitlines() if "rgbblocks:models/item/" in line and "FileNotFoundException" in line]
rgb_missing_blocks=[line for line in game.splitlines() if "rgbblocks:blockstates/" in line and "missing model for variant" in line]
result={"rgb_item_model_missing_count":len(rgb_missing_models),"rgb_block_model_variant_missing_count":len(rgb_missing_blocks),"first_missing_item":rgb_missing_models[:2],"first_missing_block":rgb_missing_blocks[:2],
        "scope":"Real production Forge 1.20.1+RGB 1.3.1+C&B20.1.20+Embeddium0.3.31+Oculus1.8.0, Xvfb/Mesa",
        "build":str(own),"launcher":"PortableMC v5.0.6, full version Forge 1.20.1-47.4.28",
        "embeddium":embeddium,"oculus":oculus,
        "seconds":round(time.monotonic()-start,1),
        "exit_code":p.returncode,"minecraft_log":bool(game),
        "markers":signs,"fatal_patterns":bad,"crash_reports":[f.name for f in crashfiles]}
(OUT/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
if rgb_missing_models or rgb_missing_blocks:raise AssertionError("RGB model/texture parity FAILED: missing items %d, blocks %d"%(len(rgb_missing_models),len(rgb_missing_blocks)))
print("RESULT",json.dumps(result,ensure_ascii=False),flush=True)
if bad or crashfiles:raise AssertionError("Production Forge RGB client crashed; check log details")
if not game or not signs["Render thread"] or not signs["Created:"]:raise AssertionError("Production Forge client did not finish resource-atlas graphics initialization")
print("PASS: real production Forge 1.20.1 client reached graphics with RGB+C&B+Embeddium+Oculus",flush=True)
