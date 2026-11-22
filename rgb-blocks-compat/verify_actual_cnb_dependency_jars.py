#!/usr/bin/env python3
"""Verify the EXACT native Chisels & Bits jars used by both REAL-game tests.

These jars are dependencies (NOT the original RGB Blocks author JAR).
Checks actual published .class method names and official revision-pinned
upstream source interfaces, not guessed/mocked C&B APIs.
Does not require owner's unpublished 1.3.1 source package.
"""
import hashlib
import io
import json
import urllib.request
import zipfile

VERSIONS={
    "forge1201":{
        "game":"1.20.1",
        "loader":"Forge",
        "version":"20.1.20",
        "file":"chisels-and-bits-forge-20.1.20.jar",
        "expected_sha256":"682dab9c016b12b3da49ed4df037cc9483917cd50ec76b2bd6da4bfbf1237a2b",
        "url":"https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",
        "upstream":"97a7ab0e25f8806ccb0fa483d5cbe40b181c8756",
        "info_api":"api/src/main/java/mod/chiselsandbits/api/blockinformation/IBlockInformation.java",
        "scena_baseline_tag":"1.0.103",
        "info_method":"getBlockState",
        "info_class":"mod/chiselsandbits/api/blockinformation/IBlockInformation.class",
    },
    "neoforge1211":{
        "game":"1.21.1",
        "loader":"NeoForge",
        "version":"21.1.32",
        "file":"chisels-and-bits-neoforge-21.1.32.jar",
        "expected_sha256":"982f4523abc12c5de1e84410f4e0ee29e134e854272c3bdb2c8fe24841a21265",
        "nested_sha256":{
          "META-INF/jarjar/chisels-and-bits-api-21.1.32.jar":"df68e9f53db006a18d999e4a39b543d3d90fe0962bd6d7f975ca5a973f683bf8",
          "META-INF/jarjar/chisels-and-bits-core-21.1.32.jar":"1ce714fb438ea624bc04458097f3c80a1651d2e8b5d94ae34f31f77080e0aa8c"},
        "url":"https://mediafilez.forgecdn.net/files/7405/270/chisels-and-bits-neoforge-21.1.32.jar",
        "upstream":"3412262011aebd68996f33275c302e864ba9ee11",
        "info_api":"api/src/main/java/mod/chiselsandbits/api/blockinformation/BlockInformation.java",
        "scena_baseline_tag":"21.1.27",
        "info_method":"blockState",
        "info_class":"mod/chiselsandbits/api/blockinformation/BlockInformation.class",
    },
}
BASE="https://raw.githubusercontent.com/ChiselsAndBits/Chisels-and-Bits/"
STAT_API="api/src/main/java/mod/chiselsandbits/api/multistate/statistics/IMultiStateObjectStatistics.java"
TILE_API="core/src/main/java/mod/chiselsandbits/block/entities/ChiseledBlockEntity.java"
BLOCKS_API="core/src/main/java/mod/chiselsandbits/registrars/ModBlocks.java"
MODEL_EXECUTOR_API="core/src/main/java/mod/chiselsandbits/client/model/data/ChiseledBlockModelDataExecutor.java"
MODEL_PROPERTIES_API="core/src/main/java/mod/chiselsandbits/registrars/ModModelProperties.java"
SCENA_BASE="https://raw.githubusercontent.com/Communi-Suggestu/Scena/"
SCENA_MODEL_DATA_API="core/src/main/java/com/communi/suggestu/scena/core/client/models/data/IBlockModelData.java"
SCENA_MODEL_KEY_API="core/src/main/java/com/communi/suggestu/scena/core/client/models/data/IModelDataKey.java"
MUST_INCLUDE_IN_JAR={
    "tile":"mod/chiselsandbits/block/entities/ChiseledBlockEntity.class",
    "statistics":"mod/chiselsandbits/api/multistate/statistics/IMultiStateObjectStatistics.class",
    "blocks":"mod/chiselsandbits/registrars/ModBlocks.class",
    "model_executor":"mod/chiselsandbits/client/model/data/ChiseledBlockModelDataExecutor.class",
    "model_properties":"mod/chiselsandbits/registrars/ModModelProperties.class",
}

def get(url):
    assert url.startswith(("https://mediafilez.forgecdn.net/files/",
                           "https://raw.githubusercontent.com/ChiselsAndBits/",
                           "https://raw.githubusercontent.com/Communi-Suggestu/Scena/"))
    request=urllib.request.Request(url,headers={
        "User-Agent":"RGB-Blocks-1.3.1-native-dependency-contract-check/1.0"})
    with urllib.request.urlopen(request,timeout=150) as response:
        return response.read()

def upstream(config,relative):
    content=get(BASE+config["upstream"]+"/"+relative)
    return content.decode("utf-8")

for target,config in VERSIONS.items():
    source_info=upstream(config,config["info_api"])
    source_stat=upstream(config,STAT_API)
    source_tile=upstream(config,TILE_API)
    source_mods=upstream(config,BLOCKS_API)
    source_model_executor=upstream(config,MODEL_EXECUTOR_API)
    source_properties=upstream(config,MODEL_PROPERTIES_API)
    # Verify the ACTUAL Scena API contract behind RGB's reflective mesh
    # oracle using upstream tags pinned to the loaders' dependency baselines.
    # This is independent from the locally mocked Java fixture.
    scena=config["scena_baseline_tag"]
    scena_data=get(SCENA_BASE+scena+"/"+SCENA_MODEL_DATA_API).decode("utf-8")
    scena_key=get(SCENA_BASE+scena+"/"+SCENA_MODEL_KEY_API).decode("utf-8")
    assert "interface IBlockModelData" in scena_data
    assert "<T> T getData(IModelDataKey<T> prop)" in scena_data, (
        "Scena model-data getter signature diverged",target,scena)
    assert "interface IModelDataKey<T>" in scena_key
    assert "public static IModelDataKey<Map<RenderType, BakedModel>> KNOWN_LAYER_MODEL_PROPERTY" in source_properties, (
        "Native C&B KNOWN_LAYER_MODEL_PROPERTY type/visibility changed",target)
    assert 'KNOWN_LAYER_MODEL_PROPERTY, renderTypedModels' in source_model_executor, (
        "C&B native async model no longer publishes a known-layer BakedModel Map",target)
    assert "getBlockModelData()" in source_tile, (
        "C&B native tile no longer exposes reflective render-layer data",target)
    # Both actual shipped C&B versions dispatch native model baking to
    # CompletableFuture, then publish tile model data only on completion.
    # updateModelData() returning from RGB's reflection is NOT a quad-ready
    # result. A bounded retry when quads remain EMPTY is required.
    for asynchronous_stage in (
        "CompletableFuture.supplyAsync(",
        ".thenAcceptAsync(tileEntity::setModelData, recalculationService)",
        ".thenRunAsync(onCompleteCallback, recalculationService)",
        "requestModelDataRefresh(tileEntity)",
    ):
        assert asynchronous_stage in source_model_executor, (
            "Published C&B upstream async model publication changed",
            target,asynchronous_stage)
    if target=="forge1201":
        assert "interface IBlockInformation" in source_info
        assert "BlockState getBlockState()" in source_info
        assert "record BlockInformation(" not in source_info
    else:
        assert "record BlockInformation(BlockState blockState" in source_info
        assert "BlockState getBlockState()" not in source_info
    assert "getStateCounts()" in source_stat
    assert "getStatistics()" in source_tile
    assert "void updateModelData()" in source_tile
    assert 'register("chiseled"' in source_mods or '"chiseled",' in source_mods
    body=get(config["url"])
    digest=hashlib.sha256(body).hexdigest()
    assert digest==config["expected_sha256"],(
        "Changed C&B published binary; native RGB compatibility test would no longer be pinned",
        target,digest,config["expected_sha256"])
    assert len(body)>250000,("Incomplete C&B JAR",target,len(body))
    assert zipfile.is_zipfile(io.BytesIO(body)),("Invalid C&B published JAR",target)
    with zipfile.ZipFile(io.BytesIO(body)) as jar:
        root_names=set(jar.namelist())
        modules={"outer":{name:jar.read(name)
                          for name in root_names if name.endswith(".class")}}
        nested_manifest={}
        nested_jars=sorted(
            name for name in root_names if
            name.startswith("META-INF/jarjar/chisels-and-bits-") and name.endswith(".jar"))
        if target=="neoforge1211":
            expected={
                "META-INF/jarjar/chisels-and-bits-api-21.1.32.jar",
                "META-INF/jarjar/chisels-and-bits-core-21.1.32.jar",
            }
            assert expected.issubset(set(nested_jars)), (
                "Published 21.1.32 NeoForge JAR lacks embedded API and core",
                nested_jars)
            assert "META-INF/jarjar/metadata.json" in root_names, (
                "NeoForge nested modules lack JarJar metadata")
            jarjar_metadata=json.loads(jar.read("META-INF/jarjar/metadata.json"))
            assert "jars" in jarjar_metadata and len(jarjar_metadata["jars"])>=2
        else:
            assert not nested_jars, (
                "20.1.20 Forge JAR changed from normal direct-class package",
                nested_jars)
        for entry in nested_jars:
            if "-api-" not in entry and "-core-" not in entry:
                continue
            inner=jar.read(entry)
            assert zipfile.is_zipfile(io.BytesIO(inner)),(
                "Published nested C&B module is not a ZIP",target,entry)
            nested_manifest[entry]=hashlib.sha256(inner).hexdigest()
            with zipfile.ZipFile(io.BytesIO(inner)) as mod:
                modules[entry]={name:mod.read(name) for name in mod.namelist()
                                if name.endswith(".class")}
        for name,wanted in config.get("nested_sha256",{}).items():
            assert nested_manifest.get(name)==wanted,(
                "NeoForge nested C&B API/Core module bytes changed",
                name,nested_manifest.get(name),wanted)
        def find_class(entry):
            found=[(module,files[entry]) for module,files in modules.items()
                   if entry in files]
            assert len(found)==1, (
                "C&B class missing/duplicate across actual published modules",
                target,entry,
                [key for key,value in modules.items() if entry in value],
                {key:len(value) for key,value in modules.items()})
            return found[0]
        for label,entry in MUST_INCLUDE_IN_JAR.items():
            find_class(entry)
        info_location,info_class=find_class(config["info_class"])
        tile_location,tile_class=find_class(MUST_INCLUDE_IN_JAR["tile"])
        stats_location,stats_class=find_class(MUST_INCLUDE_IN_JAR["statistics"])
        blocks_location,blocks_class=find_class(MUST_INCLUDE_IN_JAR["blocks"])
        model_location,model_class=find_class(MUST_INCLUDE_IN_JAR["model_executor"])
        properties_location,properties_class=find_class(MUST_INCLUDE_IN_JAR["model_properties"])
        for bytecode_symbol in (b"KNOWN_LAYER_MODEL_PROPERTY",b"UNKNOWN_LAYER_MODEL_PROPERTY"):
            assert bytecode_symbol in properties_class, (
                "Published C&B model property missing in real bytecode",
                target,bytecode_symbol)
        assert b"getBlockModelData" in tile_class,(
            "Published C&B tile lacks real Scena model-data accessor",target)
        for stage in (b"supplyAsync",b"thenAcceptAsync",b"thenRunAsync",
                      b"requestModelDataRefresh"):
            assert stage in model_class,(
                "Published native C&B bytecode no longer has async model pipeline",
                target,stage)
        assert config["info_method"].encode() in info_class, (
            "Published C&B information accessor differs from source contract",
            target,config["info_method"])
        assert b"getStateCounts" in stats_class,(
            "Published C&B does not expose required statistics map",target)
        assert b"getStatistics" in tile_class and b"updateModelData" in tile_class,(
            "Published C&B does not expose model regeneration or statistics",target)
        assert b"chiseled" in blocks_class,("C&B canonical block ID missing",target)
        print("RGB_CNB_PUBLISHED_DEPENDENCY_CONTRACT_PASS",json.dumps({
            "target":target,"mc":config["game"],"loader":config["loader"],
            "jar":config["file"],"size_bytes":len(body),
            "sha256":digest,"pinned_upstream_commit":config["upstream"],
            "block_registry_id":"chiselsandbits:chiseled",
            "stats":"getStatistics.getStateCounts",
            "material_accessor":config["info_method"],
            "model_regeneration":"updateModelData",
            "model_build_async":"supplyAsync_thenAcceptAsync_thenRunAsync",
            "async_model_jar_bytecode_verified":True,
            "scena_baseline_api_verified":scena,
            "model_data_getter":"IBlockModelData.getData(IModelDataKey)",
            "cnb_model_layer":"KNOWN_LAYER_MODEL_PROPERTY",
            "bytecode_placements":{
                "info":info_location,"statistics":stats_location,
                "tile":tile_location,"blocks":blocks_location,
                "model_executor":model_location,
                "model_properties":properties_location},
            "nested_module_sha256":nested_manifest,
            "real_published_binary_verified":True,
        }),flush=True)
print("RGB_CNB_BOTH_REAL_DEPENDENCY_JARS_VERIFIED",flush=True)
