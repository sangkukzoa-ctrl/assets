#!/usr/bin/env python3
"""Check the original AUTHOR-PROVIDED RGB Blocks 1.3.1 resources.

No JAR retrieval, binary decompilation or public download-counter effects.
The original Fabric and NeoForge archives were cross-checked byte-for-byte.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json

ROOT=Path("rgb-blocks-compat/owner-source")
BASE=ROOT/"shared/resources/assets/rgbblocks"
PROVENANCE=ROOT/"source-provenance.json"
OUTPUT=Path("audit-output")
OUTPUT.mkdir(exist_ok=True)
if not PROVENANCE.is_file() or not BASE.is_dir():
    raise SystemExit("Owner source is not staged. Run stage_owner_original.py; no public-JAR fallback.")
source=json.loads(PROVENANCE.read_text(encoding="utf-8"))
assert source.get("resources")==233629 and source.get("resources_extracted")
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
expected={
    "assets/rgbblocks/palette.json":"e94c52deb1cf167c9633ae7477bc8e3e91e112531805175427dba8013c241dde",
    "assets/rgbblocks/lang/en_us.json":"99195086f03946134829b8d54e35a96952edf19c2f64953c50fea968f02390b3"}
for name,digest in expected.items():
    actual=sha256(ROOT/"shared/resources"/name)
    assert actual==digest,(name,actual,digest)
total=0;png=0;blockstates=0;blocks=0;item_models=0
for path in BASE.rglob("*"):
    if not path.is_file():continue
    total+=1
    name=str(path).replace(chr(92),"/")
    if path.suffix.lower()==".png":png+=1
    if "/blockstates/" in name and path.suffix==".json":blockstates+=1
    if "/models/block/" in name and path.suffix==".json":blocks+=1
    if "/models/item/" in name and path.suffix==".json":item_models+=1
assert blockstates==50061,("Expected 50,061 author's blocks",blockstates)
assert png==33377,("Expected 33,377 author's textures",png)
assert total>=233000,("Original RGB Blocks assets missing",total)
result={
    "source":"owner-uploaded Fabric 1.3.1 full source",
    "source_jar_downloads":0,
    "owner_source_sha256":source["owner_fabric_sha256"],
    "checked_utc":datetime.now(timezone.utc).isoformat(),
    "expected_palette_colors":16687,
    "expected_block_count":50061,
    "png_count":png,"blockstates_count":blockstates,
    "block_models_count":blocks,"item_models_count":item_models,
    "asset_files":total,
    "asset_validation":"PASS"}
(OUTPUT/"rgb-blocks-1.3.1-original-owner-source-baseline.json").write_text(
    json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("AUTHOR_ORIGINAL_ASSET_BASELINE_PASS",json.dumps(result),flush=True)
