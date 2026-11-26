# Development environment — actual reproducible Android build

## Real verified baseline
Latest public signed release v1.3.1 was produced by GitHub Actions and marked success:
https://github.com/sangkukzoa-ctrl/assets/actions/runs/42159936750

Source ZIP is official asset:
https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1-Source.zip

It was SHA256-verified and materialized as text files in this branch under project/ (see materialization workflow run for proof). If future Chat LLM has GitHub read access, operate on this tree; do not reverse-engineer APK or guess from prior chat.

## Pinned environment (from actual source/workflow)
- Runner: ubuntu-latest (GitHub-hosted). No user-side Android Studio or SDK required.
- Android Gradle Plugin 8.10.1
- Gradle 8.11.1 (action setup-gradle@v4; wrapper distribution 8.11.1)
- Temurin JDK 17; Java source/target compatibility VERSION_17
- Android compileSdk 36; targetSdk 36; minSdk 26 (Android 8.0)
- Android SDK platform android-36; build-tools 36.0.0
- dependency: com.tom-roush:pdfbox-android:2.0.27.0 for original JPEG extraction; rasterization from built-in PdfRenderer.
- GitHub Actions artifacts must be retrieved explicitly after confirmed success.

## Safe nonpublishing continuous integration for HANDOFF branch
Workflow: .github/workflows/pdfimage-handoff-ci.yml on branch pdfimage-handoff/2026-11-26. It runs:
1. Checkout
2. Set up Java 17
3. Install Android SDK platform 36 and build-tools 36.0.0
4. Gradle 8.11.1
5. Plain Java tests: javac L10n.java + PageSelection.java + PageSelectionTest.java, then run class
6. Gradle debug APK + unsigned release APK + unsigned release AAB
7. Upload artifacts "JPTI-Handoff-CI-Debug-APK" and "JPTI-Handoff-CI-Unsigned"

It does **not** sign production binaries, create tags, or publish GitHub releases. This distinction is intentional. The handoff requires no new functional work. If you cannot trigger Actions from ordinary Chat LLM, you may give the user a GitHub Actions link to run, or commit an approved change to trigger CI when write permission exists.

## Local alternative (only if Chat LLM environment actually has execution support)
At the project directory, not at repository root:
  gradle --no-daemon :app:assembleDebug :app:assembleRelease :app:bundleRelease --stacktrace

Page-range unit test:
  mkdir -p /tmp/jpti-tests
  javac -d /tmp/jpti-tests app/src/main/java/com/hsiwan/pdfimage/L10n.java app/src/main/java/com/hsiwan/pdfimage/PageSelection.java tests/PageSelectionTest.java
  java -cp /tmp/jpti-tests PageSelectionTest

Or from repository root:
  gradle --no-daemon -p project :app:assembleDebug :app:assembleRelease :app:bundleRelease --stacktrace

Expected outputs relative to project:
  app/build/outputs/apk/debug/app-debug.apk (debug signed install test)
  app/build/outputs/apk/release/app-release-unsigned.apk (not installable as-is)
  app/build/outputs/bundle/release/app-release.aab (not an APK; unsigned)
Never describe these as production updates.

## GitHub structure and hazards
- Github repository: sangkukzoa-ctrl/assets (contains unrelated content).
- main is an unrelated assets branch and must remain untouched.
- Last published release branch: pdfimage-ci/v1.3.1. This contains encrypted/compressed payload, release signing choreography and is NOT a clean working source root. Its workflow is hard-coded to refuse redeploying v1.3.1.
- Clean handoff working branch: pdfimage-handoff/2026-11-26; **all readable actual source in project/**.
- Handoff documents: HANDOFF/. Machine-readable state: HANDOFF/STATE.json. Tasks: HANDOFF/TASKS.md.
- Future development should use isolated successor branch based on the handoff branch (or a distinct dedicated repo when available), never changing unrelated assets/main.
- Branch creation, file push, Actions run and artifact download must be verified from actual tool responses. GitHub connector may be read-only inside ChatLLM; never claim actions if not actually executed.
- Release and signing are never automatic side effects of a development commit.
