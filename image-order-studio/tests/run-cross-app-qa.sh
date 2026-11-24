#!/usr/bin/env bash
# android-emulator-runner invokes each configured script line in a separate sh.
# Keeping all orchestration in one Bash invocation preserves functions and pipefail.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project="$(cd "$script_dir/.." && pwd)"
collect_diagnostics() {
  adb logcat -d -v time > "$project/android-e2e-logcat.txt" 2>&1 || true
  adb shell dumpsys activity activities > "$project/android-e2e-activities.txt" 2>&1 || true
  mkdir -p "$project/crossuid-diagnostics"
  adb pull /sdcard/Download/. "$project/crossuid-diagnostics/" || true
}
bash "$script_dir/gradle-with-retry.sh" app -p "$project" --no-daemon :app:connectedDebugAndroidTest || {
  collect_diagnostics
  exit 1
}
adb install -r "$project/app/build/outputs/apk/debug/app-debug.apk"
adb shell pm grant com.twobornot.imageorder android.permission.READ_MEDIA_IMAGES
bash "$script_dir/gradle-with-retry.sh" external -p "$project" --no-daemon :externalcaller:connectedDebugAndroidTest || {
  collect_diagnostics
  exit 1
}
adb logcat -d -s AndroidRuntime:E > "$project/android-e2e-crashes.log"
