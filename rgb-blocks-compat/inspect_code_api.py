#!/usr/bin/env python3
"""Generate API migration inventory from official binary, not user source.

Output is an inventory only. Does not port code or prove runtime compatibility.
"""
import io
import json
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

URL="https://mediafilez.forgecdn.net/files/8426/251/RgbBlocksmod-26.1.2-1.3.1.jar"
req=urllib.request.Request(URL,headers={"User-Agent":"RGBBlocks-Binary-API-Inventory/1.0"})
data=urllib.request.urlopen(req,timeout=120).read()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    classes=sorted(n for n in z.namelist() if n.endswith(".class"))
    configs=sorted(n for n in z.namelist() if n.endswith((".mixins.json",".mods.toml","neoforge.mods.toml","fabric.mod.json")) or "mixin" in n.lower() and n.endswith(".json"))
    sources={}
    for cls in classes:
        b=z.read(cls)
        sources[cls]={
            "bytes":len(b),
            "references_quadinstance": b"QuadInstance" in b,
            "references_neoforge": b"net/neoforged" in b,
            "references_chiselsbits": b"chiselsandbits" in b.lower() or b"chiselsAndBits" in b,
            "references_sodium": b"sodium" in b.lower(),
            "references_network": b"customPayload" in b or b"CustomPacketPayload" in b,
        }
    summary={
        "original_minecraft":"26.1.2","original_mod_version":"1.3.1",
        "source":"official published NeoForge JAR",
        "class_count":len(classes),
        "classes":sources,
        "configuration_files":configs,
    }
    out=Path("audit-output");out.mkdir(exist_ok=True)
    (out/"java-api-migration-inventory.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Original compiled Java class count: {len(classes)}")
    print("Class names and migration flags:")
    for name,v in sources.items():
        flags=[k.replace("references_","") for k,b in v.items() if b is True]
        print(f"  {name} ({v['bytes']} bytes) {' '.join(flags)}")
    print("Config candidates:", configs)
