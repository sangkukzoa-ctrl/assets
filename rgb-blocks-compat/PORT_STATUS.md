# RGB Blocks 1.3.1 — legacy port recovery and verification ledger

> **OWNER'S LATEST TARGET REQUIREMENT (2026-11-07):** Release Minecraft **1.21.1 NeoForge** and Minecraft **1.20.1 Forge**, each with **the entire original RGB Blocks 1.3.1 architecture and functionality**. Former 1.21.1 Fabric work is diagnostic/intermediate only; it must NOT be presented as the required 1.21.1 release. Read [EXACT_131_PORT_CONTRACT.md](./EXACT_131_PORT_CONTRACT.md) before any additional changes. Work in bounded per-turn iterations: when the owner says "진행", continue from the last successful commit/build check, never reinterpret targets or silently relax original functionality.
>
> Current NeoForge 1.21.1 builder: `build_mc1211_neoforge.py`, CI `.github/workflows/rgb-blocks-port-mc1211-neoforge.yml`. Baseline dependency: official NeoForge C&B 21.1.32 (21.1.33 has reported startup failure). Native NeoForge port is **NOT YET FINAL VALIDATED**.


Last verified: 2026-11-07 (Asia/Seoul)
Branch: `rgb-blocks-legacy-compat-audit`

## Goal and source
Maintain original RGB Blocks 1.3.1 blocks, colors, glow/glass, light engine,
Chisels & Bits microblocks, shader integration, lighting persistence and
singleplayer/multiplayer semantics on:
- Minecraft 1.21.1 **NeoForge** (Java 21, NeoForge 21.1.265, C&B NeoForge 21.1.32, Sodium 0.6.13, Iris 1.8.12). Old Fabric work is a non-release reference.
- Minecraft 1.20.1 Forge (Java 17, Forge 47.4.28, C&B 20.1.20, Embeddium 0.3.31, Oculus 1.8.0).

The owner-uploaded source archives (~460MB each) cannot pass the connected
GitHub file transport, so the owner-published 1.3.1 binaries were downloaded
and Java was decompiled with Vineflower on GitHub Actions. The outputs are
reconstructions, not bit-for-bit replacement for the author's source archives.
Preserve/compare against author's original assets where possible.

## 2026-11-08 phase 5: verified actual microbit RGB; fix meaningful visual evidence
- **PASS strict NeoForge C&B microbit colored light** [run 42414727822](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414727822). The **server** retained the real `chiselsandbits:chiseled` tile after batching `initializeWith` and a microcut, fixture prints `actualBlock=chiselsandbits:chiseled`. The **client** emitted `RGB_PORT_LIGHT_PROBE_PASS source=ba4860 emitted=[15,6,8] neighboringLight=[238,85,119] ticks=30` and `RGB_PORT_CNB_LIGHT_PROBE_PASS emitter=[15,6,8] nearby=[238,85,119] ticks=30`. Actual nonwhite red-dominant RGB C&B light propagation verified in regular C&B+Sodium+Iris dedicated-client session (CI-only instrumentation, not release code).
- **PASS** NeoForge 1.21.1 real client with Iris 1.8.12, Sodium 0.6.13, Complementary Reimagined r5.9.3 **ENABLED** [run 42414719507](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414719507). Shader active true and no detected fatal crash. Mesa GLSL emitted `lmCoord used uninitialized` warning (not a fatal error); do not infer pixel-correct color from startup alone.
- Python screenshot script had an accidental trailing quote that caused SyntaxError in [shader CI 42414330603](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414330603). Fixed in commit `e621caf` and added `python3 -m py_compile` as a fail-fast step before expensive Gradle in NeoForge inworld, shader and strict workflows.
- **Visual evidence concern discovered by opening actual saved screenshots:** old shader ON/OFF frames showed sky and flat grass with **no RGB blocks visible**, despite genuine shader active and server-side RGB fixture. Player teleported to Y=120 over **no floor at Z=0.5** and fell before screenshot. Updated `test_mc1211_neoforge_inworld.py` to extend stone floor beneath observer (Y=119,Z=-3..12), assert normal/glow/glass fixtures independently and acknowledge teleport; commit `709bc45`. Rechecks: [shader ON 42415322328](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322328), [shader OFF 42415322379](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322379), and [C&B strict 42415322347](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322347). **Must inspect the new PNG visually; script still tests screenshot existence rather than individual pixels.**
- Expanded **Forge 1.20.1** CI-only C&B fixture with same outer `batch()` and **surviving chiselled tile** checks, commit `0a8c11e`. Old Forge inworld script shared the empty-floor defect. Patched floor, teleport acknowledgement and normal+glow+glass server assertions, commit `2b60629`; automatic Forge inworld [run 42415498055](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415498055). Early `python3 -m py_compile` and instrumenter changes now trigger Forge inworld test, commit `fc80c67`. Await inner `RGB_PORT_CNB_*` logs; do not consider mere Forge server boot sufficient.
- New **simultaneous** NeoForge C&B colored microbit + Iris Sodium Complementary shader ON acceptance workflow [run 42415588092](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415588092); explicit `RGB_PORT_STRICT_LIGHT_PROBE=1` plus `RGB_PORT_SHADER_ON=1`. This combines two previously independently passing checks into one real session, not yet confirmed.
- Directly compared original owner-uploaded NeoForge 1.3.1 source ZIP (31 Java files) against generated NeoForge 1.21.1 FULL-SOURCE inner ZIP (37 Java files including 6 port-specific adapters). All **31 original class paths are present**. Original `RGBRealLightEngine` has 92 lexically detectable method names and the generated port retains all 92. Some API methods were renamed/rewritten, so this is only method-name coverage, not full semantic equivalence.
- **Remaining release gates**: genuinely visible RGB building screenshot with shader ON/OFF; Forge client+strict C&B+Embeddium/Oculus runtime; 2-client live sync; integrated singleplayer; C&B mixed colors / glass microbits / world persistence and dirty-set/bake with unloaded chunks; shader output correctness. No final release until both native loaders pass.

## 2026-11-08 bounded continuation checkpoint
- [NeoForge 1.21.1 JAR + dedicated server #42414075937](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414075937) **PASS** after restoring original `/rgb bake get` alias and adding command-gate test. This remains a candidate, not public release.
- The first strict C&B batch attempt [#42414009108](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414009108) failed. Its downloaded `launcher.log` still found `rgbblocks:rgb_red_186_72_96_glow` at fixture (full block) and no tile, despite full-block RGB color propagation passing. Investigated test generator and found batch patch accidentally placed under `TARGET=="fabric1211"` branch, not NeoForge! That explains why the log still printed old unverified `RGB_PORT_CNB_FIXTURE_PASS`.
- **Fixed the branch placement** in `inject_ci_only_light_probe.py` commit `6d327f0`. NeoForge branch now wraps `initializeWith` + `clearInAreaTarget` in one outer `batch()`, then checks actual chiseled block ID and surviving tile before a fixture PASS. Fabric/Forge paths remain as before. [New correct strict C&B test #42414524849](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414524849) was started; inspect final result and archived `launcher.log` + `server.log`.
- Separate real NeoForge Iris/Sodium + **Complementary ON** test [#42414330603](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414330603) was started and must be judged from client shader log and screenshot. Earlier CI passed only shader OFF.
- The user's source archives are locally available in the working runtime. Original 1.3.1 NeoForge `RGBRealLightEngine.java` and generated 1.21.1 NeoForge full source each have **92 distinct named routines** in a simple method-name audit. Source name correspondence is not full semantic/render equivalence. The imported generated source archive and baseline source were inspected, including C&B lifecycle mixins.
- Do not claim release-ready before RGB glow microbits propagate under C&B, Complementary ON/OFF matches, and all original single-/multiplayer workflows are checked on BOTH native loaders.

## 2026-11-08 phase 4: complete building ecosystem cross-version contract
- Owner clarified: not Chisels & Bits only. Public original Modrinth description requires full **C&B + Iris + Sodium + Complementary Shaders + singleplayer/multiplayer** environment. Forge 1.20.1 uses the equivalent **Embeddium + Oculus** renderer/shader-loader stack; preserve actual behavior, not literal dependency names. Matrix and quality gates are written into `EXACT_131_PORT_CONTRACT.md`.
- Confirmed [full NeoForge 1.21.1 MRPACK #42374038373](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42374038373) PASS, including C&B 21.1.32, Iris 1.8.12, Sodium 0.6.13, Complementary Reimagined r5.9.3. This tests pack creation, NOT shader ON gameplay.
- Strict NeoForge light probe [#42373740535](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373740535) failed a meaningful assertion: vanilla/full-block RGB *colored* light propagated to neighboring voxels (PASS), test claimed C&B fixture (PASS), **no C&B neighboring colored light (FAIL)**.
- Downloaded strict evidence archive, inspected `launcher.log` and `server.log`. Client repeatedly found `rgbblocks:rgb_red_186_72_96_glow` **full block** at the intended C&B fixture coordinate, no block entity. The earlier fixture was a false-positive: `initializeWith` created homogeneous 4096-bit C&B, whose own `setChanged` converted it to full block before `clearInAreaTarget` ran.
- Read C&B 1.21.1 upstream real `ChiseledBlockEntity#batch()`, `initializeWith()`, `clearInAreaTarget()`, and `MutableStatistics#updatePrimaryState()`. Patched **CI-only** NeoForge fixture to wrap initialize-plus-carve in an outer batch; then assert the actual live server block ID remains `chiselsandbits:chiseled` and the original block entity still exists before printing PASS. No release light engine workaround or fake green test.
- New strict test [#42414009108](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414009108) started. Check final result and `RGB_PORT_CNB_LIGHT_PROBE_*` from archived launcher.log next.
- Separate discrepancy found via user's original 1.3.1 uploaded Java: **NeoForge backport omitted `/rgb bake get`** (the Forge port had it). Restored the alias to the NeoForge 1.21.1 builder and added a real dedicated-server command check. New build [#42414075937](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414075937) started.
- Read original uploaded NeoForge source archive and earlier generated source ZIP from actual CI: `RGBRealLightEngine` has 92 distinct method names in original and in the generated NeoForge backport. This is **method-name coverage only**, not an equivalence proof. C&B lifecycle class and engine need full semantic verification against the author's Java.
- To verify the **rest** of the ecosystem and not stop at C&B, added actual NeoForge Iris/Sodium **Complementary ON** test mode to `test_mc1211_neoforge_inworld.py`, with pinned r5.9.3 download and hash check, Iris shader enabled config, required loaded-shader evidence and RGB scene screenshot. Separate [shader ON CI #42414330603](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414330603) started; inspect exact client log and screenshot. Earlier NeoForge GUI baseline is shader OFF.
- Release still blocked until actual Chisels & Bits RGB microbits, shader ON/OFF, two clients and original architectural parity all pass on target loaders.

## 2026-11-07 phase 3: proved client launch, isolated strict RGB test in progress
- **PASS** actual NeoForge 1.21.1 + RGB Blocks + C&B 21.1.32 + Sodium 0.6.13 + Iris 1.8.12 production game client, with REAL separate dedicated server join, renderer/atlas and screenshot, 0 missing RGB models / 0 detected crashes. [NeoForge GUI run #42373308766](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373308766) contains the glass-render-type fix and generated scene PNG. It does not prove per-channel light/glass pixel fidelity, mixed microbits or shader ON.
- **PASS** [NeoForge native build+server+parity #42373270757](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373270757): 16,687 glass models with explicitly translucent JSON, static parity, C&B server boot and RGB normal/glow/glass save/reload. Full source ZIP now includes Gradle 8.10.2 wrapper.
- **PASS** [Forge 1.20.1 independent regression #42373285390](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373285390): real runtime test printed PASS in inner log even though this workflow marks it continue-on-error. Confirmed main Forge JAR build, asset/glass parity, C&B server persistence and MANUAL/BAKE ALL.
- Added distinct **CI-ONLY** strict RGB runtime instrumenter for NeoForge 1.21.1, without changing original release JAR. `inject_ci_only_light_probe.py neoforge1211`; `test_mc1211_neoforge_inworld.py` now supports `RGB_PORT_STRICT_LIGHT_PROBE=1`. The strict test asserts real adjacent red RGB light and sculpted C&B RGB microbit emitter/neighbor propagation, not a synthetic green workflow result. Workflow `.github/workflows/rgb-blocks-1211-neoforge-rgb-probe.yml`; first run [#42373740535](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373740535) was started. Inspect compilation and inner scene telemetry and repair if failing.
- Added NeoForge test ecosystem MRPACK profile with official-origin C&B 21.1.32, Sodium 0.6.13, Iris 1.8.12 and Complementary Reimagined r5.9.3. `package_ecosystem.py neoforge1211` and isolated CI [#42374038373](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42374038373). This is a test profile; shaders are installed but not automatically enabled.
- **Still required** before release: true RGB lighting, Chisels & Bits sculpted storage/lighting, shader ON/OFF visual evaluation, two-client synchronization, owner original source vs decompiled code method-level audit. Do NOT call any port release-ready yet.

## 2026-11-07 phase 2: resumed development (actual progress)
- **Confirmed PASS:** [NeoForge native runtime #42368322195](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42368322195). First server boot and saved-world reopen both clean exit 0; real NeoForge 21.1.265 + C&B 21.1.32 loaded; full RGB palette, /rgb get, MANUAL + BAKE ALL persisted with same world ID; normal, glow and glass RGB blocks persisted. Does NOT verify the RGB optical engine or C&B sculpting.
- Implemented real 1.21.1 **NeoForge production launcher** client/server in-world smoke (not Fabric dev runtime) with C&B 21.1.32, Sodium 0.6.13 NeoForge, Iris 1.8.12 NeoForge and RGB normal/glow/glass screenshot. Source: `test_mc1211_neoforge_inworld.py`; workflow: `.github/workflows/rgb-blocks-1211-neoforge-inworld.yml`. Strict checks include actual player join, rendering startup, atlas, RGB model loading, crash patterns and screenshot; **explicitly does not count C&B sculpting or RGB channel optical validation**.
- First graphics run [#42373043374](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373043374) started on pre-glass-fix code; updated run [#42373308766](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373308766) started after fixing glass models. Inspect exact job and evidence logs; do not infer success from workflow started.
- **Found and fixed real parity gap**: the initial NeoForge adaptation replaced the Fabric translucent block render registration, leaving model JSON without `render_type`. 1.21.1 NeoForge defaults unknown blocks to SOLID. Builder now writes `minecraft:translucent` to all 16,687 glass models and `validate_full_parity.py neoforge1211` explicitly fails if any glass model loses transparency.
- Source deliverable CI updated to generate Gradle **8.10.2** wrapper and include `gradlew`, `gradlew.bat` and `gradle/wrapper/` in NeoForge full source ZIP. Reverify successful source artifact after updated run.
- 1.20.1 Forge **unchanged in port source**, but the shared transparency checker update triggered Forge regression CI [#42373285390](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42373285390). Check outcome next.
- Next: read final GUI run logs / launcher or classloading blockers; repair concrete NeoForge incompatibilities; once true game join and block scene pass, add separate RGB channel/C&B microbit/sodium-iris-shader tests. Check source parity from author source archive separately when a readable mount is available.

## 2026-11-07 session recovery and next native validation
- **Confirmed:** 1.21.1 NeoForge [CI run 42360013264](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42360013264) completed successfully: native Gradle compilation and static asset/registry parity. Previous session ended before reading this result.
- **Static evidence:** 16,687 palette entries / 50,061 models, 33,380 original PNG/language/palette files byte-identical, all 31 original NeoForge class paths present. Not an RGB lighting pixel/runtime proof.
- Candidate NeoForge [JAR artifact 13568774719](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42360013264/artifacts/13568774719) and [migrated source artifact 13568839618](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42360013264/artifacts/13568839618). Neither is release-ready.
- Added `rgb-blocks-compat/test_mc1211_neoforge_server.py` using NeoForge 21.1.265 + real C&B 21.1.32 + RGB Blocks 1.3.1. Mandatory integration test covers boot, commands, normal/glow/glass block saving, and manual/bake state after restart.
- Native CI workflow updated to require this server test (no `continue-on-error`), and archive its logs even on failure. [First test run 42367864596](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42367864596) started; read its final status and actual inner failure logs in next iteration.
- Still unverified: C&B sculpting, RGB micro-emissive lighting in real gameplay, rendered RGB pixels, shader/performance renderer compatibility, multi-client sync.
- Original uploaded source archives are preferable for architecture/method parity; decompiled GitHub recovered classes are not asserted source-identical.
## Confirmed successes (do not confuse with visual acceptance)
- Source recovery: [run 42343318500](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42343318500),
  32 Fabric and 31 NeoForge decompiled Java files.
- MC1.21.1 Fabric production JAR + full source:
  [run 42346443341](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346443341).
  Both native Gradle compile and JAR packing completed. Minecraft Fabric+C&B
  dedicated server started, registered 16,687 palette colors and 50,061 RGB
  blocks; commands, save/restart, re-placement validation for normal, glow,
  glass, MANUAL setting and full bake scope all passed.
- MC1.20.1 Forge production JAR + full source:
  [run 42346469171](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346469171).
  Both native Gradle compile and JAR packing completed. Minecraft Forge+C&B
  dedicated server started, registered 16,687 palette colors and 50,061
  RGB blocks; commands, save/restart, normal/glow/glass block persistence,
  MANUAL setting and full bake scope passed.
- Blockstates=50,061, block models=50,061, item models=50,063,
  PNG resources=33,377 packaged in each candidate.
- Keep old successful artifacts available while iterating, do not overwrite
  with an unverified GUI build.

## Latest verified installable test profiles (2026-11-07)

- 1.20.1 Forge actual JAR, complete source with Gradle wrapper, complete MRPACK:
  [run 42347086552](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42347086552).
  Dedicated server, RGB settings, placed RGB normal/glow/glass save/reload passed;
  **full ecosystem MRPACK generated successfully** with official-origin C&B,
  Embeddium, Oculus, Complementary shader references.
- 1.21.1 Fabric actual JAR, complete source with Gradle wrapper, complete MRPACK:
  [run 42347086607](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42347086607).
  Same game server and persistence checks passed; **complete ecosystem MRPACK
  generated successfully** with official-origin C&B, Fabric API, Sodium,
  Iris and Complementary shader references.
- 1.21.1 Fabric GUI startup: [run 42346527015](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346527015).
  Sodium 0.6.13, Iris 1.8.8, C&B were loaded; Minecraft render thread, texture
  atlases, Iris overworld render pipeline initialized; no fatal Mixin error.
  Test killed by scheduled 390-second process limit; OpenAL never initialized,
  **not evidence of a finished in-game scene or visually correct RGB lighting**.
- 1.20.1 Forge GPU dev-client:
  [Oculus-enabled run 42346387709](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346387709)
  failed due Oculus `@Shadow f_117950_` on Mojang-named dev Minecraft.
  [Embeddium-only run 42346992388](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346992388)
  failed similarly: Embeddium `@Shadow m_5601_` not found in its target.
  These prove raw production SRG Mixin refmaps cannot run directly in
  ForgeGradle Mojang-named dev runtime; **no conclusion about production
  Launcher/NeoForge game launch**. New RGB+C&B vanilla client dev test is queued
  independently, while the full MRPACK allows proper production loader tests.

## Production Forge client validation added

- Graphical ForgeGradle development runtime fails with external third-party
  production SRG Mixin `@Shadow` symbols (Oculus `f_117950_`,
  Embeddium `m_5601_`). These are not failures of the RGB code by themselves.
- Independent real production-mapped Forge 1.20.1 launcher-based GUI test
  added to `rgb-blocks-compat/test_mc1201_forge_production_client.py`
  and `.github/workflows/rgb-blocks-1201-production-client.yml`.
- Initial [production loader run 42347945272](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42347945272)
  initiated with official Forge 47.4.28, real C&B20.1.20, Embeddium0.3.31,
  Oculus1.8.0 under Xvfb software OpenGL. Verify its inner log / result.json.
- Fabric [run 42346527015](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346527015)
  completed successfully through Render thread, Iris overworld pipeline and
  atlas creation, no observed fatal Mixin errors. This is startup, not RGB
  color accuracy.
- Full ready-to-import test ecosystem packages available:
  [Fabric MRPACK](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42347086607/artifacts/13564545703)
  and [Forge MRPACK](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42347086552/artifacts/13564445793).
  Unzip the GitHub Actions artifact wrapper, then import inner .mrpack into
  PrismLauncher/compatible launcher. These are NOT final stable releases.

## Remaining release gates (NOT YET passed)
1. Graphical Minecraft GUI client startup and RGB vertex lighting with Sodium,
   Embeddium, Iris and Oculus. Headless virtual GL automated tests are present,
   but boot `Render thread` alone is not proof of correct RGB scene colors.
2. Chisels & Bits sculpted RGB glowing pixels and color mixing against actual
   in-world render scene; test all color channels and occlusion boundaries.
3. Iris/Oculus Complementary shader visuals and shader ON/OFF comparisons.
4. Client-server synchronization and at least two-player live session.
5. Preservation gate of unchanged assets and model compatibility where codec
   downgrade is necessary.

## Last checked GUI evidence / blockers
- Forge GUI [run 42346387709](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42346387709)
  failed IN GRAPHICAL DEV runtime due Oculus 1.8.0 production obfuscation
  `mixins.oculus.json:texture.MixinAbstractTexture`,
  `@Shadow f_117950_` not found in Mojang-named ForgeGradle target.
  This is specifically a test environment remapping mismatch, NOT proven
  RGB Blocks release runtime bug. A follow-on separate RGB+C&B+Embeddium
  GUI test with Oculus isolated is running.
- Fabric GUI earlier attempted Iris 1.8.12, which was NeoForge-only;
  corrected to official Fabric 1.8.8 for MC1.21.1 and rerun.
- Full Modrinth ecosystem test pack `.mrpack` generator created to include
  RGB JAR and download official third-party assets via hashes, not rehost.
  Sodium version string order differs: `mc1.21.1-0.6.13`; corrected pack
  version token matching and started new CI. Treat pack as exploratory until
  its own success log is checked.

## Code and workflows
- `rgb-blocks-compat/build_mc1211_fabric.py`: reconstructed source,
  resource codec migration, Fabric entrypoint, C&B hooks and Sodium bridge.
- `rgb-blocks-compat/build_mc1201_forge.py`: Forge Java17 port, MixinGradle
  mappings, registries, commands, network sync, Embeddium RGB bridge.
- `rgb-blocks-compat/test_mc1211_fabric_server.py`, `test_mc1201_forge_server.py`:
  actual server acceptance with world save/reopen and placed-block checks.
- `rgb-blocks-compat/test_mc1211_fabric_client.py`,
  `test_mc1201_forge_client.py`: graphical software OpenGL development
  environment test with explicit limits.
- Build workflows:
  `.github/workflows/rgb-blocks-port-mc1211.yml`,
  `.github/workflows/rgb-blocks-port-mc1201-forge.yml`.
- Client workflows:
  `.github/workflows/rgb-blocks-1211-client.yml`,
  `.github/workflows/rgb-blocks-1201-client.yml`.

## Next action
Inspect the latest runs of client and complete-ecosystem workflows, read
**inner step logs** (some steps use `continue-on-error` and may leave a
green overall workflow after a failing GUI test), fix the concrete failure,
rerun, then verify an in-world RGB/shader scene before approving release.
