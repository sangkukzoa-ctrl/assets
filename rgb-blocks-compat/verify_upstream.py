#!/usr/bin/env python3
"""Public upstream dependency inspection for RGB Blocks 1.3.1 legacy ports.

No claim of RGB Blocks build or in-game verification. Inspect official released jars
and dependency metadata; download from authors' distribution CDN.
"""
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("audit-output")
OUT.mkdir(exist_ok=True)

TARGETS = [
    ("1.21.1", "neoforge", "21.1.33", 7441123, "chisels-and-bits-neoforge-21.1.33.jar"),
    ("1.21.1", "fabric", "21.1.40", 9455172, "chisels-and-bits-fabric-21.1.40.jar"),
    ("1.20.1", "forge", "20.1.20", 7620767, "chisels-and-bits-forge-20.1.20.jar"),
]
KNOWN_PROBLEM = "com/communi/suggestu/saecularia/caudices/core/block/IBlockWithWorldlyProperties.class"

def fetch(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "RGBBlocks-Compatibility-Audit/1.0 (GitHub Actions; static archive verification)",
        "Accept": "*/*",
    })
    with urllib.request.urlopen(request, timeout=80) as response:
        return response.read()

def download_curseforge(file_id, filename):
    path = f"files/{file_id // 1000}/{file_id % 1000}/{filename}"
    errors = []
    for host in ("mediafilez.forgecdn.net", "edge.forgecdn.net"):
        url = f"https://{host}/{path}"
        try:
            data = fetch(url)
            if not zipfile.is_zipfile(io.BytesIO(data)):
                raise ValueError(f"not a ZIP-compatible JAR: {len(data)} bytes")
            return data, url
        except Exception as e:
            errors.append(f"{url}: {e}")
    raise RuntimeError("; ".join(errors))

def check_zip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as jar:
        bad = jar.testzip()
        return bad is None, len(jar.namelist())

def nested_scan(data, depth=0, record=None, route="root"):
    if record is None:
        record = {"nested": [], "class_found": [], "manifests": [], "fabric_mod_ids": []}
    if depth > 7 or not zipfile.is_zipfile(io.BytesIO(data)):
        return record
    with zipfile.ZipFile(io.BytesIO(data)) as jar:
        names = set(jar.namelist())
        if KNOWN_PROBLEM in names:
            record["class_found"].append(route)
        if "fabric.mod.json" in names:
            try:
                mod_data = json.loads(jar.read("fabric.mod.json"))
                record["fabric_mod_ids"].append({"path":route, "id":mod_data.get("id"), "version":mod_data.get("version")})
            except Exception as e:
                record["fabric_mod_ids"].append({"path":route, "error":str(e)})
        if "META-INF/MANIFEST.MF" in names:
            manifest = jar.read("META-INF/MANIFEST.MF").decode("utf-8", "replace")
            modtype = [x.strip() for x in manifest.splitlines() if x.lower().startswith("fmlmodtype:")]
            record["manifests"].append({"path":route, "fml_mod_type":modtype})
        for name in sorted(names):
            if name.endswith(".jar") and ("META-INF/jarjar/" in name or depth < 1):
                nested = jar.read(name)
                record["nested"].append({"path":route+"/"+name, "size_bytes":len(nested)})
                nested_scan(nested, depth+1, record, route+"/"+name)
    return record

def inspect_cnb(mc, loader, version, file_id, name):
    row = {
        "minecraft":mc, "loader":loader, "cnb_version":version,
        "official_page":f"https://www.curseforge.com/minecraft/mc-mods/chisels-bits-for-fabric/files/{file_id}"
            if loader == "fabric" else f"https://www.curseforge.com/minecraft/mc-mods/chisels-bits/files/{file_id}",
        "cnb_id":file_id, "name":name
    }
    try:
        data, url = download_curseforge(file_id, name)
        row["download_url"] = url
        row["bytes"] = len(data)
        row["sha256"] = hashlib.sha256(data).hexdigest()
        row["zip_crc_ok"], row["archive_entries"] = check_zip(data)
        scanned = nested_scan(data)
        row.update(scanned)
        row["known_saecularia_interface_found"] = bool(scanned["class_found"])
        row["possible_nested_manifest_issue"] = any(
            "saecularia-caudices" in x["path"] and
            "FMLModType: MOD" in x["fml_mod_type"]
            for x in scanned["manifests"]
        )
        if loader=="neoforge" and version=="21.1.33":
            row["warning"] = "Known public NeoForge 21.1.33 NoClassDefFoundError issue #1369; jarjar manifest type problem. Successful ZIP integrity does not prove runtime loading."
        row["status"] = "inspected" if row["zip_crc_ok"] else "corrupt"
    except Exception as e:
        row["status"] = "download_failed"
        row["error"] = str(e)
    return row

def modrinth_version(slug, version):
    try:
        # Public metadata; not a Minecraft runtime test.
        from urllib.parse import quote
        url = f"https://api.modrinth.com/v2/project/{quote(slug)}/version"
        versions = json.loads(fetch(url))
        selected = [v for v in versions if v.get("version_number") == version]
        return [{"version": v.get("version_number"), "loaders":v.get("loaders"),
                 "game_versions":v.get("game_versions"),
                 "dependencies":[{"project_id":d.get("project_id"),"version_id":d.get("version_id"),
                                  "dependency_type":d.get("dependency_type")} for d in v.get("dependencies",[])]}
                for v in selected]
    except Exception as e:
        return {"error":str(e)}

def main():
    rows = [inspect_cnb(*x) for x in TARGETS]
    result = {
        "audit_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "upstream mod jar integrity and declared dependency metadata only; RGB Blocks not compiled or game tested",
        "chisels_and_bits":rows,
        "iris_neoforge_versions":modrinth_version("iris", "1.8.12+1.21.1-neoforge"),
        "sodium_neoforge_versions":modrinth_version("sodium", "mc1.21.1-0.6.13-neoforge"),
        "oculus_forge_versions":modrinth_version("oculus", "1.20.1-1.8.0"),
        "embeddium_forge_versions":modrinth_version("embeddium", "0.3.31+mc1.20.1"),
    }
    (OUT/"upstream-artifact-audit.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    table = ["# RGB Blocks legacy upstream artifact audit", "",
        "This is **not** an RGB Blocks build, Minecraft launch, singleplayer, or multiplayer test.", "",
        "| Minecraft | Loader | C&B version | JAR integrity | Nested SC class | Manifest risk |",
        "| --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        table.append(f"| {row['minecraft']} | {row['loader']} | {row['cnb_version']} | {row.get('status')} | {row.get('known_saecularia_interface_found','N/A')} | {row.get('possible_nested_manifest_issue','N/A')} |")
    table.extend(["", "## Caution", "- Upstream NeoForge 21.1.33 has a known classloading failure (#1369).",
                  "- Forge 20.1.20 release notes explicitly fix the empty VoxelShape crash present in 20.1.19.",
                  "- For 1.21.1 Fabric 21.1.40 was published on 2026-11-05; inspect with actual game runtime before release.",
                  "- This static audit makes no claim about compatible RGB lights or shaders."])
    markdown = "\n".join(table)+"\n"
    (OUT/"README.md").write_text(markdown,encoding="utf-8")
    print(markdown)
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:
            f.write(markdown)
    if all(r["status"] == "download_failed" for r in rows):
        print("No upstream jars could be fetched.",file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
