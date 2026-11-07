#!/usr/bin/env python3
"""Minecraft 1.21.1 Fabric RGB Blocks backport dedicated-server acceptance test.
Author-requested game runtime tests: boot, palette registration, RGB commands,
state storage and reload. Does not claim visual shader/client multiplayer tests.
"""
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
import urllib.request
import zipfile

PROJECT=Path("port-work/mc1211-fabric")
JARS=[p for p in (PROJECT/"build/libs").glob("*.jar") if not p.name.endswith(("-dev.jar","-sources.jar"))]
if not JARS:raise RuntimeError("No remapped mod jar. Compile/build first.")
JAR=max(JARS,key=lambda p:p.stat().st_size)
TEST=Path("mc1211-fabric-runtime")
TEST.mkdir(exist_ok=True)
MODS=TEST/"mods";MODS.mkdir(exist_ok=True)
print("RGB artifact:",JAR,JAR.stat().st_size,flush=True)
palette_files={}
with zipfile.ZipFile(JAR) as z:
    names=z.namelist()
    colors=json.loads(z.read("assets/rgbblocks/palette.json"))
    assert len(colors)==16687, len(colors)
    first_color=next(c for c in colors if int(c["red"])>180 and int(c["green"])<100 and int(c["blue"])<100)
    color_base="rgbblocks:rgb_%s_%d_%d_%d"%(first_color["group"],first_color["red"],first_color["green"],first_color["blue"])
    palette_files={
      "jar_file_entries":len(names),
      "block_states":sum(n.startswith("assets/rgbblocks/blockstates/") and n.endswith(".json") for n in names),
      "block_models":sum(n.startswith("assets/rgbblocks/models/block/") and n.endswith(".json") for n in names),
      "item_models":sum(n.startswith("assets/rgbblocks/models/item/") and n.endswith(".json") for n in names),
      "png":sum(n.endswith(".png") for n in names),
      "fabric.mod.json":"fabric.mod.json" in names,
      "resource_palette":"assets/rgbblocks/palette.json" in names
    }
    assert palette_files["block_states"]==50061,palette_files
    assert palette_files["block_models"]==50061,palette_files
    assert palette_files["png"]==33377,palette_files
    assert palette_files["fabric.mod.json"] and palette_files["resource_palette"],palette_files
print("JAR entries check:",json.dumps(palette_files),flush=True)

def fetch(url,dst):
    req=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Owner-LegacyGameTest/1.0"})
    with urllib.request.urlopen(req,timeout=240) as resp:
        data=resp.read()
    dst.write_bytes(data)
    print("FETCHED",dst,len(data),flush=True)
    return data

import shutil
shutil.copy2(JAR,MODS/"RGBBlocks-1.3.1-MC1.21.1-Fabric.jar")
fetch("https://meta.fabricmc.net/v2/versions/loader/1.21.1/0.19.5/1.1.2/server/jar",TEST/"fabric-server.jar")
fetch("https://mediafilez.forgecdn.net/files/9455/172/chisels-and-bits-fabric-21.1.40.jar",MODS/"chisels-and-bits-fabric-21.1.40.jar")
req=urllib.request.Request("https://api.modrinth.com/v2/project/P7dR8mSH/version",headers={"User-Agent":"RGBBlocks-Owner-LegacyGameTest/1.0"})
with urllib.request.urlopen(req,timeout=120) as resp: releases=json.load(resp)
for version in releases:
    if version.get("version_number")=="0.116.17+1.21.1":
        files=sorted(version["files"],key=lambda f:not f.get("primary"))
        api_file=files[0];break
else:raise RuntimeError("Missing required Fabric API release")
fetch(api_file["url"],MODS/api_file["filename"])

(TEST/"eula.txt").write_text("eula=true\n",encoding="utf-8")
(TEST/"server.properties").write_text("""online-mode=false
server-ip=127.0.0.1
server-port=25565
motd=RGB Blocks 1.3.1 Minecraft 1.21.1 compatibility test
max-players=2
view-distance=4
simulation-distance=4
enable-command-block=true
white-list=true
""",encoding="utf-8")
reports=[]
def cycle(label,commands):
    proc=subprocess.Popen(["java","-Xms512M","-Xmx4G","-jar","fabric-server.jar","nogui"],
             cwd=TEST,text=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
    lines=[]
    def read():
        for ln in proc.stdout:
            lines.append(ln)
            print(label,ln.rstrip(),flush=True)
    t=threading.Thread(target=read,daemon=True);t.start()
    start=time.monotonic()
    success=False
    while time.monotonic()-start<360:
        if proc.poll() is not None:break
        if any("Done (" in ln and "For help" in ln for ln in lines):
            success=True;break
        time.sleep(0.7)
    if success:
        for cmd in commands:
            proc.stdin.write(cmd+"\n");proc.stdin.flush()
            time.sleep(1.2)
        time.sleep(4)
    if proc.poll() is None:
        proc.stdin.write("stop\n");proc.stdin.flush()
    try:proc.wait(timeout=65)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
    t.join(timeout=5)
    log="".join(lines)
    (TEST/f"{label}.log").write_text(log,encoding="utf-8")
    errors=["MixinApplyError","MixinTransformerError","NoClassDefFoundError","ClassNotFoundException","NoSuchMethodError","Failed to start the minecraft server"]
    fatal=[err for err in errors if err.lower() in log.lower()]
    rep={"label":label,"started":success,"exit_code":proc.returncode,
         "palette_16687_found":"16687" in log,
         "rgb_command_response":"RGB mode:" in log,
         "fatal_patterns":fatal,
         "world_dir_created":(TEST/"world").exists(),
         "log":f"{label}.log"}
    reports.append(rep)
    print("CYCLE",json.dumps(rep,ensure_ascii=False),flush=True)
    return rep,log

first,log1=cycle("first-launch",["rgb get","forceload add 0 0",f"setblock 0 120 0 {color_base}",f"setblock 1 120 0 {color_base}_glow",f"setblock 2 120 0 {color_base}_glass",f"execute if block 0 120 0 {color_base} run say RGB_NORMAL_PERSIST_PASS",f"execute if block 1 120 0 {color_base}_glow run say RGB_GLOW_PERSIST_PASS",f"execute if block 2 120 0 {color_base}_glass run say RGB_GLASS_PERSIST_PASS","rgb manual","rgb setbake all","rgb bake","rgb get"])
if first["started"] and not first["fatal_patterns"]:
    second,log2=cycle("reload-world",[f"execute if block 0 120 0 {color_base} run say RGB_NORMAL_PERSIST_PASS",f"execute if block 1 120 0 {color_base}_glow run say RGB_GLOW_PERSIST_PASS",f"execute if block 2 120 0 {color_base}_glass run say RGB_GLASS_PERSIST_PASS","rgb get","rgb bake"])
else:second={"started":False,"fatal_patterns":["SKIPPED due to initial startup failure"]}
result={"version":"1.21.1 Fabric","scope":"Dedicated server + RGB registry/commands + world persistence; not client-rendering proof",
        "jar":JAR.name, "assets":palette_files,"initial":first,"reload":second}
(TEST/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
assert first["started"],"RGB Blocks dedicated server failed to reach ready state"
assert not first["fatal_patterns"],"RGB Blocks caused class-loading or Mixin failure"
assert first["palette_16687_found"],"RGB palette did not register all colors"
assert first["rgb_command_response"],"RGB commands not functioning on server"
assert second["started"],"RGB Blocks server failed to reload saved world"
assert not second["fatal_patterns"],"Fatal runtime error on reload"
assert second["rgb_command_response"],"RGB runtime state not responding after reload"
for marker in ("RGB_NORMAL_PERSIST_PASS","RGB_GLOW_PERSIST_PASS","RGB_GLASS_PERSIST_PASS"):
    assert marker in log1, "RGB block placement fails: "+marker
    assert marker in log2, "RGB block persistence fails: "+marker
assert "RGB mode: MANUAL" in log2, "RGB runtime mode not persisted"
assert "Bake scope: ALL" in log2, "RGB bake scope not persisted"
print("PASS: 1.21.1 Fabric server / C&B / RGB command registration / world reload",flush=True)
