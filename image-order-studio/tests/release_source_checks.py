"""No secret key or unsafe Android permissions in the distributable source."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=(p/'app/src/main/java/com/twobornot/imageorder/MainActivity.java').read_text()
export=(p/'app/src/main/java/com/twobornot/imageorder/ImageExporter.java').read_text()
ledger=(p/'app/src/main/java/com/twobornot/imageorder/SequenceLedger.java').read_text()
manifest=(p/'app/src/main/AndroidManifest.xml').read_text()
gradle=(p/'app/build.gradle').read_text()
assert "versionCode 3" in gradle and "versionName '0.2.0'" in gradle
assert 'applicationId \'com.twobornot.imageorder\'' in gradle
assert 'android.permission.INTERNET' not in manifest
assert 'READ_MEDIA_IMAGES' not in manifest and 'READ_EXTERNAL_STORAGE' not in manifest
assert 'android:allowBackup="false"' in manifest
for required in ['renderNumbered(store,ids,true)', 'renderNumbered(store,ids,compact)', 'store.sequence.snapshot()', 'copyManifest()', 'rebuildVisible()']:
    assert required in source, required
for required in ['compact?"jpg":"png"', 'writeJpeg(', 'writePng(', 'ORDER  %04d / %04d']:
    assert required in export, required
assert '.sort(' not in ledger and 'Collections.swap(' in ledger
assert not list(p.rglob('*.jks')) and not list(p.rglob('*.p12'))
print('Release source and permission checks PASS')
