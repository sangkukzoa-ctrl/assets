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



## 2026-11-18 continued: actual owner-source conversion and native mixin repair

### Real author-source tests (NOT a Minecraft runtime pass)
- Applied the current exact Java RGBRuntime SavedData conversion function to the actual author Fabric 26.1.2 `RGBRuntime.java`, not the decompiled reference. Original 10,634 bytes -> 10,045 bytes; `RuntimeData.TYPE` migrated to `SavedData.Factory` while `StatePayload` and `BakePayload` Java bodies remained byte-identical (935 / 696 bytes). The previous test falsely counted the NEXT class's indentation as part of BakePayload; fixed strict braces-only payload-body comparison (commits `5680610`, `9a3df03`).
- Author Fabric source distributes mixins across **two** JSON configs (2 common plus 12 client); author NeoForge distributes same hooks in **one** JSON config (2 common plus 12 client). Earlier port builders silently discarded client config under Forge or duplicated injections under Neo. Fixed staging to register owner-client-only callbacks in the Fabric client config ONLY (`b978041`). Rebuilt native Forge unified config, carrying original C&B/RGB rendering hooks plus Forge-specific packet/Embeddium patches (`b2b29d9`), and NeoForge native unified original config plus explicitly ported Sodium06 and chunk hooks (`1f0d0a8`). Actual owner-config local inventory audit: each target has **11** client mixins, **0** duplicate applications.
- Removed obsolete `jpath.unlink()` leftover after original public JAR download was deleted. Without this, every source-first intermediate build would fail on an undefined variable at the end.
- Added a hard native Mixin-inventory checker (`verify_native_owner_mixin_inventory.py`, `9bf1b0d`), invoked by both LIVE/STRESS and CHAOS workflows BEFORE Java compilation (`100b8d1`, `732f234`). It checks all expected C&B/RGB hooks and actual Java mixin source files, exact original Neo plugin, client/server config counts, zero duplicates and no Fabric metadata.
- Source-stage resume previously reused files based solely on identical SIZE, allowing same-length corruption; it now compares actual bytes and verifies original Java/Mixin sentinel hashes and full 233,627-resource count when reusing a staged full-source cache (`a72be51`, `a4a4d45`).

### 233k resource performance + original-source invariants
- Initial 931MB owner resource tree is never modified by native generation. New `clone_owner_resources.py` (`42c9d88`) creates hardlinks for **immutable** palette/texture/blockstate/normal models and independent copies of mutable RGB glass JSON, `pack.mcmeta`, Fabric/Neo/Forge mixin metadata. The Fabric, Forge and NeoForge builders now use it (`5108aff`, `95f1643`, `9d4b6f8`), avoiding three full copies of 233k individual resource files without allowing altered port models to change the author's original.
- Independently tested with real filesystem writes to each generated glass/mixin/pack file at three port levels: original SHA-256 and intermediate SHA-256 remained unchanged, while normal immutable assets were preserved.
- Added fully no-network source-first static workflow. Actual Github CI **PASS**: [#44140411679](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44140411679), including Python compilation of all build/stage/audit tools, Java transform smoke test, non-Modrinth download guard, and the **real filesystem copy-on-write regression**. Run emitted `RGB_SOURCE_FIRST_OFFLINE_STATIC_PASS` and `RGB_OWNER_COW_RESOURCE_CLONE_PASS`. This is NOT a real game compile or gameplay test.
- To avoid 404 and waste from automatic real-game jobs until the exact author archive exists in GitHub private draft, gated the two main game workflows on `RGB_OWNER_SOURCE_READY` for push events while retaining strict explicit dispatch (`c3f1f93`, `9d92b38`). The one-time owner bootstrap script now sets this variable after SHA-verifying and uploading original source, then dispatches both native matrices (`60c921f`). The updated v2 bootstrap package is an attached ChatGPT conversation file, **not committed to the public repository**.
- Legacy upstream audit no longer runs on every source/doc change (`755c986`), preventing repeated irrelevant failures; still manually dispatchable.

### Hard status at this checkpoint
**STATIC SOURCE-GENERATOR CI: PASS.** **TRUE NATIVE Minecraft 1.20.1 Forge and 1.21.1 NeoForge COMPILATION + C&B/render/shader/2-client/chaos on author-original source: NOT YET RUN/NOT VERIFIED**; correct nonpublic author archive has not been registered in GitHub draft source storage. No new Modrinth RGB Blocks download performed. Original source remains authoritative, with 10 explicitly inventoried legacy port compatibility overlays still to reconcile individually. Public release remains HOLD.
