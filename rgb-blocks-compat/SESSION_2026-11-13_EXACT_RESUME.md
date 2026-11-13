# RGB Blocks 1.3.1 — EXACT CONTINUATION SNAPSHOT (2026-11-13, 22:45+ KST)
**NOT A NEW PORT PROJECT.** This is the runnable checkpoint for the next conversation in the SAME RGB Blocks Project. Resume the existing GitHub branch and test pipeline; do not reimplement or choose a different loader. The owner uses one-word **"진행"** to order continuing the actual edit/build/test loop immediately.

## 0. Verified truth at session boundary (checked against GitHub Actions, NOT prior-chat claims)
- Repo: `sangkukzoa-ctrl/assets`, working branch: `rgb-blocks-legacy-compat-audit`.
- Code HEAD at initial handoff verification: `5209a8c7f278ee2ac0a431f484c362a91db82297`. This file and later status-doc commits will move HEAD. Read the live branch HEAD FIRST before writing.
- Latest **actual production code** fix commit: `3f29f0d8dd31bdecbdd51bba6d337ea3244bdd14`, Forge-only live source invalidation. It **compiled** and passed all old single-client/runtime gates but **FAILED the new two-client live red→green light correction**; do not call the bug solved.
- Last two-client strict run `43432414030` on `3f29f0d`: **FAILED** at `RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS` on both clients. Its instrumentation verified the changed green block and direct emitter but neighboring light stays red. [run and complete logs](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414030). This must be the immediate next code/debug task, not starting a fresh port.
- Five regression workflows on the SAME `3f29f0d`:
  - Forge full native build/server/parity/source ZIP/MRPACK [#43432413655](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413655) **SUCCESS**.
  - Forge shader OFF strict original RGB+C&B glow real game [#43432413860](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413860) **SUCCESS**.
  - Forge shader ON + Embeddium + Oculus + Complementary [#43432414012](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414012) **SUCCESS**.
  - Forge ordinary production GUI [#43432413688](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413688) **SUCCESS**.
  - Forge two REAL concurrent clients live RGB and MANUAL/AUTO [#43432414030](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414030) **FAIL** only at live source replacement.
- NeoForge 1.21.1 previously verified independently: strict RGB+C&B OFF [#43194331152](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331152) **SUCCESS**, combined C&B+RGB+Sodium/Iris+Complementary ON [#43194331374](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331374) **SUCCESS**. Do not change the NeoForge implementation to repair Forge.

## 1. Exact owner's non-negotiable goal, not just a C&B mod
Port ORIGINAL RGB Blocks **1.3.1 from Minecraft 26.1.2** to:
1. MC **1.21.1 NeoForge 21.1.265**, Java 21. **NOT Fabric** final release.
2. MC **1.20.1 Forge 47.4.28**, Java 17. **NOT NeoForge** final release.

Preserve the 1.3.1 **full building ecosystem** and same practical behavior:
- Exactly **16,687 palette colors**, **50,061 RGB normal/glow/glass blocks**, registered items/models/texture/language parity, same RGB items and two tools.
- 16³ Chisels & Bits microblocks, mixed colors, sculpted Glow/Glass, micro-bit RGB colored emission, updates to geometry/light, sources preserved when chunk loads/unloads.
- Original per-channel propagated RGB light + real vertex/shader integration + direct block color/glass.
- Runtime `AUTO`, `MANUAL`, `/rgb bake`, `/rgb get`, `/rgb bake get`, `/rgb setbake all` and `/rgb setbake 4..256`, dirty ledger, client-server sync and world/dimension persistence. No feature deletion.
- Both actual singleplayer and dedicated server multiplayer with two clients and edit/reconnect/save/reload acceptance.
- Full original building compatibility versions: 1.21.1 **C&B NeoForge 21.1.32 + Sodium 0.6.13 + Iris 1.8.12 + Complementary Reimagined r5.9.3**; 1.20.1 **C&B Forge 20.1.20 + Embeddium 0.3.31 + Oculus 1.8.0 + Complementary Reimagined r5.9.3**. Names differ by platform but equivalent building ecosystem MUST remain.
- Release artifacts: JAR + complete reproducible source ZIP + matching ecosystem pack (MRPACK/dependencies) **FOR EACH target**. No green CI by disabling assertion/altering tests.
- The detailed full contract is permanently in `rgb-blocks-compat/EXACT_131_PORT_CONTRACT.md`. Read it.

## 2. Repository IS the continuing work environment
The essential source is versioned in this existing branch. Local CI `port-work/` is **generated** and not persisted (recreate with builders). Do not confuse an ephemeral conversation/container path with the actual durable project state.

Paths:
- `rgb-blocks-compat/build_mc1211_fabric.py` — intermediate shared staging/compat reference ONLY, not a shipping target.
- `rgb-blocks-compat/build_mc1211_neoforge.py` — actual NeoForge port generator.
- `rgb-blocks-compat/build_mc1201_forge.py` — actual Forge port generator; **latest gameplay patch here**.
- `rgb-blocks-compat/recovered/neoforge/com/rgbblocks/**` and `recovered/fabric/**` — original 1.3.1 decompiled class implementation reference. Do not replace them with guessed simplified classes; 1.20.1 patches are applied by builder.
- `rgb-blocks-compat/inject_ci_only_light_probe.py` — runtime C&B RGB correctness probes, CI ONLY.
- `rgb-blocks-compat/inject_ci_two_client_sync_probe.py` — dual Forge client sync and live green source probe, CI ONLY.
- `rgb-blocks-compat/test_mc1201_forge_two_clients.py` — real dedicated Forge server, two distinct real PortableMC Forge clients and Xvfb screens, strict green validation.
- `rgb-blocks-compat/test_mc1201_forge_inworld.py`, `test_mc1201_forge_production_client.py`, `test_mc1211_neoforge_inworld.py` — real game acceptance harnesses.
- `rgb-blocks-compat/validate_full_parity.py`, `package_ecosystem.py`, `verify_upstream.py`, `ecosystem-lock.json`.
- `.github/workflows/rgb-blocks-1201-two-client-sync.yml` — **current failing strict gate**; corresponding Forge OFF/ON/full-build/GUI workflows also committed.
- `.github/workflows/rgb-blocks-1211-neoforge-rgb-probe.yml`, `rgb-blocks-1211-neoforge-combined-acceptance.yml` for NeoForge.
- `rgb-blocks-compat/PORT_STATUS.md`, `NEXT_SESSION_CONTINUE.md`, **this file** — progress and recovery.
- Project owner provided original 1.3.1 source archives in this RGB Blocks project at `/mnt/data/RGB-Blocks-1.3.1-Fabric-26.1.2-full-source.tar` and `/mnt/data/RGB1.3.1 네오포지.zip`. They are sizeable. Original runtime artifacts and reconstructed code/asset parity are retrieved reproducibly by existing builder/CI. The reconstructed decompiled source is **not claimed byte-identical Java source** to uploaded author archives.

### Established native environment
- Forge 1.20.1: Java 17, Gradle 8.8, Forge 47.4.28, C&B 20.1.20, Embeddium 0.3.31, Oculus 1.8.0.
- NeoForge 1.21.1: Java 21, NeoForge 21.1.265, C&B 21.1.32, Sodium 0.6.13, Iris 1.8.12.
- Actual game CI: Linux GitHub Actions, PortableMC v5.0.6, dedicated server, headless `Xvfb` + Mesa `llvmpipe` + screenshot; same configs and original test scripts.
- Baseline stats from build-parity acceptance: palette 16,687; block-model pairs 50,061; resource comparison includes 33,380 byte-equal original PNG/language/palette files, no missing RGB model files. A static parity PASS alone is not in-game PASS.

## 3. Precise chronological progress, with real commits
- Pre-2026-11-13: Forge 1.20.1 real microbit RGB source had `NoSuchMethodException ChiseledBlockEntity.getBlockPos()`. Forge runtime remaps inherited Minecraft methods; fixed with compiled `BlockEntity#getBlockPos()` in `build_mc1201_forge.py` at `9000f7e52fd0ea88b485ae62722670c51c0a3899`. Since then original 4095-bit C&B emissive fixture emits RGB correctly with shader OFF and ON.
- 2026-11-13 new two-client test: `2e4bcb1` CI-only sync probe, `56863b5` real two-client harness, `d9e00dd`/ `bf38f1c` dedicated workflow.
- First dual run [#43427634724](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43427634724) **FAIL**: BOTH clients join and pass normal RGB and C&B 4095-bit RGB, BOTH receive MANUAL and AUTO state, remain alive; red→green source edit fails neighbor-light validation.
- Diagnostics `b5fecdc` added `RGB_PORT_PEER_LIVE_GREEN_DIAG`; second dual [#43430303743](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43430303743) **FAIL** with decisive readouts:
  ```
  server command: setblock 0 121 7 rgbblocks:rgb_green_59_209_25_glow
  first and second client: Block{rgbblocks:rgb_green_59_209_25_glow}
  parsed RGB = 0x3bd119
  direct sourceColorAt = RGBLightColor4[r=4,g=15,b=2]
  neighboring stored light at (0,121,6) = RGBLightColor8[r=238,g=85,b=119]
  auto=true
  ```
  Thus **network block sync, source-color calculation and mode packet sync work; stale light storage remains**. Strict green test has never passed.
- Production Forge-only attempted fix `3f29f0d8dd31bdecbdd51bba6d337ea3244bdd14`: `build_mc1201_forge.py` adds `RGBSourceIndex.hasSourceAt` and patches `ClientLevelMixin#setBlock` to call `RGBRealLightEngine.invalidateAround(pos)` instead of only `settleAfterServerSync(pos)` on relevant transitions. This patch compiles, all older tests PASS, **dual latest FAIL**, with identical stale red neighboring light. Do not falsely label the issue solved.
- CI-only harness files unchanged by latest production fix. Latest dual strict output:
  ```json
  {"server_ready":true,"client_joined":true,"peer_joined":true,
   "first_rgb_probe_verified":true,"first_cnb_rgb_probe_verified":true,
   "peer_rgb_probe_verified":true,"peer_cnb_rgb_probe_verified":true,
   "two_clients_manual_sync":true,"two_clients_auto_sync":true,
   "two_clients_live_rgb_sync_verified":false,
   "both_clients_alive_after_sync":true}
  ```
  Source at both clients still GREEN [4,15,2]; neighboring light unchanged RED [238,85,119], even >3000 client ticks later. Dual test is deliberately FAIL. Run #43432414030, job `131908934723`.

## 4. Immediate next implementation task, with code locations (do NOT restart plan)
1. On next **"진행"**, **verify live branch HEAD and read #43432414030 failure log** (already completed), then inspect `rgb-blocks-compat/build_mc1201_forge.py` roughly lines **380–435**, especially `forge_live_source_index`, `forge_live_rgb_invalidations`. Inspect `recovered/neoforge/com/rgbblocks/mixin/client/ClientLevelMixin.java` and `recovered/neoforge/com/rgbblocks/client/lighting/{RGBLightEngine,RGBRealLightEngine,RGBSourceIndex}.java`.
2. Determine WHY invalidation does not take effect: (a) whether `ClientLevelMixin#setBlock` actually fires on network block replacements (Mixin target signature/refmap/overloads), (b) whether `invalidateAround` is deferred by AUTO/MANUAL bake state and `shouldDeferNewEvent`, (c) whether `RGBLightEngine.invalidateAround` removes old red voxel entries and recalculates in READY sections or is later overwritten, (d) whether existing C&B red emitter at `(4,121,7)` contributes to red source (test green must still dominate at `(0,121,6)`), (e) whether derived RGB storage `STORAGE`/section `READY_SECTIONS`/source index invalidation path is called for both clients. Avoid guessing without new telemetry.
3. Add **temporary CI-only instrumentation** to the correct Forge runtime code path or mixin: log hook invocation with old/new BlockState, `pos`, `previousSource`, `lightRelevant`, `shouldDeferNewEvent`, mode, old/new sourceIndex, RGB voxels immediately before/after invalidation and next client tick. No change to release JAR for pure diagnostics.
4. Fix **the actual root cause** in Forge builder/compat Mixin, preserving original per-channel propagation math, C&B glow/Glass and NeoForge state. No assertion skips, color thresholds loosened, false PASS or returning to single-client-only test.
5. Commit and use existing workflow `.github/workflows/rgb-blocks-1201-two-client-sync.yml`. Require **TWO** `RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS` markers plus BOTH `RGB_PORT_PEER_MANUAL_SYNC_PASS`, `RGB_PORT_PEER_AUTO_SYNC_PASS`, normal RGB and sculpted C&B `RGB_PORT_CNB_LIGHT_PROBE_PASS`; require `two_clients_live_rgb_sync_verified=true`. Re-run Forge build, shader OFF, Complementary ON and ordinary GUI. Log real run IDs. Do not mark released before all parity gates.
6. After strict Forge two-client dynamic edit PASS, implement/test equivalent two-client 1.21.1 NeoForge protocol; C&B mixed RGB + glass microbits + real chisel edits; source removal, AUTO/MANUAL dirty bake, radius scopes, both targets world/dimension restart, chunk unload/reload, reconnect/save and renderer pixel/screenshot checks. Packaging then final source/JAR ecosystem deliverables.

## 5. Exact latest artifacts (workflow artifacts usually expire; builders reproduce them)
All these are from production fix `3f29f0d`:
- [Forge 1.20.1 JAR (unverified as full release)](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413655/artifacts/14042385322), [Forge full source ZIP](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413655/artifacts/14042310355), [Forge full building ecosystem MRPACK](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413655/artifacts/14042345321).
- [Forge shader OFF actual in-game evidence](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413860/artifacts/14042215696), [Forge Complementary shader ON real game evidence](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414012/artifacts/14040329105), [Forge production GUI evidence](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413688/artifacts/14042855526).
- [Two-client failing exact primary + peer logs, full server log, result.json](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414030/artifacts/14041740420).
- [NeoForge strict RGB+C&B screenshot+logs](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331152/artifacts/13932541555), [NeoForge Iris/Complementary ON evidence](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43194331374/artifacts/13933240436).
- Full source model is committed as builders + recovered originals, but **generated `port-work`** and modpack output files are GitHub CI artifacts, not committed as huge files.

## 6. How to restore tools and work immediately (future assistant)
- GitHub connector is connected. Via `functions.exec` discover tool signatures using `ALL_TOOLS`; use `tools.mcp__GitHub__fetch({url:"https://api.github.com/repos/sangkukzoa-ctrl/assets/branches/rgb-blocks-legacy-compat-audit"})`, `mcp__GitHub__fetch_file({repository_full_name:"sangkukzoa-ctrl/assets",ref:"rgb-blocks-legacy-compat-audit",path:"..."})`, `mcp__GitHub__update_file({repository_full_name,branch,path,sha,content,message})`. Use GitHub Actions job listings and job logs for real evidence.
- Do not use generic web search to access user's connected GitHub branch. Do not ask owner to reupload or copy entire work; the durable branch contains the real code and test scripts.
- Use bounded real code+CI iterations; after each change update `PORT_STATUS.md` and this file/`NEXT_SESSION_CONTINUE.md` with exact commits and CI statuses. Single user input `진행` means start executing, not re-explain the plan.
- Avoid reporting a queued/in_progress Actions run as PASS. Completed GUI/Forge normal paths PASS, but **strict dual dynamic RGB FAIL** remains highest-priority blocker.
- Preserve the user's preference for a **complete source ZIP and JAR per target** once fully validated. Testing is a release gate, not a reason to omit functionality.
