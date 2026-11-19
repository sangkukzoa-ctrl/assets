"""Fail a release if default upload pipeline mutates original image content."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=(p/'app/src/main/java/com/twobornot/imageorder/MainActivity.java').read_text()
provider=(p/'app/src/main/java/com/twobornot/imageorder/OriginalImageProvider.java').read_text()
store=(p/'app/src/main/java/com/twobornot/imageorder/GalleryStore.java').read_text()
manifest=(p/'app/src/main/AndroidManifest.xml').read_text()
gradle=(p/'app/build.gradle').read_text()
assert "versionCode 8" in gradle and "versionName '0.5.2'" in gradle
assert 'applicationId \'com.twobornot.imageorder\'' in gradle
assert 'android.permission.INTERNET' not in manifest
assert 'BIND_ACCESSIBILITY_SERVICE' not in manifest
assert 'UploadAssistService' not in manifest
assert 'NativeGalleryActivity' in manifest
assert 'OriginalImageProvider' in manifest and 'android:grantUriPermissions="true"' in manifest
assert 'OriginalImageProvider.uriFor(this,store,item)' in source
assert 'setResult(RESULT_OK,result)' in source
assert 'Intent.FLAG_GRANT_READ_URI_PERMISSION' in source
assert 'ClipData.newRawUri(' in source
assert 'result.setClipData(clip)' in source
assert 'Intent.EXTRA_STREAM' in source
assert 'store.sequence.snapshot()' in source
assert 'sourceHasVerifiedOrder' in source
assert 'new GalleryStore(this,externalMode)' in source
assert 'shareOriginals();' in source
assert 'returnToCaller();' in source
assert 'EXTRA_MAX_SELECTION,externalMode&&!externalAllowsMultiple?1:100' in source
assert 'renderNumbered(' not in source and 'renderCombined(' not in source
assert 'publishGallery(' not in source and 'GalleryMediaExporter.publish(' not in source
assert 'writePng(' not in source and 'writeJpeg(' not in source
assert 'getString("name")' in provider and 'getString("mime")' in provider
assert 'ParcelFileDescriptor.MODE_READ_ONLY' in provider
assert 'getString("path")' in provider
assert 'out.write(buf,0,n)' in store
assert not list(p.rglob('*.jks')) and not list(p.rglob('*.p12'))
print('Original-only upload, filename, MIME and permissions: PASS')
