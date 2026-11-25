"""Static release gates for zero-copy image selection, system integration and no rewriting."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
src=p/'app/src/main/java/com/twobornot/imageorder'
main=(src/'MainActivity.java').read_text()
native=(src/'NativeGalleryActivity.java').read_text()
helper=(src/'MediaIntentResult.java').read_text()
provider=(src/'OriginalImageProvider.java').read_text()
mime=(src/'ImageMimePolicy.java').read_text()
manifest=(p/'app/src/main/AndroidManifest.xml').read_text()
gradle=(p/'app/build.gradle').read_text()
assert "versionCode 11" in gradle and "versionName '0.5.5'" in gradle
assert "applicationId 'com.twobornot.imageorder'" in gradle
assert 'android.permission.INTERNET' not in manifest
assert 'BIND_ACCESSIBILITY_SERVICE' not in manifest and 'UploadAssistService' not in manifest
assert 'NativeGalleryActivity' in manifest and 'OriginalImageProvider' in manifest
assert 'android:grantUriPermissions="true"' in manifest
assert 'android.intent.action.GET_CONTENT' in manifest and 'android.intent.action.PICK' in manifest
assert 'android.intent.category.LAUNCHER' in manifest
assert 'android:mimeType="*/*"' in manifest
# Cross-package permission tests MUST be a different applicationId, with no storage permission.
external=p/'externalcaller'
foreign_manifest=(external/'src/main/AndroidManifest.xml').read_text()
assert "applicationId 'com.twobornot.imageorder.caller'" in (external/'build.gradle').read_text()
assert 'systemDocumentsUiReturnsReadableOriginalWithoutMediaPermission' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/SafExternalCallerTest.java').read_text()
assert 'Intent.ACTION_OPEN_DOCUMENT.equals(pickerAction)' in (external/'src/main/java/com/twobornot/imageorder/caller/AttachmentCallerActivity.java').read_text()
assert 'WebUploadCallerActivity' in foreign_manifest
assert 'WebUploadCallerActivity' not in manifest
html_host=(external/'src/main/java/com/twobornot/imageorder/caller/WebUploadCallerActivity.java').read_text()
assert "type='file'" in html_host and 'multiple' in html_host
assert 'WebChromeClient.FileChooserParams.parseResult' in html_host
assert 'OrderedWebFileChooserResult.parse(result,data)' in html_host
assert 'result.getClipData()' in (external/'src/main/java/com/twobornot/imageorder/caller/OrderedWebFileChooserResult.java').read_text()
assert 'https://imageorder-local.invalid/' in html_host
assert 'WebUploadCallerTest.java' in {x.name for x in (external/'src/androidTest/java/com/twobornot/imageorder/caller').iterdir()}
assert 'localHtmlMultiUploadPreservesOriginalFilesAndTapOrder' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/WebUploadCallerTest.java').read_text()
assert "android.permission.READ_MEDIA_IMAGES" not in foreign_manifest and "android.permission.READ_EXTERNAL_STORAGE" not in foreign_manifest
assert 'CrossAppMediaFixtureActivity' in (p/'app/src/debug/AndroidManifest.xml').read_text()
assert 'CrossAppMediaFixtureActivity' not in manifest
assert 'clickPhotoAndWaitForCount(device,desc,++expectedCount)' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/CrossPackagePickerTest.java').read_text()
assert 'hadAccessBeforeUserSelection' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/CrossPackagePickerTest.java').read_text()
assert 'fiveMixedMimeOriginalsKeepExplicitTapOrderAcrossApps' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/CrossPackagePickerTest.java').read_text()
assert 'externalCallerKeepsVerifiedOrderThroughScreenRotation' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/CrossPackagePickerTest.java').read_text()
assert 'imageorder.photo:' in native
assert 'imageorder.confirm' in native

assert '"*/*".equals(type)' in main
# NativeGallery is now the launcher; no intermediate home/import step for normal use.
assert '<activity android:name=".NativeGalleryActivity" android:exported="true"' in manifest
assert 'launchedFromHome=Intent.ACTION_MAIN.equals(action)' in native
# Direct external intent integration: avoid intermediate MainActivity for standard uploads.
import re
native_manifest=manifest.split('<activity android:name=".NativeGalleryActivity"',1)[1].split('</activity>',1)[0]
main_manifest=manifest.split('<activity android:name=".MainActivity"',1)[1].split('</activity>',1)[0]
assert 'android.intent.action.GET_CONTENT' in native_manifest
assert 'android.intent.action.PICK' in native_manifest
assert 'android:mimeType="*/*"' in native_manifest
assert 'android.intent.action.GET_CONTENT' not in main_manifest
assert 'getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false)' in native
assert 'MediaStore.EXTRA_PICK_IMAGES_IN_ORDER' in native
# Legacy denied-permission GET_CONTENT chooser must never recurse into our own gallery.
assert 'new ComponentName(context,NativeGalleryActivity.class)' in native
assert 'new ComponentName(context,MainActivity.class)' in native
assert 'supportsSystemPhotoPicker()' in native
assert 'legacyChooserExcludesBothImageOrderActivities' in (p/'app/src/androidTest/java/com/twobornot/imageorder/OrderedAttachmentInstrumentedTest.java').read_text()
assert 'fallbackPickerPending' in native and 'STATE_FALLBACK_PENDING' in native
assert 'fallbackPickerPendingStateSurvivesActivityRecreation' in (p/'app/src/androidTest/java/com/twobornot/imageorder/OrderedAttachmentInstrumentedTest.java').read_text()
assert 'orderedSystemPhotoPickerFallbackDeliversUnchangedMixedOriginals' in (p/'app/src/androidTest/java/com/twobornot/imageorder/OrderedAttachmentInstrumentedTest.java').read_text()
assert 'supportsOrderedSystemPicker()' in native
assert 'System picker originals return directly' in native
assert 'MediaIntentResult.forShare(getContentResolver(),uris)' in native
assert 'MediaIntentResult.forSelection(getContentResolver(),uris)' in native
assert 'EXTRA_ORDER_VERIFIED,true' in native
assert 'MediaStore.Images.Media.MIME_TYPE' in native
assert 'ImageMimePolicy.accepts(' in native
# External picker requests are returned immediately from the gallery without copying.
assert 'if(externalMode)deliverDirectToCaller(uris)' in main
assert 'if(trustOrder && !uris.isEmpty())' in main
assert 'else importAll(uris,false)' in main
assert 'setResult(RESULT_OK,result)' in main
assert 'if(externalMode)cancelExternal();' in main
assert 'path.contains("images")' in main # MIME-less ACTION_PICK handling
assert 'OriginalImageProvider.uriFor(this,store,item)' in main # legacy imported shares
# Both direct and legacy forms provide correct image ClipData, ordered URIs and grants.
assert 'new ClipData("Image Order",new String[]{mime,"image/*"}' in helper
assert 'Intent.FLAG_GRANT_READ_URI_PERMISSION' in helper
assert 'intent.putParcelableArrayListExtra(Intent.EXTRA_STREAM,' in helper
assert 'new ClipData.Item' in helper
assert 'OriginalDelivery.commonMime(mimes)' in helper
assert 'renderNumbered(' not in main and 'renderCombined(' not in main
assert 'ImageExporter.java' not in {x.name for x in src.iterdir()}
assert 'GalleryMediaExporter.java' not in {x.name for x in src.iterdir()}
assert 'Bitmap.compress' not in helper and 'Bitmap.compress' not in native
assert 'getString("name")' in provider and 'getString("mime")' in provider
assert 'openFileDescriptor(photoUri(' in (src/'OrderedDocumentsProvider.java').read_text()
assert 'SafDocumentIds.photo(' in (src/'OrderedDocumentsProvider.java').read_text()
assert 'OriginalImageProvider' in provider
assert not list(p.rglob('*.jks')) and not list(p.rglob('*.p12'))
assert 'PickerHostActivity' not in manifest
assert (p/'app/src/debug/java/com/twobornot/imageorder/PickerHostActivity.java').is_file()
assert 'externalPickerRoundTripPreservesTapSequence' in (p/'app/src/androidTest/java/com/twobornot/imageorder/OrderedAttachmentInstrumentedTest.java').read_text()
assert not (src/'OrderedOutbox.java').exists()
assert 'OrderedOutbox' not in (src/'OrderedDocumentsProvider.java').read_text()
assert 'queryRecentDocuments(' in (src/'OrderedDocumentsProvider.java').read_text()
assert 'querySearchDocuments(' in (src/'OrderedDocumentsProvider.java').read_text()
assert 'hundredOriginalsKeepOrderAtLimitAndAfterReselection' in (p/'app/src/androidTest/java/com/twobornot/imageorder/OrderedAttachmentInstrumentedTest.java').read_text()
print('v0.5.5 original-byte SAF and independent cross-UID grant coverage: PASS')

assert 'duplicateNamesAcrossAlbumsAndReselectionPreserveOriginalIdentity' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/CrossPackagePickerTest.java').read_text()

# Legacy fixture and permission helpers must remain test-only.
fixture=(p/'app/src/debug/java/com/twobornot/imageorder/TestMediaFixture.java').read_text()
assert 'MediaStore.Images.Media.DATA' in fixture and 'Build.VERSION.SDK_INT>=29' in fixture
assert not (src/'TestMediaFixture.java').exists()
assert not (src/'TestMediaPermissions.java').exists()
for tree in (p/'app/src/androidTest',external/'src/androidTest'):
    grants=next(tree.rglob('TestMediaPermissions.java')).read_text()
    assert 'Build.VERSION.SDK_INT>=28' in grants and 'WRITE_EXTERNAL_STORAGE' in grants
    assert 'com.twobornot.imageorder' in grants and 'pm grant' in grants
assert 'TestMediaFixture.insert' in (p/'app/src/androidTest/java/com/twobornot/imageorder/OrderedAttachmentInstrumentedTest.java').read_text()
assert 'TestMediaFixture.insert' in (p/'app/src/debug/java/com/twobornot/imageorder/CrossAppMediaFixtureActivity.java').read_text()

# Actual HTTP receiver is test-only and never exposes a network listener externally.
receiver=(external/'src/main/java/com/twobornot/imageorder/caller/LoopbackUploadServer.java').read_text()
assert 'InetAddress.getByName("127.0.0.1")' in receiver and 'multipart/form-data' in receiver
assert 'new FormData(document.getElementById' in html_host and 'Intent.createChooser(request' in html_host
assert 'else request.setPackage(TARGET)' in html_host and 'queryIntentActivities(request' in html_host
assert not (src/'LoopbackUploadServer.java').exists()
webtest=(external/'src/androidTest/java/com/twobornot/imageorder/caller/WebUploadCallerTest.java').read_text()
assert 'actualHttpMultipartPreservesOriginalFilesAndTapOrder' in webtest
assert 'systemChooserCanSelectImageOrderAndUploadOriginals' in webtest
assert 'Actual server SHA-256' in webtest

assert 'Image Order (Files)' in (src/'OrderedDocumentsProvider.java').read_text()
assert 'selectRealSystemGallery' in webtest and 'Resolver candidates:' in webtest

assert 'Open Image Order (Files)' in webtest
assert 'selectProviderOriginal' in (external/'src/androidTest/java/com/twobornot/imageorder/caller/SafExternalCallerTest.java').read_text()
