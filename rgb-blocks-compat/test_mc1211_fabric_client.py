#!/usr/bin/env python3
"""GUI startup smoke: Minecraft 1.21.1 Fabric, RGB Blocks and building ecosystem.
Real Minecraft client under xvfb/Mesa llvmpipe. Checks game log and splash/menu;
does NOT pretend this replaces human RGB light / shader scene comparison.
"""
import json,os,pathlib,shutil,signal,subprocess,time,urllib.request,urllib.parse,zipfile
WORK=pathlib.Path("port-work/mc1211-fabric")
LOGROOT=pathlib.Path("mc1211-fabric-client-test")
LOGROOT.mkdir(exist_ok=True)
run=WORK/"run"
mods=run/"mods"
mods.mkdir(parents=True,exist_ok=True)
headers={"User-Agent":"RGBBlocks-1.3.1-Owner-CI-Client-Compatibility/1.0"}
def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120) as r:
        return json.load(r)
def fetch_file(url,path):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=200) as r:
        data=r.read()
    path.write_bytes(data)
    if not zipfile.is_zipfile(path):raise ValueError("Not a valid mod jar: "+str(path))
    print("MOD",path.name,len(data),flush=True)
def get_version(project,prefix,mc="1.21.1"):
    query=urllib.parse.urlencode({"game_versions":json.dumps([mc]),"loaders":json.dumps(["fabric"])})
    versions=fetch_json(f"https://api.modrinth.com/v2/project/{project}/version?{query}")
    vs=[v for v in versions if (v.get("version_number","")==prefix or v.get("version_number","").startswith(prefix+"+")
       or v.get("version_number","").startswith(prefix+"-") or prefix in v.get("version_number",""))
       and any("fabric" in x.lower() for x in v.get("loaders",[]))]
    if not vs:raise RuntimeError(f"No {project} version {prefix} for {mc}")
    vs.sort(key=lambda v:v.get("date_published",""),reverse=True)
    f=sorted(vs[0]["files"],key=lambda f:not f.get("primary",False))[0]
    return vs[0],f
dependencies={}
for project,prefix in (("sodium","0.6.13"),("iris","1.8.8")):
    version,file=get_version(project,prefix)
    fetch_file(file["url"],mods/file["filename"])
    dependencies[project]={"version":version["version_number"],"file":file["filename"]}
# Latest functional C&B 21.1.40 already confirmed from actual server boot.
fetch_file("https://mediafilez.forgecdn.net/files/9455/172/chisels-and-bits-fabric-21.1.40.jar",
           mods/"chisels-and-bits-fabric-21.1.40.jar")
dependencies["chiselsandbits"]="21.1.40"
print("TEST DEPENDENCIES",json.dumps(dependencies),flush=True)
(run/"options.txt").write_text("""fullscreen:false
renderDistance:2
simulationDistance:2
maxFps:20
graphicsMode:0
mipmapLevels:0
enableVsync:false
""")
env=os.environ.copy()
env.update({
 "LIBGL_ALWAYS_SOFTWARE":"1","MESA_GL_VERSION_OVERRIDE":"4.5",
 "MESA_GLSL_VERSION_OVERRIDE":"450",
 "SDL_VIDEODRIVER":"x11","GALLIUM_DRIVER":"llvmpipe"
})
cmd=["xvfb-run","-a","-s","-screen 0 1280x720x24","gradle","--no-daemon","runClient",
     "--console=plain","-Dorg.gradle.jvmargs=-Xmx4G"]
print("LAUNCH"," ".join(cmd),flush=True)
start=time.monotonic()
try:
 p=subprocess.Popen(cmd,cwd=WORK,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                    start_new_session=True,bufsize=1,env=env)
except Exception as e:
 raise RuntimeError("Could not launch client environment: "+str(e))
lines=[]
import threading
def reader():
 for line in p.stdout:
    lines.append(line)
    print("CLIENT",line.rstrip(),flush=True)
t=threading.Thread(target=reader,daemon=True);t.start()
# Client may need first-time full Minecraft assets (Mojang downloads via Loom).
time_limit=390
while time.monotonic()-start<time_limit and p.poll() is None:
 time.sleep(1)
 if len(lines)>60000:break
if p.poll() is None:
 try:os.killpg(p.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 try:p.wait(timeout=20)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
t.join(timeout=5)
log="".join(lines)
(LOGROOT/"client-console.log").write_text(log,encoding="utf-8")
game_log=run/"logs/latest.log"
if game_log.exists():
 shutil.copy2(game_log,LOGROOT/"minecraft-latest.log")
 game=game_log.read_text(encoding="utf-8",errors="replace")
else:game=""
fatal=[p for p in ["MixinApplyError","MixinInitialisationError","NoSuchMethodError","NoClassDefFoundError",
                   "ExceptionInInitializerError","Crash report saved","Failed to start Minecraft"]
       if p.lower() in (log+"\n"+game).lower()]
scene_patterns=["Backend library: LWJGL version","OpenAL initialized","Created:","Sound engine started","Render thread"]
signs={q:q.lower() in (log+"\n"+game).lower() for q in scene_patterns}
crash=list((run/"crash-reports").glob("*.txt")) if (run/"crash-reports").exists() else []
for crash_file in crash:
 shutil.copy2(crash_file,LOGROOT/crash_file.name)
result={"scope":"Real 1.21.1 Fabric RGBBlocks + C&B + Sodium + Iris Xvfb software-GL client startup only",
        "deps":dependencies,
        "seconds":round(time.monotonic()-start,1),
        "exit_code":p.returncode,
        "java_or_minecraft_log":bool(game),
        "render_signs":signs,
        "fatal_patterns":fatal,"crash_reports":[c.name for c in crash],
        "time_limit":time_limit}
(LOGROOT/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
print("RESULT",json.dumps(result,ensure_ascii=False),flush=True)
if fatal or crash:
 raise AssertionError("Game crash / Mixin incompatibility detected: "+repr(result))
if not signs["Render thread"] or not game:
 raise AssertionError("Minecraft client did not reach a render thread; inspect logs")
print("PASS: Minecraft client reached graphics startup with C&B+Sodium+Iris",flush=True)
