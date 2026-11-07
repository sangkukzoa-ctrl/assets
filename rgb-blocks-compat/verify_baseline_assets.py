#!/usr/bin/env python3
"""Audit byte-identical asset preservation baseline in the official RGB Blocks 1.3.1 NeoForge JAR.

Only establishes an independently reproducible fingerprint/reference for future backports.
Does not port code and does not simulate Minecraft.
"""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

FILE_ID = 8426251
NAME = "RgbBlocksmod-26.1.2-1.3.1.jar"
SOURCE = f"https://mediafilez.forgecdn.net/files/{FILE_ID//1000}/{FILE_ID%1000}/{NAME}"
DEST = Path("audit-output")
DEST.mkdir(exist_ok=True)

request = urllib.request.Request(SOURCE, headers={"User-Agent":"RGBBlocks-Backward-Compat-Asset-Integrity-Test/1.0"})
with urllib.request.urlopen(request,timeout=120) as response:
    source_bytes=response.read()
assert zipfile.is_zipfile(io.BytesIO(source_bytes)), "Upstream jar is not a ZIP"
p = {"source_url":SOURCE, "timestamp_utc":datetime.now(timezone.utc).isoformat(),
     "source_jar_sha256":hashlib.sha256(source_bytes).hexdigest(), "source_jar_size":len(source_bytes),
     "expected_palette_colors":16687,"expected_block_count":50061}

with zipfile.ZipFile(io.BytesIO(source_bytes)) as z:
    bad=z.testzip()
    assert bad is None, f"Corrupted CRC entry: {bad}"
    names=[x for x in z.namelist() if not x.endswith("/")]
    asset_names=[x for x in names if x.startswith("assets/")]
    png_names=[x for x in asset_names if x.lower().endswith(".png")]
    blockstates=[x for x in asset_names if "/blockstates/" in x and x.endswith(".json")]
    block_models=[x for x in asset_names if "/models/block/" in x and x.endswith(".json")]
    item_models=[x for x in asset_names if "/models/item/" in x and x.endswith(".json")]
    languages=[x for x in asset_names if "/lang/" in x and x.endswith(".json")]
    p.update({
        "total_jar_files":len(names), "total_asset_files":len(asset_names),
        "png_count":len(png_names),"blockstates_count":len(blockstates),
        "block_models_count":len(block_models),"item_models_count":len(item_models),
        "lang_files":languages[:40],
        "asset_roots":dict(Counter(x.split("/")[1] for x in asset_names if len(x.split("/"))>=3)),
        "sample_names":sorted(names[:30]),
    })
    fingerprints={}
    for cat,paths in [
        ("png",png_names),("blockstates",blockstates),
        ("block_models",block_models),("item_models",item_models),("languages",languages)
    ]:
        h=hashlib.sha256()
        for name in sorted(paths):
            digest=hashlib.sha256(z.read(name)).hexdigest()
            h.update((name+"\t"+digest+"\n").encode())
        fingerprints[cat]={"file_count":len(paths),"path_and_content_sha256":h.hexdigest()}
    p["fingerprints"]=fingerprints
    p["count_invariants"]={
        "three_blocks_per_color":len(blockstates)==3*p["expected_palette_colors"],
        "png_count_equal_expected_33377":len(png_names)==33377
    }
    # Check shape but do not insist on old version asset paths.
    p["artifact_validation"]="PASS" if all(p["count_invariants"].values()) else "CHECK_COUNTS"

(DEST/"rgb-blocks-1.3.1-official-asset-baseline.json").write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding="utf-8")
print("RGB Blocks 1.3.1 official published JAR asset baseline")
for key in ("source_url","source_jar_sha256","total_jar_files","total_asset_files","png_count","blockstates_count","block_models_count","item_models_count","artifact_validation"):
    print(f"{key}: {p[key]}")
for cat,record in fingerprints.items():
    print(f"{cat} SHA256(path + bytes): {record['path_and_content_sha256']}")
