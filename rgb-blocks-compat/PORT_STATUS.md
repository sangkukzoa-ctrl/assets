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
