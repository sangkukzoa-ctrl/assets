#!/usr/bin/env python3
"""No-EULA-acceptance Fabric 1.21.1 upstream C&B loader smoke test.

The test deliberately stops at the Minecraft EULA requirement; it does NOT
start a game world, accept the terms, or validate RGB Blocks multiplayer.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from datetime import datetime,timezone

BASE=Path("smoke-fabric-1.21.1");BASE.mkdir(exist_ok=True)
MODS=BASE/"mods";MODS.mkdir(exist_ok=True)
OUT=Path("audit-output");OUT.mkdir(exist_ok=True)

def download(url, path):
    req=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Fabric-Loader-SmokeTest/1.0"})
    with urllib.request.urlopen(req,timeout=120) as resp:
        data=resp.read()
    Path(path).write_bytes(data)
    print(f"Downloaded {url}, {len(data)} bytes",flush=True)

def fabric_api_url():
    req=urllib.request.Request("https://api.modrinth.com/v2/project/P7dR8mSH/version",headers={"User-Agent":"RGBBlocks-Fabric-Loader-SmokeTest/1.0"})
    with urllib.request.urlopen(req,timeout=120) as resp:
        versions=json.load(resp)
    for v in versions:
        if v.get("version_number")=="0.116.17+1.21.1" and "fabric" in v.get("loaders",[]):
            files=v.get("files",[])
            primary=next((x for x in files if x.get("primary") and x.get("filename","").endswith(".jar")),None)
            if not primary:
                primary=next((x for x in files if x.get("filename","").endswith(".jar")),None)
            return primary["url"], primary["filename"]
    raise RuntimeError("Pinned Fabric API 0.116.17+1.21.1 unavailable from Modrinth API.")

def main():
    download("https://meta.fabricmc.net/v2/versions/loader/1.21.1/0.19.5/1.1.2/server/jar",BASE/"fabric-server.jar")
    download("https://mediafilez.forgecdn.net/files/9455/172/chisels-and-bits-fabric-21.1.40.jar",MODS/"chisels-and-bits-fabric-21.1.40.jar")
    api,filename=fabric_api_url();download(api,MODS/filename)
    cmd=["java","-Xms512M","-Xmx3G","-jar","fabric-server.jar","nogui"]
    timed_out=False
    try:
        r=subprocess.run(cmd,cwd=BASE,capture_output=True,text=True,timeout=240)
        log=r.stdout+"\n"+r.stderr
        exit_code=r.returncode
    except subprocess.TimeoutExpired as e:
        timed_out=True
        log=(e.stdout or b"").decode("utf-8","replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
        log+="\n"+((e.stderr or b"").decode("utf-8","replace") if isinstance(e.stderr,bytes) else (e.stderr or ""))
        exit_code=124
    (OUT/"fabric-server-first-launch.log").write_text(log,encoding="utf-8")
    lower=log.lower()
    eula=BASE/"eula.txt"
    has_cnb="chiselsandbits" in lower or "chisels-and-bits" in lower
    reached_eula=eula.exists() and ("eula" in lower)
    exception=any(word in lower for word in ("noclassdeffounderror","modresolutionexception","mixinapplyerror","nosuchmethoderror"))
    status="EULA_GATE_REACHED" if reached_eula and has_cnb and not exception else "FAIL_OR_INCONCLUSIVE"
    report={"timestamp":datetime.now(timezone.utc).isoformat(),
            "scope":"Fabric/C&B upstream pre-EULA classloading only; no world; RGB Blocks absent",
            "minecraft":"1.21.1","loader":"Fabric 0.19.5",
            "chisels_and_bits":"21.1.40","fabric_api":"0.116.17+1.21.1",
            "status":status,"exit_code":exit_code,"timed_out":timed_out,
            "cnb_mentioned":has_cnb,"eula_file_present":eula.exists(),
            "eula_accepted":False,"jvm_classloading_exception_detected":exception}
    (OUT/"fabric-loader-smoke.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)
    print("Last lines of launch log:",flush=True)
    print("\n".join(log.splitlines()[-45:]),flush=True)
    # Distinguish network issues from compatibility; both remain unverified.
    return 0 if status=="EULA_GATE_REACHED" else 1
if __name__=="__main__":
    sys.exit(main())
