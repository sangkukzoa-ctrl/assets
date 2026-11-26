# Image Order / 이미지 순서 (공개 v0.5.4 · 개발 v0.5.5)

**Immutable goal:** one natural Android gallery for image upload across apps and web sites, returning the exact original photographs in the user's selection order. The global picker invocation and receiver-side order guarantee remain open engineering objectives; no app-specific workaround is considered completion.

Android 8+ · `com.twobornot.imageorder` · by 2bornot · no ads · no network permission.

## Original photos, zero edits

Compatible `ACTION_GET_CONTENT` (including generic `*/*` upload requests) and `ACTION_PICK` requests launch the app's gallery, where numbered overlays show **tap order only**. The result is a grantable `ClipData` containing the **original MediaStore URIs, in that order**. No compression, modification, stamping, merge, renaming or copy of photos takes place in the primary upload path.

The launcher opens the same gallery; Done opens the normal Android sharing sheet for original photos.

For `ACTION_OPEN_DOCUMENT` callers, Android Files can now display Image Order as an independent read-only source showing **all accessible original photos, native albums, recents, search and thumbnails**, directly backed by MediaStore (not the old numbered export batches). Opening a document streams the original MediaStore bytes, with the original filename and MIME type. Grant photo access in the app gallery first if the Android Files source appears empty. Android's own DocumentsUI controls ordering within SAF; our native gallery controls tap ordering in supported GET_CONTENT/PICK callers.

**Android platform boundary:** An ordinary sideloaded APK cannot globally replace the system Photo Picker `ACTION_PICK_IMAGES` or intercept every custom app uploader. Neither this version nor older versions should be described as achieving that fixed goal.

## Build and release

Gradle 8.11.1, Java 17, compileSdk 36, targetSdk 35. GitHub dev/release CI tests order, image types, SAF IDs, Android emulator original bytes, signed installation and public release integrity. Signed v0.5.4 beta is published only after all release gates pass. Signing identity must remain unchanged.


### Independent external-app URI permission regression (v0.5.5)

The included `:externalcaller` is a **separate appId/UID** with no READ_MEDIA_IMAGES.
It tests `GET_CONTENT` for image-only and wildcard upload requests, uses UI Automator
to tap three actual target-owned gallery images, and verifies only selected URI
read grants, exact selection ordering, MIME, original names and SHA-256 contents.
The target's media fixture is in `app/src/debug` only and is absent from signed
release APK. Run `:app:connectedDebugAndroidTest`, reinstall `:app` debug and
then `:externalcaller:connectedDebugAndroidTest` on one Android 35 emulator.

### Official name and development handoff

Official name: **Image Order**. Current development branch: `image-order/dev-v2`. Legacy project path, app ID and public v0.5.4 APK URL are preserved for backward compatibility.

### Verified real-browser attachment route (development v0.5.5)

On the Android 14/15 Google Play emulator images, installed Chrome 113.0.5672.136 and 124.0.6367.219 passed both image-only and generic HTML multiple file input tests. Five original PNG/JPEG/WebP images were selected in the order 5→2→4→1→3, sent by Chrome using real HTTP multipart, and checked for filename, MIME, order, and SHA-256 on the receiving server. [Four real Chrome checks](https://github.com/sangkukzoa-ctrl/assets/actions/runs/45780368542). [Android API 26–36 independent caller regression](https://github.com/sangkukzoa-ctrl/assets/actions/runs/45664554476).

When Chrome opens the system Photo Picker, use **Browse** (or the overflow menu containing Browse), then open the navigation drawer in Files. Select the separate **Open Image Order (Files)** app-launch action if the Files source and app appear merged. Tapping only the provider name opens SAF, which does not promise selection order. A generic file chooser may first require **Media / Media picker / Files**. Actual labels vary with the device and Android version.

한국어: 웹사이트 사진 첨부 → 시스템 사진 선택창의 더보기/찾아보기 → 파일 앱 탐색 메뉴 → Image Order (Files)의 앱 실행 버튼 → 원하는 순서대로 사진 선택 → 완료. 일반 파일 첨부는 앞에서 Media/Media picker/Files를 선택할 수 있습니다. 공급자 이름만 누르는 SAF 경로는 순서 지정용 갤러리와 다릅니다.

This is a supported real-world route, not automatic replacement of every uploader. These results are emulator results for the listed versions; current Chrome releases, Samsung Internet, and direct ACTION_PICK_IMAGES callers are separate compatibility targets. Public v0.5.4 is unchanged.
