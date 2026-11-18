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
        "url":"https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",
        "upstream":"97a7ab0e25f8806ccb0fa483d5cbe40b181c8756",
        "info_api":"api/src/main/java/mod/chiselsandbits/api/blockinformation/IBlockInformation.java",
        "info_method":"getBlockState",
        "info_class":"mod/chiselsandbits/api/blockinformation/IBlockInformation.class",
    },
    "neoforge1211":{
        "game":"1.21.1",
        "loader":"NeoForge",
        "version":"21.1.32",
        "file":"chisels-and-bits-neoforge-21.1.32.jar",
        "url":"https://mediafilez.forgecdn.net/files/7405/270/chisels-and-bits-neoforge-21.1.32.jar",
        "upstream":"3412262011aebd68996f33275c302e864ba9ee11",
        "info_api":"api/src/main/java/mod/chiselsandbits/api/blockinformation/BlockInformation.java",
        "info_method":"blockState",
        "info_class":"mod/chiselsandbits/api/blockinformation/BlockInformation.class",
    },
}
BASE="https://raw.githubusercontent.com/ChiselsAndBits/Chisels-and-Bits/"
STAT_API="api/src/main/java/mod/chiselsandbits/api/multistate/statistics/IMultiStateObjectStatistics.java"
TILE_API="core/src/main/java/mod/chiselsandbits/block/entities/ChiseledBlockEntity.java"
BLOCKS_API="core/src/main/java/mod/chiselsandbits/registrars/ModBlocks.java"
MUST_INCLUDE_IN_JAR={
    "tile":"mod/chiselsandbits/block/entities/ChiseledBlockEntity.class",
    "statistics":"mod/chiselsandbits/api/multistate/statistics/IMultiStateObjectStatistics.class",
    "blocks":"mod/chiselsandbits/registrars/ModBlocks.class",
}

def get(url):
    assert url.startswith(("https://mediafilez.forgecdn.net/files/",
                           "https://raw.githubusercontent.com/ChiselsAndBits/"))
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
            "bytecode_placements":{
                "info":info_location,"statistics":stats_location,
                "tile":tile_location,"blocks":blocks_location},
            "nested_module_sha256":nested_manifest,
            "real_published_binary_verified":True,
        }),flush=True)
print("RGB_CNB_BOTH_REAL_DEPENDENCY_JARS_VERIFIED",flush=True)
