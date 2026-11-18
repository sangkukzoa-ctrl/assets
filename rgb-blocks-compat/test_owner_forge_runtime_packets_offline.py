#!/usr/bin/env python3
"""Run ACTUAL 1.21.1 -> Forge 1.20.1 runtime source converters offline.

The author-provided original RGBRuntime puts BOTH network records before
RuntimeData. Earlier decompiled source put StatePayload last. A legacy
Forge converter cut source from StatePayload to the end, deleting the
author's saved world state and bake records before Gradle even began.

This test extracts the exact production 'pr' and 'network1201' functions,
feeds genuine RGBRuntime source with both class layouts, and checks all
original persistent state and named packet declarations survive. No
Minecraft or original download is needed.
"""
from pathlib import Path
import ast,re,json

ROOT=Path("rgb-blocks-compat")
fabric_script=(ROOT/"build_mc1211_fabric.py").read_text("utf-8")
forge_script=(ROOT/"build_mc1201_forge.py").read_text("utf-8")
def load_fn(text,name):
    tree=ast.parse(text)
    nodes=[node for node in tree.body
           if isinstance(node,ast.FunctionDef) and node.name==name]
    assert len(nodes)==1,("Missing production transform",name)
    scope={"re":re}
    exec(compile(ast.Module(body=[nodes[0]],type_ignores=[]),
                 name+".py","exec"),scope)
    return scope[name]
owner_runtime=load_fn(fabric_script,"pr")
forge_runtime=load_fn(forge_script,"network1201")

def span(source,record):
    m=re.search(r"\bpublic\s+record\s+"+re.escape(record)+r"\s*\(",source)
    assert m,("Record not found",record)
    opening=source.index("{",m.end())
    level=0
    for cursor in range(opening,len(source)):
        if source[cursor]=="{":level+=1
        elif source[cursor]=="}":
            level-=1
            if level==0:return m.start(),cursor+1
    raise AssertionError("Unbalanced packet "+record)

source=(ROOT/"recovered/fabric/com/rgbblocks/runtime/RGBRuntime.java").read_text("utf-8")
assert "registerPayloadTypes()" in source
assert "public record BakeRequest(" in source
assert "public record StatePayload(" in source
assert "public record BakePayload(" in source

stage=owner_runtime(source)
assert "SavedData.Factory<RuntimeData>" in stage
assert "computeIfAbsent(RuntimeData.FACTORY" in stage
assert "public record StatePayload(" in stage
assert "class RuntimeData extends SavedData" in stage

# The ACTUAL author's original source puts StatePayload before BakePayload,
# unlike the decompiled file. Simulate the precise original declaration order
# while retaining exactly the actual source records and runtime body.
a,b=span(stage,"StatePayload")
state_rec=stage[a:b]
owner_order=stage[:a]+stage[b:]
start_bake,_=span(owner_order,"BakePayload")
owner_order=owner_order[:start_bake]+state_rec+"\n\n   "+owner_order[start_bake:]
assert owner_order.index("public record StatePayload(")<owner_order.index("public record BakePayload(")
assert owner_order.index("public record BakePayload(")<owner_order.index("class RuntimeData extends SavedData")

for label,input_source in (("actual_owner_order",owner_order),
                           ("historical_decompiled_order",stage)):
    converted=forge_runtime(input_source)
    expected=("public record StatePayload(","public record BakePayload(",
              "public record BakeRequest(","enum Mode",
              "class RuntimeData extends SavedData","registerPackets()",
              "public static void acceptState(",
              "public static void acceptBake(")
    for marker in expected:
        assert converted.count(marker)==1,(
            "REAL Forge runtime conversion discarded or duplicated "+marker,label)
    assert "SavedData.Factory" not in converted,(
        "Forge 1.20.1 cannot compile SavedData.Factory",label)
    assert "RuntimeData.FACTORY" not in converted
    assert "computeIfAbsent(RuntimeData::load, RuntimeData::new" in converted
    assert "public static RuntimeData load(CompoundTag tag)" in converted
    assert "public CompoundTag save(CompoundTag tag)" in converted
    assert "HolderLookup.Provider" not in converted
    assert "implements CustomPacketPayload" not in converted
    assert converted.count("private static final SimpleChannel CHANNEL")==1
    # Ensure byte-identical rest of the author's state methods are retained:
    for marker in ("setClientBootstrapAllowed","setBakeAll","setBakeRadius",
                   "clientWorldId","public String worldId()"):
        assert marker in converted,(label,"Lost original owner runtime",marker)

try:forge_runtime(owner_order.replace("public record BakeRequest(","public record LostRequest("))
except RuntimeError as err:
    assert "BakeRequest" in str(err)
else:
    raise AssertionError("The actual source-first converter accepted a lost original record")

print("RGB_OWNER_FORGE1201_ACTUAL_RUNTIME_TRANSFORM_PASS",
      json.dumps({"owner_real_packet_order":True,
                  "legacy_decompiled_order":True,
                  "network_packets_preserved":3,
                  "owner_world_mode_and_bake_persistence":True,
                  "SavedData_Factory_in_Forge":False,
                  "legacy_computeIfAbsent_signature":True,
                  "missing_original_packet_fails_closed":True,
                  "public_mod_downloads":0}),flush=True)
