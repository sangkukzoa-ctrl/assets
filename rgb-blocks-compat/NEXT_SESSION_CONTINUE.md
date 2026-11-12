# RGB Blocks 1.3.1 — EXECUTE CONTINUATION, not a fresh planning prompt

> Owner command: **"진행"** means resume **actual source editing, real GitHub Actions build, failure diagnosis and commit** from the most recent live CI status. Do not ask the owner to restate goals or redo work. Do not give a progress-summary-only answer. Work in bounded iterations to avoid long-turn failure. This file is the entrypoint if chat memory or the prior context collapses.

## LIVE UPDATE: 2026-11-09 third session (supersedes old four-run checkpoint below)
**Latest persisted branch work:** `cc119150` status ledger, `57e470d` fixed CI-only Forge diagnostic injection, `aa8953d` real Forge C&B vanilla-emission hook getter fix, `3b996fc` added CI-only C&B state/cache telemetry. The existing section "Exact active work as of commit 1b9a0ef" below is HISTORICAL. Do not revert these edits.

**Checked old four runs:** 42505523026 native Forge build/server/JAR/source+MRPACK PASS; 42505522986 normal production GUI PASS; 42505523022 (shader OFF) and 42505522987 (shader ON) real Forge C&B RGB microbit emitted [0,0,0] FAIL, despite full block RGB emission [15,6,8] and verified surviving chiselsandbits:chiseled fixture. NeoForge 1.21.1 combined C&B+Iris/Sodium+Complementary previously PASSED.

**New work**:
- Real source `build_mc1201_forge.py` also changes `CnbMutableStatisticsLightEmissionMixin` reflection `getMethod("blockState")` to Forge C&B 20.1.20 `getMethod("getBlockState")`; preserves original no-vanilla-double-emission rule, no change to NeoForge.
- CI-only `inject_ci_only_light_probe.py` Forge variant now logs C&B client tile, state count, RGB bit states, RGB engine CNB_PENDING/CNB_CACHE/MANUAL_CNB_SHADOW. The first exploratory runs #42506526231 and #42506526355 failed BEFORE runtime due diagnostic text anchor whitespace; fixed in `57e470d`.
- **Check these real runtime runs based on corrected injection `57e470d`:** [Forge shader OFF #42506740128](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42506740128), [Forge shader ON #42506740170](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42506740170). Inspect `RGB_PORT_CNB_CLIENT_DETAILS`, `RGB_PORT_CNB_CLIENT_COUNTS`, `RGB_PORT_CNB_CLIENT_ENTRY`, `RGB_PORT_CNB_ENGINE_MAP` and build/game exceptions. NeoForge regression [#42506740366](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42506740366), combined [#42506740144](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42506740144).
- Do NOT mark Forge release-ready from compile alone, do NOT disable C&B strict test. Fix any diagnosed real Forge client C&B issue then commit. Next acceptance after strict PASS: two-client sync, C&B mixed colors/glass and world reload/dirty bake parity on both targets.


## LIVE UPDATE 2026-11-12 — resume after Free-plan interruption, actual root cause found

- Resumed at live branch head `5b546a` and recovered completed diagnostics: Forge shader OFF [#43194331180](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331180) and shader ON [#43194331204](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331204) failed strict `cnb_rgb_propagation_verified`. NeoForge strict [#43194331152](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331152) and NeoForge combined shader [#43194331374](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331374) both PASS.
- Definitive Forge production diagnostic: `NoSuchMethodException: mod.chiselsandbits.block.entities.ChiseledBlockEntity.getBlockPos()` from the ORIGINAL `RGBRealLightEngine.cnbBlockEntityPos` reflective lookup. In Forge 1.20.1, Minecraft inherited method names are runtime remapped; `Class#getMethod("getBlockPos")` could not find it. Client C&B block entity and all 4095 RGB bits are correct, `EFFECTIVE_MODE AUTO`, tracking enabled; but `CNB_PENDING=0`, `CNB_CACHE=0`; direct RGB ordinary full-block glow passes. Earlier `getBlockState()` port patch was necessary but could not work while C&B position lookup failed.
- **Real production Forge port fix committed [`9000f7e`](https://github.com/sangkukzoa-ctrl/assets/commit/9000f7e52fd0ea88b485ae62722670c51c0a3899)**: Forge-only `build_mc1201_forge.py` changes `cnbBlockEntityPos` to use Java-compiled `instanceof net.minecraft.world.level.block.entity.BlockEntity tile` and `tile.getBlockPos().immutable()` (remapper aware), with original reflection fallback retained. Existing recovered original and 1.21.1 NeoForge are untouched. Exact template was compared with recovered 1.3.1 Java; match confirmed.
- **IMMEDIATE NEXT**: inspect these *new* CI runs launched by `9000f7e`: [Forge full build #43195703246](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703246), [Forge real multiplayer shader OFF #43195703488](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703488), [Forge Oculus/Complementary ON #43195703426](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703426), [Forge real production GUI #43195703260](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703260). Require explicit `RGB_PORT_CNB_LIGHT_PROBE_PASS` and ordinary `RGB_PORT_LIGHT_PROBE_PASS`; compiling alone does NOT meet release requirements. If any fails, read `fetch_workflow_job_logs` for failure and patch production builder, not probe thresholds.
- After these PASS: validate actual two-client color sync, mixed C&B glass/Glow microbits, persistence/dimension switch and MANUAL dirty bake with full original architecture. No premature release.

## The work itself survives across sessions
- **GitHub repository:** `sangkukzoa-ctrl/assets`
- **Active source branch:** `rgb-blocks-legacy-compat-audit`
- **All builders, recovered class sources, modified port implementations, Java resource/model mappings, game acceptance test harnesses and GitHub Actions are COMMITTED TO THIS BRANCH**. The next session continues this branch, not a fresh workspace.
- **Primary real work files:**
  - `rgb-blocks-compat/build_mc1211_fabric.py` — shared 1.21.1 staging only (Fabric is NOT a target release).
  - `rgb-blocks-compat/build_mc1211_neoforge.py` — target 1, native Minecraft 1.21.1 NeoForge 21.1.265, Java 21.
  - `rgb-blocks-compat/build_mc1201_forge.py` — target 2, native Minecraft 1.20.1 Forge 47.4.28, Java 17.
  - `rgb-blocks-compat/recovered/fabric/com/rgbblocks/**` and `recovered/neoforge/com/rgbblocks/**` — decompiled original 1.3.1 code to preserve implementation logic.
  - `rgb-blocks-compat/inject_ci_only_light_probe.py` — CI-only probe, **never put it in a release JAR**.
  - `rgb-blocks-compat/test_mc1211_neoforge_inworld.py`, `test_mc1201_forge_inworld.py` — actual production launcher, dedicated server, screenshot and strict color-light assertion.
  - `rgb-blocks-compat/validate_full_parity.py`, `EXACT_131_PORT_CONTRACT.md`, `PORT_STATUS.md`.
- **Read `EXACT_131_PORT_CONTRACT.md` and newest heading(s) in `PORT_STATUS.md`** before changing anything.

## Owner's exact required deliverables — two old versions, same *complete building ecosystem* as 1.3.1
1. **1.21.1 NeoForge** (NOT Fabric) and **1.20.1 Forge** (NOT NeoForge). Original `1.3.1` must be the sole feature baseline, including **16,687 RGB palette colors, 50,061 Normal/Glow/Glass blocks, original textures and names, two RGB tools, original commands and settings, RGB per-channel light, color bleed, 16×16×16 voxel construction, AUTO/MANUAL baking, dirty positions, world/dimension lightmap persistence and multi-player synchronization**. No stripped-down approximation.
2. **Full stated mod ecosystem**, NOT Chisels & Bits alone: original C&B + Sodium + Iris + Complementary shader + singleplayer/multiplayer. On 1.20.1 Forge, use **C&B 20.1.20 + Embeddium 0.3.31 + Oculus 1.8.0 + Complementary Reimagined r5.9.3**, preserving **behavior** where names differ. On 1.21.1 NeoForge use C&B 21.1.32, Sodium 0.6.13, Iris 1.8.12 and same shader. Need real gameplay, not only Gradle success.
3. **Stable release artifacts**: runnable JAR, full-source ZIP, and preferably Modrinth complete ecosystem MRPACK per target with logs and screenshots; keep released builds separate from CI-only telemetry. User prefers full ZIPs and uses GitHub Actions to build (Java 17/21; builds expensive).
4. **Use real CI findings**: do NOT claim feature parity based only on static model counts, successful Minecraft launch, or green smoke test. In particular verify actual surviving `chiselsandbits:chiseled` tile, per-channel colored light from RGB microbits, Complementary ON, persistence + rejoin, 2-client sync.
5. **Workflow rule**: each short "진행" turn checks latest runs, diagnoses failure, commits actual code and triggers CI, updates status, reports concrete commits/artifact links. Do not ask for clarification/redundant planning, and do not promise background work. GitHub workflow reruns automatically on matching pushes.

## Exact active work as of commit 1b9a0ef5a1ee1e2dc6192c20b6e30dacaa42ac3c
**Latest actual source code change:** `rgb-blocks-compat/build_mc1201_forge.py`, commit [1b9a0ef](https://github.com/sangkukzoa-ctrl/assets/commit/1b9a0ef5a1ee1e2dc6192c20b6e30dacaa42ac3c).
The **Forge 1.20.1 C&B code reads `IBlockInformation#getBlockState()`**, whereas source 1.3.1 C&B 26.x used record `blockState()`. Original `RGBRealLightEngine#addCnbInformation` reflects `blockState` and swallowed a `NoSuchMethodException`, causing *0* RGB emission for a real C&B 4095-bit glow sculpture on Forge. The Forge port builder now translates **only** `invokeNoArg(information, "blockState")` to `invokeNoArg(information, "getBlockState")`; original lighting mathematics remains intact. Check actual game results.

**Immediately check these four GitHub Actions run IDs:**
- [42505523022](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505523022) **Forge actual C&B + RGB colored-light world smoke, shader OFF**.
- [42505522987](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505522987) **Forge actual C&B + RGB colored-light + Embeddium + Oculus + Complementary shader ON**.
- [42505523026](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505523026) **Forge build, parity, dedicated server, JAR/source+MRPACK artifact**.
- [42505522986](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505522986) **Forge production client GUI**.
When check is done, inspect exact failed **job** logs AND `mc1201-forge-inworld/evidence/minecraft-client-latest.log`, `server-console.log`, `result.json`, `forge-rgb-probe-diagnostics.log`. Do not fake acceptance.

**Known verified success before this latest C&B API correction:**
- 1.21.1 NeoForge full **simultaneous** C&B microbit RGB colored light + Iris/Sodium + Complementary r5.9.3 ON: [run #42415588092](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415588092). Green with `shader_active=true, rgb_light_propagation_verified=true, cnb_sculpted_fixture=true, cnb_rgb_propagation_verified=true`. This was a CI-only probe in real client/server.
- 1.21.1 NeoForge shader OFF and ON screenshots with actually visible Normal/Glow/Glass blocks: [#42415322379](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322379) and [#42415322328](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322328). Full original palette 16,687 and 50,061 block models, 33,380 original PNG/lang/palette files byte-identical, 31 original Java class paths retained.
- 1.21.1 NeoForge full JAR + dedicated-server world reopen and `/rgb bake get` alias: [#42414075937](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414075937).
- 1.20.1 Forge regular mod builder + real dedicated-server two boots + compiled Java source/JAR/complete MRPACK: [#42503809546](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809546), PASS. JAR artifact was explicitly `RUNTIME-UNVERIFIED` before latest C&B source fix.
- 1.20.1 Forge **normal RGB glow** colored light fixed by [#4843895](https://github.com/sangkukzoa-ctrl/assets/commit/48438957e8a2bcdeb2a7ab217a2923833e0018da): native Forge `ClientTickEvent.END` invokes `RGBRealLightEngine.processClientTick()`. Previously disconnected `MinecraftDisconnectMixin` tick was never executed and `bootstrap=false`; after fix Forge CI [#42503809539](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809539) has `RGB_PORT_LIGHT_PROBE_PASS source=ba4860 emitted=[15,6,8] neighboringLight=[238,85,119]`, worldId valid, bootstrap true.
- Forge Oculus 1.8.0 + Embeddium 0.3.31 Complementary r5.9.3 ON also loaded correctly in actual production client [#42503844791](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503844791). **Overall run failed** only because C&B microbit `emitter=[0,0,0]`; strict RGB C&B test must not be bypassed.

## Why unfinished and where to fix if new C&B test still fails
C&B 1.20.1 upstream source: `ChiselsAndBits/Chisels-and-Bits`, branch `version/1.20.1`, file `core/src/main/java/mod/chiselsandbits/block/entities/ChiseledBlockEntity.java`. It implements `getStatistics()`, private mutable-statistics `getStateCounts()` and `stream()`. `BlockInformation.java` in `core/src/main/java/mod/chiselsandbits/blockinformation/` has `public BlockState getBlockState()` (line ~91). In original RGB engine `computeCnbSourceFromStatistics` calls `addCnbInformation`, which previously reflected `blockState()`. Both target C&B versions use different interfaces; **do not change shared original NeoForge engine source**, use version-specific Forge translation only.

If corrected `getBlockState()` still fails, inspect `computeCnbSourceFromStatistics()`, `invokeNoArg()`, C&B `getStateCounts()` and client block entity/statistics, add **CI-only** telemetry before guessing. Also examine whether C&B `refreshCnbBlockEntity` callback reaches `processClientTick()`; normal direct RGB light works already.

## Next feature acceptance after Forge RGB C&B strict PASS
Build shader OFF and ON RGB scene screenshots, compare visually, test C&B **mixed colors** and **glass microbits**, two clients, integrated singleplayer, reload/chunk unload and bake persistence on both targets. Do not silently drop original RGB mode/scope/persistence/dirty-ledger behavior. Then produce release candidate JAR + full source ZIP + MRPACK for BOTH target loaders. Update `PORT_STATUS.md` after each step.

**Important:** merely reading this document is not the requested continuation. The user's requirement is to use the actual persisted branch, check live CI, and perform the next code edit/build as necessary.
