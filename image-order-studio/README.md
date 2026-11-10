# Image Order Studio · Android 0.1.1 (beta source)

Developer: **2bornot** · Android 8.0+ · Korean and English UI

**Problem:** Image pickers, apps and websites may reorder attachment arrays independently of how a person selected them. The sequence is explicitly created inside this app by tapping imported images in the desired order. Filesystem order, file titles and content-type extensions never determine the logical sequence.

## What is implemented

1. Import multiple local images using Android Storage Access Framework; also receive images from other apps' share sheets. The incoming order is **not** treated as selection order.
2. Tap thumbnails in the app to assign the authoritative selection rank 1, 2, 3…; tap again to deselect. A badge shows the rank. Move selected entries earlier/later and deselect using **Edit order**.
3. Persist library copies, UUIDs, original filenames and ranks in app-private storage via atomic metadata writes, including across restarts.
4. **Share numbered:** generates PNGs with a *visible* `ORDER 0001 / 0005` banner and numbered filenames; share in correct order via Android's `ACTION_SEND_MULTIPLE` and `ClipData`.
5. **Save to folder:** select a SAF folder, then write numbered PNGs there for use with website file input controls. The rendered sequence banner survives site-side sorting.
6. **Combine to one:** create a single tall PNG with ordered numbered sections when total dimensions are safe; avoids multi-file reordering entirely. An oversized set fails clearly rather than silently omitting images.
7. **Share originals:** shares the unmodified app-private copies in ordered `EXTRA_STREAM`, useful when another app honors the list. This is *not* a universal ordering guarantee.
8. No INTERNET permission, advertising SDKs, logins, broad media library access, analytics or background uploading.

## Security / integrity design

- No renaming of the originals on the user's device. App works on copies.
- A private UUID is the identity of each image; filenames and MIME types do not define sequence.
- External image bytes are copied via ContentResolver and are never uploaded by the app itself.
- Exported numbered PNGs lose the original EXIF metadata. The original sharing mode preserves bytes.
- Larger imports such as 166 images are handled one image at a time for export rather than constructing a single gigantic canvas.

## Known beta limitations

- The order must be assigned **inside Image Order Studio**, after importing photos. The system file picker's selection order is never assumed to be reliable.
- Third-party sites can reorder the *position* of attachments; the `ORDER n / total` banner preserves the intended logical order, not the actual HTML attachment position. A **single combined image** is the strongest one-file option for smaller batches.
- The combined mode limits 12 images and 14,000 pixels in height, due to Android memory and upload constraints.
- Sequence badges are burned into **exported PNGs**, never into the originals. Numbered outputs may be downsampled when source dimensions exceed memory-safe limits.
- Supported render formats depend on the Android platform image decoders. An unsupported image causes a visible export error; the entire batch cannot be silently truncated.
- Static image EXIF orientation is applied on Android 8+ during export. Thumbnails may still appear unrotated; GIF animations export the first frame.
- There is not yet a built-in web browser / automatic web-login uploader. Exported files or Android Sharesheet are used.
- Debug builds are signed by Android's standard *debug* signing identity; release distribution requires a durable developer-owned release signing key. No release has been published by this source package.

## Build (GitHub Actions)

The workflow `.github/workflows/image-order-ci.yml` expects the project files under `image-order-studio/` on a separate branch named `image-order-studio/dev` in `sangkukzoa-ctrl/assets`. The repository default branch, previous apps, signing credentials, and existing release tags are untouched.

The workflow runs the pure Java ledger regression test, installs SDK 36, builds `assembleDebug` and `assembleRelease`, and publishes the APKs as private Actions artifacts for testing. It **does not** publish a GitHub Release; beta publication should follow functional QA and signing.

To build from an independent repository root, move `image-order-studio/*` to root and change the workflow working directory/paths accordingly.

## QA acceptance matrix

- Tap B→A→D→C→E after importing A,B,C,D,E => exactly B,A,D,C,E in the ledger and in export labels.
- Re-import images named `1.jpg`, `1.png`, `1.webp` => names never determine sequence.
- Restart the app => imported copies and numbered ranks remain.
- Import 166 photos => assign ranks and use numbered export; never silently cap the count.
- Send from another gallery app => images appear unranked; reselect within the app.
- Save numbered files to a folder => each file contains both an order-prefixed basename and a visible sequence banner.
- Try a 13-image or extremely tall combined export => clear error; no incomplete output accepted.
- Cancel SAF folder/picker => no changes to the sequence.
- Reorder or deselect one image => subsequent ranks update contiguously and persist.
- Upload exported files to several unrelated sites, verify whether they reorder positions, and whether the sequence banner allows the intended order to be unambiguously reconstructed.

## Developer-build commands

```sh
javac -d build/testclasses app/src/main/java/com/twobornot/imageorder/SequenceLedger.java tests/SequenceLedgerTest.java
java -cp build/testclasses SequenceLedgerTest
gradle --no-daemon :app:assembleDebug :app:assembleRelease
```
