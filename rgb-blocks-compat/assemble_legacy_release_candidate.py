#!/usr/bin/env python3
"""Build the complete TEST/RELEASE-CANDIDATE handoff for both native legacy ports.

This is NOT a claim that every original player-side 1.3.1 behavior is perfect.
CI gameplay proof is independently recorded at the immutable workflow run URLs.
Only owner's RGB JAR and source are bundled; third-party ecosystem downloads
remain pinned SHA-512 authenticated remote links inside the Modrinth .mrpack.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

ROOT = Path.cwd()
EXPECTED = {
    "neoforge1211": {
        "game": "1.21.1", "loader": "NeoForge", "loader_id": "neoforge",
        "source": "port-work/mc1211-neoforge", "min_java": 21,
        "modmeta": "META-INF/neoforge.mods.toml",
        "pack": "RGBBlocks-1.3.1-MC1.21.1-neoforge-complete-ecosystem.mrpack",
        "lock": "RGBBlocks-1.3.1-MC1.21.1-neoforge-complete-ecosystem-lock.json",
        "shader_run": 44029914251,
        "dimension_run": 44033632613,
        "integrated_run": 44033632635,
        "world_restart_run": 44033632688,
    },
    "forge1201": {
        "game": "1.20.1", "loader": "Forge", "loader_id": "forge",
        "source": "port-work/mc1201-forge", "min_java": 17,
        "modmeta": "META-INF/mods.toml",
        "pack": "RGBBlocks-1.3.1-MC1.20.1-forge-complete-ecosystem.mrpack",
        "lock": "RGBBlocks-1.3.1-MC1.20.1-forge-complete-ecosystem-lock.json",
        "shader_run": 44029919077,
        "dimension_run": 44032050646,
        "integrated_run": 44032721736,
        "world_restart_run": 43950863449,
    },
}
GITHUB = "https://github.com/sangkukzoa-ctrl/assets"
OUTPUT = Path("release-stage")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def put_zip_archive(source, dest):
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for p in sorted((source / "src").rglob("*")):
            if p.is_file():
                z.write(p, str(p.relative_to(source)))
        for name in ("build.gradle", "settings.gradle", "gradle.properties", "gradlew", "gradlew.bat"):
            p = source / name
            assert p.is_file(), f"Missing full build source: {p}"
            z.write(p, name)
        for p in sorted((source / "gradle").rglob("*")):
            if p.is_file():
                z.write(p, str(p.relative_to(source)))
        assert any(n.endswith("gradle/wrapper/gradle-wrapper.jar") for n in z.namelist()), (
            "Full source ZIP has no Gradle wrapper JAR, cannot standalone build"
        )

def build_one(target):
    c = EXPECTED[target]
    source = Path(c["source"])
    jars = [p for p in (source / "build/libs").glob("*.jar")
            if "-sources" not in p.name and "-dev" not in p.name]
    assert len(jars) == 1, ("Expected ONE native production JAR", [str(p) for p in jars])
    jar = jars[0]
    corrected = (source / "src/main/java/com/rgbblocks/client/lighting/RGBLightPersistence.java").read_text()
    assert "saveCurrentBlocking();\n                  RGBRealLightEngine.prepareForPersistenceDimensionSwitch();" in corrected, (
        "RELEASE BLOCKER: departing-dimension saved RGB+C&B lightmap fix is missing"
    )
    with zipfile.ZipFile(jar) as z:
        assert z.testzip() is None, "Damaged production JAR"
        names = z.namelist()
        asset_count = sum(n.startswith("assets/rgbblocks/blockstates/") and n.endswith(".json") for n in names)
        model_count = sum(n.startswith("assets/rgbblocks/models/block/") and n.endswith(".json") for n in names)
        item_count = sum(n.startswith("assets/rgbblocks/models/item/") and n.endswith(".json") for n in names)
        palette = json.loads(z.read("assets/rgbblocks/palette.json"))
        assert len(palette) == 16687, len(palette)
        assert asset_count == model_count == 50061, (asset_count, model_count)
        assert item_count >= 50063, item_count
        assert c["modmeta"] in names, c["modmeta"]
        assert "com/rgbblocks/client/lighting/RGBLightPersistence.class" in names
        assert not any(n.startswith("com/rgbblocks/ci/") for n in names), (
            "RELEASE BLOCKER: gameplay diagnostic/test-only classes leaked into distributable JAR"
        )
    out = OUTPUT / target
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    prefix = f"RGBBlocks-1.3.1-MC{c['game']}-{c['loader']}"
    real_jar = out / (prefix + ".jar")
    shutil.copy2(jar, real_jar)
    fullsrc = out / (prefix + "-FULL-SOURCE.zip")
    put_zip_archive(source, fullsrc)
    packaged = Path("rgb-blocks-compat/packages") / c["pack"]
    lock_path = Path("rgb-blocks-compat/packages") / c["lock"]
    assert packaged.is_file() and lock_path.is_file(), (
        "RELEASE BLOCKER: matching pinned complete C&B/shader/renderer ecosystem not created",
        packaged, lock_path
    )
    with zipfile.ZipFile(packaged) as pack:
        assert pack.testzip() is None
        index = json.loads(pack.read("modrinth.index.json"))
        assert index["dependencies"]["minecraft"] == c["game"]
        assert c["loader_id"] in index["dependencies"]
        assert len(index["files"]) == 4, "C&B, shader and two rendering mods must be pinned"
        assert all(set(f["hashes"]) >= {"sha512", "sha1"} for f in index["files"])
        own_mods = [n for n in pack.namelist() if n.startswith("overrides/mods/") and n.endswith(".jar")]
        assert len(own_mods) == 1
        assert hashlib.sha256(pack.read(own_mods[0])).hexdigest() == sha(jar), (
            "RELEASE BLOCKER: ecosystem MRPACK ships a different RGB JAR than standalone file"
        )
        assert not any(n.startswith("overrides/mods/") and n.endswith(".jar")
                       and n not in own_mods for n in pack.namelist())
    shutil.copy2(packaged, out / packaged.name)
    shutil.copy2(lock_path, out / lock_path.name)
    static_parity = Path("audit-output") / f"parity-{target}.json"
    assert static_parity.is_file(), "Original 1.3.1 full palette / models / textures parity not verified"
    parity = json.loads(static_parity.read_text())
    assert parity["rgb_color_count"] == 16687
    assert parity["registered_rgb_block_model_pairs"] == 50061
    assert parity["glass_render_type_parity"]
    assert parity["original_png_language_palette_byte_identical"] > 33377
    assert parity["ported_jar_sha256"] == sha(jar), "Parity audit verified a different build JAR"
    shutil.copy2(static_parity, out / ("parity-" + target + ".json"))
    proof = {key.removesuffix("_run"): GITHUB + "/actions/runs/" + str(value)
             for key, value in c.items() if key.endswith("_run")}
    manifest = {
        "mod": "RGB Blocks", "upstream": "1.3.1",
        "target": target, "minecraft": c["game"], "loader": c["loader"],
        "min_java": c["min_java"], "variant": "native build / test candidate",
        "jar_registry_colors": len(palette),
        "jar_blockstate_count": asset_count, "jar_blockmodel_count": model_count,
        "jar_itemmodels": item_count,
        "original_assets_byte_identical": True,
        "cnb_shaders": "Pinned third-party download pointers with SHA-512, not repackaged",
        "no_ci_diagnostics_in_release_jar": True,
        "verified_prior_real_gameplay_runs": proof,
        "release_files_sha256": {
            p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()
        },
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
    readme = f"""RGB Blocks 1.3.1 — Minecraft {c['game']} {c['loader']} test candidate

FILES
{real_jar.name}
  Native mod JAR; place in the correct loader's mods/ directory.
{packaged.name}
  Complete Modrinth/PrismLauncher importable profile: RGB JAR is embedded
  plus official SHA-512-pinned creators' Chisels & Bits, renderer, shader loader
  and Complementary Reimagined r5.9.3 download pointers.
{fullsrc.name}
  Full editable Java source, assets, Gradle wrapper, Windows + Linux scripts.
{lock_path.name}
  Mod and shader download lock and checksums.
MANIFEST.json / SHA256SUMS.txt / parity-{target}.json
  Build metadata, checksum table, evidence of original palette/resource parity.

REQUIREMENTS
Minecraft {c['game']} / {c['loader']}, Java {c['min_java']}.
Do NOT install the other loader's JAR. Import the .mrpack as a separate
instance; it already contains this RGB Blocks JAR.
Client-only shader/renderer files must never be copied to dedicated server mods/.
Complementary Reimagined is installed but not automatically enabled.
With shaders, enable in Minecraft Video Settings as appropriate.

TESTED ACTUAL GAMEPLAY
Both independent native clients, 16^3 4096-bit mixed C&B GLOW/NORMAL/GLASS,
RED/GREEN/BLUE RGB, MANUAL and /rgb bake, peer synchronization, snapshots,
fresh login and real server JVM restart, Nether/Overworld saved lightmaps,
integrated singleplayer and Complementary shader active:
"""
    readme += "\n".join(f"{key}: {url}" for key, url in proof.items())
    readme += "\n\nThese are developer-verified native backport test candidates; avoid\n"
    readme += "calling them original 26.1.2 builds or formal upstream stable releases.\n"
    (out / "README.txt").write_text(readme, encoding="utf-8")
    sums = "\n".join(f"{sha(p)}  {p.name}" for p in sorted(out.iterdir()) if p.is_file())
    (out / "SHA256SUMS.txt").write_text(sums + "\n")
    print("RELEASE_STAGE_PASS", target, "jar_bytes", real_jar.stat().st_size,
          "source_zip_bytes", fullsrc.stat().st_size,
          "mrpack_bytes", packaged.stat().st_size,
          "assets", asset_count, "colors", len(palette), "files", len(list(out.iterdir())), flush=True)

def master_bundle(paths):
    root = Path("RGBBlocks-1.3.1-Legacy-Forge1201-NeoForge1211-TEST-CANDIDATES")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    entries = {}
    for target, p in zip(EXPECTED, paths):
        src = Path(p)
        assert (src / "MANIFEST.json").is_file(), ("Missing staged candidate", src)
        info = json.loads((src / "MANIFEST.json").read_text())
        assert info["target"] == target, (target, info["target"])
        stage = root / target
        shutil.copytree(src, stage)
        for filename, checksum in info["release_files_sha256"].items():
            assert sha(stage / filename) == checksum, (target, filename)
        entries[target] = {"minecraft": info["minecraft"], "loader": info["loader"],
                           "files": info["release_files_sha256"],
                           "proof": info["verified_prior_real_gameplay_runs"]}
    root_manifest = {"title": "RGB Blocks 1.3.1 native legacy ports",
                     "status": "developer-verified test candidates",
                     "ports": entries}
    (root / "BUNDLE_MANIFEST.json").write_text(json.dumps(root_manifest,indent=2,ensure_ascii=False))
    (root / "START_HERE.txt").write_text(
        "RGB Blocks 1.3.1 legacy ports — each folder is an INDEPENDENT build.\n"
        "forge1201/ is Minecraft 1.20.1 Forge (Java 17).\n"
        "neoforge1211/ is Minecraft 1.21.1 NeoForge (Java 21).\n"
        "Import the correct .mrpack or install the single matching RGB .jar.\n"
        "Each contains a FULL-SOURCE ZIP, tests/provenance and SHA256 sums.\n"
        "Do not mix Minecraft versions or Forge/NeoForge loader families.\n",encoding="utf-8")
    dest = Path(str(root) + ".zip")
    with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                z.write(p,str(p.relative_to(root.parent)))
        assert z.testzip() is None
    assert dest.stat().st_size > 1000000
    print("RELEASE_BUNDLE_PASS", dest, dest.stat().st_size,
          "SHA256", sha(dest), "contained_files", len(list(root.rglob("*"))),flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=[*EXPECTED, "bundle"])
    parser.add_argument("inputs", nargs="*")
    args = parser.parse_args()
    if args.target == "bundle":
        assert len(args.inputs) == 2, "Expect input directories: neoforge1211 and forge1201"
        master_bundle(args.inputs)
    else:
        assert not args.inputs
        build_one(args.target)
