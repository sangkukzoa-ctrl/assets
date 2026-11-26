#!/usr/bin/env bash
# Install the published beta, then update it WITHOUT uninstalling or clearing data.
# This smoke test is strictly limited to a clean disposable Android emulator.
set -euo pipefail
if [ "$#" -ne 3 ]; then
  echo "Usage: bash verify-candidate-upgrade.sh emulator-5554 /path/to/published-v0.5.4.apk /path/to/ImageOrder-v0.5.5-RC.apk" >&2
  exit 2
fi
serial="$1"
old="$(realpath "$2")"
new="$(realpath "$3")"
[[ "$serial" =~ ^emulator-[0-9]+$ ]] || { echo "Only a disposable emulator is supported" >&2; exit 2; }
tools="${ANDROID_HOME:-${ANDROID_SDK_ROOT:?Set Android SDK path}}/build-tools/35.0.0"
pkg=com.twobornot.imageorder
a(){ adb -s "$serial" "$@"; }
test "$(a get-state | tr -d '\r')" = device
qemu="$(a shell getprop ro.kernel.qemu | tr -d '\r')"
bootqemu="$(a shell getprop ro.boot.qemu | tr -d '\r')"
[[ "$qemu" == 1 || "$bootqemu" == 1 ]] || { echo "Not an emulator; stopping" >&2; exit 2; }
if a shell pm path "$pkg" | grep -q '^package:'; then
  echo "Image Order is already present. Use a fresh test emulator; nothing was changed." >&2
  exit 2
fi
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
report="${REPORT_DIR:-$PWD/imageorder-upgrade-report}"
mkdir -p "$report"
report="$(realpath "$report")"
expected="$(tr -d '\r\n' < "$dir/expected-signer-sha256.txt")"
[[ "$expected" =~ ^[a-fA-F0-9]{64}$ ]]
verify_apk(){
  local file="$1" version="$2" code="$3" label="$4" actual
  "$tools/apksigner" verify --verbose --print-certs --min-sdk-version 26 "$file" > "$report/$label-signature.txt"
  actual="$(awk '/^Signer #1 certificate SHA-256 digest: /{print $NF}' "$report/$label-signature.txt")"
  [[ "${actual,,}" == "${expected,,}" ]]
  "$tools/aapt" dump badging "$file" > "$report/$label-badging.txt"
  grep -F "package: name='$pkg' versionCode='$code' versionName='$version'" "$report/$label-badging.txt"
}
verify_apk "$old" 0.5.4 10 published
verify_apk "$new" 0.5.5 11 candidate
grep -F 'Verified using v2 scheme (APK Signature Scheme v2): true' "$report/candidate-signature.txt"
grep -F 'Verified using v3 scheme (APK Signature Scheme v3): true' "$report/candidate-signature.txt"
"$tools/zipalign" -c -p 4 "$new"
sha256sum "$old" "$new" > "$report/apk-sha256.txt"
snapshot(){
  a shell dumpsys package "$pkg" | tr -d '\r' > "$1"
}
identity(){
  awk -F= '/^[[:space:]]*(userId|appId|firstInstallTime)=/{gsub(/^[[:space:]]+/,"",$1); print $1"="$2}' "$1" | sort -u
}
a install "$old" | tee "$report/install-v054.txt"
grep -x 'Success' "$report/install-v054.txt"
snapshot "$report/package-before.txt"
grep -E 'versionCode=10([[:space:]]|$)' "$report/package-before.txt"
grep -F 'versionName=0.5.4' "$report/package-before.txt"
identity "$report/package-before.txt" > "$report/identity-before.txt"
grep -E '^(userId|appId)=' "$report/identity-before.txt"
grep -F 'firstInstallTime=' "$report/identity-before.txt"
# No uninstall, clear-data, downgrade flag, or debug signature substitution.
a install -r "$new" | tee "$report/update-v055.txt"
grep -x 'Success' "$report/update-v055.txt"
snapshot "$report/package-after.txt"
grep -E 'versionCode=11([[:space:]]|$)' "$report/package-after.txt"
grep -F 'versionName=0.5.5' "$report/package-after.txt"
identity "$report/package-after.txt" > "$report/identity-after.txt"
cmp "$report/identity-before.txt" "$report/identity-after.txt"
grep -F "$pkg.documents" "$report/package-after.txt"
grep -F "$pkg.originals" "$report/package-after.txt"
for mime in 'image/*' '*/*'; do
  a shell cmd package resolve-activity --brief -a android.intent.action.GET_CONTENT -c android.intent.category.OPENABLE -t "'$mime'" -p "$pkg" | tr -d '\r' | tee "$report/resolve-${mime//[^a-zA-Z]/_}.txt" | grep -F "$pkg/.NativeGalleryActivity"
done
a shell cmd package resolve-activity --brief -a android.intent.action.PICK -t "'image/*'" -p "$pkg" | tr -d '\r' | tee "$report/resolve-pick.txt" | grep -F "$pkg/.NativeGalleryActivity"
a shell am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n "$pkg/.NativeGalleryActivity" | tr -d '\r' | tee "$report/launch.txt"
grep -F 'Status: ok' "$report/launch.txt"
a shell dumpsys activity activities > "$report/activities.txt"
grep -F "$pkg/.NativeGalleryActivity" "$report/activities.txt"
a logcat -d -s AndroidRuntime:E > "$report/android-runtime.txt"
if grep -E "Process: $pkg(,|$)" "$report/android-runtime.txt"; then
  echo "Image Order crash detected" >&2; exit 1
fi
echo "PASS: certificate-matched update installation, package identity retained, picker registration and launch"
echo "Actual signed image selection, Play Protect on a physical device and OEM/browser checks remain separate."
