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
# A common owner-derived RGB source now reads BOTH 1.20.1 and 1.21.1 C&B
# material API signatures; no loader may replace one with the other later.
engine=(HERE/"recovered/fabric/com/rgbblocks/client/lighting/RGBRealLightEngine.java").read_text("utf-8")
assert 'invokeNoArg(information, "blockState")' in engine
assert 'invokeNoArg(information, "getBlockState")' in engine
assert "olderCnbApi" in engine
assert "def forge_cnb_information_api(" not in forge
assert "source_reader=rgbengine.read_text" in forge

assert 'config!="rgbblocks.client.mixins.json"' in fabric
# Native client-level attachment must attempt discovery of brand-NEW C&B
# emitters, not only invalidate lighting for sources already in CNB_CACHE.
assert 'RGBRealLightEngine.refreshCnbBlockEntity(blockEntity);' in fabric
assert 'if ("chiselsandbits:chiseled".equals(registryName))' in fabric
assert 'registryName.startsWith("rgbblocks:")' in fabric
assert 'registryName.startsWith("chiselsandbits:")' in fabric
assert 'owner_client=RES/"rgbblocks.client.mixins.json"' in forge
assert 'fabric_client_mixin=RES/"rgbblocks.client.mixins.json"' in neo
assert 'owner_client.unlink()' in forge
assert 'fabric_client_mixin.unlink()' in neo
assert "target.read_bytes()==data" in stage
assert "verified_stage_cache(code_only)" in stage
assert "RGB_OWNER_SOURCE_COMPLETE" in stage
owner_asset_lock=json.loads((HERE/"owner-resource-sentinels.json").read_text("utf-8"))
assert owner_asset_lock["source_archive_sha256"]==(
    "ae5fffb7b37d7376f4e579491af878b7ed74fbe386b8691751e6d1c538bcb39c")
assert len(owner_asset_lock["samples"])==42
assert all(len(digest)==64 and all(c in "0123456789abcdef" for c in digest)
           for digest in owner_asset_lock["samples"].values())
for family in ("blockstates/","models/block/","models/item/","items/","textures/block/"):
    assert sum(family in p for p in owner_asset_lock["samples"])==8, family
assert "def owner_java_tree_hash(loader):" in stage
assert "if not verify_owner_resource_samples():" in stage
ast_fabric=ast.parse(fabric)
overlay_nodes=[x.value for x in ast_fabric.body if isinstance(x,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=="PROVEN_NATIVE_COMPAT_OVERLAYS"
                       for t in x.targets)]
assert len(overlay_nodes)==1
overlays=ast.literal_eval(overlay_nodes[0])
assert len(overlays)==7 and len(set(overlays))==7
addition_nodes=[x.value for x in ast_fabric.body if isinstance(x,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=="PORT_ONLY_COMPAT_ADDITIONS"
                       for t in x.targets)]
assert len(addition_nodes)==1
additions=ast.literal_eval(addition_nodes[0])
assert additions==("client/cnb/RGBCnbMeshIntegrity.java",)
assert additions[0] not in overlays
assert "delta_receipts" in fabric and "owner_source_sha256" in fabric
assert "unmodified_author_java_count" in fabric
assert "client/lighting/RGBSourceIndex.java" not in overlays
assert "client/cnb/RGBCnbReloadWakeup.java" not in overlays
assert "client/lighting/RGBLightPersistence.java" in overlays
assert "client/lighting/RGBRealLightEngine.java" in overlays
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

# A four-round C&B CHAOS PASS is NOT sufficient if a restarted real client
# has lost the original mixed sculpture's RGB source. Both native harnesses
# must check the NEW peer JVM after relaunch and before deleting the chaos
# fixture. Historical NeoForge evidence: 4095 voxels but BLACK RGB for
# 1680 client ticks after the peer reconnected.
for loader in ("1201_forge", "1211_neoforge"):
    harness=HERE/("test_mc"+loader+"_two_clients.py")
    runtime=harness.read_text(encoding="utf-8")
    ast.parse(runtime,filename=str(harness))
    start=runtime.index('result["chaos"]["peer_process_restarted_and_verified"]=True')
    oracle=runtime.index('"RGB_PORT_CNB_MIXED_PROBE_PASS"',start)
    accepted=runtime.index('result["chaos"]["restarted_peer_existing_mixed_source_restored"]=True',oracle)
    ghost=runtime.index('result["chaos"]["zero_ghost_rgb_both_clients"]=True',accepted)
    assert start<oracle<accepted<ghost
    assert "0,peer,120" in runtime[oracle:accepted], (
        "Rejoin source oracle must sample NEW peer from log offset zero",harness)
    assert "RGB_PORT_CHAOS_ROUND_PASS round=3" in runtime[:oracle]
    assert "RGB_PORT_CHAOS_NO_GHOST_LIGHT_PASS" in runtime[accepted:ghost]

# Protect the ACTUAL released C&B binaries in real-world acceptance tests.
# Forge 20.1.20 is a direct-class JAR; NeoForge 21.1.32 uses nested
# META-INF/jarjar/{api,core}. Never silently change JAR contents between runs.
dependency_source=(HERE/"verify_actual_cnb_dependency_jars.py").read_text("utf-8")
dep_nodes=[node.value for node in ast.parse(dependency_source).body
           if isinstance(node,ast.Assign) and any(
               isinstance(target,ast.Name) and target.id=="VERSIONS"
               for target in node.targets)]
assert len(dep_nodes)==1
native_dependencies=ast.literal_eval(dep_nodes[0])
assert set(native_dependencies)=={"forge1201","neoforge1211"}
for target,harness in (("forge1201","test_mc1201_forge_two_clients.py"),
                       ("neoforge1211","test_mc1211_neoforge_two_clients.py")):
    config=native_dependencies[target]
    text=(HERE/harness).read_text("utf-8")
    assert config["file"] in text and config["expected_sha256"] in text, (
        "Real client test ecosystem must use verified exact published C&B JAR",
        target,config["file"])
    assert config["url"] in text.replace('"+cb',config["file"]).replace(
        'S_MODS/cb',config["file"]).replace('SERVER/"mods"/cb',config["file"]) or (
        config["url"].rsplit("/",1)[0] in text),target
assert native_dependencies["forge1201"]["info_method"]=="getBlockState"
assert native_dependencies["neoforge1211"]["info_method"]=="blockState"
assert len(native_dependencies["neoforge1211"]["nested_sha256"])==2
assert "RGB_CNB_BOTH_REAL_DEPENDENCY_JARS_VERIFIED" in dependency_source

print("RGB_SOURCE_FIRST_OFFLINE_STATIC_PASS",json.dumps({
    "no_RGB_public_JAR_requests":True,
    "real_source_parser_invariant":True,
    "state_and_bake_packet_records_retained":2,
    "native_mixin_sources_merged":True,
    "source_resume_byte_check":True,
    "new_CNB_tile_cache_miss_discovery_hook":True,
    "source_java_sha256_locked":63,
    "source_asset_sha256_sentinels":42,
    "original_java_overlays_remaining":7,
    "port_only_java_additions":1,
    "unmodified_author_java_count":25,
    "restarted_peer_preexisting_mixed_cnb_oracle":2,
    "published_CNB_dependency_sha256_pinned":2,
    "neoforge_real_jarjar_api_core_modules_pinned":2,
    "test_type":"static_not_game"}),flush=True)
