#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$(cd "$script_dir/.." && pwd)"
diagnostics(){
  adb logcat -d -v time > "$project/chrome-qa-logcat.txt" 2>&1 || true
  adb logcat -d -v brief -s ImageOrderChrome:I ImageOrderResolver:I ImageOrderHttp:I || true
  adb logcat -d -v brief -s ActivityTaskManager:I | grep -E 'START.*(GET_CONTENT|OPEN_DOCUMENT|PICK_IMAGES|CHOOSER|com.android.chrome|com.twobornot.imageorder)' || true
  adb shell dumpsys activity activities > "$project/chrome-qa-activities.txt" 2>&1 || true
  mkdir -p "$project/chrome-qa-diagnostics"
  adb pull /sdcard/Download/. "$project/chrome-qa-diagnostics/" || true
}
trap diagnostics EXIT
adb shell pm path com.android.chrome | grep -q 'package:' || { echo 'Chrome not installed in this emulator image'; exit 1; }
adb shell dumpsys package com.android.chrome | grep -m1 versionName || true
# Disposable emulator only: suppress onboarding; leave all picker feature flags untouched.
adb shell am set-debug-app --persistent com.android.chrome
adb shell 'printf "%s\n" "_ --no-first-run --disable-fre --no-default-browser-check" > /data/local/tmp/chrome-command-line'
adb shell am force-stop com.android.chrome
# The host already built all three APKs. Run the exact same AndroidJUnitRunner
# directly: AGP's connectedDebugAndroidTest otherwise downloads extra host UTP
# plugins even though the instrumentation APK is complete.
target="$project/app/build/outputs/apk/debug/app-debug.apk"
caller="$project/externalcaller/build/outputs/apk/debug/externalcaller-debug.apk"
instrumentation="$project/externalcaller/build/outputs/apk/androidTest/debug/externalcaller-debug-androidTest.apk"
for apk in "$target" "$caller" "$instrumentation"; do
  test -s "$apk" || { echo "Missing prebuilt APK: $apk" >&2; exit 1; }
  sha256sum "$apk"
  adb install -r -t "$apk"
done
adb shell pm grant com.twobornot.imageorder android.permission.READ_MEDIA_IMAGES
runner="com.twobornot.imageorder.caller.test/androidx.test.runner.AndroidJUnitRunner"
adb shell pm list instrumentation | tr -d '\r' | grep -F "$runner"
method="${CHROME_QA_METHOD:?Select the independent Chrome test method}"
case "$method" in
  chromeGenericInputUploadsOriginalsInTapOrder|chromeImageInputUploadsOriginalsInTapOrder) ;;
  *) echo "Invalid Chrome test method: $method" >&2; exit 2 ;;
esac
result="$project/chrome-qa-instrumentation.txt"
# One clean emulator, one method, one explicit positive success result.
timeout 12m adb shell am instrument -w -r \
  -e class "com.twobornot.imageorder.caller.ChromeUploadTest#$method" \
  -e chromeQa true -e nativeOnlyQa "${IMAGE_ORDER_NATIVE_ONLY_QA:-false}" "$runner" | tee "$result"
python3 "$script_dir/check-chrome-instrumentation.py" "$result" "$method"
