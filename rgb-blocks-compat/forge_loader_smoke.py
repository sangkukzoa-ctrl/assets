#!/usr/bin/env python3
"""Forge 1.20.1 + Chisels & Bits 20.1.20 pre-EULA loader smoke.

Intentionally never accepts EULA or creates a playable world. RGB Blocks
is NOT installed; results cannot validate RGB functionality or multiplayer.
"""
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
from datetime import datetime,timezone
BASE=Path("smoke-forge-1.20.1");BASE.mkdir(exist_ok=True)
MODS=BASE/"mods";MODS.mkdir(exist_ok=True)
OUT=Path("audit-output");OUT.mkdir(exist_ok=True)
FORGE_VERSION="47.4.28"

def download(url,path):
    req=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Forge-Loader-SmokeTest/1.0"})
    with urllib.request.urlopen(req,timeout=180) as resp:
        data=resp.read()
    Path(path).write_bytes(data)
    print(f"Downloaded {url} ({len(data)} bytes)",flush=True)

def execute(cmd,timeout):
    try:
        r=subprocess.run(cmd,cwd=BASE,capture_output=True,text=True,timeout=timeout)
        return r.returncode,r.stdout+"\n"+r.stderr,False
    except subprocess.TimeoutExpired as e:
        out=(e.stdout or b"").decode("utf-8","replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
        err=(e.stderr or b"").decode("utf-8","replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
        return 124,out+"\n"+err,True

def main():
    download("https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.28/forge-1.20.1-47.4.28-installer.jar",BASE/"forge-installer.jar")
    download("https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",MODS/"chisels-and-bits-forge-20.1.20.jar")
    installer_code,installer_log,installer_timeout=execute(["java","-jar","forge-installer.jar","--installServer"],420)
    (OUT/"forge-installer.log").write_text(installer_log,encoding="utf-8")
    if installer_code!=0 or not (BASE/"run.sh").exists():
        print("Forge installation did not finish. Logs:\n"+installer_log[-7000:],flush=True)
        raise AssertionError("Forge server installer failure, no runtime claim")
    code,log,timed_out=execute(["bash","./run.sh","nogui"],240)
    (OUT/"forge-server-first-launch.log").write_text(log,encoding="utf-8")
    lower=log.lower()
    reached=(BASE/"eula.txt").exists() and "eula" in lower
    cnb="chiselsandbits" in lower or "chisels-and-bits" in lower
    exception=any(x in lower for x in ("noclassdeffounderror","modloadingexception","mixinapplyerror","nosuchmethoderror"))
    status="EULA_GATE_REACHED" if reached and cnb and not exception else "FAIL_OR_INCONCLUSIVE"
    report={"timestamp":datetime.now(timezone.utc).isoformat(),"scope":"upstream Forge 1.20.1 C&B pre-EULA classloading only; RGB Blocks absent; no world",
            "minecraft":"1.20.1","forge":"47.4.28","chisels_and_bits":"20.1.20",
            "status":status,"exit_code":code,"timed_out":timed_out,
            "cnb_mentioned":cnb,"eula_file_present":(BASE/"eula.txt").exists(),
            "eula_accepted":False,"jvm_classloading_exception_detected":exception}
    (OUT/"forge-loader-smoke.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)
    print("Last 45 lines of startup log:\n"+"\n".join(log.splitlines()[-45:]),flush=True)
    return 0 if status=="EULA_GATE_REACHED" else 1

if __name__=="__main__":
    sys.exit(main())
