# RGB Blocks 1.3.1 — native legacy-port release-candidate test report

## Hard dependency independence — tested with ONLY RGB Blocks installed

**PASS on BOTH native loaders, without any optional mod in either client or server.** The generated Forge `mods.toml` and NeoForge `neoforge.mods.toml` list only the game and native loader as mandatory. C&B is optional; its block entity inspection is reflection-based with optional Mixin targets. Sodium/Iris and Embeddium/Oculus are also optional renderer/shader integration, not required to start RGB Blocks.

- [Actual RGB-only dedicated server acceptance #44045407305](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44045407305): Forge 1.20.1 and NeoForge 1.21.1 with exactly one mod JAR, both boot, register 16,687 RGB colors, place all normal/glow/glass variants, persist world/manual mode, restart same saved world. All actual game tests PASS; no C&B loaded, no fatal.
- [Actual RGB-only GUI client AND server #44045724254](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44045724254): BOTH loader jobs SUCCESS. Each actual Minecraft GUI client and server has only RGB Blocks JAR; **no C&B, Sodium, Embeddium, Iris, Oculus or Complementary**. Both joined, loaded 50,061 RGB registrations/models, rendered in-game screenshot, emitted actual RGB source and adjacent colored light, zero resource-model omissions and no fatal class crashes. Forge direct source [15,6,8] and neighbor [238,85,119].
- The `complete-ecosystem.mrpack` installs the **chosen optional compatibility toolchain** as a convenience pack; its pack-level `required` entries are not hard dependencies in the mod's own metadata. The **standalone JAR alone** runs without those add-ons.
- [Independent compatibility contract](./STANDALONE_AND_OPTIONAL_ECOSYSTEM.md) documents exact source and proof.


### 2026-11-17 phase 13s — BOTH native distribution archives built and verified

**FULL NATIVE LEGACY TEST-CANDIDATE DISTRIBUTION SUCCESS** [workflow #44037516139](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44037516139), commit `0597fc55079878b7465df35b251ad6b9eb8c1a4f`, all THREE jobs SUCCESS: build NeoForge native, build Forge native, independently assemble and SHA256-verify the two-version all-in-one. **Download EXACT artifacts**:
- **BOTH loaders all-in-one ZIP**: [GitHub artifact #14308835721](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44037516139/artifacts/14308835721). Internally contains `RGBBlocks-1.3.1-Legacy-Forge1201-NeoForge1211-TEST-CANDIDATES.zip`, **72,782,166 bytes SHA256 `09ea9ddecda5e268632a9ef644cb4f831ed0857138e728e15dc660f8c5cb4fa1`**, with separate `neoforge1211/` and `forge1201/` and 20 files, checked manifests and all sources/JARs.
- **NeoForge 1.21.1** complete isolated [artifact #14307464634](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44037516139/artifacts/14307464634): native original 1.3.1 JAR **70,757,379 bytes**, FULL-SOURCE Gradle-wrapper ZIP **74,914,143 bytes**, pinned C&B+Sodium+Iris+Complementary .mrpack **17,232,634 bytes**.
- **Forge 1.20.1** complete isolated [artifact #14308367210](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44037516139/artifacts/14308367210): native original 1.3.1 JAR **69,832,093 bytes**, FULL-SOURCE ZIP **74,919,088 bytes**, pinned C&B+Embeddium+Oculus+Complementary .mrpack **9,700,217 bytes**.
- Release stage scripts [`ea2e7a52`](https://github.com/sangkukzoa-ctrl/assets/commit/ea2e7a52d049faaeffd11baacede5282707d536a) / versioned zip fix [`6da97ed4`](https://github.com/sangkukzoa-ctrl/assets/commit/6da97ed473058953911e22076c7ca3ee5498a7ef). Bundling workflow [`0597fc55`](https://github.com/sangkukzoa-ctrl/assets/commit/0597fc55079878b7465df35b251ad6b9eb8c1a4f).
- These are **UNINSTRUMENTED production JARs**; packager verifies `com/rgbblocks/ci/` absent, actual generated Java contains departing-dimension RGBLightPersistence fix, 16,687 exact palette and 50,061 block state+model entries; static parity confirms **33,380 PNG/lang/palette files byte-identical** with upstream source. Source ZIPs include actual complete Java/assets and Windows/Linux Gradle wrapper. Both separate MRPACKs embed SHA256-identical own RGB JAR and use official SHA512-pinned remote links for C&B, renderer, shader loader and Complementary, no third-party JAR repacking. Source code and third-party lock, per-loader SHA256SUMS, manifests, instructions are included.
- NeoForge candidate job evidence `RELEASE_STAGE_PASS neoforge1211`, actual C&B21.1.32 server smoke PASS; Forge `RELEASE_STAGE_PASS forge1201`, actual C&B20.1.20 server smoke PASS; cross-loader bundle `RELEASE_BUNDLE_PASS`. One separate [complete test report](https://github.com/sangkukzoa-ctrl/assets/blob/rgb-blocks-legacy-compat-audit/rgb-blocks-compat/RELEASE_TEST_REPORT_2026-11-17.md) records independent two-player, mixed 4096-bit microbit, MANUAL bake, server restart, Nether/Overworld saved snapshots, integrated singleplayer, and active Complementary shader ON real game proof. All these independently passed as of 2026-11-17.
- Repo `sangkukzoa-ctrl/assets` branch `rgb-blocks-legacy-compat-audit`. Distribution ZIP is a candidate ready for owner's install/release staging, not a fabricated sandbox link and not a claimed public Modrinth 1.20.1/1.21.1 upload. **Next steps only if requested:** Windows hand-install acceptance, version naming, upload to hosting; don't silently rewrite/replace proven native binaries. Original requirements broadly met including JAR+full sources and ecosystem bundle for BOTH supported loaders.

*2026-11-17, Minecraft 1.20.1 Forge / Minecraft 1.21.1 NeoForge*

## Scope / compatibility contract
- **Exactly 16,687 original palette RGB colors**, each as Normal, Glow and Glass; **50,061 static block states**, 50,061 block model entries, 50,063+ item models, original PNG/language/palette byte-identical. Original 1.3.1 lighting implementation preserved across API migration except the diagnosed disappearing dimensional lightmap save fix.
- **Minecraft 1.21.1: NeoForge 21.1.265, Java 21; Chisels & Bits 21.1.32; Sodium 0.6.13; Iris 1.8.12; Complementary Reimagined r5.9.3**.
- **Minecraft 1.20.1: Forge 47.4.28, Java 17; Chisels & Bits 20.1.20; Embeddium 0.3.31; Oculus 1.8.0; Complementary Reimagined r5.9.3**.
- All tests below use actual target-loaders, production client GUI and server JVM, except code probes temporarily injected in separate CI-only builds (never included in release candidate JAR).

## Real game verification with immutable GitHub Actions records

| Test class | NeoForge 1.21.1 | Forge 1.20.1 | Evidence |
|---|---|---|---|
| 2 simultaneous production game clients and real dedicated server | [PASS #43931436154](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43931436154) | [PASS #43639004500](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43639004500) | Client/server/FML joins, RGB source and adjacent per-channel updates, RED→GREEN→AIR |
| MANUAL freeze and /rgb bake | [PASS #43943898365](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43943898365) | [PASS #43639004500](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43639004500) | Two clients observe old RED until bake then GREEN |
| 4095 red RGB C&B microbits and 4096-bit mixed 5-material sculpture | [PASS #43948616600](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43948616600) | [PASS #43947596105](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43947596105) | C&B real getStateCounts(): [3071, 256, 256, 256, 256] plus 1 air; red, green, blue glow, normal green and green glass |
| Real client logout/restart same directory, chunk unload/return | [PASS #43943898365](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43943898365) | [PASS #43639004500](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43639004500) | World UUID and GREEN RGB + red C&B retained, x256 real chunk removal and return |
| True server JVM shutdown/restart SAME WORLD, no fixture re-sculpt | [PASS #44033632688](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44033632688) | [PASS #43950863449](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43950863449) | Exact five-material saved voxel counts and GREEN source, same world ID and client relog |
| True Overworld→Nether→Overworld→Nether RGB color and dimensional snapshots | [PASS #44033632613](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44033632613) | [PASS #44032050646](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44032050646) | Two separate .rgl.gz files; Nether BLUE / Overworld GREEN and red + mixed C&B sources persist |
| Real singleplayer IntegratedServer, opening saved dedicated world | [PASS #44033632635](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44033632635) | [PASS #44032721736](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44032721736) | Actual Quick Play --join-world, existing .mca/level.dat, same RGB world ID + mix + client screenshot |
| Shader ON with two real clients; original and mixed glass C&B scene | [PASS #44029914251](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44029914251) | [PASS #44029919077](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44029919077) | Iris/Oculus shader_active TRUE; real C&B colored emission probes and real screenshots; no missing models |
| Native production build, byte-for-byte original safe assets and full source ZIP | [PASS #44032194411](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44032194411) | [PASS #44032202165](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44032202165) | Gradle 8.10.2 / 8.8, parity 16,687 colors / 50,061 models, standalone wrapper, real server tests |

### Corrected original port defect
Initial dimensional tests failed after successful Nether BLUE and Overworld GREEN lighting because **Nether client section/cache was replaced without saving before dimension switch**. The actual common production input `recovered/fabric/com/rgbblocks/client/lighting/RGBLightPersistence.java` was changed at [1594f37d](https://github.com/sangkukzoa-ctrl/assets/commit/1594f37ddba8d5d6ba738b5c5ea90802bad1c575) to call `saveCurrentBlocking()` prior to dimension cache clearing. Both native builder scripts now assert this exact fix is in generated Java source. Real separate saved Nether+Overworld snapshots subsequently **passed** on both loaders.

### Distribution composition
The all-in-one test-candidate ZIP contains two completely independent directories `neoforge1211/` and `forge1201/`; each has:
- Native loader-specific RGB Blocks JAR; not a Fabric launcher artifact and not a CI-instrumented JAR.
- Full Java source+assets ZIP with Gradle wrapper, Windows and Unix launch scripts.
- Importable .mrpack profile embedding the exact same RGB JAR plus external creator download pointers for C&B, renderer, shader loader and Complementary, SHA-512 verified.
- Parity report, MANIFEST.json, SHA256SUMS.txt and installation instructions.

Build/packaging workflow: [RGBBlocks both native legacy release candidate](https://github.com/sangkukzoa-ctrl/assets/actions/workflows/rgb-blocks-legacy-two-native-release-candidates.yml).

### Scope of verification
An explicit PASS means the actual scripted assertions passed with real Minecraft client/server, not a guarantee of zero edge-case issues in every unrelated mod stack. Shader tests verified real shader activation, colored C&B source values, no missing RGB models and screenshot file generation. This is not a manual pixel-by-pixel visual acceptance of transparency in every scene. Manual long-form gameplay beyond scripted cases can be performed before labeling these as stable releases.

### Release ownership
Third-party mods and shaders are not rehosted in the candidate ZIP: .mrpack's download links point to official creators' distribution URLs with verified SHA-512. Original RGB source/art belongs to its original mod developer. A successful build alone is not substituted for the above real-game acceptance tests.
