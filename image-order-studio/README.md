# Image Order Studio v0.5.0 — Upload-first Android Gallery

Developer: **2bornot**. Android 8.0+, Korean/English, offline, no advertisements.

## Goal: one user workflow

Tap **Attach photo** in a site/app → when Android offers a third-party image picker, choose **Image Order Studio** → browse actual device **Photos / Albums** in its built-in dark gallery → tap images in intended order → **Done**. The app imports/marks images and returns a `content://` result with read grants to the calling activity. For single-image callers, it combines 2–12 images into one numbered page. No extra share sheet or manual filename numbering is required.

### Android boundaries (not hidden)

- A normal installed app cannot become Android's system Photo Picker (ACTION_PICK_IMAGES); that implementation is reserved for pre-installed/system applications. Third-party GET_CONTENT/PICK handlers are supported.
- For apps that hardcode a system picker, an **optional, user-enabled accessibility shortcut** can display a compact **Ordered upload** bubble when a recognized image/file picker appears. Tapping it opens the same gallery UI, then the app saves numbered images into Pictures/Image Order Studio and returns to the prior picker. **It cannot force the parent app to accept those images**; the user must select them from the original picker.
- Accessibility detection may be unavailable on protected surfaces, OEM apps, or apps that do not expose a discoverable UI. This feature does not silently rewrite third-party app upload parameters.
- The app does not intercept network requests, bypass app sandboxes, perform root-only hooks, or upload anything to a server.

## Implementation

- `NativeGalleryActivity` is a real MediaStore-based gallery with Photos and Albums views, direct touch ordering, cached thumbnails, and a single Done action. No dependence on Samsung Gallery internals, Chrome's file manager, or arbitrary ClipData ordering.
- Runtime photo access on Android 8–12 uses READ_EXTERNAL_STORAGE; Android 13 uses READ_MEDIA_IMAGES; Android 14+ also supports user-selected partial access. When denied, users can still invoke Android's system photo selection and explicitly tap images in order in the imported preview.
- `MainActivity` distinguishes external GET_CONTENT/PICK from the standalone/overlay use. Externally, it returns ordered, visible-numbered image URIs directly. In standalone/assist mode, it writes results into `Pictures/Image Order Studio` for selection from other apps.
- `UploadAssistService` is **off by default**. Activating it requires a clear in-app explanation and the user's explicit Android Accessibility authorization. It checks only on-device window events/visible upload-related button labels to display a small popup. It does not transmit, log, or upload other apps' text or photos.
- `OrderedDocumentsProvider`, FileProvider, GalleryMediaExporter, and Quick Settings tile remain supported integrations. No INTERNET permission.

## Build & release

Keep package ID `com.twobornot.imageorder`, signing identity and versionCode monotonic (v0.5.0, versionCode 6). Release artifact only after GitHub Android compile, signature verification, and install tests pass. Preserve stable public beta at `https://github.com/sangkukzoa-ctrl/assets/releases/tag/image-order-beta`.

## QA

Tests verify logical selection order independence, ordered gallery intent handling and static manifest permissions. Real Galaxy verification must check Samsung One UI, Android 14/15 partial photo access, and accessibility popup behavior in at least two native apps and two browser upload contexts. The platform's system-only picker restriction means universal interception must not be claimed.
