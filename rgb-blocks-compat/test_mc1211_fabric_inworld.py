#!/usr/bin/env python3
"""MC1.21.1 Fabric+RGB Blocks1.3.1 real in-world multiplayer client test.
Real Fabric server, regular launcher (not FabricLoom dev runClient), real
ChiselsBits/Sodium/Iris, screenshots, network join and model/asset gate.
"""
import json,os,signal,pathlib,subprocess,threading,time,urllib.request,zipfile,tarfile,hashlib,shutil
from urllib.parse import urlencode
from pathlib import Path
ROOT=Path("mc1211-fabric-inworld"); SERVER=ROOT/"server";GAME=ROOT/"client";EVIDENCE=ROOT/"evidence"
for p in (SERVER/"mods",GAME/"mods",EVIDENCE):p.mkdir(parents=True,exist_ok=True)
def info(msg):
    print(msg,flush=True)
    with (EVIDENCE/"events.log").open("a") as f:f.write(msg+"\n")
def fetch(url,out):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-1.3.1-Fabric-RealGameplay-Acceptance/1.0"}),timeout=240) as r:data=r.read()
    out.write_bytes(data);info("FETCH "+str(out)+" "+str(len(data)));return data
def jsonurl(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-1.3.1-Fabric-RealGameplay-Acceptance/1.0"}),timeout=120) as r:return json.load(r)
def download_mod(project,target):
    params=urlencode({"game_versions":json.dumps(["1.21.1"]),"loaders":json.dumps(["fabric"])})
    releases=jsonurl(f"https://api.modrinth.com/v2/project/{project}/version?{params}")
    versions=[v for v in releases if target in v.get("version_number","")]
    if not versions:raise RuntimeError("Missing Fabric mod "+project+" version "+target)
    versions.sort(key=lambda v:v.get("date_published",""),reverse=True)
    file=next(f for f in sorted(versions[0]["files"],key=lambda x:not x.get("primary",False)) if f["filename"].endswith(".jar"))
    data=fetch(file["url"],GAME/"mods"/file["filename"])
    expect=file.get("hashes",{}).get("sha512")
    if expect:assert hashlib.sha512(data).hexdigest()==expect,project+" checksum failure"
    return file["filename"]
def proc_reader(proc,label,path):
    lines=[]
    def read():
        with path.open("w",encoding="utf-8") as f:
            for line in proc.stdout:
                lines.append(line);f.write(line);f.flush()
                if any(x in line for x in ("Done (","joined the game","lost connection","ERROR","FATAL","RGB mode","Render thread","Failed")):
                    info(label+" "+line.rstrip()[:340])
    t=threading.Thread(target=read,daemon=True);t.start();return lines,t
def await_line(lines,needle,proc,limit):
    start=time.monotonic()
    while time.monotonic()-start<limit:
        if needle in "".join(lines[-1000:]):return True
        if proc.poll() is not None:break
        time.sleep(.7)
    info("MISSING "+needle+" after "+str(time.monotonic()-start))
    return False
def cmd(p,s):
    p.stdin.write(s+"\n");p.stdin.flush();info("SERVER "+s)
def terminate(p):
    if p.poll() is None:
        try:os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:p.wait(timeout=25)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)

jar_candidates=[p for p in Path("port-work/mc1211-fabric/build/libs").glob("*.jar") if "-dev" not in p.name and "-sources" not in p.name]
assert jar_candidates,"Missing built RGB Blocks 1.21.1 Fabric production jar"
jar=max(jar_candidates,key=lambda p:p.stat().st_size)
with zipfile.ZipFile(jar) as z:
    colors=json.loads(z.read("assets/rgbblocks/palette.json"));assert len(colors)==16687
    assert json.loads(z.read("pack.mcmeta"))["pack"]["pack_format"]==34
chosen=next(c for c in colors if c["red"]>180 and c["green"]<100 and c["blue"]<100)
block="rgbblocks:rgb_%s_%d_%d_%d"%(chosen["group"],chosen["red"],chosen["green"],chosen["blue"])
shutil.copy2(jar,GAME/"mods"/jar.name);shutil.copy2(jar,SERVER/"mods"/jar.name)
cb="chisels-and-bits-fabric-21.1.40.jar"
fetch("https://mediafilez.forgecdn.net/files/9455/172/"+cb,SERVER/"mods"/cb)
shutil.copy2(SERVER/"mods"/cb,GAME/"mods"/cb)
api=download_mod("fabric-api","0.116.17")
shutil.copy2(GAME/"mods"/api,SERVER/"mods"/api)
sodium=download_mod("sodium","0.6.13")
iris=download_mod("iris","1.8.8")
info("CLIENT_ECOSYSTEM "+json.dumps({"fabric-api":api,"chiselsandbits":cb,"sodium":sodium,"iris":iris}))
fetch("https://meta.fabricmc.net/v2/versions/loader/1.21.1/0.19.5/1.1.2/server/jar",SERVER/"fabric-server.jar")
(SERVER/"eula.txt").write_text("eula=true\n")
(SERVER/"server.properties").write_text("""online-mode=false
server-ip=127.0.0.1
server-port=25567
max-players=4
view-distance=3
simulation-distance=3
spawn-protection=0
allow-flight=true
level-type=minecraft:flat
motd=RGBBlocks 1.21.1 Fabric real network and in-world color fixture
""")
server=subprocess.Popen(["java","-Xms512M","-Xmx2500M","-jar","fabric-server.jar","nogui"],
    cwd=SERVER,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
slog,sthread=proc_reader(server,"SERVER",EVIDENCE/"server.log")
client=None; xvfb=None
result={"minecraft":"1.21.1","loader":"Fabric 0.19.5","scope":"Actual dedicated-server+real launcher in-world RGB gameplay",
        "palette_count":len(colors),"rgb_test_block":block,"server_ready":False,"fml_player_joined":False,
        "rgb_commands":False,"rgb_light_propagation_verified":False,"cnb_sculpted_fixture":False,"cnb_rgb_propagation_verified":False,"render_thread":False,"texture_atlas_ready":False,
        "missing_rgb_models":None,"crashes":[],"screenshots":[]}
try:
    result["server_ready"]=await_line(slog,"Done (",server,180)
    if not result["server_ready"]:raise AssertionError("Fabric server failed to become ready")
    for c in ["gamerule doDaylightCycle false","time set midnight","weather clear","forceload add 0 0",
              "fill -4 119 1 4 119 10 minecraft:stone",
              f"setblock -2 121 7 {block}",f"setblock 0 121 7 {block}_glow",f"setblock 2 121 7 {block}_glass",
              "setblock 4 121 7 chiselsandbits:chiseled",
              f"execute if block 0 121 7 {block}_glow run say RGB_GLOW_FIXTURE_READY",
              "rgb auto","rgb setbake all","rgb get"]:
        cmd(server,c);time.sleep(.35)
    assert await_line(slog,"RGB_GLOW_FIXTURE_READY",server,50),"RGB glow fixture not present"
    result["cnb_sculpted_fixture"]=await_line(slog,"RGB_PORT_CNB_FIXTURE_PASS",server,70)
    result["rgb_commands"]=await_line(slog,"RGB mode: AUTO",server,50)
    assert result["rgb_commands"],"Server RGB mode command failed"
    tarpath=ROOT/"portablemc.tar.gz"
    fetch("https://github.com/theorzr/portablemc/releases/download/v5.0.6/portablemc-5.0.6-linux-x86_64-gnu.tar.gz",tarpath)
    launcher=ROOT/"portablemc"
    with tarfile.open(tarpath,"r:gz") as tar:
        entry=next(x for x in tar.getmembers() if x.isfile() and Path(x.name).name=="portablemc")
        with tar.extractfile(entry) as f:launcher.write_bytes(f.read())
    launcher.chmod(0o755)
    (GAME/"options.txt").write_text("fullscreen:false\nrenderDistance:2\nsimulationDistance:5\nmaxFps:20\nmipmapLevels:0\nenableVsync:false\n")
    display=":87"
    xvfb=subprocess.Popen(["Xvfb",display,"-screen","0","1280x720x24","-ac","+extension","GLX"],
            stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(2)
    env=os.environ.copy();env.update({"DISPLAY":display,"LIBGL_ALWAYS_SOFTWARE":"1","GALLIUM_DRIVER":"llvmpipe",
          "MESA_GL_VERSION_OVERRIDE":"4.5","MESA_GLSL_VERSION_OVERRIDE":"450","ALSOFT_DRIVERS":"null"})
    launchcmd=[str(launcher.resolve()),"--main-dir",str((ROOT/"launcher-data").resolve()),"start","fabric:1.21.1:0.19.5",
       "--mc-dir",str(GAME.resolve()),"-u","RGBPortTester","--join-server","127.0.0.1",
       "--join-server-port","25567","--resolution","1280x720"]
    info("LAUNCH "+str(launchcmd))
    client=subprocess.Popen(launchcmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
        bufsize=1,env=env,start_new_session=True)
    clog,cthread=proc_reader(client,"CLIENT",EVIDENCE/"launcher.log")
    result["fml_player_joined"]=await_line(slog,"RGBPortTester joined the game",server,190)
    if not result["fml_player_joined"]:
        info("JOIN DIAGNOSTIC — client process state="+str(client.poll()))
        for pth in (GAME/"logs/latest.log", EVIDENCE/"launcher.log", EVIDENCE/"server.log"):
            if pth.exists():
                tail=pth.read_text(encoding="utf-8",errors="replace").splitlines()[-70:]
                info("LAST 70 LINES "+str(pth)+"\n"+"\n".join(tail))
    result["render_thread"]=await_line(clog,"Render thread",client,55)
    result["texture_atlas_ready"]=await_line(clog,"Created:",client,180)
    if result["fml_player_joined"]:
        cmd(server,"tp RGBPortTester 0.5 120.0 0.5 facing 0.5 121.5 7.5")
        cmd(server,"effect give RGBPortTester minecraft:night_vision 45 0 true")
        cmd(server,"gamemode creative RGBPortTester")
        cmd(server,"rgb bake")
        time.sleep(35)
        screenshot=EVIDENCE/"real-fabric-rgb-normal-glow-glass.png"
        shot=subprocess.run(["scrot",str(screenshot.resolve())],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
        if shot.returncode==0 and screenshot.is_file():
            result["screenshots"].append({"name":screenshot.name,"bytes":screenshot.stat().st_size})
        else:info("FAILED SCREENSHOT "+shot.stdout)
    live=GAME/"logs/latest.log"
    txt=live.read_text(encoding="utf-8",errors="replace") if live.is_file() else ""
    if live.is_file():shutil.copy2(live,EVIDENCE/"minecraft-client.log")
    result["rgb_light_propagation_verified"]="RGB_PORT_LIGHT_PROBE_PASS" in (txt+"\n"+"".join(clog))
    result["cnb_rgb_propagation_verified"]="RGB_PORT_CNB_LIGHT_PROBE_PASS" in (txt+"\n"+"".join(clog))
    result["missing_rgb_models"]=sum(("rgbblocks:models/item/" in line and "FileNotFoundException" in line) or
      ("rgbblocks:blockstates/" in line and "missing model for variant" in line)
       for line in txt.splitlines()) if txt else -1
    result["crashes"]=[needle for needle in ("MixinApplyError","NoSuchMethodError","NoClassDefFoundError","Crash report saved")
      if needle in txt]
finally:
    if client:terminate(client)
    if xvfb:terminate(xvfb)
    if server.poll() is None:
        try:cmd(server,"stop")
        except Exception:pass
        try:server.wait(timeout=45)
        except subprocess.TimeoutExpired:terminate(server)
    sthread.join(timeout=5)
    if "cthread" in locals():cthread.join(timeout=5)
    (EVIDENCE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    info("RESULT "+json.dumps(result,ensure_ascii=False))
assert result["server_ready"] and result["fml_player_joined"],"MC1.21.1 real client/server connection failure"
assert result["render_thread"] and result["texture_atlas_ready"],"MC1.21.1 graphical scene not loaded"
assert result["missing_rgb_models"]==0,"One or more RGB models unavailable in actual Fabric client"
assert not result["crashes"],"Actual client RGB/C&B/Sodium/Iris Mixin or class crash"
assert result["screenshots"],"No screenshot of real in-world RGB scene"
assert result["rgb_light_propagation_verified"],"RGB light propagation runtime pixel-channel probe failed"
assert result["cnb_sculpted_fixture"],"C&B 4095 RGB microbits fixture was not constructed"
assert result["cnb_rgb_propagation_verified"],"C&B chiselled RGB-colored light failed to propagate into adjacent voxel"
info("PASS: MC1.21.1 actual RGB game scene + client/server networking + full model asset recognition")
