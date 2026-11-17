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
    r"\bpublic\s+static\s+final\s+class\s+RuntimeData",original)
start_new=re.search(r"\bpublic\s+static\s+final\s+class\s+RuntimeData",migrated)
assert start_original and start_new
original_before=original[:start_original.start()]
new_before=migrated[:start_new.start()]
for marker in ("public record StatePayload(","public record BakePayload("):
    assert marker in original_before and marker in new_before
def record_body(source, record):
    """Extract only the original payload definition; exclude class-leading trivia.

    The owner's source and ported source need not use the same whitespace
    before the NEXT Java class, but the actual codec body must be identical.
    """
    found=re.search(r"\bpublic\s+record\s+"+re.escape(record)+r"\s*\(",source)
    if not found:
        raise AssertionError("Missing author-original packet "+record)
    opening=source.find("{",found.end())
    if opening<0:
        raise AssertionError("Malformed packet "+record)
    depth=0
    for cursor in range(opening,len(source)):
        if source[cursor]=="{":
            depth+=1
        elif source[cursor]=="}":
            depth-=1
            if depth==0:
                return source[found.start():cursor+1]
    raise AssertionError("Unbalanced author-original packet "+record)

for packet in ("StatePayload","BakePayload"):
    before=record_body(original_before,packet)
    after=record_body(new_before,packet)
    assert before==after, "The original "+packet+" codec/body changed during SavedData migration"

print("RGB_OWNER_ORIGINAL_RUNTIME_SOURCE_MIGRATION_PASS",
      json.dumps({"original_bytes":len(original),"migrated_bytes":len(migrated),
                  "original_packet_records_intact":2,
                  "original_runtime_class_replaced":1,
                  "public_mod_downloads":0}),flush=True)
