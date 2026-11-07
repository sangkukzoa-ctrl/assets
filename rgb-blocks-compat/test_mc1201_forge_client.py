#!/usr/bin/env python3
"""Launch real Forge 1.20.1 RGB Blocks+ChiselsBits+Embeddium+Oculus graphical client.
Virtual display Mesa llvmpipe; launcher lifecycle and Mixin smoke, NOT final in-world color/appearance proof.
"""
import json,os,pathlib,shutil,signal,subprocess,threading,time,urllib.parse,urllib.request,zipfile
WORK=pathlib.Path("port-work/mc1201-forge")
OUT=pathlib.Path("mc1201-forge-client-test");OUT.mkdir(exist_ok=True)
RUN=WORK/"run";MODS=RUN/"mods";MODS.mkdir(parents=True,exist_ok=True)
HEAD={"User-Agent":"RGBBlocks-1.3.1-owner-Forge-1.20.1-client-test"}
def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=100) as resp:return json.load(resp)
def get_file(url,dst):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=180) as r:data=r.read()
    dst.write_bytes(data)
    with zipfile.ZipFile(dst) as z:assert z.testzip() is None
    print("MOD",dst.name,len(data),flush=True)
def modrinth(project,target):
    opts=urllib.parse.urlencode({"game_versions":json.dumps(["1.20.1"]),"loaders":json.dumps(["forge"])})
    versions=get_json(f"https://api.modrinth.com/v2/project/{project}/version?{opts}")
    matching=[v for v in versions if target in v.get("version_number","")]
    if not matching:raise RuntimeError(f"Modrinth version {project} {target} 1.20.1 Forge missing")
    matching.sort(key=lambda v:v.get("date_published",""),reverse=True)
    v=matching[0]
    files=sorted(v["files"],key=lambda f:not f.get("primary"))
    file=next(x for x in files if x["filename"].endswith(".jar"))
    get_file(file["url"],MODS/file["filename"])
    return {"version":v["version_number"],"file":file["filename"]}
deps={}
get_file("https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",
         MODS/"chisels-and-bits-forge-20.1.20.jar")
deps["chiselsandbits"]="20.1.20"
for name,version in [("embeddium","0.3.31"),("oculus","1.8.0")]:
    deps[name]=modrinth(name,version)
(RUN/"options.txt").write_text("""fullscreen:false
renderDistance:2
simulationDistance:2
graphicsMode:0
mipmapLevels:0
maxFps:20
enableVsync:false
""")
env=os.environ.copy()
env.update({"LIBGL_ALWAYS_SOFTWARE":"1","MESA_GL_VERSION_OVERRIDE":"4.5",
            "MESA_GLSL_VERSION_OVERRIDE":"450","GALLIUM_DRIVER":"llvmpipe"})
cmd=["xvfb-run","-a","-s","-screen 0 1280x720x24","gradle","--no-daemon",
     "runClient","--console=plain","-Dorg.gradle.jvmargs=-Xmx4G"]
print("START",cmd,"deps",deps,flush=True)
proc=subprocess.Popen(cmd,cwd=WORK,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                      text=True,env=env,bufsize=1,start_new_session=True)
lines=[]
def reader():
 for line in proc.stdout:
    lines.append(line);print("CLIENT",line.rstrip(),flush=True)
t=threading.Thread(target=reader,daemon=True);t.start()
start=time.monotonic()
timeout=420
while time.monotonic()-start<timeout and proc.poll() is None:time.sleep(1)
if proc.poll() is None:
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:proc.wait(timeout=25)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=15)
t.join(timeout=5)
log="".join(lines)
(OUT/"client-console.log").write_text(log,encoding="utf-8")
live=RUN/"logs/latest.log"
game=""
if live.exists():
    game=live.read_text(errors="replace")
    shutil.copy2(live,OUT/"minecraft-latest.log")
crashes=list((RUN/"crash-reports").glob("*.txt")) if (RUN/"crash-reports").exists() else []
for c in crashes:shutil.copy2(c,OUT/c.name)
marks=["Render thread","OpenAL initialized","Backend library: LWJGL version","Sound engine started"]
signs={mark:mark.lower() in (log+"\n"+game).lower() for mark in marks}
fatal=[s for s in ["MixinApplyError","MixinInitialisationError","NoSuchMethodError","NoClassDefFoundError",
                    "ExceptionInInitializerError","Crash report saved","Failure to launch"]
       if s.lower() in (log+"\n"+game).lower()]
result={"scope":"Real MC1.20.1 Forge RGBBlocks + C&B + Embeddium + Oculus Xvfb GUI launch",
        "dependencies":deps,"exit_code":proc.returncode,"timed_out":time.monotonic()-start>=timeout,
        "render_signs":signs,"fatal_patterns":fatal,"crashes":[x.name for x in crashes]}
(OUT/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print("RESULT",json.dumps(result,ensure_ascii=False),flush=True)
if fatal or crashes:raise AssertionError("Minecraft client startup contains fatal error; examine logs")
if not signs["Render thread"]:raise AssertionError("Minecraft graphical client did not reach Render thread")
print("PASS: RGBBlocks Minecraft 1.20.1 + C&B/Embeddium/Oculus actual graphical client start",flush=True)
