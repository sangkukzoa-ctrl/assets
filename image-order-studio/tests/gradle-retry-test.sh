#!/usr/bin/env bash
# Exercise the retry policy without Android, Maven, or real delays.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export MOCK_COUNT="$tmp/count"
export PATH="$tmp:$PATH"
cat > "$tmp/gradle" <<'MOCK'
#!/usr/bin/env bash
set -eu
n="$(cat "$MOCK_COUNT")"
n=$((n+1))
echo "$n" > "$MOCK_COUNT"
case "$MOCK_CASE" in
  success) exit 0 ;;
  transient)
    if [ "$n" -eq 1 ]; then
      echo 'Received status code 429 from server: Too Many Requests' >&2
      exit 1
    fi
    exit 0 ;;
  permanent) echo 'Received status code 429' >&2; exit 1 ;;
  test-fail) echo 'java.lang.AssertionError: original order changed' >&2; exit 1 ;;
  mixed-fail)
    echo 'Received status code 429' >&2
    echo 'java.lang.AssertionError: original order changed' >&2
    exit 1 ;;
  compile-fail) echo 'Compilation failed' >&2; exit 1 ;;
esac
MOCK
printf '#!/usr/bin/env bash\nexit 0\n' > "$tmp/sleep"
chmod +x "$tmp/gradle" "$tmp/sleep"
check() {
  export MOCK_CASE="$1"
  local want_status="$2" want_count="$3" status=0
  echo 0 > "$MOCK_COUNT"
  bash "$script_dir/gradle-with-retry.sh" mock :fakeTask > "$tmp/output" 2>&1 || status=$?
  if [ "$status" -ne "$want_status" ] || [ "$(cat "$MOCK_COUNT")" -ne "$want_count" ]; then
    cat "$tmp/output"
    echo "FAIL $MOCK_CASE: status=$status attempts=$(cat "$MOCK_COUNT")" >&2
    exit 1
  fi
  echo "PASS $MOCK_CASE status=$status attempts=$want_count"
}
check success 0 1
check transient 0 2
check permanent 1 3
check test-fail 1 1
check mixed-fail 1 1
check compile-fail 1 1
