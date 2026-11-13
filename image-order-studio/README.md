# Image Order Studio v0.5.1 — Upload-first Android Gallery

Developer: **2bornot**. Android 8.0+, Korean/English, offline, no advertisements.

## Goal: one user workflow

Tap **Attach photo** in a site/app → when Android offers a third-party image picker, choose **Image Order Studio** → browse actual device **Photos / Albums** in its built-in dark gallery → tap images in intended order → **Done**. The app imports/marks images and returns a `content://` result with read grants to the calling activity. For single-image callers, it combines 2–12 images into one numbered page. No extra share sheet or manual filename numbering is required.

### Android boundaries (not hidden)

- A normal installed app cannot become Android's system Photo Picker (ACTION_PICK_IMAGES); that implementation is reserved for pre-installed/system applications. Third-party GET_CONTENT/PICK handlers are supported.
- The sideloaded 0.5.0 Accessibility shortcut has been **removed** in v0.5.1 after a Google Play Protect block. No system-wide interception is claimed. Apps using their own protected picker can still see ordered exports in the Image Order Studio Gallery album.
- Protected/system Photo Pickers cannot be replaced by ordinary third-party apps; their content cannot be intercepted. This app keeps its native gallery and standard share/GET_CONTENT/PICK workflows instead.
- The app does not intercept network requests, bypass app sandboxes, perform root-only hooks, or upload anything to a server.

## Implementation

- `NativeGalleryActivity` is a real MediaStore-based gallery with Photos and Albums views, direct touch ordering, cached thumbnails, and a single Done action. No dependence on Samsung Gallery internals, Chrome's file manager, or arbitrary ClipData ordering.
- Runtime photo access on Android 8–12 uses READ_EXTERNAL_STORAGE; Android 13 uses READ_MEDIA_IMAGES; Android 14+ also supports user-selected partial access. When denied, users can still invoke Android's system photo selection and explicitly tap images in order in the imported preview.
- `MainActivity` distinguishes external GET_CONTENT/PICK from the standalone/overlay use. Externally, it returns ordered, visible-numbered image URIs directly. In standalone/assist mode, it writes results into `Pictures/Image Order Studio` for selection from other apps.
- No AccessibilityService, SMS or notification access. The Android picker interfaces remain user-initiated only.
- `OrderedDocumentsProvider`, FileProvider, GalleryMediaExporter, and Quick Settings tile remain supported integrations. No INTERNET permission.

## Build & release

Keep package ID `com.twobornot.imageorder`, signing identity and versionCode monotonic (v0.5.1, versionCode 7). Release artifact only after GitHub Android compile, signature verification, and install tests pass. Preserve stable public beta at `https://github.com/sangkukzoa-ctrl/assets/releases/tag/image-order-beta`.

## QA

Tests verify logical selection order independence, ordered gallery intent handling and static manifest permissions. Real Galaxy verification must check Samsung One UI, Android 14/15 partial photo access, in at least two native apps and two browser upload contexts; Play Protect installation is a separate device-side check. The platform's system-only picker restriction means universal interception must not be claimed.
