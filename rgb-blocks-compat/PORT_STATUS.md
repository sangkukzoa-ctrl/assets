# RGB Blocks 1.3.1 — legacy port recovery and verification ledger
Last verified: 2026-11-07 (Asia/Seoul)
Branch: `rgb-blocks-legacy-compat-audit`

## Goal and source
Maintain original RGB Blocks 1.3.1 blocks, colors, glow/glass, light engine,
Chisels & Bits microblocks, shader integration, lighting persistence and
singleplayer/multiplayer semantics on:
- Minecraft 1.21.1 Fabric (Java 21, Fabric API 0.116.17+1.21.1, C&B 21.1.40, Sodium 0.6.13, Iris 1.8.8).
- Minecraft 1.20.1 Forge (Java 17, Forge 47.4.28, C&B 20.1.20, Embeddium 0.3.31, Oculus 1.8.0).

The owner-uploaded source archives (~460MB each) cannot pass the connected
GitHub file transport, so the owner-published 1.3.1 binaries were downloaded
and Java was decompiled with Vineflower on GitHub Actions. The outputs are
reconstructions, not bit-for-bit replacement for the author's source archives.
Preserve/compare against author's original assets where possible.

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
