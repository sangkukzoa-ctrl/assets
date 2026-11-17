# RGB Blocks 1.3.1 legacy ports — standalone contract (2026-11-17)

## Hard requirement
The entire **RGB Blocks 1.3.1 RGB palette and colored-light system functions on the matching Minecraft and native mod loader ALONE**. Original RGB Blocks is not a hard dependency of Chisels & Bits and does not require Chisels & Bits, Sodium, Embeddium, Iris, Oculus, or Complementary Shaders to start.

- **1.21.1 NeoForge**: generated `META-INF/neoforge.mods.toml` has ONLY `minecraft` and `neoforge` required. `build.gradle` has only NeoForge toolchain and no C&B runtime dependency.
- **1.20.1 Forge**: generated `META-INF/mods.toml` has ONLY `minecraft` and `forge` mandatory. `build.gradle` has no C&B, Embeddium or shader runtime dependency.
- **C&B interaction**: RGB microbit inspection in RGBRealLightEngine uses reflection over optional C&B block-entity/statistics APIs. NeoForge native optional C&B-specific mixins use `@Pseudo` and missing-target-safe injection; the Forge port's mixin plugin checks whether optional C&B/renderer mods are installed before activating their mixins.
- **Rendering extensions**: Sodium/Embeddium and Iris/Oculus are optional adapters. They are for performance/shader compatibility, not for registering the 50,061 RGB block variants.
- **No separate setting** is required when running the shipped production RGB JAR alone. `RGB_PORT_STANDALONE_NO_CNB=1` appears ONLY in CI test scripts and has no effect on the production mod.

## Verified real standalone dedicated-server runtime (without ANY optional mods)
The entire `mods/` directory contained exactly **one JAR: RGB Blocks**. No C&B or renderer/shader mods installed.
- **Forge 1.20.1**: [CI #44044626970](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44044626970), **Forge standalone job SUCCESS**. Actual server boot, original 16,687 RGB colors, normal/glow/glass block placement, /rgb commands, saved world reopen. Zero fatal class/mixin errors.
- **NeoForge 1.21.1**: [CI #44045407305](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44045407305), **NeoForge standalone job SUCCESS**. Actual server boot, 16,687 RGB colors, normal/glow/glass block placement, /rgb, save/reopen. Explicit `cnb_loaded=false`, zero fatal class/mixin errors.
- An earlier NeoForge CI run failed AFTER all real game assertions passed because its test incorrectly treated the log text `ClassNotFoundException: mod/chiselsandbits/...` (a harmless missing optional mixin target warning) as proof C&B had been installed. This was a TEST BUG, not an RGB runtime dependency: later CI checks actual `mods/` JAR entries instead. It passed.
- Optional independent real GUI client/server test [#44045724254](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44045724254) exercises unmodified Minecraft GUI rendering and colored-light probes with ONLY RGB Blocks in both client/server mods directories; do not mark this separate gate passed until the workflow completes.

## What the full ecosystem `.mrpack` actually means
The packaged `*complete-ecosystem.mrpack` is a **preassembled convenience test profile** that chooses to install compatible C&B, renderer/shader loaders and Complementary shaders **alongside** RGB Blocks. Its manifest declares those components `required` *within that particular modpack profile* so the launcher installs the tested combination. It does **not** turn them into runtime dependencies of the RGB Blocks JAR.

For standalone use, install only the **matching RGB Blocks .jar** in the appropriate Forge 1.20.1 or NeoForge 1.21.1 mods directory. For full optional sculpting and shader ecosystem use, import that version's .mrpack.
