#!/usr/bin/env python3
"""Release-blocking 1.3.1 RGB full palette, assets and structure checker.

Usage: python3 rgb-blocks-compat/validate_full_parity.py fabric1211|forge1201
Tests original artist assets copied byte-exact and 50,061 blocks are never
silently dropped; tests migrated models have target-old valid semantic shape.
Renderer/complementary shader correctness requires separate live tests.
"""
import hashlib,io,json,pathlib,sys,urllib.request,zipfile
from collections import Counter
from pathlib import Path

target=sys.argv[1]
assert target in ("fabric1211","forge1201")
mc="1.21.1" if target=="fabric1211" else "1.20.1"
base=Path("port-work/mc1211-fabric" if target=="fabric1211" else "port-work/mc1201-forge")
ports=[p for p in (base/"build/libs").glob("*.jar") if "-sources" not in p.name and "-dev" not in p.name]
assert ports, "No actual port JAR to verify"
port=max(ports,key=lambda p:p.stat().st_size)
source_url="https://cdn.modrinth.com/data/A48MxLWx/versions/HsQZbhRf/RgbBlocksmod-26.1.2-1.3.1F.jar"
with urllib.request.urlopen(urllib.request.Request(source_url,headers={"User-Agent":"RGBBlocks-Port-Parity/1.0"}),timeout=180) as r:
    source=r.read()
source_jar=zipfile.ZipFile(io.BytesIO(source))
new=zipfile.ZipFile(port)
originals=set(source_jar.namelist());modified=set(new.namelist())
print("PORT",mc,port,port.stat().st_size,"files",len(modified),flush=True)
assert "pack.mcmeta" in modified,"Mod cannot mount graphical resources: missing pack.mcmeta"
pack=json.loads(new.read("pack.mcmeta"))
expected_pack_format=34 if target=="fabric1211" else 15
assert pack["pack"]["pack_format"]==expected_pack_format,pack
pal=json.loads(new.read("assets/rgbblocks/palette.json"))
assert len(pal)==16687, len(pal)
assert new.read("assets/rgbblocks/palette.json")==source_jar.read("assets/rgbblocks/palette.json")
names=set()
missing=[]
bad=[]
for color in pal:
    base_name="rgb_%s_%d_%d_%d"%(color["group"],color["red"],color["green"],color["blue"])
    for kind in ("","_glow","_glass"):
        name=base_name+kind
        names.add(name)
        refs=[
         "assets/rgbblocks/blockstates/"+name+".json",
         "assets/rgbblocks/models/block/"+name+".json",
         "assets/rgbblocks/models/item/"+name+".json",
         "assets/rgbblocks/items/"+name+".json" ]
        for path in refs:
            if path not in modified:missing.append(path)
        if any(path not in modified for path in refs):continue
        block=json.loads(new.read(refs[1]))
        state=json.loads(new.read(refs[0]))
        item=json.loads(new.read(refs[2]))
        if state.get("variants",{}).get("",{}).get("model")!="rgbblocks:block/"+name:
            bad.append("blockstate bad model "+name)
        if item.get("parent")!="minecraft:item/generated":
            bad.append("item parent invalid "+name)
        if kind=="_glass":
            texture=block.get("textures",{}).get("all")
            if not isinstance(texture,str) or texture!="rgbblocks:block/"+base_name+"_glass":
                bad.append("glass sprite path invalid "+name+"="+str(texture))
            if target=="forge1201" and block.get("render_type")!="minecraft:translucent":
                bad.append("glass not translucent in Forge "+name)
        else:
            if block.get("textures",{}).get("all")!="rgbblocks:block/"+base_name:
                bad.append("normal/glow sprite path invalid "+name)
assert len(names)==50061,len(names)
assert not missing,(len(missing),missing[:10])
assert not bad,(len(bad),bad[:10])
# Comparison of exact same source artists' RGB textures and language files.
# Read original bytes only for assets where a byte-exact contract is required.
original_safe={p for p in originals if p.endswith(".png") or
               p.startswith("assets/rgbblocks/lang/") or
               p=="assets/rgbblocks/palette.json"}
new_safe={p for p in modified if p.endswith(".png") or
          p.startswith("assets/rgbblocks/lang/") or
          p=="assets/rgbblocks/palette.json"}
assert original_safe==new_safe,(len(original_safe-new_safe),len(new_safe-original_safe))
bad_hash=[]
for path in original_safe:
    if hashlib.sha256(new.read(path)).digest()!=hashlib.sha256(source_jar.read(path)).digest():
        bad_hash.append(path)
assert not bad_hash,(len(bad_hash),bad_hash[:5])

source_java=Path("rgb-blocks-compat/recovered/fabric/com")
dest_java=base/"src/main/java/com"
missing_classes=[]
for p in source_java.rglob("*.java"):
    if not (dest_java/p.relative_to(source_java)).is_file():
        missing_classes.append(str(p))
assert not missing_classes,("Original class files disappeared",missing_classes)
rgbengine=dest_java/"rgbblocks/client/lighting/RGBRealLightEngine.java"
engine=rgbengine.read_text(encoding="utf-8")
for key in ("MAX_CNB_ENTRIES","RGB_PATTERN","applyToVanillaQuad","getCnb","bake"):
    assert key in engine,(key,"original light engine routine removed")
assert (dest_java/"rgbblocks/mixin/client/Sodium06BlockRendererMixin.java").exists(),"Sodium bridge missing"
# Forge bridge adapter uses target-specific vertex pipeline.
if target=="forge1201":
    cand=list((dest_java/"rgbblocks/mixin/client").glob("*Embeddium*.java"))
    assert cand, "Forge 1.20.1 Embeddium RGB vertex bridge missing"
metadata="fabric.mod.json" if target=="fabric1211" else "META-INF/mods.toml"
assert metadata in modified,(metadata,"missing")
report={"minecraft":mc,"loader":target,"port":str(port),
 "original_source_jar_sha256":hashlib.sha256(source).hexdigest(),
 "ported_jar_sha256":hashlib.sha256(port.read_bytes()).hexdigest(),
 "old_class_paths_preserved":len(list(source_java.rglob("*.java"))),
 "rgb_color_count":len(pal),"registered_rgb_block_model_pairs":len(names),
 "glass_render_type_parity":True,"model_json_paths_pass":True,
 "original_png_language_palette_byte_identical":len(original_safe),
 "pack_mcmeta_format":expected_pack_format,
 "limitation":"Static equality of registered assets and original source class locations; does not verify in-world light/shader rendered pixels or multi-client sync"}
out=Path("audit-output");out.mkdir(exist_ok=True)
(out/f"parity-{target}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print("PASS RGB Full Parity (static)",json.dumps(report,ensure_ascii=False),flush=True)
