# RGB Blocks 1.3.1 legacy port — analysis-error recovery checkpoint

Updated: **2026-11-18 KST**. This file is an **executable engineering handoff**, not a claim of a tested release.

## Repository, exact targets and user acceptance
- Repo: `sangkukzoa-ctrl/assets`, branch `rgb-blocks-legacy-compat-audit`.
- Ship only **Minecraft 1.20.1 Forge** and **1.21.1 NeoForge**, matching original **RGB Blocks v1.3.1** architecture/ecosystem, including Chisels & Bits, lighting, Complementary Unbound shader-compatible render path, AUTO/MANUAL/Bake, original 16,687 palette colors and 50,061 blockstates.
- Test true Minecraft singleplayer/LAN host, dedicated server and TWO actual clients, mixed C&B Glow/Normal/Glass voxels, shader enabled, distant rapid Bake and transparent-mesh recovery, reconnect, world/dimension reload, multiple seeded four-round random stress/CHAOS sequences. Do not pass a compile or Java unit test off as a Minecraft acceptance test.
- User uses "**진행**" as instruction to continue implementation and validation immediately; no need to repeat requirements or ask again for the two original source archives.

## Source authenticity and critical current gate
- Author-supplied original archive: `RGB-Blocks-1.3.1-Fabric-26.1.2-full-source.tar`, SHA-256 `ae5fffb7b37d7376f4e579491af878b7ed74fbe386b8691751e6d1c538bcb39c`.
- Author-supplied original NeoForge archive: `RGB1.3.1 네오포지.zip`, SHA-256 `f267b09141811f3eeb64e8247fff1d08ed2e11fdbea6c5b165f52b93e31607e1`.
- Complete canonical author bundle already generated as conversation artifact: `RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst`, SHA-256 `1aea93f67e0375ecea72c86a5a72add5488d43d87a6b058dbce93128f250d007`. A prepared user-side `RGB-Blocks-OWNER-SOURCE-CI-BOOTSTRAP-v2.zip` includes the one-time private GitHub draft release provisioning script.
- **Blocking**: as of this checkpoint, original bundle was NOT uploaded to the GitHub draft release tagged `rgbblocks-131-private-original-source`. Connected GitHub API tools do not expose uploading the binary archive, and local container/Python runtime calls returned ClientError during this turn. Existing user source files have NOT been discarded. Do not download the public Modrinth/CurseForge JAR as a substitute or commit all-rights-reserved source to the public repository. Until provisioned, actual source-first Minecraft Gradle builds / 2-client CHAOS are SKIPPED, not PASS.
- Source-first loader staging: `stage_owner_original.py`; common builder: `build_mc1211_fabric.py`; native builders: `build_mc1201_forge.py` and `build_mc1211_neoforge.py`. Original Java count 32 Fabric + 31 NeoForge, 233,627 identical shared original resources. 25 untouched original Java classes, 7 SHA-tracked compatibility overlays, 1 port-only C&B mesh watchdog. Static integrity checks operate on original source SHA and 42 asset sentinels.
- Main gameplay workflows: `.github/workflows/rgb-blocks-cnb-post-login-and-distant-rapid-bake.yml` and `rgb-blocks-cnb-seeded-chaos-real-clients.yml`. These require source-ready gate and run true native gameplay. 29 other legacy jobs remain opt-in full matrix.

## Known genuine game failures (from PREVIOUS actual game evidence; fixes are not yet re-tested in real game)
1. **Forge 1.20.1 C&B carved Glow becomes dark**. Production `RGBRealLightEngine.addCnbInformation` now supports both `getBlockState()` (1.20.1 C&B) and `blockState()` (1.21.1); removed Forge one-way rewriting. Java 17+21 source tests PASS, full Minecraft unknown.
2. **Forge multiplayer chaos blue RGB source stuck after the C&B 4095 bits/12 quads turn green.** Bounded AUTO actual-voxel-to-cache reconciliation plus stale packet/removed tile protection implemented; JAVA 17+21 PASS, full Minecraft unknown.
3. **NeoForge after peer relaunch C&B model/4095 bit counts intact but light BLACK >1680 ticks.** Added bounded loaded-chunk cache-miss C&B discovery and strict post-rejoin original mixed source oracle in BOTH real-game harnesses; Java 17+21 PASS, real Minecraft unknown.
4. **Remote, rapid Bake may leave C&B model invisible while light data remains.** Fixed trailing model generation reflection, AIR-only false geometry, and bounded diagnostics. Java 17+21 PASS, real Minecraft unknown.
5. **LAN integrated host client previously skipped trailing mesh repair** because `isRemoteClientWorld()` required `getSingleplayerServer()==null`. Corrected to check live actual CLIENT level (not integrated server presence), preserving server/stale world rejection. Java 17+21 test PASS in run [#44298199139](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44298199139). 

## EXACT last interrupted subtask — resolved after analysis failure
- Analysis was interrupted after edits to `inject_ci_integrated_probe.py` and real Forge/Neo harnesses. Those edits require a new **live, in-game LAN host C&B mesh-repair gate** before integrated-world acceptance, not just the old mixed-color probes.
- Last committed recovery work: `test_cnb_integrated_lan_probe_offline.py` added in `4f0858e`. It executes the ACTUAL integrated Java test injector on synthetic two-native workspaces, confirms LAN guard before real RGB PASS, and checks both actual Python harnesses enforce the marker. Workflow integration committed as `21f6de690`.
- **Real GitHub Actions PASS**: [#44307857285](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44307857285) emitted `RGB_PORT_INTEGRATED_LAN_CNB_PROBE_INJECTION_PASS` for BOTH `forge1201` and `neoforge1211`, following the prior full [#44299454423](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44299454423) static PASS. Source edit and test state persisted; no need to redo these static steps in a new chat.

## Next implementation steps (small independent batches)
1. Register exact 4MB author bundle via existing private-draft bootstrap, then run owner SHA gate and actual common/native **Gradle builds**, examining real compiler errors. Do not claim source-ready before verification.
2. Execute core 2-client LIVE/distant-Bake and CHAOS with real C&B, shader and original ecology on BOTH loaders. Require post-relogin mixed source light, AUTO/MANUAL Bake, zero ghost RGB, successful distant mesh and model/quads, screenshots and evidence logs. Re-run failed seeds.
3. Examine returned artifacts and patch focused runtime causes; after each small change, keep Java offline gates green but do NOT treat them as final gameplay acceptance.
4. Only after native builds and gameplay acceptance pass, package per-loader JAR+source+exact dependency versions and server/client evidence. **Public release HOLD** until user explicitly releases.

## Chat continuation rule
For next "**진행**", read this file and the existing `OWNER_SOURCE_FIRST_MIGRATION_2026-11-18.md` / `BUGFIX_CNB_LIVE_AND_REMOTE_BAKE_2026-11-17.md` plus GitHub current branch head. Do not restart the port, re-download original RGB public binaries, overwrite earlier fixes, or assert a real-game PASS based only on mock/Java tests.
