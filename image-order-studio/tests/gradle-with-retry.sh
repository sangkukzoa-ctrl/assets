#!/usr/bin/env bash
# Only retry a Gradle failure caused by a temporary repository rate limit.
set -euo pipefail
if [ "$#" -lt 2 ]; then
  echo "Usage: gradle-with-retry.sh LABEL GRADLE_ARGS..." >&2
  exit 2
fi
label="$1"
shift
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
for attempt in 1 2 3; do
  if gradle "$@" --stacktrace 2>&1 | tee "$log"; then
    exit 0
  fi
  if [ "$attempt" -lt 3 ] &&
     grep -Eqi 'Received status code 429|HTTP 429|Too Many Requests' "$log" &&
     ! grep -Eqi 'Tests (on .* failed|[0-9]+/[0-9]+ completed.*\([1-9][0-9]* failed\))|AssertionError|Compilation failed|error: (cannot find symbol|incompatible types|void cannot be dereferenced)' "$log"; then
    echo "::warning::Maven rate limit; retry ${attempt}/3 for ${label}"
    sleep "$((attempt*15))"
  else
    exit 1
  fi
done
exit 1
