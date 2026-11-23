# Image Order Studio / 이미지 순서 스튜디오 v0.5.4

**Immutable goal:** one natural Android gallery for image upload across apps and web sites, returning the exact original photographs in the user's selection order. The global picker invocation and receiver-side order guarantee remain open engineering objectives; no app-specific workaround is considered completion.

Android 8+ · `com.twobornot.imageorder` · by 2bornot · no ads · no network permission.

## Original photos, zero edits

Compatible `ACTION_GET_CONTENT` and `ACTION_PICK` requests launch the app's gallery, where numbered overlays show **tap order only**. The result is a grantable `ClipData` containing the **original MediaStore URIs, in that order**. No compression, modification, stamping, merge, renaming or copy of photos takes place in the primary upload path.

The launcher opens the same gallery; Done opens the normal Android sharing sheet for original photos.

For `ACTION_OPEN_DOCUMENT` callers, Android Files can now display Image Order Studio as an independent read-only source showing **all accessible original photos, native albums, recents, search and thumbnails**, directly backed by MediaStore (not the old numbered export batches). Opening a document streams the original MediaStore bytes, with the original filename and MIME type. Grant photo access in the app gallery first if the Android Files source appears empty. Android's own DocumentsUI controls ordering within SAF; our native gallery controls tap ordering in supported GET_CONTENT/PICK callers.

**Android platform boundary:** An ordinary sideloaded APK cannot globally replace the system Photo Picker `ACTION_PICK_IMAGES` or intercept every custom app uploader. Neither this version nor older versions should be described as achieving that fixed goal.

## Build and release

Gradle 8.11.1, Java 17, compileSdk 36, targetSdk 35. GitHub dev/release CI tests order, image types, SAF IDs, Android emulator original bytes, signed installation and public release integrity. Signed v0.5.4 beta is published only after all release gates pass. Signing identity must remain unchanged.
