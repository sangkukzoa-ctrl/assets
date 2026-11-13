#!/usr/bin/env python3
"""Minecraft 1.20.1 REAL Forge server + TWO CONCURRENT clients RGB sync test.

Joins via actual Forge mod handshake and capture RGB normal, glow and glass
placed in server world; verifies world edit, remote connection, render pipeline,
persisted network commands and 3D screenshot. This is a strict smoke, not a
shader pixel-equivalence proof.
"""
import json,os,signal,pathlib,subprocess,threading,time,urllib.request,zipfile,tarfile,hashlib,shutil
from pathlib import Path

SHADER_ON=False  # This dedicated dual-client acceptance checks vanilla/Embeddium renderer.
ROOT=Path("mc1201-forge-two-clients")
SERVER=ROOT/"server";GAME=ROOT/"client";PEER=ROOT/"peer"
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
green_choice=next(c for c in palette if c["green"]>200 and c["red"]<80 and c["blue"]<80)
green="rgbblocks:rgb_%s_%d_%d_%d"%(green_choice["group"],green_choice["red"],green_choice["green"],green_choice["blue"])
shutil.copy2(jar,S_MODS/jar.name)
shutil.copy2(jar,C_MODS/jar.name)
cb="chisels-and-bits-forge-20.1.20.jar"
fetch("https://mediafilez.forgecdn.net/files/7620/767/"+cb,S_MODS/cb)
shutil.copy2(S_MODS/cb,C_MODS/cb)
emb=fetch_mod("embeddium","0.3.31")
oculus=fetch_mod("oculus","1.8.0")
shader_filename=None
if SHADER_ON:
    # Oculus 1.20.1 is Iris-based, but uses MODID 'oculus', so its
    # actual config file is config/oculus.properties (verified upstream).
    version=jsonurl("https://api.modrinth.com/v2/version/Bqen1mJX")
    assert version["version_number"]=="r5.9.3","Complementary version changed"
    shaderfile=next(x for x in version["files"] if x["filename"].lower().endswith(".zip"))
    shader_filename=shaderfile["filename"]
    dest=GAME/"shaderpacks"/shader_filename
    dest.parent.mkdir(parents=True,exist_ok=True)
    data=fetch(shaderfile["url"],dest)
    if shaderfile.get("hashes",{}).get("sha512"):
        assert hashlib.sha512(data).hexdigest()==shaderfile["hashes"]["sha512"],"Shader integrity mismatch"
    cfg=GAME/"config";cfg.mkdir(parents=True,exist_ok=True)
    (cfg/"oculus.properties").write_text("shaderPack="+shader_filename+"\nenableShaders=true\n",encoding="utf-8")
    record("FORGE_COMPLEMENTARY_SHADER_REQUESTED "+shader_filename)

# Real Forge install server and a pre-generated flat world.
fetch("https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.28/forge-1.20.1-47.4.28-installer.jar",SERVER/"installer.jar")
install=subprocess.run(["java","-jar","installer.jar","--installServer"],cwd=SERVER,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=380)
(EVIDENCE/"forge-installer.log").write_text(install.stdout,encoding="utf-8")
assert install.returncode==0 and (SERVER/"run.sh").exists(),"Forge server installation failed"
(SERVER/"eula.txt").write_text("eula=true\n")
(SERVER/"user_jvm_args.txt").write_text("-Xms512M\n-Xmx2000M\n-Dforge.logging.markers=NETWORK,REGISTRIES\n-Dforge.logging.console.level=debug\n")
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
peer=None
peer_display=None
result={"scope":"Minecraft 1.20.1 production Forge 47.4.28 RGBBlock+C&B+Embeddium/Oculus, actual network connected RGB test scene",
        "shader_enabled":False,"shader_requested":SHADER_ON,"shader_pack":shader_filename,"screenshots":[],"block":block,"server_ready":False,"client_joined":False,
        "rgb_server_commands":False,"rgb_light_propagation_verified":False,"cnb_sculpted_fixture":False,"cnb_rgb_propagation_verified":False,"render_thread":False,"atlas_ready":False,"resource_model_missing":None}
result.update({"peer_joined":False,"peer_rgb_probe_verified":False,
               "peer_cnb_rgb_probe_verified":False,"first_rgb_probe_verified":False,
               "first_cnb_rgb_probe_verified":False,"two_clients_manual_sync":False,
               "two_clients_auto_sync":False,"two_clients_live_rgb_sync_verified":False,
               "both_clients_alive_after_sync":False,"green_block":green})
try:
    result["server_ready"]=await_pattern(slog,"Done (",server,180,"server_boot")
    if not result["server_ready"]:raise AssertionError("Forge dedicated server did not reach Ready")
    for c in ["gamerule doDaylightCycle false","time set midnight","weather clear","forceload add 0 0",
              "fill -5 119 -3 5 119 12 minecraft:stone",
              f"setblock -2 121 7 {block}",
              f"setblock 0 121 7 {block}_glow",
              f"setblock 2 121 7 {block}_glass",
              "setblock 4 121 7 chiselsandbits:chiseled",
              f"execute if block -2 121 7 {block} run say RGB_FIXTURE_NORMAL_READY",
              f"execute if block 0 121 7 {block}_glow run say RGB_FIXTURE_GLOW_READY",
              f"execute if block 2 121 7 {block}_glass run say RGB_FIXTURE_GLASS_READY",
              "rgb auto","rgb setbake all","rgb get"]:
        command(server,c);time.sleep(0.4)
    assert await_pattern(slog,"RGB_FIXTURE_NORMAL_READY",server,50,"normal_fixture"),"RGB normal block not placed"
    assert await_pattern(slog,"RGB_FIXTURE_GLOW_READY",server,50,"glow_fixture"),"RGB glow block not placed"
    assert await_pattern(slog,"RGB_FIXTURE_GLASS_READY",server,50,"glass_fixture"),"RGB glass block not placed"
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
    launchcmd.append("--jvm-arg=-Xmx1600M")
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

    # Real two-peer verification: both independent game processes remain connected
    # to the same Forge dedicated server during manual/auto and live RGB changes.
    assert result["client_joined"] and result["atlas_ready"],"Primary Forge client not ready"
    result["first_rgb_probe_verified"]=await_pattern(clog,"RGB_PORT_LIGHT_PROBE_PASS",client,100,"first_rgb_source")
    result["first_cnb_rgb_probe_verified"]=await_pattern(clog,"RGB_PORT_CNB_LIGHT_PROBE_PASS",client,100,"first_cnb_rgb")
    assert result["first_rgb_probe_verified"] and result["first_cnb_rgb_probe_verified"],"First client lacks RGB+C&B microbit light"

    (PEER/"mods").mkdir(parents=True,exist_ok=True)
    shutil.copytree(C_MODS,PEER/"mods",dirs_exist_ok=True)
    shutil.copy2(GAME/"options.txt",PEER/"options.txt")
    peer_display=subprocess.Popen(["Xvfb",":87","-screen","0","1024x576x24","-ac","+extension","GLX"],
           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    time.sleep(2)
    peer_env=env.copy()
    peer_env["DISPLAY"]=":87"
    peer_cmd=list(launchcmd)
    peer_cmd[peer_cmd.index(str(GAME.resolve()))]=str(PEER.resolve())
    peer_cmd[peer_cmd.index("RGBPortTester")]="RGBPortPeer"
    peer_cmd[peer_cmd.index("1280x720")]="1024x576"
    record("LAUNCH_SECOND_CLIENT "+str(peer_cmd))
    peer=subprocess.Popen(peer_cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=peer_env,
                          text=True,start_new_session=True,bufsize=1)
    peerlog,peerthread=runthread(peer,"PEER",EVIDENCE/"peer-console.log")
    result["peer_joined"]=await_pattern(slog,"RGBPortPeer joined the game",server,210,"second_FML_player_join")
    assert result["peer_joined"],"Second real Forge client did not join the same server"
    command(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    command(server,"gamemode creative RGBPortPeer")
    result["peer_rgb_probe_verified"]=await_pattern(peerlog,"RGB_PORT_LIGHT_PROBE_PASS",peer,150,"second_rgb_source")
    result["peer_cnb_rgb_probe_verified"]=await_pattern(peerlog,"RGB_PORT_CNB_LIGHT_PROBE_PASS",peer,150,"second_cnb_rgb")
    assert result["peer_rgb_probe_verified"] and result["peer_cnb_rgb_probe_verified"],"Second client lacks RGB/C&B per-channel light"

    # Server-authoritative RGB modes must reach BOTH simultaneously online users.
    command(server,"rgb manual")
    manual_first=await_pattern(clog,"RGB_PORT_PEER_MANUAL_SYNC_PASS",client,75,"primary_manual_packet")
    manual_peer=await_pattern(peerlog,"RGB_PORT_PEER_MANUAL_SYNC_PASS",peer,75,"peer_manual_packet")
    result["two_clients_manual_sync"]=manual_first and manual_peer
    assert result["two_clients_manual_sync"],"MANUAL mode not synchronized on both clients"
    command(server,"rgb auto")
    auto_first=await_pattern(clog,"RGB_PORT_PEER_AUTO_SYNC_PASS",client,75,"primary_auto_packet")
    auto_peer=await_pattern(peerlog,"RGB_PORT_PEER_AUTO_SYNC_PASS",peer,75,"peer_auto_packet")
    result["two_clients_auto_sync"]=auto_first and auto_peer
    assert result["two_clients_auto_sync"],"AUTO mode not restored on both clients"

    # A live server edit must replace the original red full-block source with
    # a green source for both clients, and adjacent computed light must turn green.
    command(server,f"setblock 0 121 7 {green}_glow")
    green_first=await_pattern(clog,"RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS",client,100,"primary_live_green")
    green_peer=await_pattern(peerlog,"RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS",peer,100,"peer_live_green")
    result["two_clients_live_rgb_sync_verified"]=green_first and green_peer
    result["both_clients_alive_after_sync"]=client.poll() is None and peer.poll() is None
    assert result["two_clients_live_rgb_sync_verified"],"Live server RGB source/lighting edit did not propagate to both clients"
    assert result["both_clients_alive_after_sync"],"At least one multiplayer client exited during live update"
    if result["client_joined"]:
        command(server,"tp RGBPortTester 0.5 120.0 0.5 facing 0.5 121.5 7.5")
        # The camera must stand on a stone floor at Y=119 through capture;
        # otherwise it falls from Y=120 and a green CI result can show empty sky.
        assert await_pattern(slog,"Teleported RGBPortTester to 0.500000, 120.000000, 0.500000",server,25,"camera_teleport"),"Camera teleport not acknowledged"
        command(server,"effect give RGBPortTester minecraft:night_vision 45 0 true")
        command(server,"gamemode creative RGBPortTester")
        command(server,"rgb bake")
        time.sleep(35)
        screenshot=EVIDENCE/("inworld-rgb-glow-glass-shader-"+("ON" if SHADER_ON else "OFF")+".png")
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
        if SHADER_ON:
            shader_lines=[ln for ln in (txt+"\n"+"".join(clog)).splitlines()
                if ("iris" in ln.lower() or "oculus" in ln.lower()
                    or "shaderpack" in ln.lower() or "complementary" in ln.lower())]
            (EVIDENCE/"oculus-shader-on-evidence.log").write_text(
                "\n".join(shader_lines),encoding="utf-8")
            evidence="\n".join(shader_lines).lower()
            missing=("shaders are disabled","shaderpack could not be loaded",
                     "failed to load shaderpack","falling back to normal rendering")
            result["shader_enabled"]=(shader_filename.lower() in evidence
                and any(phrase in evidence for phrase in
                  ("using shaderpack","loading shaderpack","loaded shaderpack",
                   "shaderpack loaded","shader pack"))
                and not any(reason in evidence for reason in missing))
            record("FORGE_COMPLEMENTARY_SHADER_ACTIVE "+str(result["shader_enabled"])
                   +" log_lines="+str(len(shader_lines)))

        # Keep CI diagnosis in the job log: the client and launcher output are
        # otherwise only uploaded to an artifact, making a failed gate opaque.
        probe_lines=[ln for ln in (txt+"\n"+"".join(clog)).splitlines()
           if any(token in ln for token in (
             "RGB_PORT_", "RGBRealLightEngine", "RGBLightEngine",
             "RGBClientConfig", "RGB Blocks client", "MixinApplyError"))]
        (EVIDENCE/"forge-rgb-probe-diagnostics.log").write_text(
             "\n".join(probe_lines),encoding="utf-8")
        for diagnostic in probe_lines[-36:]:
            record("FORGE_RGB_DIAGNOSTIC "+diagnostic[:500])
        result["probe_diagnostic_count"]=len(probe_lines)
        result["forge_tick_event_seen"]=any("RGB_PORT_FORGE_TICK_EVENT_RECEIVED" in ln for ln in probe_lines)
        result["world_tick_sample_seen"]=any("RGB_PORT_PROBE_CLIENT_TICK_ACTIVE" in ln for ln in probe_lines)

        result["resource_model_missing"]=sum("FileNotFoundException: rgbblocks:models/" in x or
          ("rgbblocks:blockstates/" in x and "missing model for variant" in x)
          for x in txt.splitlines())
        result["fatal"]=[x for x in ["MixinApplyError","NoSuchMethodError","NoClassDefFoundError","Crash report saved"] if x in txt]
    else:
        result["resource_model_missing"]=-1
        result["fatal"]=["Missing client game logfile"]
finally:
    if peer:terminate(peer)
    if peer_display:terminate(peer_display)
    if client:terminate(client)
    if "xvfb" in locals():terminate(xvfb)
    if server.poll() is None:
        try:command(server,"stop")
        except Exception:pass
        try:server.wait(timeout=40)
        except subprocess.TimeoutExpired:terminate(server)
    sthread.join(timeout=5)
    if "cthread" in locals():cthread.join(timeout=5)
    if "peerthread" in locals():peerthread.join(timeout=5)
    if (PEER/"logs/latest.log").is_file():
        shutil.copy2(PEER/"logs/latest.log",EVIDENCE/"minecraft-peer-latest.log")
    (EVIDENCE/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    record("RESULT "+json.dumps(result,ensure_ascii=False))
assert result["server_ready"] and result["client_joined"],"Real client did not join real multiplayer server"
assert result["render_thread"] and result["atlas_ready"],"Client did not render its scene/texture atlases"
assert result["forge_login_compressed"] and result["forge_login_restored"],"Lossless 50k RGB registry sync not confirmed on both Forge endpoints"
assert result["resource_model_missing"]==0,"RGB asset paths not loaded by client"
assert not result["fatal"],"Minecraft client fatal shader/renderer/C&B incompatibility"
assert result["screenshots"],"Failed to capture real game scene"
if SHADER_ON:
    assert result["shader_enabled"],"Oculus failed to activate Complementary in real Forge 1.20.1 game"
assert result["rgb_light_propagation_verified"],"RGB light propagation runtime pixel-channel probe failed"
assert result["cnb_sculpted_fixture"],"C&B 4095 RGB microbits fixture was not constructed"
assert result["cnb_rgb_propagation_verified"],"C&B chiselled RGB-colored light failed to propagate into adjacent voxel"
assert result["first_rgb_probe_verified"] and result["first_cnb_rgb_probe_verified"],"First client's light probes absent"
assert result["peer_joined"] and result["peer_rgb_probe_verified"] and result["peer_cnb_rgb_probe_verified"],"Second client lacks C&B RGB light"
assert result["two_clients_manual_sync"] and result["two_clients_auto_sync"],"Both clients did not receive mode synchronization"
assert result["two_clients_live_rgb_sync_verified"] and result["both_clients_alive_after_sync"],"Two-peer live RGB edit failed"
record("PASS: Two simultaneously connected Forge 1.20.1 production clients, RGB/C&B microbit light, MANUAL/AUTO mode packets and live green edit propagated")
