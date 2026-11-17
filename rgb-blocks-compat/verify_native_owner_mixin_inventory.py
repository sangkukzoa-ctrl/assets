#!/usr/bin/env python3
"""Hard gate: the two native ports use ALL author-original RGB+C&B client Mixins.

The OWNER source has 2 Fabric Mixin files but only ONE original NeoForge
config. Old port builders silently discarded/duplicated client hooks when
they assumed the decompiled JAR layout. Verify actual staged native resources,
not merely another transform applied to a synthetic source string.
"""
from pathlib import Path
import hashlib, json, sys

if len(sys.argv)!=2 or sys.argv[1] not in ("forge1201","neoforge1211"):
    raise SystemExit("usage: verify_native_owner_mixin_inventory.py forge1201|neoforge1211")
target=sys.argv[1]
root=Path("rgb-blocks-compat/owner-source")
work=Path("port-work/mc1201-forge" if target=="forge1201" else "port-work/mc1211-neoforge")
resources=work/"src/main/resources"
code=work/"src/main/java/com/rgbblocks/mixin"
fabric_common=json.loads((root/"fabric/resources/rgbblocks.mixins.json").read_text("utf-8"))
fabric_client=json.loads((root/"fabric/resources/rgbblocks.client.mixins.json").read_text("utf-8"))
neo_native=json.loads((root/"neoforge/resources/rgbblocks.mixins.json").read_text("utf-8"))
assert len(fabric_common["mixins"])==2
assert len(fabric_client["client"])==12
assert neo_native["client"]==fabric_client["client"], (
    "Unexpected original NeoForge/Fabric RGB client hooks discrepancy")
assert not (resources/"rgbblocks.client.mixins.json").exists(), (
    "Fabric-only split client config must be merged, never double-loaded")
mixin_files=list(resources.glob("*mixins*.json"))
assert len(mixin_files)==1, (
    "Native port must have ONE mixin config, got "+str([p.name for p in mixin_files]))
assert mixin_files[0].name=="rgbblocks.mixins.json"
assert not (resources/"fabric.mod.json").exists(), "Fabric loader metadata leaked into native port"
native=json.loads(mixin_files[0].read_text("utf-8"))
assert native["package"]=="com.rgbblocks.mixin"
assert native["compatibilityLevel"]==("JAVA_17" if target=="forge1201" else "JAVA_21")
common=native["mixins"]
client=native["client"]
assert len(common)==len(set(common)) and len(client)==len(set(client))
assert len(set(common+client))==len(common)+len(client), "Mixin class applied twice"
expected_common=set(fabric_common["mixins"])
old_sodium={"client.SodiumChunkBuilderMeshingTaskMixin",
            "client.SodiumMutableQuadViewImplMixin",
            "client.SodiumQuadViewImplAccessorMixin"}
base=set(fabric_client["client"])-old_sodium
if target=="forge1201":
    expected_common.add("ForgeRegistrySnapshotCompressionMixin")
    expected_client=(base-{"client.MinecraftDisconnectMixin"})|{
        "client.LevelBlockEntityAttachedMixin",
        "client.Embeddium03BlockRendererMixin",
        "client.ForgeCnbLivePacketMixin"}
    assert "client.Sodium06BlockRendererMixin" not in client
    assert "client.SodiumChunkBuilderMeshingTaskMixin" not in client
else:
    expected_common=set(neo_native["mixins"])
    expected_client=base|{
        "client.LevelBlockEntityAttachedMixin",
        "client.Sodium06BlockRendererMixin"}
    owner_plugin=(root/"neoforge/com/rgbblocks/mixin/RGBBlocksMixinPlugin.java").read_bytes()
    port_plugin=(code/"RGBBlocksMixinPlugin.java").read_bytes()
    assert owner_plugin==port_plugin, "NeoForge loader plugin no longer matches actual owner source"

assert set(common)==expected_common, {
    "common_missing":sorted(expected_common-set(common)),
    "common_extra":sorted(set(common)-expected_common)}
assert set(client)==expected_client, {
    "client_missing":sorted(expected_client-set(client)),
    "client_extra":sorted(set(client)-expected_client)}
assert len(common)==(3 if target=="forge1201" else 2)
assert len(client)==11
missing=[]
for name in common+client:
    path=code/("/".join(name.split("."))+".java")
    if not path.is_file():missing.append(str(path))
assert not missing,"Registered Mixin Java class files absent: "+str(missing)
print("RGB_OWNER_NATIVE_MIXIN_INVENTORY_PASS",
      json.dumps({"target":target,"owner_original_client_mixins":12,
        "port_common":len(common),"port_client":len(client),
        "original_required_CNB_light_and_mesh_callbacks_retained":True,
        "client_hook_duplicates":0,"native_mixin_configs":1}),flush=True)
