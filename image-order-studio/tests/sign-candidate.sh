#!/usr/bin/env bash
# Execute only in an environment with the developer's existing PKCS#12 identity.
# No new signing key, no upload, no password in the command line.
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo "Usage: bash sign-candidate.sh /path/to/existing-release.p12 /path/to/secure-password-file" >&2
  exit 2
fi
ks="$(realpath "$1")"
password="$(realpath "$2")"
test -s "$ks" && test -s "$password"
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$dir"
tools="${ANDROID_HOME:-${ANDROID_SDK_ROOT:?Set Android SDK path}}/build-tools/35.0.0"
test -x "$tools/apksigner"
sha256sum -c SHA256SUMS.txt
unsigned="ImageOrder-v0.5.5-UNSIGNED.apk"
out="ImageOrder-v0.5.5-RC.apk"
test ! -e "$out" || { echo "Remove old output first: $out"; exit 1; }
expected="$(tr -d '\r\n' < expected-signer-sha256.txt)"
[[ "$expected" =~ ^[a-fA-F0-9]{64}$ ]]
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
# PasswordRetriever reads distinct lines when the same file is reused.
# Use two independent files for the identical PKCS#12 store/key password.
chmod 700 "$temp"
cp "$password" "$temp/key-password.txt"
chmod 600 "$temp/key-password.txt"
"$tools/apksigner" sign --ks "$ks" --ks-key-alias imageorder \
  --ks-pass "file:$password" --key-pass "file:$temp/key-password.txt" \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --min-sdk-version 26 --out "$temp/signed.apk" "$unsigned"
"$tools/apksigner" verify --verbose --print-certs --min-sdk-version 26 "$temp/signed.apk" > "$temp/report.txt"
grep -F 'Verified using v2 scheme (APK Signature Scheme v2): true' "$temp/report.txt"
grep -F 'Verified using v3 scheme (APK Signature Scheme v3): true' "$temp/report.txt"
actual="$(grep -E '^Signer #1 certificate SHA-256 digest: [a-fA-F0-9]{64}$' "$temp/report.txt" | awk '{print $NF}')"
[[ "${actual,,}" == "${expected,,}" ]] || { echo "Existing public certificate mismatch; refusing output." >&2; exit 1; }
"$tools/zipalign" -c -p 4 "$temp/signed.apk"
"$tools/aapt" dump badging "$temp/signed.apk" | grep -F "package: name='com.twobornot.imageorder' versionCode='11' versionName='0.5.5'"
mv "$temp/signed.apk" "$out"
cp "$temp/report.txt" candidate-signature.txt
sha256sum "$out" > SHA256SUMS-SIGNED.txt
echo "Certificate-matched candidate generated. Installation/upgrade tests remain mandatory."
