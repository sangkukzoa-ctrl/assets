# RGB Blocks 1.3.1 — ready-to-run Windows native server ZIPs (2026-11-17)

## User-supplied real current server BAT
```bat
@echo off
REM Forge requires a configured set of both JVM and program arguments.
REM Add custom JVM arguments to the user_jvm_args.txt
REM Add custom program arguments {such as nogui} to this file in the next line before the %* or
REM  pass them to this script directly
java @user_jvm_args.txt @libraries/net/minecraftforge/forge/1.20.1-47.4.20/win_args.txt %*
pause
```
This BAT proves the existing server is **Minecraft 1.20.1 Forge 47.4.20** and uses the system `java` command on PATH. It cannot reveal the actual installed Java executable/version nor the JVM arguments in the user's separate `user_jvm_args.txt`. Do not assume which JDK is installed.

## Tested original 1.3.1 building ecosystem EXACT versions

| Component | Forge 1.20.1 | NeoForge 1.21.1 |
|---|---|---|
| Native loader | **Forge 47.4.28** | **NeoForge 21.1.265** |
| Java major | **17** | **21** |
| RGB Blocks | Native 1.3.1 backport | Native 1.3.1 backport |
| Chisels & Bits (optional) | **20.1.20** | **21.1.32** |
| Client renderer (optional) | **Embeddium 0.3.31** | **Sodium 0.6.13** |
| Shader integration (optional, client ONLY) | **Oculus 1.8.0** | **Iris 1.8.12** |
| Shader (optional, client ONLY) | **Complementary Reimagined r5.9.3** | Same r5.9.3 |

No hard third-party mod dependency; default `mods/` contains ONE native RGB Blocks JAR. Only install other mods if the building ecosystem needs them. Full independent GUI+dedicated-world C&B-free tests of BOTH loaders passed: https://github.com/sangkukzoa-ctrl/assets/actions/runs/44045724254

## Separate standalone downloadable WINDOWS server ZIPs

- **Forge 1.20.1 / Forge 47.4.28, Windows x64 + portable Temurin JRE 17:**
  https://github.com/sangkukzoa-ctrl/assets/actions/runs/44072353473/artifacts/14323930414
  - Inner ZIP: `RGBBlocks-1.3.1-MC1.20.1-Forge-47.4.28-WINDOWS-READY-SERVER.zip`
  - 199,954,320 bytes; SHA256 `e672790253d6bf24560773e85736eefe29769b050ebeeb6b4d2f5aabf3ce4046`
  - All 96 installed native Forge Java libraries, correct `libraries/net/minecraftforge/forge/1.20.1-47.4.28/win_args.txt`, owner-verified JAR, verified Eclipse Adoptium JRE 17.0.21, defaults server port 25566.
- **NeoForge 1.21.1 / NeoForge 21.1.265, Windows x64 + portable Temurin JRE 21:**
  https://github.com/sangkukzoa-ctrl/assets/actions/runs/44072353473/artifacts/14323177543
  - Inner ZIP: `RGBBlocks-1.3.1-MC1.21.1-NeoForge-21.1.265-WINDOWS-READY-SERVER.zip`
  - 228,899,683 bytes; SHA256 `51aca3073a8216df1a42b4b3b7d8113f6d574be8f4a864d73846f222fb3891ff`
  - All 94 installed native NeoForge Java libraries, correct `libraries/net/neoforged/neoforge/21.1.265/win_args.txt`, owner-verified JAR, verified Eclipse Adoptium JRE 21.0.13, defaults server port 25567.

These are ZIP **inside** the GitHub Actions artifact ZIP downloaded using the above links. Unzip both levels, then double-click **`run.bat`** in the extracted server root.

New `run.bat` uses **the bundled portable Windows Java** (`runtime/java/bin/java.exe`) and same native `@user_jvm_args.txt @libraries/.../win_args.txt` structure as the user's existing BAT, with `nogui`. No system Java or PATH modifications required; the two supported Java major versions do not conflict. To force existing system Java, run **`run-system-java.bat`**; to inspect paths and versions, run **`check-java.bat`**.

User's existing server likely already uses the default port 25565; these packages default to **25566** and **25567** respectively. Edit `server.properties` if desired. Each includes `user_jvm_args.txt` default `-Xmx4G`, `eula.txt`, `mods/` with only RGB, official installed native `libraries/`, Java JRE, and setup/install logs.

## Modpack import fails? Direct optional installation without .mrpack

Each ready server ZIP contains:
- **`INSTALL-OPTIONAL-CNB-SERVER.bat`**: downloads the exact officially hosted, SHA512-verified C&B 20.1.20 (Forge) or 21.1.32 (NeoForge) into this server's `mods/`. Optional; never needed for RGB Blocks itself.
- **`DOWNLOAD-CLIENT-EXTRAS-NO-MRPACK.bat`**: downloads the matching C&B, Sodium/Iris or Embeddium/Oculus and Complementary shader using creators' official links and SHA512 validation into `CLIENT_ADDONS/mods/` and `CLIENT_ADDONS/shaderpacks/`. Copy downloaded files into the matching Minecraft CLIENT; never put renderer or shader mods in a dedicated server.
- **`DIRECT_CLIENT_MOD_DOWNLOAD_LINKS.txt`**: raw exact download links, checksums and which side a mod runs on.
- **`REMOVE-OPTIONAL-CNB-SERVER.bat`** to move optional C&B out of the server's mods folder.

Upstream third-party content is **not rehosted** in server ZIP; only tested owner RGB JAR, native Forge/NeoForge server libraries, and portable Eclipse Temurin runtime are bundled. The Modrinth .mrpack is completely unnecessary to install these ready servers.

## Build and verification evidence
- [Two separate preinstalled server packages, BOTH CI jobs SUCCESS](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44072353473), commit `998c3de71f03a093f214b1f9008afbccf995d682`. All native Windows args installed and checked, official Temurin Windows JRE verified by upstream SHA256, full ZIP CRC verified, only one RGB jar in root mods. Actual owner RGB binaries are bit-identical with individually verified native release packages.
- [True native Windows runner smoke tests](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44072992392): NeoForge 1.21.1 JRE 21 first boot, RGB block placement, world save and SAME-world restart PASS. Forge JRE 17 started, ran commands and cleanly stopped, but initial strict CI string-matching of palette output failed; latest smoke source `deed7ebb1954cdcdc954eea85c229f5e531adf99` reruns exact registry and RGB markers [workflow #44073605384](https://github.com/sangkukzoa-ctrl/assets/actions/runs/44073605384), result initially pending.
- Windows packaging and optional downloader scripts: `rgb-blocks-compat/build_windows_ready_server.py` and `.github/workflows/rgb-blocks-two-windows-ready-servers.yml`; Windows real test `rgb-blocks-compat/test_windows_ready_server.py`. This packaging does **not modify** the already approved production Minecraft mod binaries.

