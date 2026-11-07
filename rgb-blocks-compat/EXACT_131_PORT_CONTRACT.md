# RGB Blocks 1.3.1 — exact functional port contract
Source of truth: user-uploaded original RGB Blocks 1.3.1 NeoForge/Fabric source archives and publicly released original 1.3.1 artifacts. Target loader selection amended by owner on 2026-11-07.

## Shipping targets (do not substitute loaders)
| Minecraft | Loader | Java | Target output |
|---|---|---|---|
| 1.21.1 | **NeoForge 21.1.265** | 21 | `RGBBlocksmod-MC1.21.1-NeoForge-1.3.1+mc1.21.1.jar` and full Java/asset/Gradle source |
| 1.20.1 | **Forge 47.4.28** | 17 | `RGBBlocksmod-MC1.20.1-Forge-1.3.1+mc1.20.1.jar` and full Java/asset/Gradle source |

Fabric 1.21.1 source is an **intermediate compatibility reference only**, and must not be shipped as the user's requested 1.21.1 release. Original 1.3.1 NeoForge package/class structure is the porting reference.

## Non-negotiable original 1.3.1 behavior on BOTH targets
1. Identical `rgbblocks` registry namespace, all **16,687 original palette colors** and **50,061** RGB normal/glow/glass blocks, block-items, all original creative tabs, two original RGB tools, exact texture and language bytes.
2. Identical model-facing output (blockstates, block/item models; 1.20.1/1.21.1 schemas translated without changing material meaning), including translucent glass and glow light emission.
3. Identical dynamic RGB light algorithm: per-channel colored light propagation, attenuation, occlusion, tri-linear sampling, no unintended albedo replacement, stable fragment/vertex color handling, bootstrap on loading previously unseen multiplayer chunks, invalidation after server sync.
4. Original Chisels & Bits **16×16×16** microblock workflow: RGB sculpting and edits, mixed RGB microbits, micro-emissive source calculation, model cache wakeup, invalidation, persistence, no lost source after world reload. Compatibility must be checked against *real* matching loader build, not merely registered classes.
5. All original RGB runtime controls, commands, persistence and client config: `/rgb auto`, `/rgb manual`, `/rgb bake`, `/rgb get`, `/rgb setbake all`, `/rgb setbake <4..256>`, RGB light mode switch and baker items, world ID, bake dirty scope, RGB client JSON settings, auto/manual update/bake and recovery, save/load across dimensions and restarts.
6. Genuine dedicated and integrated server support, multiple clients and client-server state sync, original safe level chunk unload/disconnect handling.
7. Original renderer/shader interoperability and RGB color presentation: both vanilla renderer and Sodium 0.6.13 + Iris 1.8.12 for 1.21.1 NeoForge, Embeddium 0.3.31 + Oculus 1.8.0 for 1.20.1 Forge, and Complementary Reimagined shader ON/OFF. No class/mixin crash, colored-light proof and actual screenshot/pixel evaluation.
8. Original code organization/classes, retaining implementation logic unless adaptation is required by version APIs. Do not equate reconstructed/decompiled code with user's uploaded source until structure and method-level comparisons are performed.

## Tested dependency candidates
- 1.21.1 NeoForge: Chisels & Bits **21.1.32** (official file 7405270) as baseline. The immediately newer 21.1.33 build has an upstream `IBlockWithWorldlyProperties` startup failure reported against NeoForge, issue #1343; no dependency-skipping or false pass allowed. Verify this 21.1.32 choice in actual game before finalizing.
- 1.21.1 NeoForge: Sodium **0.6.13 NeoForge** and Iris **1.8.12 NeoForge**, shader Complementary Reimagined.
- 1.20.1 Forge: Chisels & Bits **20.1.20**, Embeddium **0.3.31**, Oculus **1.8.0**.

## Acceptance stages — each target independently
- [ ] Native loader Gradle compilation and final playable JAR, full *original-equivalent* source ZIP.
- [ ] Automated byte-exact original palette/PNG/language and registry/model structure parity.
- [ ] Real dedicated server startup, commands, content count, save and reload.
- [ ] Actual game client connects to real server, registry handshake, places/reloads all RGB block kinds and sculpts C&B.
- [ ] Actual positive per-channel RGB light propagation, including C&B microemissive light (not only vanilla luminance).
- [ ] Actual rendering/screenshot color proof in vanilla and performance renderers with Iris/Oculus and Complementary ON/OFF.
- [ ] Two real clients synchronize all changes, automatic/manual/bake, world persistence and reconnect.
- [ ] Compare target with original 1.3.1 behavior and structure (class/method mapping, original source archive inspection).
- [ ] Distributable artifacts and exact versions/hash + complete reproducible Gradle workflows.
Only mark a target **release ready** when every relevant check is PASS.

## Verified source/work history
The earlier 1.21.1 **Fabric** candidate built, joined multiplayer, and exposed defects in initial RGB propagation. This is relevant diagnostic/reference code but is not the requested final NeoForge deliverable.
The earlier 1.20.1 **Forge** candidate built and passed server command/palette/world persistence, but complete in-world RGB color/C&B+shader parity has not been proved.
Native 1.21.1 NeoForge builder: `rgb-blocks-compat/build_mc1211_neoforge.py`.
Native build workflow: `.github/workflows/rgb-blocks-port-mc1211-neoforge.yml`.
Forge builder: `rgb-blocks-compat/build_mc1201_forge.py`.
This ledger intentionally distinguishes genuine verified results from active work.
