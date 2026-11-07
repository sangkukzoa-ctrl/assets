#!/usr/bin/env python3
"""Minecraft 1.20.1 REAL Forge server + production client in-world RGB test.

Joins via actual Forge mod handshake and capture RGB normal, glow and glass
placed in server world; verifies world edit, remote connection, render pipeline,
persisted network commands and 3D screenshot. This is a strict smoke, not a
shader pixel-equivalence proof.
"""
import json,os,signal,pathlib,subprocess,threading,time,urllib.request,zipfile,tarfile,hashlib,shutil
from pathlib import Path

ROOT=Path("mc1201-forge-inworld")
SERVER=ROOT/"server";GAME=ROOT/"client"
EVIDENCE=ROOT/"evidence";S_MODS=SERVER/"mods";C_MODS=GAME/"mods"
for p in (EVIDENCE,S_MODS,C_MODS):p.mkdir(parents=True,exist_ok=True)
logfile=EVIDENCE/"test-event.log"
def record(msg):
    print(msg,flush=True)
    with logfile.open("a",encoding="utf-8") as f:f.write(msg+"\n")
def fetch(url,out):
    req=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Owner-Inworld-Remote-Test/1.0"})
    with urllib.request.urlopen(req,timeout=230) as r:data=r.read()
    out.write_bytes(data)
    record("FETCH "+str(out)+" "+str(len(data)))
    return data
def runthread(p,label,out):
    lines=[]
    def reader():
        with out.open("w",encoding="utf-8") as f:
            for line in p.stdout:
                lines.append(line)
                f.write(line);f.flush()
                if any(q in line for q in ("Done (","joined the game","lost connection","ERROR","FATAL","Fatal","Traceback","Render thread","RGB mode","Server thread","Failed")):
                    record(label+" "+line.rstrip()[:450])
    t=threading.Thread(target=reader,daemon=True);t.start()
    return lines,t
def await_pattern(lines,pat,proc,seconds,label):
    st=time.monotonic()
    while time.monotonic()-st<seconds:
        if pat in "".join(lines[-1200:]):return True
        if proc.poll() is not None:break
        time.sleep(0.7)
    record("TIMEOUT/MISSING "+label+" pattern="+pat+" return="+str(proc.poll()))
    return False
def command(server,s):
    server.stdin.write(s+"\n");server.stdin.flush()
    record("SERVER_COMMAND "+s)
def terminate(p):
    if p.poll() is None:
        try:os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:p.wait(timeout=25)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL)
            p.wait(timeout=20)
HEAD={"User-Agent":"RGBBlocks-InWorld-Client/1.0"}
def jsonurl(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEAD),timeout=120) as r:return json.load(r)
def fetch_mod(name,ver):
    from urllib.parse import urlencode
    q=urlencode({"game_versions":json.dumps(["1.20.1"]),"loaders":json.dumps(["forge"])})
    versions=jsonurl(f"https://api.modrinth.com/v2/project/{name}/version?{q}")
    versions=[v for v in versions if ver in v.get("version_number","")]
    if not versions:raise RuntimeError("Missing "+name+ver)
    versions.sort(key=lambda x:x.get("date_published",""),reverse=True)
    file=next(f for f in versions[0]["files"] if f["filename"].endswith(".jar"))
    buf=fetch(file["url"],C_MODS/file["filename"])
    if file.get("hashes",{}).get("sha512"):
        assert hashlib.sha512(buf).hexdigest()==file["hashes"]["sha512"],"Mod checksum mismatch "+name
    return file["filename"]
jars=[p for p in Path("port-work/mc1201-forge/build/libs").glob("*.jar") if "-sources" not in p.name and "-dev" not in p.name]
assert jars
jar=max(jars,key=lambda p:p.stat().st_size)
with zipfile.ZipFile(jar) as zip:
    palette=json.loads(zip.read("assets/rgbblocks/palette.json"))
    assert len(palette)==16687
    assert json.loads(zip.read("pack.mcmeta"))["pack"]["pack_format"]==15
chosen=next(c for c in palette if c["red"]>180 and c["green"]<100 and c["blue"]<100)
block="rgbblocks:rgb_%s_%d_%d_%d"%(chosen["group"],chosen["red"],chosen["green"],chosen["blue"])
shutil.copy2(jar,S_MODS/jar.name)
shutil.copy2(jar,C_MODS/jar.name)
cb="chisels-and-bits-forge-20.1.20.jar"
fetch("https://mediafilez.forgecdn.net/files/7620/767/"+cb,S_MODS/cb)
shutil.copy2(S_MODS/cb,C_MODS/cb)
emb=fetch_mod("embeddium","0.3.31")
oculus=fetch_mod("oculus","1.8.0")

# Real Forge install server and a pre-generated flat world.
fetch("https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.28/forge-1.20.1-47.4.28-installer.jar",SERVER/"installer.jar")
install=subprocess.run(["java","-jar","installer.jar","--installServer"],cwd=SERVER,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=380)
(EVIDENCE/"forge-installer.log").write_text(install.stdout,encoding="utf-8")
assert install.returncode==0 and (SERVER/"run.sh").exists(),"Forge server installation failed"
(SERVER/"eula.txt").write_text("eula=true\n")
(SERVER/"user_jvm_args.txt").write_text("-Xms512M\n-Xmx2500M\n-Dforge.logging.markers=NETWORK,REGISTRIES\n-Dforge.logging.console.level=debug\n")
(SERVER/"server.properties").write_text("""online-mode=false
server-ip=127.0.0.1
server-port=25566
max-players=4
view-distance=3
simulation-distance=3
spawn-protection=0
allow-flight=true
level-type=minecraft:flat
motd=RGB Blocks 1.20.1 Legacy Multiplayer Render Acceptance
""")
server=subprocess.Popen(["bash","./run.sh","nogui"],cwd=SERVER,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
slog,sthread=runthread(server,"SERVER",EVIDENCE/"server-console.log")
client=None
result={"scope":"Minecraft 1.20.1 production Forge 47.4.28 RGBBlock+C&B+Embeddium/Oculus, actual network connected RGB test scene",
        "shader_enabled":False,"screenshots":[],"block":block,"server_ready":False,"client_joined":False,
        "rgb_server_commands":False,"rgb_light_propagation_verified":False,"cnb_sculpted_fixture":False,"cnb_rgb_propagation_verified":False,"render_thread":False,"atlas_ready":False,"resource_model_missing":None}
try:
    result["server_ready"]=await_pattern(slog,"Done (",server,180,"server_boot")
    if not result["server_ready"]:raise AssertionError("Forge dedicated server did not reach Ready")
    for c in ["gamerule doDaylightCycle false","time set midnight","weather clear","forceload add 0 0",
              "fill -4 119 1 4 119 10 minecraft:stone",
              f"setblock -2 121 7 {block}",
              f"setblock 0 121 7 {block}_glow",
              f"setblock 2 121 7 {block}_glass",
              "setblock 4 121 7 chiselsandbits:chiseled",
              f"execute if block 0 121 7 {block}_glow run say RGB_FIXTURE_GLOW_READY",
              "rgb auto","rgb setbake all","rgb get"]:
        command(server,c);time.sleep(0.4)
    assert await_pattern(slog,"RGB_FIXTURE_GLOW_READY",server,50,"fixture_created"),"RGB block not placed"
    result["cnb_sculpted_fixture"]=await_pattern(slog,"RGB_PORT_CNB_FIXTURE_PASS",server,70,"actual_CnB_voxel_setup")
    result["rgb_server_commands"]=await_pattern(slog,"RGB mode: AUTO",server,50,"rgb_command")
    assert result["rgb_server_commands"]
    # Install real client (not a Mojang-named ForgeGradle development runtime)
    archive=ROOT/"portablemc.tar.gz"
    fetch("https://github.com/theorzr/portablemc/releases/download/v5.0.6/portablemc-5.0.6-linux-x86_64-gnu.tar.gz",archive)
    launch=ROOT/"portablemc"
    with tarfile.open(archive,"r:gz") as tar:
        member=next(x for x in tar.getmembers() if x.isfile() and Path(x.name).name=="portablemc")
        with tar.extractfile(member) as f:launch.write_bytes(f.read())
    launch.chmod(0o755)
    (GAME/"options.txt").write_text("fullscreen:false\nrenderDistance:2\nsimulationDistance:5\nmaxFps:20\nmipmapLevels:0\nenableVsync:false\n")
    display=":86"
    xvfb=subprocess.Popen(["Xvfb",display,"-screen","0","1280x720x24","-ac","+extension","GLX"],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
    time.sleep(2)
    env=os.environ.copy()
    env.update({"DISPLAY":display,"LIBGL_ALWAYS_SOFTWARE":"1","GALLIUM_DRIVER":"llvmpipe","MESA_GL_VERSION_OVERRIDE":"4.5","MESA_GLSL_VERSION_OVERRIDE":"450","ALSOFT_DRIVERS":"null"})
    launchcmd=[str(launch.resolve()),"--main-dir",str((ROOT/"launcher-data").resolve()),
             "start","forge::1.20.1-47.4.28","--mc-dir",str(GAME.resolve()),
             "-u","RGBPortTester","--join-server","127.0.0.1","--join-server-port","25566","--resolution","1280x720", "--jvm-arg=-Dforge.logging.markers=NETWORK,-Dforge.logging.console.level=debug"]
    record("LAUNCH "+str(launchcmd))
    client=subprocess.Popen(launchcmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,text=True,
         start_new_session=True,bufsize=1)
    clog,cthread=runthread(client,"CLIENT",EVIDENCE/"client-console.log")
    result["client_joined"]=await_pattern(slog,"RGBPortTester joined the game",server,190,"real_FML_player_join")
    # Full original 50k RGB registry transferred losslessly across Forge login.
    result["forge_login_compressed"] = any("Forge login registry compressed minecraft:item" in line for line in slog)
    result["forge_login_restored"] = any("Forge login registry restored minecraft:item" in line for line in clog)
    record("REGISTRY_SYNC compressed="+str(result["forge_login_compressed"])+
           " restored="+str(result["forge_login_restored"]))
    if not result["client_joined"]:
        record("JOIN DIAGNOSTIC — client process state="+str(client.poll()))
        for pth in (GAME/"logs/latest.log", EVIDENCE/"client-console.log", EVIDENCE/"server-console.log"):
            if pth.exists():
                tail=pth.read_text(encoding="utf-8",errors="replace").splitlines()[-70:]
                record("LAST 70 LINES "+str(pth)+"\n"+"\n".join(tail))
    result["render_thread"]=await_pattern(clog,"Render thread",client,50,"render_thread")
    result["atlas_ready"]=await_pattern(clog,"Created:",client,180,"texture_atlas")
    if result["client_joined"]:
        command(server,"tp RGBPortTester 0.5 120.0 0.5 facing 0.5 121.5 7.5")
        command(server,"effect give RGBPortTester minecraft:night_vision 45 0 true")
        command(server,"gamemode creative RGBPortTester")
        command(server,"rgb bake")
        time.sleep(35)
        screenshot=EVIDENCE/"inworld-rgb-glow-glass.png"
        shot=subprocess.run(["scrot",str(screenshot.resolve())],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=40)
        if shot.returncode==0 and screenshot.is_file():
            result["screenshots"].append({"file":screenshot.name,"size":screenshot.stat().st_size})
        else:record("SCREENSHOT_FAILED "+shot.stdout)
    client_game=GAME/"logs/latest.log"
    if client_game.is_file():
        txt=client_game.read_text(encoding="utf-8",errors="replace")
        shutil.copy2(client_game,EVIDENCE/"minecraft-client-latest.log")
        result["rgb_light_propagation_verified"]="RGB_PORT_LIGHT_PROBE_PASS" in (txt+"\n"+"".join(clog))
        result["cnb_rgb_propagation_verified"]="RGB_PORT_CNB_LIGHT_PROBE_PASS" in (txt+"\n"+"".join(clog))
        result["resource_model_missing"]=sum("FileNotFoundException: rgbblocks:models/" in x or
          ("rgbblocks:blockstates/" in x and "missing model for variant" in x)
          for x in txt.splitlines())
        result["fatal"]=[x for x in ["MixinApplyError","NoSuchMethodError","NoClassDefFoundError","Crash report saved"] if x in txt]
    else:
        result["resource_model_missing"]=-1
        result["fatal"]=["Missing client game logfile"]
finally:
    if client:terminate(client)
    if "xvfb" in locals():terminate(xvfb)
    if server.poll() is None:
        try:command(server,"stop")
        except Exception:pass
        try:server.wait(timeout=40)
        except subprocess.TimeoutExpired:terminate(server)
    sthread.join(timeout=5)
    if "cthread" in locals():cthread.join(timeout=5)
    (EVIDENCE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    record("RESULT "+json.dumps(result,ensure_ascii=False))
assert result["server_ready"] and result["client_joined"],"Real client did not join real multiplayer server"
assert result["render_thread"] and result["atlas_ready"],"Client did not render its scene/texture atlases"
assert result["forge_login_compressed"] and result["forge_login_restored"],"Lossless 50k RGB registry sync not confirmed on both Forge endpoints"
assert result["resource_model_missing"]==0,"RGB asset paths not loaded by client"
assert not result["fatal"],"Minecraft client fatal shader/renderer/C&B incompatibility"
assert result["screenshots"],"Failed to capture real game scene"
assert result["rgb_light_propagation_verified"],"RGB light propagation runtime pixel-channel probe failed"
assert result["cnb_sculpted_fixture"],"C&B 4095 RGB microbits fixture was not constructed"
assert result["cnb_rgb_propagation_verified"],"C&B chiselled RGB-colored light failed to propagate into adjacent voxel"
record("PASS: Real Forge 1.20.1 client/server session, registered RGB world, render, 50k assets and saved screenshot")
