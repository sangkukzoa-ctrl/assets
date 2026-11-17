#!/usr/bin/env python3
"""Create an immediately startable Windows x64 Forge/NeoForge Minecraft server ZIP.

Original owner RGB Blocks mod JAR comes from successfully validated GitHub
Actions release candidate, not a CI-instrumented rebuild. The entire native
Forge or NeoForge server libraries are installed at ZIP assembly time. A
verified portable Eclipse Temurin Windows JRE is placed at runtime/java so
different system JAVA_HOME/PATH values do not break the server BAT.

NO Chisels & Bits or shader/renderer mods are required to boot. One-click
optional official direct download scripts and exact tested client URLs are
included for users who cannot install the Modrinth .mrpack.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

CONFIG={
    "forge1201":{
        "mc":"1.20.1","loader":"Forge","loader_id":"forge",
        "loader_version":"47.4.28","java":17,"port":25566,
        "installer":"https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.28/forge-1.20.1-47.4.28-installer.jar",
        "args":"libraries/net/minecraftforge/forge/1.20.1-47.4.28/win_args.txt",
        "jarexpect":"META-INF/mods.toml",
        "artifact":"input/forge1201",
        "prefix":"RGBBlocks-1.3.1-MC1.20.1-Forge"
    },
    "neoforge1211":{
        "mc":"1.21.1","loader":"NeoForge","loader_id":"neoforge",
        "loader_version":"21.1.265","java":21,"port":25567,
        "installer":"https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.265/neoforge-21.1.265-installer.jar",
        "args":"libraries/net/neoforged/neoforge/21.1.265/win_args.txt",
        "jarexpect":"META-INF/neoforge.mods.toml",
        "artifact":"input/neoforge1211",
        "prefix":"RGBBlocks-1.3.1-MC1.21.1-NeoForge"
    }
}
assert len(sys.argv)==2 and sys.argv[1] in CONFIG,"Expected forge1201 or neoforge1211"
target=sys.argv[1]; c=CONFIG[target]
base=Path("windows-ready")
base.mkdir(exist_ok=True)
foldername="RGBBlocks-1.3.1-MC"+c["mc"]+"-"+c["loader"]+"-"+c["loader_version"]+"-WINDOWS-READY-SERVER"
server=base/foldername
if server.exists():shutil.rmtree(server)
server.mkdir(parents=True)

def sha(path,algo="sha256"):
    h=hashlib.new(algo)
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def download(url,dest,timeout=150,retries=4):
    dest.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(1,retries+1):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Legacy-Port-Windows-Server-Installer/1.0"})
            with urllib.request.urlopen(request,timeout=timeout) as r,open(dest,"wb") as f:
                while True:
                    data=r.read(1024*1024)
                    if not data:break
                    f.write(data)
            assert dest.stat().st_size>1000,(url,dest.stat().st_size)
            print("DOWNLOADED",url,dest.stat().st_size,flush=True)
            return
        except Exception as e:
            print("RETRY",attempt,"OF",retries,str(e),flush=True)
            if dest.exists():dest.unlink()
            if attempt==retries:raise
            time.sleep(5*attempt)

# Exact tested owner-compiled native production mod and pack manifest.
artifact=Path(c["artifact"])
jars=list(artifact.rglob(c["prefix"]+".jar"))
assert len(jars)==1,("One and only one independently built RGB JAR required",jars)
rgb=jars[0]
manifests=list(artifact.rglob("MANIFEST.json"))
assert len(manifests)==1,manifests
manifest=json.loads(manifests[0].read_text(encoding="utf-8"))
assert manifest["release_files_sha256"][rgb.name]==sha(rgb), "RGB JAR not the verified release candidate"
assert manifest["target"]==target and manifest["jar_registry_colors"]==16687
assert manifest["jar_blockmodel_count"]==50061
with zipfile.ZipFile(rgb) as z:
    assert z.testzip() is None
    assert c["jarexpect"] in z.namelist()
    assert not any(n.startswith("com/rgbblocks/ci/") for n in z.namelist()), "Diagnostic probe classes leaked into release"
(server/"mods").mkdir()
shutil.copy2(rgb,server/"mods"/rgb.name)

packs=list(artifact.rglob("*.mrpack"))
assert len(packs)==1,packs
with zipfile.ZipFile(packs[0]) as z:
    assert z.testzip() is None
    index=json.loads(z.read("modrinth.index.json"))
assert index["dependencies"]["minecraft"]==c["mc"]
assert index["dependencies"][c["loader_id"]]==c["loader_version"]
assert len(index["files"])==4
for entry in index["files"]:
    assert "sha512" in entry["hashes"] and len(entry["downloads"])>0,entry["path"]
cnb=[x for x in index["files"] if "chisels-and-bits" in x["path"].lower()]
assert len(cnb)==1 and cnb[0]["env"]["server"]=="required"
addons=[{"path":x["path"],"url":x["downloads"][0],"sha512":x["hashes"]["sha512"],
         "server":x["env"]["server"],"client":x["env"]["client"]} for x in index["files"]]
(server/"OPTIONAL_MOD_DOWNLOADS.json").write_text(json.dumps(addons,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Native server installer, including ALL libraries and Windows JVM argument file.
installer=server/("SERVER_INSTALLER_"+c["loader_version"]+".jar")
download(c["installer"],installer,timeout=180)
run=subprocess.run(["java","-jar",installer.name,"--installServer"],cwd=server,
                   text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=960)
(server/"SERVER_INSTALL_BUILD.log").write_text(run.stdout,encoding="utf-8",errors="replace")
if run.returncode!=0:
    raise AssertionError("Native installer failed:\n"+run.stdout[-12000:])
args=server/c["args"]
assert args.is_file() and args.stat().st_size>100,(
    "Windows installation missing the real loader win_args.txt",args,run.stdout[-4000:])
assert any((server/"libraries").rglob("*.jar")), "Installer did not resolve the full native server Java libraries"
print("NATIVE_SERVER_LIBRARIES_OK",str(args),args.stat().st_size,
      len(list((server/"libraries").rglob("*.jar"))),flush=True)
installer.unlink()
# Keep the full installation log for troubleshooting; it is not needed to run.

# Portable Windows x64 Java runtime, independently SHA-256 verified using the
# official Eclipse Adoptium API response. User's current BAT uses an unknown
# system java on PATH; this package works even if PATH is Java 17 on NeoForge.
api=("https://api.adoptium.net/v3/assets/latest/"+str(c["java"])+
     "/hotspot?architecture=x64&image_type=jre&os=windows&vendor=eclipse")
meta_file=server/"temurin-api.json"
download(api,meta_file,timeout=150)
metadata=json.loads(meta_file.read_text(encoding="utf-8"))
assert isinstance(metadata,list) and metadata
jre_obj=next((x for x in metadata
        if x.get("binary",{}).get("image_type")=="jre" and
        x.get("binary",{}).get("os")=="windows" and
        x.get("binary",{}).get("architecture")=="x64"),metadata[0])
package=jre_obj["binary"]["package"]
assert package["link"].startswith("https://") and len(package["checksum"])==64
jrezip=base/(foldername+"-temurin-jre.zip")
download(package["link"],jrezip,timeout=210)
assert sha(jrezip).lower()==package["checksum"].lower(),("Temurin SHA256 mismatch",sha(jrezip),package["checksum"])
with tempfile.TemporaryDirectory(prefix="rgb-temurin-") as d:
    temp=Path(d)
    with zipfile.ZipFile(jrezip) as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts,"Unsafe JRE archive member"
        z.extractall(temp)
    candidates=list(temp.rglob("bin/java.exe"))
    assert len(candidates)==1,("Temurin Windows java.exe missing",candidates)
    root=candidates[0].parent.parent
    shutil.copytree(root,server/"runtime/java")
assert (server/"runtime/java/bin/java.exe").is_file()
assert (server/"runtime/java/release").is_file()
jre_release=(server/"runtime/java/release").read_text(encoding="utf-8")
assert "JAVA_VERSION=" in jre_release
print("WINDOWS_TEMURIN_JRE_OK",c["java"],package["checksum"],
      (server/"runtime/java/bin/java.exe").stat().st_size,flush=True)
jrezip.unlink()
meta_file.unlink()

# Ready to launch: preserve the user's proven @jvm-args + @win_args + %* style.
# The default BAT prefers bundled JRE, while the alternative uses system java.
argfile=c["args"].replace("/","/")
runbat=("@echo off\r\nsetlocal\r\ncd /d \"%~dp0\"\r\n"+
        "set \"JAVA_EXE=%~dp0runtime\\java\\bin\\java.exe\"\r\n"+
        "if not exist \"%JAVA_EXE%\" (\r\n"+
        "  echo [ERROR] Bundled Windows Java executable missing.\r\n"+
        "  pause\r\n  exit /b 1\r\n)\r\n"+
        "echo [RGB Blocks] Minecraft "+c["mc"]+" "+c["loader"]+" "+c["loader_version"]+"\r\n"+
        "echo [RGB Blocks] Portable Eclipse Temurin Java "+str(c["java"])+"\r\n"+
        "\"%JAVA_EXE%\" -version\r\n"+
        "\"%JAVA_EXE%\" @user_jvm_args.txt @"+argfile+" nogui %*\r\n"+
        "set \"RC=%errorlevel%\"\r\n"+
        "echo.\r\necho [RGB Blocks] Server exit code: %RC%\r\npause\r\nexit /b %RC%\r\n")
(server/"run.bat").write_bytes(runbat.encode("ascii"))
systembat=("@echo off\r\nsetlocal\r\ncd /d \"%~dp0\"\r\n"+
           "echo [RGB Blocks] Using YOUR installed system Java on PATH:\r\n"+
           "where java\r\njava -version\r\n"+
           "java @user_jvm_args.txt @"+argfile+" nogui %*\r\n"+
           "set \"RC=%errorlevel%\"\r\npause\r\nexit /b %RC%\r\n")
(server/"run-system-java.bat").write_bytes(systembat.encode("ascii"))
check=("@echo off\r\ncd /d \"%~dp0\"\r\n"+
       "echo ===== System JAVA (your existing run.bat) =====\r\n"+
       "where java\r\njava -version\r\n"+
       "echo ===== Included self-contained JAVA "+str(c["java"])+" =====\r\n"+
       "\"runtime\\java\\bin\\java.exe\" -version\r\npause\r\n")
(server/"check-java.bat").write_bytes(check.encode("ascii"))
(server/"user_jvm_args.txt").write_text("-Xms1G\n-Xmx4G\n-XX:+UseG1GC\n",encoding="ascii")
(server/"eula.txt").write_text("eula=true\n",encoding="ascii")
(server/"server.properties").write_text(
    "online-mode=true\n"
    "server-ip=\n"
    "server-port="+str(c["port"])+"\n"
    "max-players=20\n"
    "view-distance=8\n"
    "simulation-distance=6\n"
    "motd=RGB Blocks 1.3.1 - Minecraft "+c["mc"]+" "+c["loader"]+"\n"
    "enable-command-block=true\n"
    "spawn-protection=0\n",encoding="ascii")

ps_source=r'''param([switch]$OnlyCnb)
$ErrorActionPreference='Stop'
$manifest=Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot 'OPTIONAL_MOD_DOWNLOADS.json') | ConvertFrom-Json
if($OnlyCnb) {
  $manifest=@($manifest | Where-Object {$_.path -match 'chisels-and-bits'})
  $folder=$PSScriptRoot
} else {
  $manifest=@($manifest | Where-Object {$_.client -eq 'required'})
  $folder=Join-Path $PSScriptRoot 'CLIENT_ADDONS'
}
foreach($item in $manifest) {
    $dest=Join-Path $folder ($item.path.Replace('/','\'))
    $parent=Split-Path -Parent $dest
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Write-Host ('Downloading original creator file: '+$item.url)
    if(!(Test-Path -LiteralPath $dest)) {
      Invoke-WebRequest -Uri $item.url -UseBasicParsing -OutFile $dest
    }
    $hash=(Get-FileHash -Algorithm SHA512 -LiteralPath $dest).Hash.ToLowerInvariant()
    if($hash -ne $item.sha512.ToLowerInvariant()) {
      Remove-Item -LiteralPath $dest -Force
      throw ('SHA-512 integrity check failed: '+$item.path)
    }
    Write-Host ('VERIFIED '+$item.path)
}
if($OnlyCnb) {
    Write-Host 'Server C&B installed as OPTIONAL interoperability mod. Restart server.'
} else {
    Write-Host 'Optional CLIENT mods and shaders downloaded to CLIENT_ADDONS directory.'
    Write-Host 'Copy CLIENT_ADDONS\mods files to your Minecraft client mods folder.'
    Write-Host 'Copy CLIENT_ADDONS\shaderpacks files to your client shaderpacks folder.'
}
'''
(server/"download-optional-mods.ps1").write_text(ps_source,encoding="utf-8-sig")
(server/"INSTALL-OPTIONAL-CNB-SERVER.bat").write_bytes(
    ("@echo off\r\ncd /d \"%~dp0\"\r\n"+
     "powershell -NoProfile -ExecutionPolicy Bypass -File \"download-optional-mods.ps1\" -OnlyCnb\r\n"+
     "pause\r\n").encode("ascii"))
(server/"DOWNLOAD-CLIENT-EXTRAS-NO-MRPACK.bat").write_bytes(
    ("@echo off\r\ncd /d \"%~dp0\"\r\n"+
     "powershell -NoProfile -ExecutionPolicy Bypass -File \"download-optional-mods.ps1\"\r\n"+
     "pause\r\n").encode("ascii"))
(server/"REMOVE-OPTIONAL-CNB-SERVER.bat").write_bytes(
    ("@echo off\r\ncd /d \"%~dp0\"\r\n"+
     "if not exist optional-mods mkdir optional-mods\r\n"+
     "for %%F in (mods\\chisels-and-bits*.jar) do if exist \"%%F\" move \"%%F\" optional-mods\\\r\n"+
     "echo CnB disabled; restart your server.\r\npause\r\n").encode("ascii"))
info_lines=[
    "RGB Blocks 1.3.1 - TESTED Minecraft "+c["mc"]+" / "+c["loader"]+" "+c["loader_version"],
    "",
    "One-click WINDOWS x64 server:",
    "  1. Extract this ZIP to a NEW directory. Keep your existing server untouched.",
    "  2. Double-click run.bat. Full Forge/NeoForge server libraries and the",
    "     correct portable Java "+str(c["java"])+" are ALREADY INCLUDED.",
    "  3. Server port "+str(c["port"])+" avoids your existing default 25565 port.",
    "     Edit server.properties to select another port.",
    "",
    "Your supplied existing run.bat:",
    "  java @user_jvm_args.txt @libraries/net/minecraftforge/forge/1.20.1-47.4.20/win_args.txt %*",
    "  pause",
    "It uses whatever java.exe is on Windows PATH; it does not expose the",
    "actual installed Java version. This ZIP's run.bat instead uses bundled",
    "runtime\\java\\bin\\java.exe, avoiding Java 17/21 collisions.",
    "run-system-java.bat preserves the same system-java and @win_args style.",
    "check-java.bat shows both your system Java and bundled Java versions.",
    "",
    "DEFAULT mods/ folder: only RGB Blocks JAR, ZERO OTHER MODS.",
    "The RGB Blocks mod has NO hard dependency on C&B, shader or renderer.",
    "OPTIONAL: INSTALL-OPTIONAL-CNB-SERVER.bat fetches exact tested C&B",
    "directly from official creator distribution and checks SHA-512.",
    "OPTIONAL: DOWNLOAD-CLIENT-EXTRAS-NO-MRPACK.bat fetches C&B, tested",
    "client renderer/shader mods and Complementary to CLIENT_ADDONS/",
    "for manual transfer into the matching client. No MRPACK import needed.",
    "Do not copy client-only Sodium/Iris/Embeddium/Oculus/shaderpacks to server mods/.",
    "",
    "TESTED C&B: "+("20.1.20" if target=="forge1201" else "21.1.32"),
    "TESTED client renderer: "+("Embeddium 0.3.31" if target=="forge1201" else "Sodium 0.6.13"),
    "TESTED client shaders: "+("Oculus 1.8.0" if target=="forge1201" else "Iris 1.8.12"),
    "TESTED shaderpack: Complementary Reimagined r5.9.3",
    "",
    "Existing world: do NOT overwrite or copy worlds without a backup.",
    "To adjust memory, edit user_jvm_args.txt (default -Xmx4G).",
    "Minecraft EULA: eula.txt is preset true for the server owner who has",
    "already operated and accepted a Minecraft server; review official terms.",
    "",
    "GitHub proof: https://github.com/sangkukzoa-ctrl/assets/actions/runs/44045724254",
]
(server/"README-FIRST-WINDOWS-SERVER.txt").write_text("\n".join(info_lines)+"\n",encoding="utf-8")
direct_lines=[
    "EXACT COMPATIBILITY MODS - DIRECT OFFICIAL URLS, NO MODPACK REQUIRED",
    "RGB Blocks is STANDALONE; the following mods are optional.",
    "Minecraft "+c["mc"]+" "+c["loader"]+" "+c["loader_version"],
    "Java "+str(c["java"]),
    ""
]
for a in addons:
    direct_lines.extend([a["path"],"  download: "+a["url"],"  SHA512: "+a["sha512"],
                         "  client: "+a["client"]+" / server: "+a["server"],""])
(server/"DIRECT_CLIENT_MOD_DOWNLOAD_LINKS.txt").write_text("\n".join(direct_lines),encoding="utf-8")
release={
    "minecraft":c["mc"],"loader":c["loader"],"loader_version":c["loader_version"],
    "java_major":c["java"],"portable_java_vendor":"Eclipse Temurin Windows x64 JRE",
    "portable_java_release":jre_obj.get("version",{}),
    "portable_java_archive_sha256":package["checksum"],
    "rgb_blocks":"1.3.1 native legacy port",
    "rgb_jar_file":rgb.name,
    "rgb_jar_sha256":sha(rgb),
    "installer":c["installer"],"server_listen_port":c["port"],
    "all_server_libraries_installed":True,
    "tested_mods":addons,"required_optional_mods":[],
    "standalone_server_default":True,
    "github_source_actions_run":44037516139
}
(server/"SERVER_VERSION_AND_HASHES.json").write_text(json.dumps(release,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
# Direct ZIP must contain all the files required for Windows startup:
assert (server/"run.bat").is_file() and (server/c["args"]).is_file()
assert len(list((server/"mods").glob("*.jar")))==1
assert (server/"runtime/java/bin/java.exe").is_file()
assert (server/"eula.txt").read_text().strip()=="eula=true"
assert (server/"user_jvm_args.txt").is_file()
for src in (rgb,server/c["args"],server/"runtime/java/bin/java.exe"):
    print("SERVER_FILE_HASH",src.name,sha(src),flush=True)

out=base/(foldername+".zip")
if out.exists():out.unlink()
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
    for file in sorted(server.rglob("*")):
        if file.is_file():
            z.write(file,str(file.relative_to(base)))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert any(n.endswith("/run.bat") for n in names)
    assert any(n.endswith("/runtime/java/bin/java.exe") for n in names)
    assert any(n.endswith("/"+c["args"]) for n in names)
    assert sum(n.endswith(".jar") and "/mods/" in n for n in names)==1
assert out.stat().st_size>20_000_000, "Unexpected tiny server archive"
print("WINDOWS_READY_SERVER_ZIP_PASS",target,out,out.stat().st_size,
      "SHA256",sha(out),"FILES",len(names),flush=True)
