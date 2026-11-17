#!/usr/bin/env python3
"""Minecraft 1.20.1 REAL Forge server + TWO CONCURRENT clients RGB sync test.

Joins via actual Forge mod handshake and capture RGB normal, glow and glass
placed in server world; verifies world edit, remote connection, render pipeline,
persisted network commands and 3D screenshot. This is a strict smoke, not a
shader pixel-equivalence proof.
"""
import json,os,signal,pathlib,subprocess,threading,time,urllib.request,zipfile,tarfile,hashlib,shutil
from pathlib import Path

SHADER_ON=os.environ.get("RGB_PORT_SHADER_ON")=="1"  # Optional strict Oculus+Complementary shader test; OFF by default.
MIXED_CNB_PROBE=os.environ.get("RGB_PORT_TEST_MIXED_CNB")=="1"
SERVER_RESTART_PROBE=os.environ.get("RGB_PORT_TEST_WORLD_RESTART")=="1"
DIMENSION_PROBE=os.environ.get("RGB_PORT_TEST_DIMENSIONS")=="1"
assert not DIMENSION_PROBE or MIXED_CNB_PROBE, "Dimension switching requires 4096bit mixed C&B test"
assert not SERVER_RESTART_PROBE or MIXED_CNB_PROBE, "True server world restart requires mixed C&B test"
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
                if any(q in line for q in ("Done (","joined the game","lost connection","ERROR","FATAL","Fatal","Traceback","Render thread","RGB mode","Server thread","Failed","RGB_PORT_PEER_","RGB_PORT_DIAG_","RGB_PORT_CNB_MIXED_","Caused by","Exception","MixinApplyError","mixin apply","Mixin config","rgbblocks.mixins")):
                    record(label+" "+line.rstrip()[:450])
    t=threading.Thread(target=reader,daemon=True);t.start()
    return lines,t
def await_pattern(lines,pat,proc,seconds,label):
    st=time.monotonic()
    while time.monotonic()-st<seconds:
        if pat in "".join(lines[-1200:]):return True
        if proc.poll() is not None:break
        time.sleep(0.7)
    if pat=="RGB_PORT_CNB_MIXED_FIXTURE_PASS":
        for line in lines:
            if "RGB_PORT_CNB_MIXED_" in line or "Caused by" in line or "Exception" in line:
                record("FORGE_MIXED_SERVER_DIAG "+line.rstrip()[-950:])
    record("TIMEOUT/MISSING "+label+" pattern="+pat+" return="+str(proc.poll()))
    return False
def await_pattern_since(lines,pat,start_index,proc,seconds,label):
    """Accept only a NEW post-command event, never an earlier login/save."""
    st=time.monotonic()
    while time.monotonic()-st<seconds:
        if any(pat in line for line in lines[start_index:]):return True
        if proc.poll() is not None:break
        time.sleep(0.7)
    record("TIMEOUT/MISSING NEW "+label+" pattern="+pat+" return="+str(proc.poll()))
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
    manifest=zip.read("META-INF/MANIFEST.MF").decode("utf-8",errors="replace")
    assert "MixinConfigs: rgbblocks.mixins.json" in manifest, "Forge runtime JAR missing MixinConfigs"
    assert "client.ClientLevelMixin" in json.loads(zip.read("rgbblocks.mixins.json")).get("client",[]), "Runtime config lacks ClientLevelMixin"
    record("FORGE_JAR_MIXIN_CONFIGURED manifest=True clientLevelMixin=True jar="+str(jar))
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
               "both_clients_alive_after_sync":False,"two_clients_live_source_removal_verified":False,
               "both_clients_alive_after_removal":False,
               "two_clients_manual_defer_verified":False,
               "two_clients_manual_bake_verified":False,
               "both_clients_alive_after_manual_bake":False,
               "peer_reconnect_login_verified":False,
               "peer_reconnect_world_id_verified":False,
               "peer_reconnect_snapshot_saved":False,
               "peer_reconnect_snapshot_loaded":False,
               "peer_reconnect_rgb_cnb_verified":False,
               "peer_chunk_unload_verified":False,
               "peer_chunk_return_verified":False,
               "primary_alive_during_reconnect":False,
               "green_block":green,
               "mixed_cnb_requested":MIXED_CNB_PROBE,
               "mixed_cnb_server_sculpted":False,
               "mixed_cnb_primary_verified":False,
               "mixed_cnb_peer_verified":False,
               "shader_mixed_screenshot":False,
               "server_restart_requested":SERVER_RESTART_PROBE,
               "dedicated_server_restarted":False,
               "world_restart_green_block":False,
               "world_restart_mixed_cnb_voxels":False,
               "world_restart_peer_joined":False,
               "world_restart_rgb_cnb_light":False,
               "world_restart_mixed_client_bits":False,
               "world_restart_same_uuid":False,
               "dimension_requested":DIMENSION_PROBE,
               "dimension_nether_entered":False,
               "dimension_nether_blue_verified":False,
               "dimension_overworld_restored":False,
               "dimension_nether_reentered":False,
               "dimension_distinct_snapshots":False})
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
    if MIXED_CNB_PROBE:
        command(server,"setblock 6 121 7 chiselsandbits:chiseled")
        result["mixed_cnb_server_sculpted"]=await_pattern(slog,
            "RGB_PORT_CNB_MIXED_FIXTURE_PASS",server,150,"real_mixed_sculpt_4096")
        assert result["mixed_cnb_server_sculpted"],"Server could not sculpt real mixed C&B Glow/Normal/Glass 16³ bits"
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
    # Keep the primary player at the same force-loaded RGB test platform as the
    # peer. Previously only the peer was teleported before the live edit; the
    # primary could leave the server's player-tracked section and retain a
    # legitimate old chunk snapshot while the peer received GREEN.
    command(server,"tp RGBPortTester -1.5 120.0 0.5 facing 0.5 121.5 7.5")
    assert await_pattern(slog,"Teleported RGBPortTester to -1.500000, 120.000000, 0.500000",
                         server,35,"primary_at_RGB_fixture"),"Primary was not moved into RGB test scene"
    command(server,"gamemode creative RGBPortTester")
    result["first_rgb_probe_verified"]=await_pattern(clog,"RGB_PORT_LIGHT_PROBE_PASS",client,100,"first_rgb_source")
    result["first_cnb_rgb_probe_verified"]=await_pattern(clog,"RGB_PORT_CNB_LIGHT_PROBE_PASS",client,100,"first_cnb_rgb")
    assert result["first_rgb_probe_verified"] and result["first_cnb_rgb_probe_verified"],"First client lacks RGB+C&B microbit light"
    if MIXED_CNB_PROBE:
        result["mixed_cnb_primary_verified"]=await_pattern(clog,
            "RGB_PORT_CNB_MIXED_PROBE_PASS",client,145,"primary_true_mixed_bit_states")
        assert result["mixed_cnb_primary_verified"],"First Forge client could not read all mixed C&B RGB/Glass voxels and emitted light"

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
    if MIXED_CNB_PROBE:
        result["mixed_cnb_peer_verified"]=await_pattern(peerlog,
            "RGB_PORT_CNB_MIXED_PROBE_PASS",peer,145,"peer_true_mixed_bit_states")
        assert result["mixed_cnb_peer_verified"],"Second Forge client could not read all mixed C&B RGB/Glass voxels and emitted light"

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

    # Explicitly verify BOTH players still stand in the loaded RGB fixture.
    # A chunk update is only networked to the client's tracking radius.
    command(server,"tp RGBPortTester -1.5 120.0 0.5 facing 0.5 121.5 7.5")
    command(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    command(server,"data get entity RGBPortTester Pos")
    command(server,"data get entity RGBPortPeer Pos")
    time.sleep(3)
    record("RGB_PORT_DUAL_CLIENT_FIXTURE_POSITIONS_REQUESTED primary=(-1.5,120,0.5) peer=(1.5,120,0.5)")
    # A live server edit must replace the original red full-block source with
    # a green source for both clients, and adjacent computed light must turn green.
    command(server,f"setblock 0 121 7 {green}_glow")
    green_first=await_pattern(clog,"RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS",client,100,"primary_live_green")
    green_peer=await_pattern(peerlog,"RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS",peer,100,"peer_live_green")
    result["two_clients_live_rgb_sync_verified"]=green_first and green_peer
    if not result["two_clients_live_rgb_sync_verified"]:
        for name,folder in (("PRIMARY",GAME),("SECONDARY",PEER)):
            path=folder/"logs/latest.log"
            if path.is_file():
                diag=[line for line in path.read_text(encoding="utf-8",errors="replace").splitlines()
                      if any(token in line for token in (
                          "RGB_PORT_PEER_", "RGB_PORT_DIAG_", "Mixin", "mixin",
                          "setServerVerifiedBlockState", "RGBRealLightEngine", "ERROR", "FATAL"))]
                for line in diag[-140:]:
                    record("TWO_CLIENT_DIAG_"+name+" "+line[-900:])
            console=EVIDENCE/("client-console.log" if name=="PRIMARY" else "peer-console.log")
            if console.is_file():
                diag=[line for line in console.read_text(encoding="utf-8",errors="replace").splitlines()
                      if any(token in line for token in ("RGB_PORT_DIAG_", "MixinApplyError", "Mixin", "mixin", "setServerVerifiedBlockState"))]
                for line in diag[-80:]:
                    record("TWO_CLIENT_CONSOLE_"+name+" "+line[-900:])
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
    if SHADER_ON and MIXED_CNB_PROBE:
        # Screenshot of the ACTUAL sculpted five-material 4096-bit C&B block
        # in Oculus+Embeddium+Complementary. Preserve primary original camera
        # and all live/light/network assertions.
        command(server,"tp RGBPortTester 5.5 120.0 1.5 facing 6.5 121.5 7.5")
        time.sleep(12)
        mixed_image=EVIDENCE/"forge-oculus-complementary-ON-MIXED-4096bit-CNB-rgb-glass.png"
        shot_mixed=subprocess.run(["scrot",str(mixed_image.resolve())],env=env,
          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45)
        result["shader_mixed_screenshot"]=shot_mixed.returncode==0 and mixed_image.is_file() and mixed_image.stat().st_size>10000
        if result["shader_mixed_screenshot"]:
            result["screenshots"].append({"file":mixed_image.name,"size":mixed_image.stat().st_size})
        assert result["shader_mixed_screenshot"],"Real Forge 4096-bit RGB/C&B mixed glass shader-ON screenshot absent"
        command(server,"tp RGBPortTester 0.5 120.0 0.5 facing 0.5 121.5 7.5")
    # Restore-world correctness: both peers must notice removal of the GREEN
    # emitter, clear the former green light, and preserve the independent RED
    # 4095-bit C&B sculpture contribution. Keep screenshot above intact.
    command(server,"setblock 0 121 7 minecraft:air")
    command(server,"execute if block 0 121 7 minecraft:air run say RGB_PORT_SERVER_SOURCE_REMOVED_PASS")
    assert await_pattern(slog,"RGB_PORT_SERVER_SOURCE_REMOVED_PASS",server,35,"server_confirmed_source_removed"),"Server failed to remove GREEN source"
    removal_first=await_pattern(clog,"RGB_PORT_PEER_LIVE_SOURCE_REMOVAL_PASS",client,100,"primary_source_removal")
    removal_peer=await_pattern(peerlog,"RGB_PORT_PEER_LIVE_SOURCE_REMOVAL_PASS",peer,100,"peer_source_removal")
    result["two_clients_live_source_removal_verified"]=removal_first and removal_peer
    result["both_clients_alive_after_removal"]=client.poll() is None and peer.poll() is None
    assert result["two_clients_live_source_removal_verified"],"Live source removal did not update both clients' RGB light"
    assert result["both_clients_alive_after_removal"],"Client exited during live RGB source removal"
    # Strict MANUAL semantics: source changes are kept dirty without affecting
    # the baked adjacent RGB light until BOTH players receive /rgb bake.
    command(server,"rgb manual")
    assert await_pattern(slog,"RGB mode: MANUAL",server,30,"manual_bake_mode"),"Server refused MANUAL mode"
    time.sleep(4)
    command(server,f"setblock 0 121 7 {green}_glow")
    manual_held_first=await_pattern(clog,"RGB_PORT_PEER_MANUAL_DEFER_PASS",client,95,"primary_manual_deferred")
    manual_held_peer=await_pattern(peerlog,"RGB_PORT_PEER_MANUAL_DEFER_PASS",peer,95,"peer_manual_deferred")
    result["two_clients_manual_defer_verified"]=manual_held_first and manual_held_peer
    assert result["two_clients_manual_defer_verified"],"MANUAL mode changed stored RGB light before bake on a real client"
    command(server,"rgb setbake all")
    command(server,"rgb bake")
    manual_bake_first=await_pattern(clog,"RGB_PORT_PEER_MANUAL_BAKE_PASS",client,145,"primary_manual_bake")
    manual_bake_peer=await_pattern(peerlog,"RGB_PORT_PEER_MANUAL_BAKE_PASS",peer,145,"peer_manual_bake")
    result["two_clients_manual_bake_verified"]=manual_bake_first and manual_bake_peer
    result["both_clients_alive_after_manual_bake"]=client.poll() is None and peer.poll() is None
    assert result["two_clients_manual_bake_verified"],"Manual /rgb bake did not replay RGB light on both clients"
    assert result["both_clients_alive_after_manual_bake"],"Client exited during manual dirty-position bake"
    # After the actual MANUAL bake, return to AUTO and exercise a FULL
    # offline→reconnect cycle for the same production peer installation.
    # Keep the first client online on the same dedicated server throughout.
    # The 4095-bit red C&B sculpture and GREEN full emitter are NOT reset.
    initial_peer_ids=[line.split("worldId=",1)[1].split()[0]
         for line in peerlog if "RGB_PORT_PEER_MANUAL_SYNC_PASS worldId=" in line]
    assert initial_peer_ids and initial_peer_ids[-1], "Original peer had no authoritative world identity"
    initial_peer_world_id=initial_peer_ids[-1]
    command(server,"rgb auto")
    time.sleep(4)
    prior_leave=len(slog)
    prior_save=len(peerlog)
    command(server,"kick RGBPortPeer RGB_PORT_CI_RECONNECT")
    assert await_pattern_since(slog,"RGBPortPeer lost connection",prior_leave,server,45,
                               "peer_disconnected_before_restart"),"Peer did not disconnect cleanly"
    assert await_pattern_since(peerlog,"Saved RGB lightmap:",prior_save,peer,45,
                               "peer_cache_saved_on_disconnect"),"Forge peer did not persist lightmap at logout"
    snaps=sorted((PEER/"rgbblocks"/"lightmaps").rglob("*.rgl.gz"))
    result["peer_reconnect_snapshot_saved"]=bool(snaps) and all(p.stat().st_size>100 for p in snaps)
    assert result["peer_reconnect_snapshot_saved"],"Peer RGB lightmap snapshot absent or empty after disconnect"
    record("RGB_PORT_PEER_SAVED_SNAPSHOTS "+json.dumps([
        {"path":str(p.relative_to(PEER)),"bytes":p.stat().st_size,
         "sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in snaps]))
    terminate(peer)
    peerthread.join(timeout=8)
    old_peer_log=PEER/"logs/latest.log"
    if old_peer_log.is_file():shutil.copy2(old_peer_log,EVIDENCE/"minecraft-peer-before-reconnect.log")
    before_rejoin=len(slog)
    reconnect_cmd=list(peer_cmd)+["--jvm-arg=-Drgbport.ci.reconnect=true"]
    if DIMENSION_PROBE:
        reconnect_cmd.append("--jvm-arg=-Drgbport.ci.dimension=true")
    record("RELAUNCH_SAME_PEER_DIRECTORY "+str(reconnect_cmd))
    peer=subprocess.Popen(reconnect_cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          env=peer_env,text=True,start_new_session=True,bufsize=1)
    peerlog,peerthread=runthread(peer,"PEER_RECONNECT",EVIDENCE/"peer-reconnect-console.log")
    result["peer_reconnect_login_verified"]=await_pattern_since(slog,"RGBPortPeer joined the game",
         before_rejoin,server,210,"same_player_rejoined_original_server")
    assert result["peer_reconnect_login_verified"],"Former peer did not rejoin original Forge server"
    command(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    result["peer_reconnect_snapshot_loaded"]=await_pattern(peerlog,"Loaded RGB lightmap:",
         peer,105,"saved_rgb_lightmap_loaded_after_rejoin")
    assert result["peer_reconnect_snapshot_loaded"],"Saved RGB lightmap did not load on fresh client process"
    result["peer_reconnect_rgb_cnb_verified"]=await_pattern(peerlog,
         "RGB_PORT_PEER_RECONNECT_SOURCE_PASS",peer,135,"reconnected_peer_green_cnb")
    assert result["peer_reconnect_rgb_cnb_verified"],"Reconnected production client did not restore GREEN RGB + red C&B light"
    reconnected_ids=[line.split("worldId=",1)[1].split()[0]
         for line in peerlog if "RGB_PORT_PEER_RECONNECT_SOURCE_PASS worldId=" in line]
    result["peer_reconnect_world_id_verified"]=bool(reconnected_ids) and reconnected_ids[-1]==initial_peer_world_id
    assert result["peer_reconnect_world_id_verified"],"World ID changed across reconnect or missing state sync"
    result["primary_alive_during_reconnect"]=client.poll() is None
    assert result["primary_alive_during_reconnect"],"Original other client stopped during peer reconnect"

    # Actual client-side chunk eviction: force a player outside the tracking
    # radius, prove src chunk UNLOADED, then re-enter and demand light rebuild.
    command(server,"tp RGBPortPeer 256.5 120.0 0.5")
    result["peer_chunk_unload_verified"]=await_pattern(peerlog,
         "RGB_PORT_PEER_CHUNK_UNLOAD_PASS",peer,95,"peer_source_chunk_evicted")
    assert result["peer_chunk_unload_verified"],"Far-away peer never unloaded original RGB source chunk"
    command(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
    result["peer_chunk_return_verified"]=await_pattern(peerlog,
         "RGB_PORT_PEER_CHUNK_RETURN_PASS",peer,145,"peer_source_chunk_reloaded")
    assert result["peer_chunk_return_verified"],"Chunk returned without restoring RGB + C&B per-channel light"
    assert peer.poll() is None and client.poll() is None,"A client exited during reconnect/chunk reload"
    if DIMENSION_PROBE:
        # Genuine source and light-scene switch, not synthetic Level injection.
        # Source 1 is GREEN full-block in Overworld with a real RED/mixed C&B.
        # Source 2 is a BLUE glow block in Nether, with independent RGB cache.
        command(server,"gamemode creative RGBPortPeer")
        before_nether=len(peerlog)
        command(server,"execute in minecraft:the_nether run tp RGBPortPeer 0.5 200.0 0.5")
        result["dimension_nether_entered"]=await_pattern_since(peerlog,
            "RGB_PORT_DIM_NETHER_ENTER_PASS",before_nether,peer,150,
            "real_nether_dimension_entered")
        assert result["dimension_nether_entered"],"Forge peer never entered actual Nether Level"
        command(server,"execute in minecraft:the_nether run fill -5 199 -3 5 199 12 minecraft:stone")
        command(server,"execute in minecraft:the_nether run setblock 0 202 7 rgbblocks:rgb_blue_8_85_209_glow")
        command(server,"execute in minecraft:the_nether if block 0 202 7 rgbblocks:rgb_blue_8_85_209_glow run say RGB_PORT_DIM_NETHER_BLUE_BLOCK_READY")
        assert await_pattern(slog,"RGB_PORT_DIM_NETHER_BLUE_BLOCK_READY",server,45,
            "actual_nether_rgb_source_exists"),"Server did not install blue Nether RGB glow block"
        result["dimension_nether_blue_verified"]=await_pattern(peerlog,
            "RGB_PORT_DIM_NETHER_BLUE_PASS",peer,150,
            "neoforge_and_forge_real_blue_near_light")
        assert result["dimension_nether_blue_verified"],"Actual Nether per-channel blue RGB failed"
        command(server,"execute in minecraft:overworld run tp RGBPortPeer 1.5 120.0 0.5")
        result["dimension_overworld_restored"]=await_pattern(peerlog,
            "RGB_PORT_DIM_OVERWORLD_RETURN_PASS",peer,150,
            "overworld_mixed_cnb_and_green_light_after_nether")
        assert result["dimension_overworld_restored"],"Overworld source/C&B disappeared after dimension change"
        end=time.monotonic()+60;snap_files=[]
        while time.monotonic()<end:
            snap_files=sorted((PEER/"rgbblocks"/"lightmaps").rglob("*.rgl.gz"))
            if len(snap_files)>=2 and all(f.stat().st_size>100 for f in snap_files):break
            time.sleep(1)
        result["dimension_distinct_snapshots"]=len(snap_files)>=2 and all(
            f.stat().st_size>100 for f in snap_files)
        record("FORGE_DIMENSION_INDEPENDENT_LIGHTMAP_FILES "+json.dumps([
           {"file":p.name,"bytes":p.stat().st_size} for p in snap_files]))
        assert result["dimension_distinct_snapshots"],"Forge lightmap lost per-dimension independence"
        before_reentry=len(peerlog)
        command(server,"execute in minecraft:the_nether run tp RGBPortPeer 0.5 200.0 0.5")
        result["dimension_nether_reentered"]=await_pattern_since(peerlog,
           "RGB_PORT_DIM_NETHER_REENTRY_PASS",before_reentry,peer,155,
           "reloaded_blue_source_in_true_nether")
        assert result["dimension_nether_reentered"],"Forge Nether RGB blue source not restored after dimension switches"
        command(server,"execute in minecraft:overworld run tp RGBPortPeer 1.5 120.0 0.5")
        time.sleep(4)
        assert peer.poll() is None and server.poll() is None,"Server/client quit during inter-dimension lighting probe"
    if SERVER_RESTART_PROBE:
        # This tests a real second dedicated-server JVM, preserving the exact
        # original server/world directory and its saved C&B block entities.
        # CI-only -Drgbport.ci.restartCheck bans the server fixture from
        # recreating lost bits after restart.
        command(server,"save-all flush")
        time.sleep(4)
        command(server,"stop")
        try:server.wait(timeout=90)
        except subprocess.TimeoutExpired:
            terminate(server)
            raise AssertionError("Forge dedicated server did not shut down after save-all")
        terminate(peer);peerthread.join(timeout=10)
        terminate(client);cthread.join(timeout=10)
        sthread.join(timeout=10)
        jvm=(SERVER/"user_jvm_args.txt").read_text(encoding="utf-8")
        (SERVER/"user_jvm_args.txt").write_text(jvm+"\n-Drgbport.ci.restartCheck=true\n",encoding="utf-8")
        record("FORGE_DEDICATED_SERVER_REAL_RESTART sameWorld="+str(SERVER.resolve()))
        server=subprocess.Popen(["bash","./run.sh","nogui"],cwd=SERVER,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            text=True,bufsize=1,start_new_session=True)
        slog,restartthread=runthread(server,"SERVER_RESTART",EVIDENCE/"server-after-restart.log")
        result["dedicated_server_restarted"]=await_pattern(
            slog,"Done (",server,210,"restarted_same_world_forge_server")
        assert result["dedicated_server_restarted"],"Forge original saved-world server restart failed"
        result["world_restart_mixed_cnb_voxels"]=await_pattern(
            slog,"RGB_PORT_CNB_MIXED_WORLD_RESTART_PASS",server,135,
            "real_saved_cnb_voxels_exactly_unchanged")
        assert result["world_restart_mixed_cnb_voxels"],"Forge mixed C&B voxels absent after real server restart"
        command(server,f"execute if block 0 121 7 {green}_glow run say RGB_PORT_FORGE_RESTART_GREEN_BLOCK_PASS")
        result["world_restart_green_block"]=await_pattern(
            slog,"RGB_PORT_FORGE_RESTART_GREEN_BLOCK_PASS",server,30,
            "world_saved_green_glow_block")
        assert result["world_restart_green_block"],"Forge saved GREEN RGB block absent after server restart"
        record("FORGE_WORLD_RESTART_LAUNCH_PEER "+str(reconnect_cmd))
        peer=subprocess.Popen(reconnect_cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
             env=peer_env,text=True,bufsize=1,start_new_session=True)
        peerlog,peerthread=runthread(peer,"PEER_WORLD_RESTART",
             EVIDENCE/"peer-after-server-restart.log")
        result["world_restart_peer_joined"]=await_pattern(
            slog,"RGBPortPeer joined the game",server,210,
            "reconnected_after_server_restart")
        assert result["world_restart_peer_joined"],"Client could not connect to restarted Forge server"
        command(server,"tp RGBPortPeer 1.5 120.0 0.5 facing 0.5 121.5 7.5")
        result["world_restart_rgb_cnb_light"]=await_pattern(
            peerlog,"RGB_PORT_PEER_RECONNECT_SOURCE_PASS",peer,150,
            "full_rgb_and_cnb_light_from_saved_server")
        result["world_restart_mixed_client_bits"]=await_pattern(
            peerlog,"RGB_PORT_CNB_MIXED_PROBE_PASS",peer,150,
            "mixed_real_cnb_glass_source_after_server_world_restart")
        restart_ids=[line.split("worldId=",1)[1].split()[0] for line in peerlog
           if "RGB_PORT_PEER_RECONNECT_SOURCE_PASS worldId=" in line]
        result["world_restart_same_uuid"]=bool(restart_ids) and restart_ids[-1]==initial_peer_world_id
        assert all(result[k] for k in (
            "world_restart_rgb_cnb_light","world_restart_mixed_client_bits","world_restart_same_uuid"
        )), "Forge true server world restart lost saved RGB / C&B 4096bit mixed glass or world UUID"
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
    if "restartthread" in locals():restartthread.join(timeout=5)
    if "cthread" in locals():cthread.join(timeout=5)
    if "peerthread" in locals():peerthread.join(timeout=5)
    if (GAME/"logs/latest.log").is_file():
        shutil.copy2(GAME/"logs/latest.log",EVIDENCE/"minecraft-client-latest.log")
    if (PEER/"logs/latest.log").is_file():
        shutil.copy2(PEER/"logs/latest.log",EVIDENCE/"minecraft-peer-latest.log")
    if (EVIDENCE/"peer-reconnect-console.log").is_file():
        contents=(EVIDENCE/"peer-reconnect-console.log").read_text(encoding="utf-8",errors="replace")
        relevant=[line for line in contents.splitlines()
                  if any(pat in line for pat in (
                     "RGB_PORT_PEER_RECONNECT_", "RGB_PORT_PEER_CHUNK_", "RGB_PORT_CNB",
                     "RGB_PORT_LIGHT_", "RGB Blocks", "ERROR", "FATAL", "MixinApplyError"))]
        for line in relevant[-65:]:
            record("PEER_RECONNECT_DIAG "+line[:900])
    for who,folder in (("PRIMARY",GAME),("SECONDARY",PEER)):
        candidate=folder/"logs/latest.log"
        if candidate.is_file():
            contents=candidate.read_text(encoding="utf-8",errors="replace")
            matches=[line for line in contents.splitlines()
                     if any(token in line for token in (
                         "RGB_PORT_DIAG_", "ClientLevelMixin", "MixinApplyError",
                         "setServerVerifiedBlockState", "Mixin config"))]
            record("FORGE_CLIENT_MIXIN_DIAG_SUMMARY "+who
                   +" matches="+str(len(matches))
                   +" rgb_events="+str(sum("RGB_PORT_DIAG_" in x for x in matches)))
            for line in matches[-55:]:
                record("FORGE_CLIENT_MIXIN_TRACE_"+who+" "+line[-950:])
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
if MIXED_CNB_PROBE:
    assert result["mixed_cnb_server_sculpted"] and result["mixed_cnb_primary_verified"] and result["mixed_cnb_peer_verified"],"Forge mixed red/green/blue Glow + normal RGB + glass 16³ acceptance failed"
if DIMENSION_PROBE:
    assert all(result[k] for k in (
        "dimension_nether_entered","dimension_nether_blue_verified",
        "dimension_overworld_restored","dimension_nether_reentered",
        "dimension_distinct_snapshots"
    )), "Forge cross-dimension RGB/C&B persistence failed"
if SERVER_RESTART_PROBE:
    assert all(result[k] for k in (
       "dedicated_server_restarted","world_restart_green_block",
       "world_restart_mixed_cnb_voxels","world_restart_peer_joined",
       "world_restart_rgb_cnb_light","world_restart_mixed_client_bits",
       "world_restart_same_uuid"
    )), "Forge true dedicated server world restart mixed 4096-bit C&B/RGB test failed"
assert result["cnb_rgb_propagation_verified"],"C&B chiselled RGB-colored light failed to propagate into adjacent voxel"
assert result["first_rgb_probe_verified"] and result["first_cnb_rgb_probe_verified"],"First client's light probes absent"
assert result["peer_joined"] and result["peer_rgb_probe_verified"] and result["peer_cnb_rgb_probe_verified"],"Second client lacks C&B RGB light"
assert result["two_clients_manual_sync"] and result["two_clients_auto_sync"],"Both clients did not receive mode synchronization"
assert result["two_clients_live_rgb_sync_verified"] and result["both_clients_alive_after_sync"],"Two-peer live RGB edit failed"
assert result["two_clients_live_source_removal_verified"] and result["both_clients_alive_after_removal"],"Two-peer RGB source removal invalidation failed"
assert result["two_clients_manual_defer_verified"] and result["two_clients_manual_bake_verified"] and result["both_clients_alive_after_manual_bake"],"Two-peer manual bake deferred replay failed"
assert all(result[k] for k in (
    "peer_reconnect_login_verified","peer_reconnect_world_id_verified",
    "peer_reconnect_snapshot_saved","peer_reconnect_snapshot_loaded",
    "peer_reconnect_rgb_cnb_verified","peer_chunk_unload_verified",
    "peer_chunk_return_verified","primary_alive_during_reconnect"
)), "Same-client reconnect/persistence/chunk unload-reload gate failed"
record("PASS: Two simultaneous Forge 1.20.1 clients: RGB+C&B, RED->GREEN, GREEN->AIR, MANUAL bake, saved lightmap logout/reload, same peer reconnect, chunk unload/return")
