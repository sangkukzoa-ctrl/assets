# RGB Blocks 1.3.1 — native legacy-port release-candidate test report
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
