# Image Order Studio v0.5.2 — Original-byte order-only upload

By 2bornot. Android 8.0+, offline, no ads.

## One workflow

Open Image Order Studio from a compatible photo attachment action, choose original photos in the order you want, and tap Done. The app returns the selected images with their **original bytes, original MIME types and original filenames**. The numbers appear only on the selector UI.

When started directly, choose pictures and the Android Share sheet opens with the unmodified originals in the selected order. The app does not stamp numbers, resize, recompress, combine, edit EXIF, or convert formats as part of an upload.

The order contract is explicit: the app builds Android ClipData in selection order and uses read-granted `content://` URIs. The private original-byte copies are readable via a small read-only provider exposing original filenames and MIME types. The originals on the device are not modified.

**Platform boundary:** Third-party sites/apps may rearrange received files; this app cannot force a receiver to maintain list order when the receiver ignores it. System Photo Picker is managed by Android and cannot be globally replaced by an ordinary APK.

Gallery + picker intent integrations remain. No AccessibilityService is used, to avoid sideload protection blocking.

## Development

- Package `com.twobornot.imageorder`
- Stable signing certificate reused from versions 0.2–0.5.1
- `versionCode 8`, `versionName 0.5.2`
- GitHub release tag: `image-order-beta`
- CI checks original-byte delivery, no rendering in upload code, gallery, permissions, signature, and install.
