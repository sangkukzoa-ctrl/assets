#!/usr/bin/env python3
"""RGB Blocks 1.3.1 MC1.20.1 Forge + C&B actual ephemeral server boot/reload test.
Tests server classloading, 16,687 palette, RGB commands, save/reopen.
Client visual RGB/Embeddium/Oculus and multiplayer connections are separate gates.
"""
import json,pathlib,shutil,subprocess,threading,time,urllib.request,zipfile
ROOT=pathlib.Path("mc1201-forge-runtime");ROOT.mkdir(exist_ok=True)
MODS=ROOT/"mods";MODS.mkdir(exist_ok=True)
from pathlib import Path
jars=[p for p in Path("port-work/mc1201-forge/build/libs").glob("*.jar") if "-sources" not in p.name and "-dev" not in p.name]
assert jars,"No built Forge JAR found"
jar=max(jars,key=lambda p:p.stat().st_size)
with zipfile.ZipFile(jar) as z:
    files=z.namelist()
    colors=json.loads(z.read("assets/rgbblocks/palette.json"))
    assert len(colors)==16687, len(colors)
    chosen=next(x for x in colors if int(x["red"])>180 and int(x["green"])<100 and int(x["blue"])<100)
    color_base="rgbblocks:rgb_%s_%d_%d_%d"%(chosen["group"],chosen["red"],chosen["green"],chosen["blue"])
    assets={
      "blockstates":sum(n.startswith("assets/rgbblocks/blockstates/") and n.endswith(".json") for n in files),
      "blockmodels":sum(n.startswith("assets/rgbblocks/models/block/") and n.endswith(".json") for n in files),
      "itemmodels":sum(n.startswith("assets/rgbblocks/models/item/") and n.endswith(".json") for n in files),
      "png":sum(n.endswith(".png") for n in files),
      "metadata":"META-INF/mods.toml" in files,
      "entries":len(files)
    }
assert assets["blockstates"]==50061 and assets["blockmodels"]==50061 and assets["png"]==33377,assets
shutil.copy2(jar,MODS/"RGBBlocks-1.3.1-MC1.20.1-Forge.jar")
print("RGB Forge JAR verified",jar,assets,flush=True)
def fetch(url,out):
    req=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Owner-Forge-Dedicated-Server-Test/1.0"})
    with urllib.request.urlopen(req,timeout=300) as r:data=r.read()
    out.write_bytes(data)
    print("FETCHED",out,len(data),flush=True)
fetch("https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.28/forge-1.20.1-47.4.28-installer.jar",ROOT/"forge-installer.jar")
fetch("https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",MODS/"chisels-and-bits-forge-20.1.20.jar")
p=subprocess.run(["java","-jar","forge-installer.jar","--installServer"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=430)
(ROOT/"installer.log").write_text(p.stdout,encoding="utf-8")
if p.returncode!=0 or not (ROOT/"run.sh").exists():raise AssertionError("Forge installer failed: "+p.stdout[-4000:])
(ROOT/"eula.txt").write_text("eula=true\n",encoding="utf-8")
(ROOT/"user_jvm_args.txt").write_text("-Xms512M\n-Xmx4G\n",encoding="utf-8")
(ROOT/"server.properties").write_text("""online-mode=false
server-ip=127.0.0.1
server-port=25565
motd=RGB Blocks 1.20.1 Forge integration test
max-players=2
view-distance=4
simulation-distance=4
enable-command-block=true
white-list=true
""",encoding="utf-8")

reports=[]
def cycle(name,commands):
    proc=subprocess.Popen(["bash","./run.sh","nogui"],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,text=True,bufsize=1)
    lines=[]
    def read():
        for line in proc.stdout:
            lines.append(line)
            print(name,line.rstrip(),flush=True)
    t=threading.Thread(target=read,daemon=True);t.start()
    start=time.monotonic();ready=False
    while time.monotonic()-start<500:
        if proc.poll()!=None:break
        if any("Done (" in ln and "For help" in ln for ln in lines):
            ready=True;break
        time.sleep(0.7)
    if ready:
        for cmd in commands:
            proc.stdin.write(cmd+"\n");proc.stdin.flush()
            time.sleep(1)
        time.sleep(4)
    if proc.poll()==None:
        proc.stdin.write("stop\n");proc.stdin.flush()
    try:proc.wait(timeout=80)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
    t.join(timeout=4)
    log="".join(lines)
    (ROOT/(name+".log")).write_text(log,encoding="utf-8")
    failures=[msg for msg in ("MixinApplyError","NoClassDefFoundError","NoSuchMethodError","ModLoadingException") if msg.lower() in log.lower()]
    report={
      "phase":name,"started":ready,"exit_code":proc.returncode,
      "rgb_palette_found":"16687" in log,
      "rgb_command_found":"RGB mode:" in log,
      "fatal":failures,
      "world_created":(ROOT/"world").exists(),
      "log":name+".log"
    }
    reports.append(report)
    print("RESULT",json.dumps(report),flush=True)
    return report
first=cycle("first",["rgb get","forceload add 0 0",f"setblock 0 120 0 {color_base}",f"setblock 1 120 0 {color_base}_glow",f"setblock 2 120 0 {color_base}_glass",f"execute if block 0 120 0 {color_base} run say RGB_NORMAL_PERSIST_PASS",f"execute if block 1 120 0 {color_base}_glow run say RGB_GLOW_PERSIST_PASS",f"execute if block 2 120 0 {color_base}_glass run say RGB_GLASS_PERSIST_PASS","rgb manual","rgb setbake all","rgb bake","rgb get"])
second=cycle("reopen",[f"execute if block 0 120 0 {color_base} run say RGB_NORMAL_PERSIST_PASS",f"execute if block 1 120 0 {color_base}_glow run say RGB_GLOW_PERSIST_PASS",f"execute if block 2 120 0 {color_base}_glass run say RGB_GLASS_PERSIST_PASS","rgb get","rgb bake"]) if first["started"] else {"started":False,"reason":"startup_failed"}
report={"scope":"RGB Forge1.20.1 with Chisels & Bits on actual dedicated server","artifacts":assets,
        "first":first,"reopen":second}
(ROOT/"result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
assert first["started"],"Forge 1.20.1+RGB Blocks+ChiselsBits server did not start"
assert not first["fatal"],"Game crashed due to mixin/classloading"
assert first["rgb_palette_found"],"16,687 RGB colors not registered"
assert first["rgb_command_found"],"RGB commands did not respond"
assert second["started"],"Forge RGB Blocks world did not reopen"
assert second["rgb_command_found"],"RGB commands did not persist"
first_log=(ROOT/"first.log").read_text(encoding="utf-8")
reopen_log=(ROOT/"reopen.log").read_text(encoding="utf-8")
for marker in ("RGB_NORMAL_PERSIST_PASS","RGB_GLOW_PERSIST_PASS","RGB_GLASS_PERSIST_PASS"):
    assert marker in first_log, "RGB "+marker+" block not placed successfully"
    assert marker in reopen_log, "RGB "+marker+" block was lost on reload"
assert "RGB mode: MANUAL" in reopen_log, "RGB manual mode did not persist"
assert "Bake scope: ALL" in reopen_log, "RGB bake scope did not persist"
print("PASS: Forge 1.20.1 RGB Blocks C&B server registry/commands/reopen test",flush=True)
