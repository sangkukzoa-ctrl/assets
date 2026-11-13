# RGB Blocks 1.3.1 — legacy port recovery and verification ledger

## 2026-11-13 FINAL checkpoint / next-session takeover — exact resumed environment
- **[Read complete exact takeover snapshot](./SESSION_2026-11-13_EXACT_RESUME.md)**. It supersedes earlier "running" workflow wording; this file remains historical chronological status.
- Actual branch `sangkukzoa-ctrl/assets:rgb-blocks-legacy-compat-audit`. Last real Forge gameplay source patch `3f29f0d8dd31bdecbdd51bba6d337ea3244bdd14` is a **FAILED functional fix for live two-client red→green RGB light**, despite compiling and passing older probes. It should NOT be rolled back without comparing source and its effect on original strict checks.
- **Latest fully completed mandatory CI:** `43432413655` Forge native build/source ZIP/MRPACK/static parity/dedicated server SUCCESS; `43432413860` original shader-OFF in-world RGB+C&B emit SUCCESS; `43432414012` Oculus/Complementary shader-ON RGB+C&B emit SUCCESS; `43432413688` regular production GUI SUCCESS; `43432414030` strict two concurrent real clients FAIL **only** at live red→green neighboring RGB light update. NeoForge 1.21.1 strict OFF `43194331152` and shader ON `43194331374` SUCCESS.
- Both dual-test Minecraft processes joined same Forge dedicated server; both ordinary RGB and chiseled RGB microbit emit, both server MANUAL/AUTO mode notifications, both real-time GREEN block/direct source OK. Still **stale old RED neighbor-light** `[238,85,119]` after green glow emitter `[4,15,2]` arrived. Strict dual `two_clients_live_rgb_sync_verified=false`. Complete log and client+peer artifacts under [#43432414030](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414030).
- **Immediate code work**: Determine if Forge `ClientLevelMixin#setBlock` injection ever fires on actual server replacement, whether `RGBRealLightEngine.invalidateAround` is deferred or fails to clear `RGBLightEngine` storage, and whether competing C&B red source reintroduces old light. CI-only instrument before changing gameplay. Code anchors `build_mc1201_forge.py` lines approx 380–435; `recovered/neoforge/.../ClientLevelMixin.java` and RGB light/source classes. Keep strict acceptance.
- After this gate passes on both clients, finish original ecosystem parity (C&B mixed Glow/Glass actual edits, NeoForge two-client, persistence/dimension/chunk refresh, AUTO/MANUAL dirty bake) before release. Do not simplify 50,061 blocks/16,687 colors or trim components.


## 2026-11-13 phase 12 — Forge live RGB change diagnosed; production invalidation patch committed
- Second live two-client diagnostic [#43430303743](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43430303743) gave **definitive data**: BOTH clients receive `rgbblocks:rgb_green_59_209_25_glow` after the server source replacement, both parse RGB `0x3bd119`, both compute direct emission `RGBLightColor4[r=4,g=15,b=2]`, both remain `AUTO=true` but adjacent `RGBLightColor8[r=238,g=85,b=119]` indefinitely — EXACTLY the prior red light value. Thus server block network sync, RGB palette parsing, C&B microbit and mode sync are PASS; stale dynamic RGB voxel storage after existing source replacement is the actual remaining issue.
- Examined original `RGBRealLightEngine.executeSettleAfterServerSync` and `RGBLightEngine.scheduleSourceBootstrap`: only refreshes source index/schedules bootstrap; it does **not** clear already ready red RGB voxel storage. `RGBLightEngine.invalidateAround` DOES clear cubes, deindex ready sections and recompute RGB light. The Forge 1.20.1 `ClientLevelMixin#setBlock` remote-update tail previously chose `settleAfterServerSync`; original `sendBlockUpdated` changed callback did not bring full invalidation in the tested actual two-client packet path.
- **Real Forge-only source patch [`3f29f0d`](https://github.com/sangkukzoa-ctrl/assets/commit/3f29f0d8dd31bdecbdd51bba6d337ea3244bdd14)** added `RGBSourceIndex.hasSourceAt(BlockPos)` to the compiled Forge workspace, and changed Forge `ClientLevelMixin#setBlock` to call `RGBRealLightEngine.invalidateAround` when new state is light-relevant or an indexed source previously existed (supports replacement and removal); harmless legacy settle path remains for remote non-source occluder update. This uses the original real RGB light propagation math; only the platform-specific invalidation trigger changes. Original NeoForge 1.21.1 and uploaded baseline remain unchanged.
- New **mandatory regression** Actions on `3f29f0d`: [Forge strict OFF #43432413860](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413860), [Forge dual live sync #43432414030](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414030), [Forge shader ON #43432414012](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432414012), [Forge full build #43432413655](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413655), [Forge production GUI #43432413688](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43432413688). **Check actual statuses before claiming PASS**; strict dual `RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS` must appear for each client while normal RGB/C&B and MANUAL/AUTO tests keep passing.
- After all success, continue NeoForge 1.21.1 two real clients, mixed C&B Glow/Glass microbits, source removal, world/chunk/dimension persistence and AUTO/MANUAL dirty bake. Not release ready yet.


## 2026-11-13 phase 11 — 2 real simultaneous Forge clients, MODE sync PASS, live color-change remains under diagnosis
- The previously pending Forge REAL production GUI #43195703260 finished **SUCCESS**, matching prior Forge full JAR/source, strict C&B colored light OFF/ON and original assets parity successes.
- Added isolated CI (no changes to distributed port logic): `rgb-blocks-compat/test_mc1201_forge_two_clients.py`, `inject_ci_two_client_sync_probe.py`, `.github/workflows/rgb-blocks-1201-two-client-sync.yml`.
- First strict run [#43427634724](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43427634724) **FAILED live dynamic color gate only**. Actual client logs/result CONFIRMED: `client_joined=true`, `peer_joined=true`, two original RGB probes PASS, BOTH C&B RGB microbit/neighbor probes PASS, `two_clients_manual_sync=true`, `two_clients_auto_sync=true`, `both_clients_alive_after_sync=true`. After server `setblock 0 121 7 rgbblocks:rgb_green_59_209_25_glow`, neither client reported `RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS` during 100-second waits; result `two_clients_live_rgb_sync_verified=false`. Do not mark the overall two-client test PASS.
- Important distinction: the original C&B source bug is **fixed**; this exposes a *different* possible dynamic-source/block-update/color-invalidation problem OR an overstrict live-green criterion. Do not assume which one before examining per-client state, emission and nearby light.
- Added CI-only per-client heartbeat `RGB_PORT_PEER_LIVE_GREEN_DIAG` at 120-tick intervals to print actual client block state, parsed RGB, direct source emission, neighboring light and AUTO state. The launcher harness now includes those logs in the job output, plus on-failure detailed lines from both client logs. Patch [`b5fecdc`](https://github.com/sangkukzoa-ctrl/assets/commit/b5fecdcba67e8b5816bfe00c4cc23c4eb91af9dd), **active strict rerun [#43430303743](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43430303743)**. Check final logs when complete and fix exact component; do not weaken test conditions.
- Next after Forge dual live green PASS: analogous NeoForge two-client test; mixed-color C&B glass/Glow, world/dimension reload and AUTO/MANUAL dirty-bake parity for both loaders.


## 2026-11-12 phase 10b — Forge 1.20.1 strict C&B RGB regression FIX VERIFIED
- The production Forge-specific `BlockEntity#getBlockPos` compile-time remapping fix at [`9000f7e`](https://github.com/sangkukzoa-ctrl/assets/commit/9000f7e52fd0ea88b485ae62722670c51c0a3899) passed BOTH shader OFF and ON strict actual game acceptance tests, and the original 1.3.1 full static parity/build gate.
- [Forge real in-world shader OFF #43195703488](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703488): **SUCCESS**. Logged `RGB_PORT_LIGHT_PROBE_PASS` source [15,6,8], neighbor [238,85,119], then `RGB_PORT_CNB_LIGHT_PROBE_PASS` C&B emitter [15,6,8] and neighboring light [238,85,119] by tick 60. Dedicated server, player join, command, surviving 4095-bit C&B fixture, render thread, registry and atlas all PASS; zero fatal errors or missing RGB models. Screenshot produced; [artifact](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703488/artifacts/13934110124).
- [Forge Oculus+Embeddium+Complementary shader ON #43195703426](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703426): **SUCCESS**. Actual `ComplementaryReimagined_r5.9.3.zip` active and `RGB_PORT_LIGHT_PROBE_PASS` + `RGB_PORT_CNB_LIGHT_PROBE_PASS` emitted [15,6,8] with nearby [238,85,119]. In-world screenshot, no fatal errors, real multiplayer join. [Shader evidence artifact](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703426/artifacts/13933866239).
- [Forge complete original-parity build #43195703246](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703246): **SUCCESS**. Byte-identical original palette/PNG/lang resource count 33,380, 16,687 RGB colors and 50,061 RGB normal/glow/glass block-model pairs, original class locations preserved 32, 1.20.1 Forge JAR, native C&B dedicated server world first load and reopen PASS; built full source ZIP (~74.9MB uncompressed), dependency MRPACK. [JAR artifact](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703246/artifacts/13932293920), [full-source ZIP artifact](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703246/artifacts/13932054548), [ecosystem MRPACK artifact](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703246/artifacts/13934000271). Workflow's artifact name still includes `RUNTIME-UNVERIFIED` by historical naming; independent strict runtime game tests listed above now PASS.
- 1.21.1 NeoForge independent strict #43194331152 and combined Complementary ON #43194331374 both SUCCESS (original 16,687-color palette, RGB and C&B per-channel light actual scene, screenshot and multiplayer join).
- Remaining gates before *release ready*: [Forge production GUI #43195703260](https://github.com/sangkukzoa-ctrl/assets/actions/runs/43195703260) (in progress as recorded here), TWO concurrent clients for both loaders, mixed-color/glass microbits and live chisel edits, chunk unload/reload and world/dimension persistent light/dirty bake, manual AUTO/MANUAL mode switching, original implementation behavior cross-check. Do not call ports final yet.


## 2026-11-12 phase 10 — 3rd-session interrupted diagnostic recovered and Forge C&B root cause fixed
- Current release source branch: `rgb-blocks-legacy-compat-audit`, patch `9000f7e`. Existing user's original 1.3.1 whole-building-ecosystem contract remains in force, unchanged.
- Confirmed actual strict shader OFF #43194331180 and Complementary ON #43194331204 failed for C&B only. Native full RGB source probe PASS. Diagnostic emitted `RGB_PORT_CNB_CLIENT_COUNTS count=1`, one `rgbblocks:rgb_red_186_72_96_glow` state at count 4095, `EFFECTIVE_MODE AUTO`, tracking=true, but `CNB_PENDING` and `CNB_CACHE` empty, `NoSuchMethodException ...ChiseledBlockEntity.getBlockPos()`.
- Root cause: original `cnbBlockEntityPos` reflective `getBlockPos` string failed in Forge 1.20.1 runtime with remapped inherited Minecraft methods; Forge-only direct compiled `BlockEntity#getBlockPos` + fallback committed in `9000f7e`.
- Latest verification started with `9000f7e`: Forge native build #43195703246, real-world shader OFF #43195703488, shader ON #43195703426, production client GUI #43195703260. Evaluate explicit PASS logs, including `RGB_PORT_CNB_LIGHT_PROBE_PASS`, before claiming runtime success.
- Independently, NeoForge 1.21.1 latest `5b546a` strict #43194331152 and combined shader #43194331374 completed SUCCESS. No code changes to NeoForge in this patch.
- Next after strict Forge PASS: two-client sync, C&B mixed RGB/glass microbits, dynamic relight and world/dimension persistence, AUTO/MANUAL dirty bake parity for BOTH targets.


## 2026-11-09 third-session live continuation — Forge C&B microbit regression
- Recovered the persisted source branch `sangkukzoa-ctrl/assets:rgb-blocks-legacy-compat-audit`; did not restart/reconstruct the port.
- Checked the previous four acceptance runs from `1b9a0ef`: Forge full build / source ZIP / MRPACK / server PASS [#42505523026](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505523026) and production GUI PASS [#42505522986](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505522986). Real in-world shader OFF [#42505523022](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505523022) and shader ON [#42505522987](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505522987) both FAIL strict C&B colored emission. In both, normal RGB source emitted [15,6,8], but C&B 4095-bit sculpted emitter stayed [0,0,0]; server chiseled block fixture and client join succeeded. No test gate was disabled.
- New CI-only Forge client C&B statistics and internal cache diagnostics committed at [`3b996fc`](https://github.com/sangkukzoa-ctrl/assets/commit/3b996fc038ee0917694666f0dee0bc3179bb3c7d), to distinguish missing client tile, wrong contents, reflection/access failures and pending/cache status.
- The first diagnostic attempt [#42506526231](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42506526231) / [#42506526355](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42506526355) failed at a CI injector anchor assertion (7 vs 6 leading spaces), before game runtime. This was promptly corrected in [`57e470d`](https://github.com/sangkukzoa-ctrl/assets/commit/57e470d5a85b0bcc157b0e6d3beb32aeb8814830); do not mistake these runs for game regression evidence.
- A second real production source gap was found: `CnbMutableStatisticsLightEmissionMixin` still used original C&B 26.x reflective `blockState()` instead of Forge 20.1.20 `getBlockState()`. Fixed in Forge-only builder [`aa8953d`](https://github.com/sangkukzoa-ctrl/assets/commit/aa8953d70a751e1a4efcbce9b84fb216df548d62) to preserve original vanilla emission suppression and avoid duplicate C&B RGB light, without changing 1.21.1 NeoForge.
- NEXT: check Forge shader OFF/ON CI runs launched by `57e470d`, especially `RGB_PORT_CNB_CLIENT_DETAILS`, `RGB_PORT_CNB_CLIENT_COUNTS`, `RGB_PORT_CNB_CLIENT_ENTRY`, `RGB_PORT_CNB_ENGINE_MAP`; fix the exact root cause in Forge port and rerun both strict tests. Leave release status blocked until C&B colored propagation PASS and later two-client/save-load acceptance.


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

## 2026-11-09 phase 9: cross-session work-in-progress continuity (do not restart)
- **User explicitly requires continuous actual coding/build work across new ChatGPT sessions, NOT a handover memo by itself.** Repository and complete committed source are `sangkukzoa-ctrl/assets` branch `rgb-blocks-legacy-compat-audit`. The new-session entrypoint is **[NEXT_SESSION_CONTINUE.md](./NEXT_SESSION_CONTINUE.md)**, containing original owner requirements, exact builder/test paths, successful features, known failures, and live follow-up CI IDs. On "진행", start with current branch head & latest CI, fix failing code and commit, NOT merely repeat progress reports.
- Verified [Forge full build #42503809546](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809546) success: candidate JAR, full source ZIP, complete MRPACK, RGB parity, dedicated server twice with saved world re-open. The candidate JAR was marked runtime-unverified because strict RGB/C&B in-world test failed.
- [Forge in-world #42503809539](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809539) on native tick patch `4843895`: **RGB full-block color propagation PASS** (`source=ba4860 emitted=[15,6,8] neighboringLight=[238,85,119]`, `bootstrap=true`). **C&B colored light FAIL** although chiseled block survives, `emitter=[0,0,0]`. The same C&B issue persists with Oculus+Complementary shader ON [#42503844791](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503844791), where `shader_enabled=true` while strict C&B light is false.
- **New source-level fix** [1b9a0ef5](https://github.com/sangkukzoa-ctrl/assets/commit/1b9a0ef5a1ee1e2dc6192c20b6e30dacaa42ac3c): 1.20.1 C&B `IBlockInformation#getBlockState()` is its actual public API, whereas 1.3.1 decompiled engine reflects record `blockState()`. The source builder now makes **Forge-only translation** `invokeNoArg(information, "blockState")` -> `invokeNoArg(information, "getBlockState")` in `RGBRealLightEngine.addCnbInformation`; original per-channel mathematics unchanged.
- **Currently running full verification of that fix**: [Forge in-world C&B colored-light #42505523022](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505523022), [Forge Embeddium+Oculus+Complementary ON #42505522987](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505522987), [Forge full JAR/source/MRPACK + server #42505523026](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505523026), [Forge production GUI #42505522986](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42505522986). **Check their latest conclusion, inspect job logs, fix and commit if any failure.** Do not claim pass before evidence.
- **NeoForge 1.21.1 fully combined strict C&B + RGB propagation + Sodium/Iris/Complementary ON already passed** run [#42415588092](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415588092), separately verified shader ON/OFF visual RGB Normal/Glow/Glass and world persistence. Pending richer C&B mixed colors/glass microbits/two-client sync.
- Next permanent acceptance gates: verify both native loaders, actual inworld C&B RGB sculpting, 3 shader blocks, two-player state sync, integrated singleplayer, per-dimension C&B persistence and dirty ledger/bake mode. Original 1.3.1 full **building ecosystem** includes C&B+Iris+Sodium+Complementary + single/multiplayer, Forge replacement Embeddium/Oculus. No stripped-down release.

## 2026-11-09 phase 8: Forge native ClientTickEvent lighting restoration
- **Root cause confirmed by CI** [run #42502983791](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42502983791): actual Forge client `RGB_PORT_FORGE_TICK_EVENT_RECEIVED` and world probe heartbeat present; world ID nonempty (`RGBRuntime.clientWorldId`), state version 2, target auto true, RGB emitter `[15,6,8]`. But `RGB_PORT_REAL_ENGINE_TICK_ACTIVE` never appears, `bootstrap=false`, RGB neighbors zero. Original `RGBRealLightEngine.processClientTick()` was **NOT called** in Forge production client; the generated `MinecraftDisconnectMixin` callback did not run from its mixin config.
- **Fixed actual Forge 1.20.1 port**, not merely tests: `build_mc1201_forge.py` writes native Forge game-bus `RGBForgeLogoutEvents.clientTick(TickEvent.ClientTickEvent)`, calls original `RGBRealLightEngine.processClientTick()` exactly once on tick phase END. The old Minecraft.tick mixin is removed from active client Mixin configs to prevent duplicate callback; native logout event and entire RGB engine mathematics/persistence logic untouched. Commit [48438957](https://github.com/sangkukzoa-ctrl/assets/commit/48438957e8a2bcdeb2a7ab217a2923833e0018da).
- Triggered full Forge build [#42503809546](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809546), real Forge in-world client/server 4095 RGB C&B microbit/neighbor light [#42503809539](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809539), and production client GUI [#42503809524](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503809524). **Read all results and `FORGE_RGB_DIAGNOSTIC`** next. Never claim fixed in-game before confirmed pass.
- Confirmed Oculus shader pack activation **independently** in [#42502471554](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42502471554), `shader_enabled=true`, but overall failed because prior missing RGB tick. Updated dedicated Oculus Complementary ON workflow paths to re-run on port changes, [#42503844791](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42503844791). Check both shader active and actual normal/C&B RGB light simultaneously.
- CI-only Forge event / engine tick / world-ID instrumentation remains separate, never included in release artifact; original mod behavior must be preserved.
- Still required: screenshot pixel comparison on both loaders, real mixed-color and C&B glass microbits, Forge shader-on colored light, world-persistence C&B, singleplayer and two-client sync.

## 2026-11-09 phase 7: resumed Forge colored-light root cause
- **PASS full simultaneous 1.21.1 NeoForge RGB + Chisels & Bits microbits + Iris/Sodium + Complementary shader ON**: [run #42415588092](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415588092), all four runtime checks true (shader_active, RGB full block emission+neighbor, sculpted C&B fixture, C&B neighboring RGB). Artifact #13591945268. Production mapping loaded in real client+server, but the pass used a CI-only probe JAR, not released JAR.
- **FAIL Forge 1.20.1 real in-world test**: [run #42415498055](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415498055). Actual 1.20.1 Forge 47.4.28 + C&B 20.1.20 + Embeddium 0.3.31 + Oculus 1.8.0 compiled, registered RGB blocks, completed client/server handshake with compressed/restored >50k RGB registry, created verified RGB C&B sculpted fixture, created screenshot; both RGB light propagation checks false. No fatal missing classes.
- Forge CI-only diagnostic [run #42502164490](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42502164490): Forge TickEvent received; client tick probe running; `source=ba4860 emitted=[15,6,8]` correct; `enabled=true`; but `bootstrap=false`, `sourceCell=[0,0,0]`, `neighboringLight=[0,0,0]` over 600 client ticks. C&B emitter/neighbor also zero. This isolates the bug to Forge **lightmap persistence readiness / original tick engine / runtime world ID** rather than RGB color parsing, Forge login or C&B block placement.
- Added further CI-only `RGB_PORT_REAL_ENGINE_TICK_ACTIVE` heartbeat to actual `RGBRealLightEngine.processClientTick()`, and `worldId`, `stateVersion`, `targetAuto` to tick probe to distinguish missing original Minecraft tick mixin from missing Forge StatePayload. [diagnostic run #42502983791](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42502983791) started; **read actual `FORGE_RGB_DIAGNOSTIC` lines** and then fix only actual underlying cause. CI-only source instrumentation is not to enter release JARs.
- Oculus 1.8.0 + Embeddium 0.3.31 + Complementary Reimagined r5.9.3 **SHADER ON** separately confirmed with real client rendering and screenshot [run #42502471554](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42502471554), `shader_enabled=true`. Workflow strict overall failed solely RGB light bootstrap false. Upstream Asek3/Oculus `Iris.java` in branch `1.20.1-new` confirms config is `config/oculus.properties` with shaderPack and enableShaders keys. Added genuine shader ON test mode to Forge inworld test and independent workflow `.github/workflows/rgb-blocks-1201-forge-oculus-complementary.yml`.
- **Next**: determine original engine tick vs client `RGBRuntime.clientWorldId()` signal and fix Forge-specific lifecycle/packet synchronization; rerun Forge real client/server C&B colored-light **with and without Complementary**, then inspect visible RGB image. No final release until all full-ecosystem gates satisfied.

## 2026-11-08 phase 6: actual visible RGB shader ON/OFF scene verified, Forge integration next
- **PASS:** [NeoForge strict RGB + C&B #42414727822](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414727822) with real `chiselsandbits:chiseled` tile and `RGB_PORT_CNB_LIGHT_PROBE_PASS emitter=[15,6,8] nearby=[238,85,119]`; no class errors; genuine 4095-bit RGB glow microblock adjacent light, not only ordinary block.
- **PASS:** [NeoForge shader ON with Complementary Reimagined #42414719507](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42414719507). Iris + Sodium render pipeline live in actual client/server. Default screenshot setup was flawed (camera over air), so earlier screenshots were not proof of visible blocks.
- **PASS and visually inspected owner-level evidence:** new **grounded camera** [NeoForge shader OFF #42415322379](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322379) and [Complementary shader ON #42415322328](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322328). PNGs visibly contain **LEFT normal / CENTER glow / RIGHT glass** red RGB blocks over a stone platform; with Complementary ON the central red/pink emitter produces visible pink color on nearby stone. The shader ON frame has RGB glow effect clearly seen; GL shader compiler warnings are nonfatal in CI.
- Screenshot camera and fixture checks fixed in `test_mc1211_neoforge_inworld.py` commit `709bc458`: platform under camera y=119,z=-3..12; normal/glow/glass block presence asserted, player teleport log acknowledged before capture. Screenshots now show scene rather than sky + flat grass. Note: manual visual inspection performed; the CI currently does **not** programmatically compare RGB pixel channels with original MC26.1.2.
- **Forge 1.20.1 CI-only microbit strictness improved** in `inject_ci_only_light_probe.py` commit `0a8c11e`: batch initialization + one-bit carve + surviving C&B tile gate. The Forge in-world camera was grounded and three RGB variants asserted in `test_mc1201_forge_inworld.py` commit `2b60629`. Workflow preflight and path triggers extended in commit `fc80c67`. New actual client+server Forge test [#42415498055](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415498055) entered the gameplay step; **next check its conclusion and inner `RGB_PORT_CNB_*`, `REGISTRY_SYNC`, Oculus/Embeddium and screenshot logs**.
- New **simultaneous NeoForge** strict C&B microbit + RGB adjacent light **with Complementary ON** workflow [#42415588092](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415588092) entered its gameplay step. Check final result/actual instrumented neighbor RGB values and shader loaded logs.
- Other regression [NeoForge strict grounded-camera #42415322347](https://github.com/sangkukzoa-ctrl/assets/actions/runs/42415322347) finished **success**.
- Still NOT READY FOR PUBLIC RELEASE: need Forge 1.20.1 in-world end-to-end with C&B + Embeddium/Oculus, complementary shader ON for Forge, C&B mixed colors/glass microblocks + persistence and unloaded dirty ledger, integrated singleplayer and two-client multiplayer synchronization on BOTH versions.

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
