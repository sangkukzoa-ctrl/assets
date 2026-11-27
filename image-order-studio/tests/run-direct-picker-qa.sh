#!/usr/bin/env bash
set -euo pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pkg=com.twobornot.imageorder
alias="$pkg/.DirectPhotoPickerTrial"
report="$project/direct-picker-report"
mkdir -p "$report"
trap 'adb logcat -d -v brief -s ImageOrderDirect:I ImageOrderFlow:I > "$report/logcat.txt" || true' EXIT
(cd "$project" && sha256sum -c direct-apk-sha256.txt)
adb install -r -t "$project/app/build/outputs/apk/debug/app-debug.apk"
adb install -r -t "$project/externalcaller/build/outputs/apk/debug/externalcaller-debug.apk"
adb install -r -t "$project/externalcaller/build/outputs/apk/androidTest/debug/externalcaller-debug-androidTest.apk"
# Own debug alias only; no system app, preferred handler, or global setting changed.
adb shell cmd package query-activities --brief -a android.provider.action.PICK_IMAGES -t 'image/*' > "$report/baseline-resolver.txt"
adb shell pm enable "$alias"
adb shell cmd package query-activities --brief -a android.provider.action.PICK_IMAGES -t 'image/*' > "$report/trial-resolver.txt"
grep -F 'DirectPhotoPickerTrial' "$report/trial-resolver.txt"
adb shell pm grant "$pkg" android.permission.READ_MEDIA_IMAGES
runner=com.twobornot.imageorder.caller.test/androidx.test.runner.AndroidJUnitRunner
timeout 8m adb shell am instrument -w -r -e class com.twobornot.imageorder.caller.DirectPhotoPickerTrialTest -e directQa true "$runner" | tee "$report/instrumentation.txt"
adb logcat -d -v brief -s ImageOrderDirect:I > "$report/direct-log.txt"
python3 - "$report" <<'PY'
import pathlib, re, sys
p=pathlib.Path(sys.argv[1])
s=(p/'instrumentation.txt').read_text().replace('\r','')
assert re.search(r'^OK \(1 test\)\s*$',s,re.M),s[-3000:]
assert re.search(r'^INSTRUMENTATION_CODE: -1\s*$',s,re.M)
assert not re.search(r'^INSTRUMENTATION_STATUS_CODE: -|^FAILURES!!!|^INSTRUMENTATION_FAILED:',s,re.M)
assert s.count('INSTRUMENTATION_STATUS: test=firstPhotoPickerWithoutPackageOrChooser')==2
assert s.count('INSTRUMENTATION_STATUS_CODE: 1\n')==1
assert s.count('INSTRUMENTATION_STATUS_CODE: 0\n')==1
logs=(p/'direct-log.txt').read_text()
native='P0_NATIVE_SUCCESS' in logs
blocked='P0_BLOCKED' in logs
assert native != blocked, 'Missing or conflicting actual outcome'
out='P0_NATIVE_SUCCESS' if native else 'P0_BLOCKED — observed platform picker; NOT product success'
(p/'outcome.txt').write_text(out+'\n')
print(out)
PY
cat "$report/direct-log.txt"
