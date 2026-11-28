#!/usr/bin/env bash
set -euo pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
report="$project/host-integration-report"
mkdir -p "$report"
trap 'adb logcat -d -v brief -s ImageOrderHost:I ImageOrderFlow:I > "$report/logcat.txt" || true' EXIT
(cd "$project" && sha256sum -c direct-apk-sha256.txt)
adb install -r -t "$project/app/build/outputs/apk/debug/app-debug.apk"
adb install -r -t "$project/externalcaller/build/outputs/apk/debug/externalcaller-debug.apk"
adb install -r -t "$project/externalcaller/build/outputs/apk/androidTest/debug/externalcaller-debug-androidTest.apk"
adb shell pm grant com.twobornot.imageorder android.permission.READ_MEDIA_IMAGES
runner=com.twobornot.imageorder.caller.test/androidx.test.runner.AndroidJUnitRunner
timeout 8m adb shell am instrument -w -r -e class 'com.twobornot.imageorder.caller.CrossPackagePickerTest#actualExternalAppGetsReadableOriginalsInTapOrder' "$runner" | tee "$report/instrumentation.txt"
adb logcat -d -v brief -s ImageOrderHost:I > "$report/host-log.txt"
grep -F 'HOST_ROUTE_OK optedIn=true optOutUnchanged=true untrustedUnchanged=true' "$report/host-log.txt"
grep -F 'INSTRUMENTATION_STATUS: test=actualExternalAppGetsReadableOriginalsInTapOrder' "$report/instrumentation.txt"
grep -E '^OK \(1 test\)' "$report/instrumentation.txt"
if grep -E '^INSTRUMENTATION_STATUS_CODE: -|^FAILURES!!!' "$report/instrumentation.txt"; then exit 1; fi
