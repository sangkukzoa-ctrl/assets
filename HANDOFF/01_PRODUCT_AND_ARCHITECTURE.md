# Product contract and implementation architecture

## Identity, positioning, audience
Just PDF to Image — by **2bornot**. Korean/English native Android utility. User's core motivation: frequent international purchase/customs documents (invoices, receipts) often need to become image files, but competing apps add ads, subscriptions, registration or unnecessary tools. Product model: LosslessCut/JPEGView-like, extreme single-purpose productivity. A tool should remove work, not add another process. **Free, offline, no ads, no IAP, no watermark, no tracking, no conversion limits, no accounts.** This is not OCR, image editing, scanning, PDF annotation, PDF merge/split, cloud sync, or a general file manager.

Brand title in app launcher and app UI is the same Korean/English: **Just PDF to Image**. Subtitle and controls are localized using L10n.t(ko,en); ko locale displays Korean, other locales English. Developer display **2bornot**. Official slogans: "PDF를 이미지로. 그게 전부입니다." and "PDF to images. Nothing else."

## Confirmed source tree (open files in project/)
- project/app/build.gradle: Android application, namespace/applicationId com.hsiwan.pdfimage, minSdk 26, target/compileSdk 36, versionCode 5, versionName 1.3.1, Java 17; PDFBox-Android 2.0.27.0.
- project/build.gradle: Android Gradle Plugin 8.10.1.
- project/settings.gradle: rootProject.name PDFImageOffline; app module; Google Maven, Maven Central, plugin portal.
- project/gradle/wrapper/gradle-wrapper.properties: Gradle 8.11.1.
- project/app/src/main/AndroidManifest.xml: single MainActivity launcher, strings label; no INTERNET and no MANAGE_EXTERNAL_STORAGE declarations, android:allowBackup false.
- project/app/src/main/java/com/hsiwan/pdfimage/MainActivity.java: programmatic Android UI; PDF multipicker, SAF output folder, render/extraction selection, page range, DPI, JPEG quality, progress, cancellation, localized status/error text and in-app privacy notice. Single worker executor, UI posted via runOnUiThread.
- project/app/src/main/java/com/hsiwan/pdfimage/PdfConversionEngine.java: normal PDF page rasterizer and result/error collection.
- project/app/src/main/java/com/hsiwan/pdfimage/OriginalJpegExtractor.java: optional embedded DCTDecode JPEG stream extraction, NOT a whole-page renderer.
- project/app/src/main/java/com/hsiwan/pdfimage/DocumentStorage.java: SAF create-only output, PDF-based file/folder naming and collision avoidance.
- project/app/src/main/java/com/hsiwan/pdfimage/PageSelection.java: parsing ranges, sorted deduped 0-based page indices internally.
- project/app/src/main/java/com/hsiwan/pdfimage/L10n.java: Korean/English fallback based on device language.
- project/tests/PageSelectionTest.java: plain Java unit tests; no JUnit runtime needed.
- project/app/src/main/res/values*/strings.xml: launcher app name; project/docs/* privacy statement; project/LICENSE MIT, project/NOTICE.md Apache-2.0 dependency notice; project/RELEASE_NOTES.md bilingual published notes.

## Core feature and precise output behavior
1. User selects one or more PDF documents with ACTION_OPEN_DOCUMENT and EXTRA_ALLOW_MULTIPLE. URI duplicate suppression in MainActivity.
2. User chooses destination with ACTION_OPEN_DOCUMENT_TREE and persistable URI permission (SAF). The app does not ask for blanket filesystem permission.
3. Render mode: PdfRenderer + Bitmap uses 150, 200 or 300 DPI. Internal bitmap pixels capped at about 18,000,000; white background; PNG lossless image compression or JPEG at quality 70..100. Rendering entire page retains text, page graphics and overlays displayed by renderer; PNG does NOT mean extracting original PDF image bytes.
4. Page range: blank=all; syntax e.g. "1,3-5", 1-based inclusive, sorted and deduplicated; invalid entries rejected. See PageSelection.java.
5. Storage: One-page PDF saves as base filename + extension in selected root folder. Multiple selected pages create a per-PDF subfolder "{name}_PNG" or "{name}_JPG" and sequential numbered filenames. DocumentStorage avoids overwriting names by adding " (n)".
6. Original JPEG mode: PDFBox-Android loads PDF through a temporary local cache file and enumerates page resource XObjects (including nested Forms). When an image stream has exactly one DCTDecode filter, it copies raw JPEG bytes without re-encoding. Multiple JPEGs can produce multiple outputs, per-document folder "{name}_OriginalJPEG"; 0 output when no matching JPEG. This mode intentionally ignores DPI and JPEG quality. **Does not support inline images, other image types, multi-filter JPEG streams, text/graphics/annotations or general-purpose pdfimages parity.**
7. Cancellation: AtomicBoolean checked between files, page steps and copying, UI progress permille; errors tracked per page/doc. Executor is not persistent background service. A document provider can fail or revoke access.

## Invariants for future changes
- Offline, privacy-preserving and accessible. Don't add network or unrelated features simply for marketing.
- Keep selected files private; don't upload user documents, especially customs/personal data.
- Keep source PDF and existing destination items untouched; create-only naming and best-effort cleanup of incomplete output on failure.
- Preserve Korean/English parity for every new user-visible string.
- Don't rename applicationId or release signing key unless user requests a breaking migration.
- Changes must be motivated by explicit user request or demonstrated bug. Current state: no new development task.
