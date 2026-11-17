#!/usr/bin/env python3
"""Verify the authentic owner's RGBRuntime survives the legacy SavedData port.

Reads the *actual* staged owner Java and extracts the real pr() transformer
from the build script via Python AST. It does not execute a build script,
touch a public distribution, or need any Minecraft dependencies.
"""
import ast, json, re
from pathlib import Path

BASE=Path("rgb-blocks-compat")
OWNER=BASE/"owner-source/fabric/com/rgbblocks/runtime/RGBRuntime.java"
BUILDER=BASE/"build_mc1211_fabric.py"
if not OWNER.is_file():
    raise SystemExit("Original owner Java source missing: run stage_owner_original.py")
original=OWNER.read_text(encoding="utf-8")
code=BUILDER.read_text(encoding="utf-8")
nodes=ast.parse(code,filename=str(BUILDER)).body
matches=[node for node in nodes if isinstance(node,ast.FunctionDef) and node.name=="pr"]
assert len(matches)==1,"Expected one RGBRuntime source migration transform"
isolated=ast.Module(body=[matches[0]],type_ignores=[])
context={"re":re}
exec(compile(isolated,str(BUILDER),"exec"),context)
migrated=context["pr"](original)

assert original.count("public record StatePayload(")==1
assert original.count("public record BakePayload(")==1
assert migrated.count("public record StatePayload(")==1
assert migrated.count("public record BakePayload(")==1
assert "computeIfAbsent(RuntimeData.FACTORY" in migrated
assert "server.getDataStorage().computeIfAbsent(RuntimeData.TYPE)" not in migrated
assert "SavedData.Factory<RuntimeData>" in migrated
assert "class RuntimeData extends SavedData" in migrated
assert "getDataStorage().computeIfAbsent(RuntimeData.TYPE)" not in migrated
assert migrated.count("public static final class RuntimeData extends SavedData")==1

# The original's two CustomPacketPayload definitions must remain unmodified:
# compare entire original prefix through the start of the RuntimeData class,
# not a superficial count of occurrences.
start_original=re.search(
    r"\\bpublic\\s+static\\s+final\\s+class\\s+RuntimeData",original)
start_new=re.search(r"\\bpublic\\s+static\\s+final\\s+class\\s+RuntimeData",migrated)
assert start_original and start_new
original_before=original[:start_original.start()]
new_before=migrated[:start_new.start()]
for marker in ("public record StatePayload(","public record BakePayload("):
    assert marker in original_before and marker in new_before
for packet in ("StatePayload","BakePayload"):
    m=re.search(r"\\bpublic record "+packet+r"\\(",original_before)
    n=re.search(r"\\bpublic record "+packet+r"\\(",new_before)
    assert m and n
    # Compare through the other record or the original runtime-class start;
    # transformation should not touch the original packets or their codecs.
    boundary=lambda source,offset:source.find("\\n    public record BakePayload(",offset) if packet=="StatePayload" else len(source)
    oe=boundary(original_before,m.start())
    ne=boundary(new_before,n.start())
    if oe<0:oe=len(original_before)
    if ne<0:ne=len(new_before)
    assert original_before[m.start():oe]==new_before[n.start():ne], (
        "The original "+packet+" packet changed during SavedData migration")

print("RGB_OWNER_ORIGINAL_RUNTIME_SOURCE_MIGRATION_PASS",
      json.dumps({"original_bytes":len(original),"migrated_bytes":len(migrated),
                  "original_packet_records_intact":2,
                  "original_runtime_class_replaced":1,
                  "public_mod_downloads":0}),flush=True)
