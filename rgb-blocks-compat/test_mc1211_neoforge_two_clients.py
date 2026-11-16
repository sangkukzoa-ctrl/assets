#!/usr/bin/env python3
"""Strict Minecraft 1.21.1 NeoForge TWO real-production-client acceptance.

Uses actual NeoForge dedicated server, live Chisels & Bits 4095-microbit RGB
emission, native Sodium and Iris, manual/auto state packets and live server
RED -> GREEN -> AIR block changes, with per-channel neighboring RGB on BOTH.
The CI-only probe runs in an instrumented JAR, never in the release artifact.
"""
import json,os,signal,pathlib,subprocess,threading,time,urllib.request,zipfile,tarfile,hashlib,shutil
from urllib.parse import urlencode
from pathlib import Path
STRICT_LIGHT_PROBE=os.environ.get("RGB_PORT_STRICT_LIGHT_PROBE")=="1"
SHADER_ON=os.environ.get("RGB_PORT_SHADER_ON")=="1"
ROOT=Path("mc1211-neoforge-two-clients"); SERVER=ROOT/"server";GAME=ROOT/"client";PEER=ROOT/"peer";EVIDENCE=ROOT/"evidence"
for p in (SERVER/"mods",GAME/"mods",PEER/"mods",EVIDENCE):p.mkdir(parents=True,exist_ok=True)
def info(msg):
    print(msg,flush=True)
    with (EVIDENCE/"events.log").open("a") as f:f.write(msg+"\n")
def fetch(url,out):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-1.3.1-NeoForge-RealGameplay-Acceptance/1.0"}),timeout=240) as r:data=r.read()
    out.write_bytes(data);info("FETCH "+str(out)+" "+str(len(data)));return data
def jsonurl(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-1.3.1-NeoForge-RealGameplay-Acceptance/1.0"}),timeout=120) as r:return json.load(r)
def download_mod(project,target):
    params=urlencode({"game_versions":json.dumps(["1.21.1"]),"loaders":json.dumps(["neoforge"])})
    releases=jsonurl(f"https://api.modrinth.com/v2/project/{project}/version?{params}")
    versions=[v for v in releases if target in v.get("version_number","")]
    if not versions:raise RuntimeError("Missing NeoForge mod "+project+" version "+target)
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
                if any(x in line for x in ("Done (","joined the game","lost connection","ERROR","FATAL","RGB mode","Render thread","Failed","RGB_PORT_NEO_PEER_","RGB_PORT_LIGHT_PROBE_PASS","RGB_PORT_CNB_LIGHT_PROBE_PASS")):
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
def await_new_line(lines,needle,start_index,proc,limit,label):
    start=time.monotonic()
    while time.monotonic()-start<limit:
        if any(needle in line for line in lines[start_index:]):return True
        if proc.poll() is not None:break
        time.sleep(.7)
    info("MISSING NEW "+label+" : "+needle+" process="+str(proc.poll()))
    return False
def cmd(p,s):
    p.stdin.write(s+"\n");p.stdin.flush();info("SERVER "+s)
def terminate(p):
    if p.poll() is None:
        try:os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:p.wait(timeout=25)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)

jar_candidates=[p for p in Path("port-work/mc1211-neoforge/build/libs").glob("*.jar") if "-dev" not in p.name and "-sources" not in p.name]
assert jar_candidates,"Missing built RGB Blocks 1.21.1 native NeoForge production jar"
jar=max(jar_candidates,key=lambda p:p.stat().st_size)
with zipfile.ZipFile(jar) as z:
    colors=json.loads(z.read("assets/rgbblocks/palette.json"));assert len(colors)==16687
    assert json.loads(z.read("pack.mcmeta"))["pack"]["pack_format"]==34
    assert "META-INF/neoforge.mods.toml" in z.namelist(), "Expected native NeoForge mod metadata"
chosen=next(c for c in colors if c["red"]>180 and c["green"]<100 and c["blue"]<100)
block="rgbblocks:rgb_%s_%d_%d_%d"%(chosen["group"],chosen["red"],chosen["green"],chosen["blue"])
green_color=next(c for c in colors if c["green"]>200 and c["red"]<80 and c["blue"]<80)
green="rgbblocks:rgb_%s_%d_%d_%d"%(green_color["group"],green_color["red"],green_color["green"],green_color["blue"])
shutil.copy2(jar,GAME/"mods"/jar.name);shutil.copy2(jar,SERVER/"mods"/jar.name)
cb="chisels-and-bits-neoforge-21.1.32.jar"
fetch("https://mediafilez.forgecdn.net/files/7405/270/"+cb,SERVER/"mods"/cb)
shutil.copy2(SERVER/"mods"/cb,GAME/"mods"/cb)
sodium=download_mod("sodium","mc1.21.1-0.6.13-neoforge")
iris=download_mod("iris","1.8.12+1.21.1-neoforge")
info("CLIENT_ECOSYSTEM "+json.dumps({"neoforge":"21.1.265","chiselsandbits":cb,"sodium":sodium,"iris":iris}))
shader_filename=None
if SHADER_ON:
    shader=jsonurl("https://api.modrinth.com/v2/version/Bqen1mJX")
    assert shader["version_number"]=="r5.9.3", "Pinned Complementary Reimagined shader changed"
    asset=next(f for f in shader["files"] if f["filename"].lower().endswith(".zip"))
    shader_filename=asset["filename"]
    shaderpath=GAME/"shaderpacks"/shader_filename
    shaderpath.parent.mkdir(parents=True,exist_ok=True)
    buffer=fetch(asset["url"],shaderpath)
    if asset.get("hashes",{}).get("sha512"):
        assert hashlib.sha512(buffer).hexdigest()==asset["hashes"]["sha512"],"Shader SHA512 mismatch"
    cfg=GAME/"config";cfg.mkdir(parents=True,exist_ok=True)
    (cfg/"iris.properties").write_text("shaderPack="+shader_filename+"\nenableShaders=true\n",encoding="utf-8")
    info("RGB_SHADER_TEST_ON "+shader_filename)
fetch("https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.265/neoforge-21.1.265-installer.jar",SERVER/"installer.jar")
install=subprocess.run(["java","-jar","installer.jar","--installServer"],cwd=SERVER,
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=460)
(EVIDENCE/"neoforge-installer.log").write_text(install.stdout,encoding="utf-8")
assert install.returncode==0 and (SERVER/"run.sh").exists(),"NeoForge server installer failed"
(SERVER/"user_jvm_args.txt").write_text("-Xms512M\n-Xmx2000M\n",encoding="utf-8")
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
motd=RGBBlocks 1.21.1 NeoForge actual network RGB fixture
""")
server=subprocess.Popen(["bash","./run.sh","nogui"],
    cwd=SERVER,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
slog,sthread=proc_reader(server,"SERVER",EVIDENCE/"server.log")
client=None; xvfb=None; peer=None; peer_display=None
result={"minecraft":"1.21.1","loader":"NeoForge 21.1.265","scope":"Strict CI-only RGB propagation/C&B microbit probe" if STRICT_LIGHT_PROBE else "Production NeoForge client/server join, mod stack, RGB scene and screenshot; NOT colored-light or C&B sculpted proof",
        "instrumented_ci_probe":STRICT_LIGHT_PROBE,
        "shader_requested":SHADER_ON,"shader_pack":shader_filename,"shader_active":False,
        "palette_count":len(colors),"rgb_test_block":block,"server_ready":False,"fml_player_joined":False,
        "rgb_commands":False,"rgb_light_propagation_verified":False,"cnb_sculpted_fixture":False,"cnb_rgb_propagation_verified":False,"render_thread":False,"texture_atlas_ready":False,
        "missing_rgb_models":None,"crashes":[],"screenshots":[],
        "green_block":green,"primary_rgb_verified":False,"primary_cnb_rgb_verified":False,
        "peer_joined":False,"peer_rgb_verified":False,"peer_cnb_rgb_verified":False,
        "both_manual_sync":False,"both_auto_sync":False,"both_green_update":False,
        "both_source_removal":False,"both_clients_alive_after_edits":False,
        "both_manual_deferred":False,"both_manual_baked":False,
        "peer_logout_snapshot_saved":False,"peer_rejoin_verified":False,
        "peer_snapshot_loaded":False,"peer_world_id_unchanged":False,
        "peer_reconnected_rgb_cnb":False,"peer_chunk_unloaded":False,
        "peer_chunk_returned":False,"primary_alive_through_reconnect":False}
try:
    result["server_ready"]=await_line(slog,"Done (",server,180)
    if not result["server_ready"]:raise AssertionError("NeoForge server failed to become ready")
    for c in ["gamerule doDaylightCycle false","time set midnight","weather clear","forceload add 0 0",
              "fill -5 119 -3 5 119 12 minecraft:stone",
              f"setblock -2 121 7 {block}",f"setblock 0 121 7 {block}_glow",f"setblock 2 121 7 {block}_glass",
              "setblock 4 121 7 chiselsandbits:chiseled",
              f"execute if block -2 121 7 {block} run say RGB_NORMAL_FIXTURE_READY",
              f"execute if block 0 121 7 {block}_glow run say RGB_GLOW_FIXTURE_READY",
              f"execute if block 2 121 7 {block}_glass run say RGB_GLASS_FIXTURE_READY",
              "rgb auto","rgb setbake all","rgb get"]:
        cmd(server,c);time.sleep(.35)
    assert await_line(slog,"RGB_NORMAL_FIXTURE_READY",server,50),"RGB normal fixture not present"
    assert await_line(slog,"RGB_GLOW_FIXTURE_READY",server,50),"RGB glow fixture not present"
    assert await_line(slog,"RGB_GLASS_FIXTURE_READY",server,50),"RGB glass fixture not present"
    # Only instrumented strict builds can emit actual microbit fixture evidence.
    result["cnb_sculpted_fixture"]=await_line(slog,"RGB_PORT_CNB_FIXTURE_PASS",server,70) if STRICT_LIGHT_PROBE else False
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
    launchcmd=[str(launcher.resolve()),"--main-dir",str((ROOT/"launcher-data").resolve()),"start","neoforge:21.1.265",
       "--mc-dir",str(GAME.resolve()),"-u","RGBPortTester","--join-server","127.0.0.1",
       "--join-server-port","25567","--resolution","1280x720"]
    launchcmd.append("--jvm-arg=-Xmx1550M")
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
        # Platform extends under the camera at y=119 to prevent falling off
        # before the screenshot. Check that the server actually executed TP.
        assert await_line(slog,"Teleported RGBPortTester to 0.500000, 120.000000, 0.500000",server,25), "Camera teleport not acknowledged"
        cmd(server,"effect give RGBPortTester minecraft:night_vision 45 0 true")
        cmd(server,"gamemode creative RGBPortTester")
        cmd(server,"rgb bake")
        time.sleep(35)
        screenshot=EVIDENCE/("real-neoforge-rgb-normal-glow-glass-{}{}.png".format("shader-on" if SHADER_ON else "shader-off", "-strict" if STRICT_LIGHT_PROBE else ""))
        shot=subprocess.run(["scrot",str(screenshot.resolve())],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
        if shot.returncode==0 and screenshot.is_file():
            result["screenshots"].append({"name":screenshot.name,"bytes":screenshot.stat().st_size})
        else:info("FAILED SCREENSHOT "+shot.stdout)
    # Primary must already have seen BOTH real RGB color and C&B sculpted
    # neighboring light, not just the game's loader/render-thread startup.
    assert STRICT_LIGHT_PROBE and not SHADER_ON,"Strict NeoForge two-client acceptance requires CI-only light probe without shader"
    result["primary_rgb_verified"]=await_line(clog,"RGB_PORT_LIGHT_PROBE_PASS",client,100)
    result["primary_cnb_rgb_verified"]=await_line(clog,"RGB_PORT_CNB_LIGHT_PROBE_PASS",client,100)
    assert result["primary_rgb_verified"] and result["primary_cnb_rgb_verified"],"Primary real NeoForge client lacks RGB / C&B colored propagation"

    # Concurrent SECOND production NeoForge launcher, independent game
    # directory, real FML join to SAME dedicated server and source chunks.
    shutil.copytree(GAME/"mods",PEER/"mods",dirs_exist_ok=True)
    shutil.copy2(GAME/"options.txt",PEER/"options.txt")
    peer_display=subprocess.Popen(["Xvfb",":88","-screen","0","1024x576x24","-ac","+extension","GLX"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    time.sleep(2)
    peer_env=env.copy();peer_env["DISPLAY"]=":88"
    peer_cmd=list(launchcmd)
    peer_cmd[peer_cmd.index(str(GAME.resolve()))]=str(PEER.resolve())
    peer_cmd[peer_cmd.index("RGBPortTester")]="RGBPortPeer"
    peer_cmd[peer_cmd.index("1280x720")]="1024x576"
    info("LAUNCH_SECOND_REAL_NEOFORGE_CLIENT "+str(peer_cmd))
    peer=subprocess.Popen(peer_cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
         bufsize=1,env=peer_env,start_new_session=True)
    peerlog,peerthread=proc_reader(peer,"PEER",EVIDENCE/"peer-launcher.log")
    result["peer_joined"]=await_line(slog,"RGBPortPeer joined the game",server,210)
    assert result["peer_joined"],"Second NeoForge production client did not join the same dedicated server"
    cmd(server,"tp RGBPortTester -1.5 120.0 0.5 facing 0.5 121.5 7.5")
    cmd(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    cmd(server,"gamemode creative RGBPortPeer")
    result["peer_rgb_verified"]=await_line(peerlog,"RGB_PORT_LIGHT_PROBE_PASS",peer,135)
    result["peer_cnb_rgb_verified"]=await_line(peerlog,"RGB_PORT_CNB_LIGHT_PROBE_PASS",peer,135)
    assert result["peer_rgb_verified"] and result["peer_cnb_rgb_verified"],"Second NeoForge client lacks C&B sculpted microbit RGB illumination"

    cmd(server,"rgb manual")
    first_manual=await_line(clog,"RGB_PORT_NEO_PEER_MANUAL_PASS",client,85)
    peer_manual=await_line(peerlog,"RGB_PORT_NEO_PEER_MANUAL_PASS",peer,85)
    result["both_manual_sync"]=first_manual and peer_manual
    assert result["both_manual_sync"],"NeoForge MANUAL mode packet not synchronized on BOTH real clients"
    cmd(server,"rgb auto")
    first_auto=await_line(clog,"RGB_PORT_NEO_PEER_AUTO_PASS",client,85)
    peer_auto=await_line(peerlog,"RGB_PORT_NEO_PEER_AUTO_PASS",peer,85)
    result["both_auto_sync"]=first_auto and peer_auto
    assert result["both_auto_sync"],"NeoForge AUTO mode packet not restored on BOTH real clients"

    # Both are placed in the same tracked chunks BEFORE the actual live
    # source replacement. Never test an unloaded first player by accident.
    cmd(server,"tp RGBPortTester -1.5 120.0 0.5 facing 0.5 121.5 7.5")
    cmd(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    time.sleep(3)
    cmd(server,f"setblock 0 121 7 {green}_glow")
    first_green=await_line(clog,"RGB_PORT_NEO_PEER_GREEN_PASS",client,130)
    peer_green=await_line(peerlog,"RGB_PORT_NEO_PEER_GREEN_PASS",peer,130)
    result["both_green_update"]=first_green and peer_green
    assert result["both_green_update"],"Live RED->GREEN source and adjacent per-channel RGB failed on two NeoForge clients"

    # Another server-authoritative edit: remove GREEN entirely; both
    # client caches must drop it while preserving the separate RED C&B light.
    cmd(server,"setblock 0 121 7 minecraft:air")
    cmd(server,"execute if block 0 121 7 minecraft:air run say RGB_PORT_NEO_SERVER_REMOVAL_ACK")
    assert await_line(slog,"RGB_PORT_NEO_SERVER_REMOVAL_ACK",server,35),"Server source removal command failed"
    first_removed=await_line(clog,"RGB_PORT_NEO_PEER_REMOVAL_PASS",client,135)
    peer_removed=await_line(peerlog,"RGB_PORT_NEO_PEER_REMOVAL_PASS",peer,135)
    result["both_source_removal"]=first_removed and peer_removed
    result["both_clients_alive_after_edits"]=client.poll() is None and peer.poll() is None
    assert result["both_source_removal"],"NeoForge two-client GREEN->AIR did not clear stale green cache"
    assert result["both_clients_alive_after_edits"],"At least one client closed during multiplayer source edits"

    # MANUAL must suppress GREEN light propagation from a real server edit,
    # but /rgb bake must then replay the dirty positions to BOTH online users.
    cmd(server,"rgb manual")
    time.sleep(4)
    cmd(server,f"setblock 0 121 7 {green}_glow")
    frozen_first=await_line(clog,"RGB_PORT_NEO_MANUAL_DEFER_PASS",client,110)
    frozen_peer=await_line(peerlog,"RGB_PORT_NEO_MANUAL_DEFER_PASS",peer,110)
    result["both_manual_deferred"]=frozen_first and frozen_peer
    assert result["both_manual_deferred"],"NeoForge MANUAL failed to freeze old red-dominant light on both clients"
    cmd(server,"rgb setbake all")
    cmd(server,"rgb bake")
    baked_first=await_line(clog,"RGB_PORT_NEO_MANUAL_BAKE_PASS",client,155)
    baked_peer=await_line(peerlog,"RGB_PORT_NEO_MANUAL_BAKE_PASS",peer,155)
    result["both_manual_baked"]=baked_first and baked_peer
    assert result["both_manual_baked"],"NeoForge MANUAL /rgb bake did not replay GREEN on both clients"
    assert client.poll() is None and peer.poll() is None,"NeoForge client quit during dirty manual bake"

    # Save true client-side RGB lightmap on logout, restart exactly the SAME
    # peer installation and require its persisted color and 4095-bit C&B.
    original_world_ids=[line.split("worldId=",1)[1].split()[0] for line in peerlog
        if "RGB_PORT_NEO_PEER_MANUAL_PASS worldId=" in line]
    assert original_world_ids and original_world_ids[-1],"NeoForge peer did not receive the real world UUID"
    old_world_id=original_world_ids[-1]
    cmd(server,"rgb auto")
    time.sleep(4)
    before_kick=len(slog);before_save=len(peerlog)
    cmd(server,"kick RGBPortPeer RGB_PORT_NEO_RECONNECT")
    assert await_new_line(slog,"RGBPortPeer lost connection",before_kick,server,55,
                          "peer_disconnect"),"NeoForge peer failed to disconnect"
    assert await_new_line(peerlog,"Saved RGB lightmap:",before_save,peer,55,
                          "peer_rgb_snapshot_save"),"NeoForge logout did not save RGB lightmap"
    files=sorted((PEER/"rgbblocks"/"lightmaps").rglob("*.rgl.gz"))
    result["peer_logout_snapshot_saved"]=bool(files) and all(p.stat().st_size>100 for p in files)
    assert result["peer_logout_snapshot_saved"],"NeoForge peer lightmap file absent/empty after logout"
    info("NEO_PEER_SAVED_SNAPSHOTS "+json.dumps([
        {"relative":str(p.relative_to(PEER)),"bytes":p.stat().st_size,
         "sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]))
    terminate(peer);peerthread.join(timeout=8)
    previous=PEER/"logs/latest.log"
    if previous.is_file():shutil.copy2(previous,EVIDENCE/"minecraft-peer-pre-reconnect.log")
    before_rejoin=len(slog)
    reconnect_cmd=list(peer_cmd)+["--jvm-arg=-Drgbport.ci.reconnect=true"]
    info("NEO_RESTART_PEER_SAME_DIRECTORY "+str(reconnect_cmd))
    peer=subprocess.Popen(reconnect_cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,bufsize=1,env=peer_env,start_new_session=True)
    peerlog,peerthread=proc_reader(peer,"PEER_RECONNECT",EVIDENCE/"peer-reconnect-launcher.log")
    result["peer_rejoin_verified"]=await_new_line(slog,"RGBPortPeer joined the game",
         before_rejoin,server,210,"second_login_of_same_player")
    assert result["peer_rejoin_verified"],"NeoForge same client directory could not reconnect"
    cmd(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    result["peer_snapshot_loaded"]=await_line(peerlog,"Loaded RGB lightmap:",peer,105)
    assert result["peer_snapshot_loaded"],"Fresh NeoForge client did not load saved RGB/C&B lightmap"
    result["peer_reconnected_rgb_cnb"]=await_line(peerlog,"RGB_PORT_NEO_RECONNECT_LIGHT_PASS",peer,140)
    assert result["peer_reconnected_rgb_cnb"],"NeoForge reconnect lost real GREEN RGB or RED C&B bit emission"
    new_world_ids=[line.split("worldId=",1)[1].split()[0] for line in peerlog
       if "RGB_PORT_NEO_RECONNECT_LIGHT_PASS worldId=" in line]
    result["peer_world_id_unchanged"]=bool(new_world_ids) and new_world_ids[-1]==old_world_id
    assert result["peer_world_id_unchanged"],"NeoForge world UUID did not survive disconnect/reconnect"
    result["primary_alive_through_reconnect"]=client.poll() is None
    assert result["primary_alive_through_reconnect"],"First client stopped during peer reconnect"

    # Force remote player OUTSIDE view-distance, require real client chunk
    # eviction, then return and require restored GREEN and C&B colored light.
    cmd(server,"tp RGBPortPeer 256.5 120.0 0.5")
    result["peer_chunk_unloaded"]=await_line(peerlog,"RGB_PORT_NEO_CHUNK_UNLOAD_PASS",peer,105)
    assert result["peer_chunk_unloaded"],"NeoForge never unloaded remote RGB source chunk"
    cmd(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    result["peer_chunk_returned"]=await_line(peerlog,"RGB_PORT_NEO_CHUNK_RETURN_PASS",peer,150)
    assert result["peer_chunk_returned"],"NeoForge returned chunk without restoring full and C&B colored light"
    assert peer.poll() is None and client.poll() is None,"NeoForge real peer exited during chunk restore"
    live=GAME/"logs/latest.log"
    txt=live.read_text(encoding="utf-8",errors="replace") if live.is_file() else ""
    if live.is_file():shutil.copy2(live,EVIDENCE/"minecraft-client.log")
    if SHADER_ON:
        shade_lines=[line for line in (txt+"\n"+"".join(clog)).splitlines()
          if ("shader" in line.lower() or "iris" in line.lower())]
        (EVIDENCE/"iris-complementary-evidence.log").write_text("\n".join(shade_lines),encoding="utf-8")
        evidence="\n".join(shade_lines).lower()
        missing=["shaders are disabled","falling back to normal rendering",
                 "shaderpack could not be loaded","failed to load shaderpack"]
        result["shader_active"]=(shader_filename.lower() in evidence
            and any(word in evidence for word in ("using shaderpack","loading shaderpack","loaded shaderpack","shaderpack loaded","shader pack"))
            and not any(word in evidence for word in missing))
        info("SHADER_CONFIRMATION active="+str(result["shader_active"])+" lines="+str(len(shade_lines)))
    result["rgb_light_propagation_verified"]="RGB_PORT_LIGHT_PROBE_PASS" in (txt+"\n"+"".join(clog))
    result["cnb_rgb_propagation_verified"]="RGB_PORT_CNB_LIGHT_PROBE_PASS" in (txt+"\n"+"".join(clog))
    result["missing_rgb_models"]=sum(("rgbblocks:models/item/" in line and "FileNotFoundException" in line) or
      ("rgbblocks:blockstates/" in line and "missing model for variant" in line)
       for line in txt.splitlines()) if txt else -1
    result["crashes"]=[needle for needle in ("MixinApplyError","NoSuchMethodError","NoClassDefFoundError","Crash report saved","Sodium 0.6 RGB vertex bridge failed")
      if needle in txt]
finally:
    if peer:terminate(peer)
    if peer_display:terminate(peer_display)
    if "peerthread" in locals():peerthread.join(timeout=5)
    if client:terminate(client)
    if xvfb:terminate(xvfb)
    if server.poll() is None:
        try:cmd(server,"stop")
        except Exception:pass
        try:server.wait(timeout=45)
        except subprocess.TimeoutExpired:terminate(server)
    sthread.join(timeout=5)
    if "cthread" in locals():cthread.join(timeout=5)
    if (PEER/"logs/latest.log").is_file():
        shutil.copy2(PEER/"logs/latest.log",EVIDENCE/"minecraft-peer.log")
    if (EVIDENCE/"peer-reconnect-launcher.log").is_file():
        contents=(EVIDENCE/"peer-reconnect-launcher.log").read_text(encoding="utf-8",errors="replace")
        notices=[line for line in contents.splitlines()
                 if any(term in line for term in ("RGB_PORT_NEO_","RGB Blocks","ERROR","FATAL","MixinApplyError"))]
        for line in notices[-55:]:info("NEO_PEER_RECONNECT_DIAG "+line[-900:])
    for name,dir in (("PRIMARY",GAME),("PEER",PEER)):
        p=dir/"logs/latest.log"
        if p.is_file():
            records=[line for line in p.read_text(encoding="utf-8",errors="replace").splitlines()
                     if any(k in line for k in (
                         "RGB_PORT_NEO_PEER_","RGB_PORT_CNB_","RGB_PORT_LIGHT_",
                         "MixinApplyError","NoSuchMethodError","Exception"))]
            for record in records[-45:]:
                info("NEOFORGE_TWO_PEER_DIAG_"+name+" "+record[-800:])
    (EVIDENCE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    info("RESULT "+json.dumps(result,ensure_ascii=False))
assert result["server_ready"] and result["fml_player_joined"],"MC1.21.1 real client/server connection failure"
assert result["render_thread"] and result["texture_atlas_ready"],"MC1.21.1 graphical scene not loaded"
assert result["missing_rgb_models"]==0,"One or more RGB models unavailable in actual NeoForge client"
assert not result["crashes"],"Actual client RGB/C&B/Sodium/Iris Mixin or class crash"
assert result["screenshots"],"No screenshot of real in-world RGB scene"
if SHADER_ON:
    assert result["shader_active"],"Complementary Reimagined shader was not confirmed ACTIVE in Iris"
if STRICT_LIGHT_PROBE:
    assert result["rgb_light_propagation_verified"],"NeoForge adjacent RGB channel light did not propagate"
    assert result["cnb_sculpted_fixture"],"NeoForge Chisels & Bits sculpted RGB microbit fixture missing"
    assert result["cnb_rgb_propagation_verified"],"NeoForge C&B RGB microbit light did not propagate"
    assert result["primary_rgb_verified"] and result["primary_cnb_rgb_verified"]
    assert result["peer_joined"] and result["peer_rgb_verified"] and result["peer_cnb_rgb_verified"]
    assert result["both_manual_sync"] and result["both_auto_sync"]
    assert result["both_green_update"] and result["both_source_removal"]
    assert result["both_clients_alive_after_edits"],"NeoForge peer disconnected before live edit finished"
    assert result["both_manual_deferred"] and result["both_manual_baked"],"NeoForge two-client manual bake acceptance failed"
    assert all(result[key] for key in (
        "peer_logout_snapshot_saved","peer_rejoin_verified","peer_snapshot_loaded",
        "peer_world_id_unchanged","peer_reconnected_rgb_cnb",
        "peer_chunk_unloaded","peer_chunk_returned","primary_alive_through_reconnect"
    )), "NeoForge strict RGB/C&B saved restart and chunk reload acceptance failed"
    info("PASS: NeoForge 1.21.1 TWO real clients RGB+C&B, RED->GREEN->AIR, manual bake deferred/replayed, persistent lightmap logout/reconnect and real chunk unload/return")
else:
    info("PASS: MC1.21.1 NeoForge real client/server join + RGB block scene screenshot + modded render initialization; per-channel RGB/C&B microbits NOT YET VERIFIED")
