#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$(cd "$script_dir/.." && pwd)"
diagnostics(){
  adb logcat -d -v time > "$project/chrome-qa-logcat.txt" 2>&1 || true
  adb logcat -d -v brief -s ImageOrderChrome:I ImageOrderResolver:I ImageOrderHttp:I || true
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
# Build dependencies on the host before emulator startup, then reuse the exact APKs/cache.
gradle -p "$project" --offline --no-daemon :app:assembleDebug :externalcaller:assembleDebug :externalcaller:assembleDebugAndroidTest
adb install -r "$project/app/build/outputs/apk/debug/app-debug.apk"
adb shell pm grant com.twobornot.imageorder android.permission.READ_MEDIA_IMAGES
gradle -p "$project" --offline --no-daemon :externalcaller:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.twobornot.imageorder.caller.ChromeUploadTest \
  -Pandroid.testInstrumentationRunnerArguments.chromeQa=true
