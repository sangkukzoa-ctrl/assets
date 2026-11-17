# RGB Blocks 1.3.1 Legacy ports — bounded military-grade pre-release test gate

**Owner decision:** NO public release / Modrinth upload until explicit authorization. This document is the development acceptance contract, not a claim of successful release validation.

## Native target matrices (strict)
| Target | Loader | Java | Optional C&B | Graphics / Shader |
|---|---|---|---|---|
| MC 1.20.1 | Forge 47.4.28 | 17 | Chisels & Bits 20.1.20 | Embeddium 0.3.31 / Oculus 1.8.0 / Complementary **UNBOUND r5.9.3** |
| MC 1.21.1 | NeoForge 21.1.265 | 21 | Chisels & Bits 21.1.32 | Sodium 0.6.13 / Iris 1.8.12 / Complementary **UNBOUND r5.9.3** |

Original 1.3.1 parity: **16,687 colors, 50,061 Normal/Glow/Glass blocks**, RGB Tools, RGB emission/occlusion/bleeding, AUTO/MANUAL and dirty Bake, 16x16x16 C&B, world/dimension persistence, singleplayer, multiplayer, *and full standalone operation without C&B*. Fabric is NOT a target for these backports.

## Failure-prone history from original Modrinth changelog
- v1.2.4: repeated refresh / C&B light updates.
- v1.2.6: quickly placed C&B microbits disappearing, wrong collision/geometry, Sodium/Iris multiplayer sync, rejoining.
- v1.2.7: occlusion, light penetrating solids.
- v1.2.8: source scanning during cache bootstrap.
- v1.3.0: frozen Bake dirty snapshot, edits while baking deferred, unloaded chunk dirty persistence, MANUAL->AUTO catchup, per-world and per-dimension persistence.
- v1.3.1: C&B glow restored at login after server restart but still needing geometry/render chunk state rebuilt.

## Mandatory gates (same native source snapshot!)
1. **Build / static parity:** Both loaders, resources and registry counts, no class or mixin load failure. Client and dedicated server work without any optional mod; production binary has NO ci/ test package.
2. **Real two-client functional tests:** live C&B after-player-login BLUE->GREEN AUTO then RED MANUAL+BAKE; BOTH players independently verify 4095 correct bit IDs, emitting RGB + colored neighbor; original mixed NORMAL/GLOW/GLASS 4096 bit sculpture preserved; no false PASS from synthetic source refresh.
3. **Actual mesh:** 16+ MANUAL bakes across 128-block distant regions, with 2 real client JVMs, model data BakedModel quads >0 and real voxel counts on BOTH near/far; repeat runs. A successful sourceColorAt alone is insufficient.
4. **Hostile seeded chaos:** 4 rounds × 64 unpredictable commands PLUS 96 near-zero-delay Bake requests PER loader; repeated remove/reinstall, AUTO/MANUAL, teleport, RGB material/color ABA pattern, dual independent clients; preserve JSONL command trace and seed; strict BakedModel quad/color/neighbor invariants; actual peer JVM kill/restart and resynchronization. Explicit ghost-light negative oracle after final delete on BOTH clients.
5. **Real world lifecycle:** true server JVM graceful stop/reopen SAME save, client reconnect, integrated SINGLEPLAYER save, Nether/Overworld/Nether with distinct RGB cache snapshots. Preserve dirty positions when chunks are unloaded, ensure no cross-dimension contamination.
6. **Shaders / visual & occlusion:** shader OFF and both Reimagined/Unbound acceptance where applicable, visual screenshots of real RGB+C&B, solid-wall occlusion, colored-glass reflection/tint, missing-model/transparent-mesh detector and no grid leakage.
7. **Packaging / Windows:** uninstrumented JAR+full-source ZIP for each native loader; reproducible clean build; complete native Windows x64 server boot and same-world restart; actual game mod ecosystems identified and version pinned.

## Hard pass/fail rules
- **One failed REAL C&B light, baked-quad, missing mesh, incorrect dirty batch, ghost emission, two-client desync, crash or lost world state blocks release**. An earlier PASS does not erase a later FAIL.
- CI harness/template failures are separately flagged and corrected, never counted as game PASS or FAIL.
- At least **two independent seeds per loader** and two repeated distant bake validations before considering stress gate passed. The workflow currently ships fixed reproducible seeds 1313131 (Forge) / 2718281 (Neo); this criterion remains OPEN until the extra independent runs and all strict oracles pass.
- All artifacts and logs must reference the **same final commit SHA**. Don't compare green older source to red current source.
- Bounded trials, not millennial indefinite loops: per workflow maximum **110 minutes**, fixed counts per phase; after a failure preserve evidence, repair cause, rerun affected matrix and related regressions. Never silently accept timeouts or weaken thresholds.
- Owner's actual public upload stays on hold even after gate passes.

## Current actual provenance (not release-ready)
- Historic strict regression #44093373850: NeoForge LIVE passed, NeoForge STRESS FAR mesh failed, Forge LIVE third MANUAL RED failed, Forge STRESS FAR mesh failed; reproducibility is a real issue.
- Repeat #44107098923: Forge live/stress jobs passed; NeoForge live reconnect RGB-lightmap load failed and stress FAR real model failed.
- Initial chaos #44108002874: BOTH failed at CI template placeholder before gameplay; corrected in commit 400feba.
- Chaos build/test #44115007273: both loader native compilation passed and entered real graphical two-client play at verification checkpoint; final result not yet asserted here.
- Additions: real seed logs (58eba85 / 2d86ad2), CI-only chaos oracle (b8ae905), two true client launchers, post-removal ghost negative checks, loader-shared C&B geometry fix with remapped vanilla access (94235a5) and atomic trailing rebuild generation tokens (2c3cd8e). Read CURRENT workflow outcome before any status claim.

## Primary links
- Chaos workflow: https://github.com/sangkukzoa-ctrl/assets/actions/workflows/rgb-blocks-cnb-seeded-chaos-real-clients.yml
- Real live and remote bake: https://github.com/sangkukzoa-ctrl/assets/actions/workflows/rgb-blocks-cnb-post-login-and-distant-rapid-bake.yml
- Recovery log: rgb-blocks-compat/BUGFIX_CNB_LIVE_AND_REMOTE_BAKE_2026-11-17.md
