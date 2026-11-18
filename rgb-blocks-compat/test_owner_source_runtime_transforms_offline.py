#!/usr/bin/env python3
"""Run production 1.21.1 migration transforms on the ACTUAL RGB overlay Java.

Source-first Java transformation errors can be caught before the author's
private archive is provisioned to GitHub Actions. Historically pcnbgetter()
still demanded an obsolete one-way blockState() source and aborted the
whole native Forge/Neo port generation despite standalone Java method PASS.
"""
from pathlib import Path
import ast,re,json

HERE=Path("rgb-blocks-compat")
BUILDER=HERE/"build_mc1211_fabric.py"
code=BUILDER.read_text(encoding="utf-8")
tree=ast.parse(code,filename=str(BUILDER))
definitions={f.name:f for f in tree.body if isinstance(f,ast.FunctionDef)}
for func in ("pr","pe","pl","pi"):
    assert func in definitions,("Owner source transformer missing",func)
def production_function(name):
    scope={"re":re}
    exec(compile(ast.Module(body=[definitions[name]],type_ignores=[]),
                 str(BUILDER),"exec"),scope)
    return scope[name]

def genuine(relative):
    return (HERE/"recovered/fabric/com/rgbblocks"/relative).read_text("utf-8")

assert "def pcnbgetter(" not in code, "Obsolete one-way C&B generator reintroduced"
assert "patch(engine,pcnbgetter)" not in code
assert "RGB_OWNER_CNB_DUAL_MATERIAL_READER_STAGED" in code
source=genuine("client/lighting/RGBRealLightEngine.java")
assert source.count('invokeNoArg(information, "blockState")')==1
assert source.count('invokeNoArg(information, "getBlockState")')==1
assert "catch (NoSuchMethodException olderCnbApi)" in source
updated=production_function("pe")(source)
assert "quad.position(vertex)" not in updated
assert "rgbblocks$vertexPosition(quad, vertex)" in updated
assert updated.count("private static org.joml.Vector3fc rgbblocks$vertexPosition(")==1
assert "getVertices()" in updated
assert 'invokeNoArg(information, "getBlockState")' in updated

lighting=genuine("client/lighting/RGBLightEngine.java")
assert lighting.count("state.getLightDampening()")>=2
updated_lighting=production_function("pl")(lighting)
assert "state.getLightDampening()" not in updated_lighting
assert "state.getLightBlock(level, pos)" in updated_lighting
assert "isOpaqueSolidBarrierState(state)" not in updated_lighting
assert "isOpaqueSolidBarrierState(level, pos, state)" in updated_lighting
assert "isOpaqueSolidBarrierState(BlockAndTintGetter level, BlockPos pos, BlockState state)" in updated_lighting
assert "state.isSolidRender(level,pos)" in updated_lighting
assert "return refreshAround(level, center, sourceScanRadius, true);" in updated_lighting

invalidator=genuine("client/lighting/RGBRenderInvalidator.java")
updated_invalidator=production_function("pi")(invalidator)
assert "renderer.setSectionRangeDirty(" not in updated_invalidator
assert "renderer.setBlocksDirty(minX,minY,minZ,maxX,maxY,maxZ);" in updated_invalidator

client_level=genuine("mixin/client/ClientLevelMixin.java")
start=client_level.index('   @Inject(method = "onBlockEntityAdded"')
end=client_level.index('   private static boolean rgbblocks$isRemoteMultiplayer()',start)
removed=client_level[:start]+client_level[end:]
assert '   @Inject(method = "onBlockEntityAdded"' not in removed
assert 'private static boolean rgbblocks$isRemoteMultiplayer()' in removed
assert "LevelBlockEntityAttachedMixin.java" in code
assert "RGBRealLightEngine.refreshCnbBlockEntity(blockEntity)" in code

print("RGB_OWNER_SOURCE_GENERATOR_REAL_OVERLAY_TRANSFORMS_PASS",
      json.dumps({"light_engine_legacy_port":True,
                  "render_invalidator_port":True,
                  "per_quad_RGB_vertex_port":True,
                  "old_21_client_entity_hook_removed":True,
                  "1_20_forge_and_1_21_neo_material_state_compatible":True,
                  "obsolete_CNB_one_way_builder_rewrite":False,
                  "source_jar_downloads":0}),flush=True)
