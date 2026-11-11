"""No secret key or unsafe Android permissions in the distributable source."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=(p/'app/src/main/java/com/twobornot/imageorder/MainActivity.java').read_text()
export=(p/'app/src/main/java/com/twobornot/imageorder/ImageExporter.java').read_text()
ledger=(p/'app/src/main/java/com/twobornot/imageorder/SequenceLedger.java').read_text()
manifest=(p/'app/src/main/AndroidManifest.xml').read_text()
gradle=(p/'app/build.gradle').read_text()
assert "versionCode 6" in gradle and "versionName '0.5.0'" in gradle
assert 'applicationId \'com.twobornot.imageorder\'' in gradle
assert 'android.permission.INTERNET' not in manifest
assert 'READ_MEDIA_IMAGES' in manifest and 'READ_EXTERNAL_STORAGE' in manifest
assert 'android:allowBackup="false"' in manifest
assert 'android.intent.action.GET_CONTENT' in manifest and 'android.intent.action.PICK' in manifest
assert 'android.intent.category.OPENABLE' in manifest
assert '<data android:mimeType="image/*" />' in manifest
assert 'picker-sessions/' in (p/'app/src/main/res/xml/file_paths.xml').read_text()
assert 'isExternalImageRequest(' in source
assert 'returnToCaller()' in source and 'setResult(RESULT_OK,result)' in source
assert 'Intent.FLAG_GRANT_READ_URI_PERMISSION' in source
assert 'ClipData.newRawUri(' in source
assert 'MediaStore.ACTION_PICK_IMAGES' in source
assert 'MediaStore.EXTRA_PICK_IMAGES_IN_ORDER' in source
assert 'PickerDecision.supportsOrderedPicker(' in source
assert 'nativePickerOrdered' in source
assert 'sourceHasVerifiedOrder' in source
assert 'new GalleryStore(this,externalMode)' in source
assert 'EXTRA_EXCLUDE_COMPONENTS' in source
assert 'renderCombined(store,ids,!png)' in source

for required in ['renderNumbered(store,ids,true)', 'renderNumbered(store,ids,compact)', 'store.sequence.snapshot()', 'copyManifest()', 'rebuildVisible()']:
    assert required in source, required
for required in ['compact?"jpg":"png"', 'writeJpeg(', 'writePng(', 'ORDER  %04d / %04d']:
    assert required in export, required
assert '.sort(' not in ledger and 'Collections.swap(' in ledger
assert not list(p.rglob('*.jks')) and not list(p.rglob('*.p12'))
print('Release source and permission checks PASS')

# 0.4.0: Native Samsung gallery first, plus cross-site MediaStore/SAF fallbacks.
assert 'com.sec.android.gallery3d' in source
assert 'gallery.setPackage(SAMSUNG_GALLERY)' in source
assert 'Intent.ACTION_GET_CONTENT' in source
assert 'trySystemPhotoPicker()' in source
assert 'getPreferences(MODE_PRIVATE)' in source
assert 'GalleryMediaExporter.publish(this,results)' in source
assert 'OrderedOutbox.publish(this,results)' in source
assert 'WRITE_OLD_GALLERY' in source
assert 'android.permission.WRITE_EXTERNAL_STORAGE' in manifest and 'android:maxSdkVersion="28"' in manifest
assert 'android.permission.MANAGE_DOCUMENTS' in manifest
assert 'android.permission.BIND_QUICK_SETTINGS_TILE' in manifest
provider=(p/'app/src/main/java/com/twobornot/imageorder/OrderedDocumentsProvider.java').read_text()
outbox=(p/'app/src/main/java/com/twobornot/imageorder/OrderedOutbox.java').read_text()
gallery=(p/'app/src/main/java/com/twobornot/imageorder/GalleryMediaExporter.java').read_text()
tile=(p/'app/src/main/java/com/twobornot/imageorder/OrderTileService.java').read_text()
assert 'queryRoots' in provider and 'queryChildDocuments' in provider and 'openDocument' in provider
assert 'ParcelFileDescriptor.MODE_READ_ONLY' in provider
assert 'cleanOld(root,12)' in outbox
assert 'MediaStore.MediaColumns.RELATIVE_PATH' in gallery
assert 'MediaStore.MediaColumns.IS_PENDING' in gallery
assert 'Pictures/' not in gallery  # use official DIRECTORY_PICTURES instead
assert 'startActivityAndCollapse(intent)' in tile
print('v0.4.0 Android gallery / SAF / Quick Settings source checks PASS')

# 0.5.0 gallery-first UI and optional user-authorized overlay assistance.
assert 'NativeGalleryActivity' in manifest and 'UploadAssistService' in manifest
assert 'android.permission.BIND_ACCESSIBILITY_SERVICE' in manifest
assert 'android.permission.READ_MEDIA_VISUAL_USER_SELECTED' in manifest
native=(p/'app/src/main/java/com/twobornot/imageorder/NativeGalleryActivity.java').read_text()
overlay=(p/'app/src/main/java/com/twobornot/imageorder/UploadAssistService.java').read_text()
assert 'LinkedHashMap<String,Uri> ordered' in native
assert 'EXTRA_ORDER_VERIFIED' in native
assert 'setResult(RESULT_OK,data)' in native
assert 'MediaStore.Images.Media.getContentUri' in native
assert 'TYPE_ACCESSIBILITY_OVERLAY' in overlay
assert 'requestUploadAssist()' in source
assert 'ui.postDelayed' in source
print('v0.5.0 unified gallery and optional overlay source checks PASS')
