# RGB Blocks v1.3.1 — ORIGINAL OWNER SOURCE FIRST (2026-11-18)

## Authority and access policy
The owner provided BOTH complete 26.1.2 original developer archives in the ChatGPT project:
- Fabric: `RGB-Blocks-1.3.1-Fabric-26.1.2-full-source.tar`, SHA-256 `ae5fffb7b37d7376f4e579491af878b7ed74fbe386b8691751e6d1c538bcb39c`.
- NeoForge: `RGB1.3.1 네오포지.zip`, SHA-256 `f267b09141811f3eeb64e8247fff1d08ed2e11fdbea6c5b165f52b93e31607e1`.

Actual inventory: Fabric 32 Java, NeoForge 31 Java, 233,629 main resource entries per loader, 233,627 common resources BYTE-IDENTICAL between loaders; only `rgbblocks.mixins.json` differs among common-path resources. Fabric has `src/client/resources/rgbblocks.client.mixins.json` which must NOT be discarded. Keep NeoForge unique `META-INF/neoforge.mods.toml`, Fabric `fabric.mod.json`.

From the user's exact original sources, an **~4 MB lossless canonical bundle** named `RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst` was created; its SHA-256 is `1aea93f67e0375ecea72c86a5a72add5488d43d87a6b058dbce93128f250d007`. The bundle contains the *unchanged* official original Fabric TAR plus `RGB-Blocks-1.3.1-OWNER-JAVA-and-BUILD-SOURCES.zip` (63 ORIGINAL Java files, loader metadata, palette, en_US). Inner source ZIP SHA-256 `420da2011167e9dac00b6404eba29043e9a342dd61c7c1fc4d4cd85662d64607`.

**Do not mistake this chat-generated archive for a GitHub repo file.** It is in the ChatGPT conversation. GitHub Actions CANNOT access ChatGPT uploads automatically; the bundle has **NOT** been uploaded to GitHub and must not be silently made public. The owner controls whether/where to register the canonical source bundle for GitHub CI (e.g. private artifact). Until then builds fail early. Do NOT fetch the author's own Modrinth or CurseForge release as a workaround. No original owner source is committed automatically.

## Source-first pipeline
- `rgb-blocks-compat/stage_owner_original.py` verifies both source archive hashes and stages exact author's Java and resources. `RGB_OWNER_CODE_ONLY=1` avoids expanding 233,629 assets when only auditing Java (fast). Full build expands assets once.
- `rgb-blocks-compat/build_mc1211_fabric.py` now automatically invokes the source stage and constructs its intermediate from the owner's actual Java and resource tree, NOT a Modrinth 1.3.1F JAR. No public original-JAR download remains in this builder. This intermediate feeds the Forge 1.20.1 and NeoForge 1.21.1 native ports.
- There are **10 explicitly named** existing port-specific compatibility/bugfix overlays from the legacy `recovered/fabric` tree, preserved so original code cannot silently reverse fixes developed through five sessions. Track them in generated `port-work/mc1211-fabric/owner-source-overlays.json`. This is a **TEMPORARY migration bridge**, not a claim that all port code is already purely original-source-based. These files must be individually rebased onto the authentic owner versions and then the override list progressively removed.
- `rgb-blocks-compat/build_mc1211_neoforge.py` gets NeoForge's original loader mixin plugin from staged original NeoForge source.
- `rgb-blocks-compat/recover_author_sources.py` is retired to a code-only original-source staging shim. No JAR decompilation or published original-source download.
- `rgb-blocks-compat/verify_baseline_assets.py` checks original local palette SHA, locale SHA, PNG count 33,377 and 50,061 blockstates directly.
- Source-recovery CI MUST NEVER automatically commit original Java source files to the public GitHub repository.

## CI staging
The source stage looks for `rgb-blocks-compat/owner-archives/RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.tar.zst` by default, OR accepts environment variable `RGB_OWNER_SOURCE_COMPLETE` with a pre-provisioned path. A future GitHub CI job can retrieve this artifact from a private owner-approved source, verify its pinned SHA, and stage it. The staged source directory and the bundle must remain .gitignored.

The old `#44115007273` actual gameplay result predates this rebase. **NEITHER Forge 1.20.1 nor NeoForge 1.21.1 has passed real dual-client or shader acceptance on this new source-first commit yet**. Do not announce a release or interpret previous green tests as validating this source snapshot.

## Next required implementation sequence
1. Provision the exact source bundle for GitHub CI with owner's permission, without counting as RGB Blocks public Modrinth downloads.
2. Run original-source staging + generated project builds, repair any Java API compilation breakage introduced by replacing decompiled baselines.
3. Rebase each temporary compatibility overlay onto the matching owner original file using precise semantic patch logic, preserve prior real-world fixes and source-sha provenance.
4. Run Forge 1.20.1 and NeoForge 1.21.1 LIVE, STRESS, CHAOS, dedicated restart, two real clients, shaders, C&B and no-ghost-light oracles on one final commit.
5. Only then assemble both native port JARs, code ZIPs, and pinned ecosystems; public release remains owner's decision.

**Do not run `build_mc1211_fabric.py` with a legacy recovered-only tree or reintroduce the published JAR download.**


## 2026-11-18 source-first follow-up (actual local tests and executable CI bridge)

**Verified on the uploaded owner's actual files, without any network calls:**
- Unpacked the exact SHA-pinned canonical archive and staged **all** 233,629 main resources from the Fabric source TAR. Loader-specific Fabric metadata occupies 2 entries; **233,627** byte-matching RGB common resources extracted. **32** original Fabric Java and **31** original NeoForge Java also staged, plus original client Mixin config.
- Counted **50,061 RGB blockstates**, **50,061 block models**, **50,063 item models** (50,061 blocks + 2 tools) and **33,377 original textures** from real extracted files; original palette and en_US SHA-256 matched exactly.
- File-by-file extraction of 233k tiny assets exceeded one limited run after 162,356 files; resuming from partial directory completed successfully. The actual GitHub staging script now contains bound SHA-based checkpoint, interruption resume, and completed-tree reuse (`aa8e80e`).
- Found and fixed a concrete source migration crash in `build_mc1211_fabric.py`: author's original `RGBRuntime.java` puts **StatePayload and BakePayload before RuntimeData**, unlike the formerly decompiled version. The old builder deleted the wrong region via source-order indexing. The new migration uses a class-brace scan, retains both packets, converts the author's actual `RuntimeData.TYPE` storage lookup to `SavedData.Factory`, and asserts packets remain intact (`2e11cf1`, `9495a36`). Verified the exact original class matching and source boundaries locally, and added AST-extracted runtime migration test `verify_owner_runtime_migration.py` (`a3137ab`) to CI.
- Added an opt-in SHA-pinned **unpublished GitHub draft Release** original-source acquisition path to `stage_owner_original.py` (`6a8793c`). This cannot access RGB Blocks on Modrinth or CurseForge. Both main LIVE/STRESS/CHAOS workflows require valid owner source **before Gradle or Minecraft starts**, with the authenticated repo token visible only to the author-source fetch step (`7efc27b`, `6c55918`). Do not expose or upload original source to public Actions artifacts.
- Added `rgb-blocks-compat/provision_original_source_private_once.ps1`, a Windows GitHub CLI one-time setup script that checks exact SHA, refuses public release, creates/updates a DRAFT release and dispatches BOTH rigorous native real-game matrices (`7d14b47`). The original source bundle is still in ChatGPT user-uploaded assets, **NOT yet in the unpublished GitHub draft**.
- Latest real GitHub source-gated runs [LIVE/STRESS #44133654079](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44133654079) and [CHAOS #44133647577](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44133647577) stopped in the early author-source phase: GitHub Release lookup returned **HTTP 404** because the original-source draft had not been uploaded. These are **blocked by input provisioning, not runtime RGB game regressions**. No Modrinth source retrieval was attempted.
- **Still NOT established**: a native Forge 1.20.1 or NeoForge 1.21.1 JAR built from this new original-source-first snapshot, then passing all true two-client C&B light, remote mesh and shader regressions. Previous green runs on the decompiled baseline DO NOT count for this source snapshot.

**Next:** Provision the exact ChatGPT-generated 4MB canonical archive once into the **unpublished draft** with `provision_original_source_private_once.ps1` on owner's Windows machine; this starts the two source-verified CI matrices automatically. Then handle any REAL compile/game failures, rebase 10 temporary overlays file by file, and rerun validation before packaging public builds.

