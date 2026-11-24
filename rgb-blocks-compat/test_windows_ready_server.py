#!/usr/bin/env python3
"""Genuine Windows x64 acceptance of distributed preinstalled server ZIP.

Runs the exact bundled java.exe and Windows loader win_args.txt used by
run.bat, NOT a Linux server and NOT a Gradle development environment.
Tests first-launch and same-world reopen with ONLY owner RGB mod installed.
"""
from pathlib import Path
import json
import hashlib
import os
import queue
import re
import subprocess
import sys
import threading
import time
import zipfile

assert len(sys.argv)==2 and sys.argv[1] in ("forge1201","neoforge1211")
target=sys.argv[1]
c={
    "forge1201":{"java":"17","loader":"47.4.28","arg":"libraries/net/minecraftforge/forge/1.20.1-47.4.28/win_args.txt","port":25566},
    "neoforge1211":{"java":"21","loader":"21.1.265","arg":"libraries/net/neoforged/neoforge/21.1.265/win_args.txt","port":25567},
}[target]
art=Path("input")/target
zips=list(art.rglob("*WINDOWS-READY-SERVER.zip"))
assert len(zips)==1,("One Windows server bundle expected",zips)
zipfile_path=zips[0]
root=Path("windows-smoke")/target
root.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(zipfile_path) as z:
    assert z.testzip() is None
    z.extractall(root)
run_scripts=list(root.rglob("run.bat"))
assert len(run_scripts)==1,run_scripts
server=run_scripts[0].parent
java=server/"runtime/java/bin/java.exe"
assert java.is_file()
args=server/c["arg"]
assert args.is_file()
mods=list((server/"mods").glob("*.jar"))
assert len(mods)==1 and "RGBBlocks" in mods[0].name,mods
def sha256(path):
    with path.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
manifest=json.loads((server/"SERVER_VERSION_AND_HASHES.json").read_text(encoding="utf-8"))
assert sha256(mods[0])==manifest["rgb_jar_sha256"],"Windows server embedded RGB hash mismatch"
if os.environ.get("RGB_FINAL_HANDOFF")=="1":
    assert manifest["source_commit"]==os.environ["GITHUB_SHA"]
    assert str(manifest["github_source_actions_run"])==os.environ["GITHUB_RUN_ID"]
    assert sha256(zipfile_path)==os.environ["RGB_EXPECTED_WINDOWS_SHA256"]
bat=(server/"run.bat").read_text(encoding="ascii")
assert "runtime\\java\\bin\\java.exe" in bat and "@"+c["arg"] in bat and "@user_jvm_args.txt" in bat,bat
assert (server/"eula.txt").read_text().strip()=="eula=true"
version=subprocess.run([str(java.resolve()),"-version"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                       text=True,timeout=35).stdout
assert re.search(r'version "'+c["java"]+r'(?:\.|")',version),version
print("WINDOWS_BUNDLED_JAVA_PASS",target,version.splitlines()[0],flush=True)

report={"target":target,"server_zip_sha256":sha256(zipfile_path),
        "rgb_jar_sha256":sha256(mods[0]),"source_commit":manifest.get("source_commit"),"java_version":version.strip(),"mods":[m.name for m in mods],
        "bundled_runtime":True,"native_win_args":str(args.relative_to(server)),
        "first_start":False,"rgb_palette":False,"rgb_commands":False,
        "normal_glow_glass_block_created":False,
        "same_world_reopen":False,"persistent_blocks":False,
        "errors":[]}
rgb="rgbblocks:rgb_red_186_72_96"

def cycle(label,commands):
    # Exactly the JVM token structure from run.bat, while avoiding that BAT's
    # interactive "pause" so Windows CI can terminate deterministically.
    proc=subprocess.Popen([str(java.resolve()),"@user_jvm_args.txt","@"+c["arg"],"nogui"],
            cwd=server,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,text=True,encoding="utf-8",
            errors="replace",bufsize=1)
    log=[]
    mutex=threading.Lock()
    def pump():
        for line in proc.stdout:
            with mutex:log.append(line)
            if any(t in line for t in ("Done (","ERROR","FATAL","RGB mode:","RGBBlocks","Exception")):
                print(label,line.rstrip()[:550],flush=True)
    thread=threading.Thread(target=pump,daemon=True);thread.start()
    ready=False
    start=time.monotonic()
    while time.monotonic()-start<390:
        with mutex:
            recent="".join(log[-1000:])
        if "Done (" in recent and "For help" in recent:
            ready=True
            break
        if proc.poll() is not None:break
        time.sleep(1)
    if ready:
        for command in commands:
            proc.stdin.write(command+"\n");proc.stdin.flush()
            print("WINDOWS_TEST_COMMAND",label,command,flush=True)
            time.sleep(1.5)
        time.sleep(3)
    if proc.poll() is None:
        try:proc.stdin.write("stop\n");proc.stdin.flush()
        except OSError:pass
    try:proc.wait(timeout=140)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait(timeout=15)
    thread.join(timeout=15)
    with mutex:output="".join(log)
    out=root/(target+"-"+label+".log")
    out.write_text(output,encoding="utf-8")
    fatal=[x for x in ("MixinApplyError","NoClassDefFoundError","ModLoadingException",
          "Failed to start the minecraft server","ExceptionInInitializerError")
          if x.lower() in output.lower()]
    print("WINDOWS_CYCLE",json.dumps({"phase":label,"ready":ready,
          "exit_code":proc.returncode,"fatal":fatal,
          "logs":str(out),"size":len(output)}),flush=True)
    assert ready and proc.returncode==0 and not fatal,(
          "Windows exact compiled server could not boot or shutdown",label,proc.returncode,fatal,output[-7000:])
    return output

try:
    first=cycle("initial",[
       "rgb get","forceload add 0 0",
       "setblock 0 120 0 "+rgb,
       "setblock 1 120 0 "+rgb+"_glow",
       "setblock 2 120 0 "+rgb+"_glass",
       "execute if block 0 120 0 "+rgb+" run say RGB_WIN_NORMAL_PASS",
       "execute if block 1 120 0 "+rgb+"_glow run say RGB_WIN_GLOW_PASS",
       "execute if block 2 120 0 "+rgb+"_glass run say RGB_WIN_GLASS_PASS",
       "rgb manual","rgb setbake all","rgb bake","save-all flush","rgb get"
    ])
    report["first_start"]=True
    report["rgb_palette"]="16687" in first and "50061" in first
    report["rgb_commands"]="RGB mode:" in first
    report["normal_glow_glass_block_created"]=all(x in first for x in (
        "RGB_WIN_NORMAL_PASS","RGB_WIN_GLOW_PASS","RGB_WIN_GLASS_PASS"))
    print("WINDOWS_FIRST_NATIVE_FLAGS",json.dumps({k:report[k] for k in
          ("rgb_palette","rgb_commands","normal_glow_glass_block_created")}),flush=True)
    for line in first.splitlines():
        if any(t in line for t in ("16687","50061","RGB_WIN_","RGB mode:","Unknown command","Unknown block")):
            print("WINDOWS_FIRST_NATIVE_DIAG",line[:600],flush=True)
    assert report["rgb_palette"] and report["rgb_commands"] and report["normal_glow_glass_block_created"]
    assert (server/"world/level.dat").is_file(),"No real saved Minecraft world after Windows server boot"
    second=cycle("reopen",[
       "execute if block 0 120 0 "+rgb+" run say RGB_WIN_NORMAL_PASS",
       "execute if block 1 120 0 "+rgb+"_glow run say RGB_WIN_GLOW_PASS",
       "execute if block 2 120 0 "+rgb+"_glass run say RGB_WIN_GLASS_PASS",
       "rgb get","rgb bake","save-all flush"
    ])
    report["same_world_reopen"]=True
    report["persistent_blocks"]=all(x in second for x in (
         "RGB_WIN_NORMAL_PASS","RGB_WIN_GLOW_PASS","RGB_WIN_GLASS_PASS"))
    assert report["persistent_blocks"] and "RGB mode: MANUAL" in second
    print("REAL_WINDOWS_READY_SERVER_COMPLETE_PASS",target,c["loader"],
          "portable_java",c["java"],"mods",len(mods),flush=True)
finally:
    (root/"result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
