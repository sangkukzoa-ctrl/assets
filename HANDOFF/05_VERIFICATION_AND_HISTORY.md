# Verified history, uncertainty boundaries and future quality notes

## Timeline of this app
- 2026-11-05: user requested an Android standalone PDF-to-PNG/JPG app after encountering ad-heavy/paid converters. Original v1.0.0 source prepared; initial environment had no local Android SDK.
- 2026-11-05: GitHub Actions introduced, allowing remote compilation with Android SDK. Focus refined to ultra-simple/offline/batch conversion; PdfRenderer and embedded JPEG extraction as two separate modes.
- 2026-11-05: v1.2.0 Android APK and AAB built successfully by GitHub Actions. Some actual compile errors were fixed in CI.
- 2026-11-06: v1.3.0 published signed bilingual GitHub Release; first public APK.
- 2026-11-06: v1.3.1 published under final name "Just PDF to Image", credited to "2bornot"; Korean/English UI; signed with production identity from v1.3.0; success in https://github.com/sangkukzoa-ctrl/assets/actions/runs/42159936750.
- Play Store ($25 developer fee) and Galaxy Store (seller eligibility barriers reported by user) were set aside. Github Releases + Naver blog became distribution path.
- 2026-11-26: this handoff only; no new feature/release request. Official v1.3.1 Source.zip restored to readable project/ in separate GitHub branch and compared against published SHA256.

## Confirmed from actual v1.3.1 Java source
- Android API: min 26, target/compile 36, appId com.hsiwan.pdfimage, versionCode 5.
- MainActivity ACTION_OPEN_DOCUMENT multiple PDFs and ACTION_OPEN_DOCUMENT_TREE output, no broad storage permission.
- Single-thread ExecutorService with AtomicBoolean cancellation; no background Service.
- Rendering uses Android PdfRenderer; PDF copying to app-private cache fallback for non-seekable sources; bitmap ~18MP pixel cap; PNG/JPEG encode, white base.
- JPEG extraction from only single DCTDecode filter XObjects in page resources using PDFBox-Android; nested form traversal; raw bytes copied directly. Does not process inline, other-filter or non-JPEG images, and not full page raster.
- Files named based on source PDF; multi-image per PDF folder; duplicate names get suffix; output files created via DocumentsContract.
- Localizer uses inline L10n.t(ko,en) plus launcher name resources.
- Source has an in-app privacy notice; no INTERNET permission in Manifest.

## Confirmed historical validation
- Successful GitHub Actions Java PageSelection unit tests and Gradle assembleRelease/bundleRelease, resulting signed APK/AAB published.
- Official release .apk, .aab, source ZIP and checksum file are live on GitHub.
- This handoff source was downloaded directly from release and SHA256 checked in GitHub Actions. See root workflow run.

## Not confirmed, do not embellish
- Comprehensive manual testing on dozens of real Android devices or actual user reports is NOT evidenced by GitHub success.
- Stress tests across 100+ mixed PDFs, cloud SAF providers, locked PDFs, low-memory devices, and activity interruptions are NOT recorded as passing.
- A prior attempt to deliver twenty sample "PDFs" was reported by the user as thumbnails/PNGs rather than usable PDF samples; **do not present that pack as a verified test suite**. The user said actual work PDFs were available for their own trials.
- Do not treat the source README mention of project/.github/workflows/build.yml as proof that such a file exists. The published ZIP contains project/.github/workflows/pdfimage-release-v131.yml; handoff's root safe CI is .github/workflows/pdfimage-handoff-ci.yml.
- Do not claim all PDFs can be losslessly extracted or PNG output equals original scans.
- Do not claim access to the private signing key through this public repo or Chat LLM.
- No currently approved new task; lists of possible test areas are reference notes only.

## Optional risk areas ONLY WHEN USER REQUESTS DEVELOPMENT
- Large page cap (~18 MP) compromises user-requested "300 DPI" for oversized pages; memory/performance tradeoff.
- Multiple documents may require file provider robustness; own cancellation and partial write cleanup.
- Original JPEG extraction limit (DCTDecode single filter) vs broader PDF image object diversity; color space considerations.
- Background interruption: existing single Activity and Executor is not a durable job scheduler.
- Existing code handles errors but automated tests mainly cover page ranges.
- App naming, Korean/English strings, accessible UI controls, and release signing continuity.
These are **not** automatically approved feature requests.

## Product/market interpretation
The user's "publish first, learn from reports" approach is deliberate. Don't hold release indefinitely for imaginary exhaustive validation; likewise don't claim tests that never ran. Product promise is no ads, no paywalls, no arbitrary constraints, not perfect treatment of all exotic PDFs.
