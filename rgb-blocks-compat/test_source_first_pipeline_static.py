#!/usr/bin/env python3
"""Fast OFFLINE source-first porting contract smoke tests.

This checks source generation logic using tiny synthetic Java and Mixin
samples, not Minecraft runtime. No owner source JAR, CDN or network involved.
"""
import ast, json, re
from pathlib import Path

HERE=Path("rgb-blocks-compat")
fabric=(HERE/"build_mc1211_fabric.py").read_text("utf-8")
forge=(HERE/"build_mc1201_forge.py").read_text("utf-8")
neo=(HERE/"build_mc1211_neoforge.py").read_text("utf-8")
stage=(HERE/"stage_owner_original.py").read_text("utf-8")
test=(HERE/"verify_owner_runtime_migration.py").read_text("utf-8")
for filename,source in (("Fabric",fabric),("Forge",forge),("NeoForge",neo),("stage",stage),("runtime verifier",test)):
    ast.parse(source)
    if "cdn.modrinth.com/data/A48MxLWx" in source:
        raise AssertionError(filename+" still downloads the owner's public RGB JAR")
assert "jpath.unlink()" not in fabric, "Original JAR path should no longer exist"
assert 'config!="rgbblocks.client.mixins.json"' in fabric
assert 'owner_client=RES/"rgbblocks.client.mixins.json"' in forge
assert 'fabric_client_mixin=RES/"rgbblocks.client.mixins.json"' in neo
assert 'owner_client.unlink()' in forge
assert 'fabric_client_mixin.unlink()' in neo
assert "target.read_bytes()==data" in stage
assert "verified_stage_cache(code_only)" in stage
assert "RGB_OWNER_SOURCE_COMPLETE" in stage
for loader,script in (("Fabric",fabric),("Forge",forge),("NeoForge",neo)):
    assert "from clone_owner_resources import clone_resources" in script, (
        loader+" must stage immutable assets with copy-on-write-safe clones")
    assert "clone_resources(" in script

# Execute the production Java SavedData migrator, isolated from its top-level
# filesystem side effects, on a tiny synthetic Java source with ORIGINAL order.
def isolated_transform(source, name):
    definitions=[node for node in ast.parse(source).body
                 if isinstance(node,ast.FunctionDef) and node.name==name]
    assert len(definitions)==1, (name,len(definitions))
    module=ast.Module(body=[definitions[0]],type_ignores=[])
    scope={"re":re}
    exec(compile(module,"production-build-migrator","exec"),scope)
    return scope[name]

transform=isolated_transform(fabric,"pr")
java="""package com.rgbblocks.runtime;
import net.minecraft.world.level.saveddata.SavedDataType;
public final class RGBRuntime {
  static Object state(Object server) { return server.getDataStorage().computeIfAbsent(RuntimeData.TYPE); }
  public record StatePayload(int v) { public String marker(){return "unchanged";} }
  public record BakePayload(int v) { public String marker(){return "unchanged";} }
  public static final class RuntimeData extends SavedData {
    public static final SavedDataType<RuntimeData> TYPE=null;
    public RuntimeData() {}
  }
  private static int clamp(int v,int min,int max){return v;}
}"""
converted=transform(java)
assert "SavedData.Factory<RuntimeData>" in converted
assert 'server.overworld().getDataStorage().computeIfAbsent(RuntimeData.FACTORY, "rgbblocks_runtime")' in converted
assert converted.count("public record StatePayload(")==1
assert converted.count("public record BakePayload(")==1
assert "public String marker(){return \"unchanged\";}" in converted
assert "SavedDataType" not in converted
assert "public static final class RuntimeData extends SavedData" in converted
assert 'client.Sodium06BlockRendererMixin' in neo
assert 'client.Embeddium03BlockRendererMixin' in forge
assert 'client.ForgeCnbLivePacketMixin' in forge

print("RGB_SOURCE_FIRST_OFFLINE_STATIC_PASS",json.dumps({
    "no_RGB_public_JAR_requests":True,
    "real_source_parser_invariant":True,
    "state_and_bake_packet_records_retained":2,
    "native_mixin_sources_merged":True,
    "source_resume_byte_check":True,
    "test_type":"static_not_game"}),flush=True)
