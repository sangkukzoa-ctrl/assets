#!/usr/bin/env bash
set -euo pipefail
project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
report="$project/system-order-report"
mkdir -p "$report"
trap 'adb logcat -d -v brief -s ImageOrderSystem:I ImageOrderDirect:I ImageOrderFlow:I > "$report/logcat.txt" || true' EXIT
(cd "$project" && sha256sum -c direct-apk-sha256.txt)
adb install -r -t "$project/app/build/outputs/apk/debug/app-debug.apk"
adb install -r -t "$project/externalcaller/build/outputs/apk/debug/externalcaller-debug.apk"
adb install -r -t "$project/externalcaller/build/outputs/apk/androidTest/debug/externalcaller-debug-androidTest.apk"
adb shell pm grant com.twobornot.imageorder android.permission.READ_MEDIA_IMAGES
ordered="${ORDERED_PROBE:?}"
case "$ordered" in true|false) ;; *) exit 2;; esac
runner=com.twobornot.imageorder.caller.test/androidx.test.runner.AndroidJUnitRunner
timeout 8m adb shell am instrument -w -r -e class com.twobornot.imageorder.caller.SystemOrderContractTest -e systemOrderQa true -e orderedProbe "$ordered" "$runner" | tee "$report/instrumentation.txt"
adb logcat -d -v brief -s ImageOrderSystem:I > "$report/system-log.txt"
python3 - "$report" "$ordered" <<'PY'
import pathlib,re,sys
p=pathlib.Path(sys.argv[1]); ordered=sys.argv[2]
s=(p/'instrumentation.txt').read_text().replace('\r','')
assert re.search(r'^OK \(1 test\)\s*$',s,re.M)
assert re.search(r'^INSTRUMENTATION_CODE: -1\s*$',s,re.M)
assert not re.search(r'^INSTRUMENTATION_STATUS_CODE: -|^FAILURES!!!|^INSTRUMENTATION_FAILED:',s,re.M)
assert s.count('INSTRUMENTATION_STATUS: class=com.twobornot.imageorder.caller.SystemOrderContractTest')==2
assert s.count('INSTRUMENTATION_STATUS: test=platformPickerOrderControl')==2
assert 'DirectPhotoPickerTrialTest' not in s
assert s.count('INSTRUMENTATION_STATUS_CODE: 1\n')==1
assert s.count('INSTRUMENTATION_STATUS_CODE: 0\n')==1
log=(p/'system-log.txt').read_text()
lines=[l for l in log.splitlines() if 'SYSTEM_ORDER_RESULT orderedExtra='+ordered in l]
assert len(lines)==1,lines
taps=re.findall(r'Tapped fixture (\d+) count=(\d+)',log)
assert taps==[('3','1'),('0','2'),('4','3')],taps
assert 'tap=[3, 0, 4]' in lines[0],lines[0]
if ordered=='true': assert 'matches=true' in lines[0]
print(lines[0])
(p/'outcome.txt').write_text(lines[0]+'\n')
PY
