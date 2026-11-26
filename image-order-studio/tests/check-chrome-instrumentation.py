"""Require positive evidence of both actual Chrome tests, never a skipped run."""
import re
import sys
from pathlib import Path

EXPECTED = {
    "chromeGenericInputUploadsOriginalsInTapOrder",
    "chromeImageInputUploadsOriginalsInTapOrder",
}
TEST_CLASS = "com.twobornot.imageorder.caller.ChromeUploadTest"

def validate(raw, expected=EXPECTED):
    raw = raw.replace("\r", "")
    completed = []
    started = []
    status = {}
    for line in raw.splitlines():
        if line.startswith("INSTRUMENTATION_STATUS: "):
            key, sep, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            if sep:
                status[key] = value
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = int(line.rsplit(":", 1)[1].strip())
            if code < 0:
                raise ValueError(f"Failed/skipped/aborted test status {code}: {status}")
            if code in (0, 1):
                if status.get("class") != TEST_CLASS or status.get("test") not in expected:
                    raise ValueError(f"Unexpected test identity: {status}")
                (started if code == 1 else completed).append(status["test"])
            status = {}
    if sorted(started) != sorted(expected) or sorted(completed) != sorted(expected):
        raise ValueError(f"Expected each test to start and pass exactly once; starts={started}, completions={completed}")
    expected_summary = "OK (1 test)" if len(expected) == 1 else f"OK ({len(expected)} tests)"
    if not re.search(r"(?m)^"+re.escape(expected_summary)+r"\s*$", raw):
        raise ValueError("Missing positive JUnit summary: "+expected_summary)
    if not re.search(r"(?m)^INSTRUMENTATION_CODE: -1\s*$", raw):
        raise ValueError("Missing successful instrumentation finish")
    if re.search(r"(?m)^(FAILURES!!!|INSTRUMENTATION_FAILED:|INSTRUMENTATION_ABORTED:|INSTRUMENTATION_RESULT: shortMsg=)", raw):
        raise ValueError("Instrumentation reported an error")
    return True

def self_test():
    def run(code=0):
        parts=[]
        for method in sorted(EXPECTED):
            for state in (1, code):
                parts.extend([f"INSTRUMENTATION_STATUS: class={TEST_CLASS}",
                    f"INSTRUMENTATION_STATUS: test={method}",
                    f"INSTRUMENTATION_STATUS_CODE: {state}"])
        return "\n".join(parts)+"\nOK (2 tests)\nINSTRUMENTATION_CODE: -1\n"
    good=run()
    assert validate(good)
    bad=[run(-3),run(-4),run(-2),good.replace("OK (2 tests)","OK (0 tests)"),
        good.replace("INSTRUMENTATION_CODE: -1","INSTRUMENTATION_CODE: 0"),
        good.replace("chromeGenericInputUploadsOriginalsInTapOrder","unrelated"),
        good+"\nINSTRUMENTATION_FAILED: crash\n","OK (2 tests)\nINSTRUMENTATION_CODE: -1"]
    for sample in bad:
        try:
            validate(sample)
        except ValueError:
            continue
        raise AssertionError("Accepted invalid instrumentation transcript")
    one=next(iter(EXPECTED))
    single="\n".join(f"INSTRUMENTATION_STATUS: class={TEST_CLASS}\nINSTRUMENTATION_STATUS: test={one}\nINSTRUMENTATION_STATUS_CODE: {code}" for code in (1,0))+"\nOK (1 test)\nINSTRUMENTATION_CODE: -1\n"
    assert validate(single,{one})
    try:
        validate(single,EXPECTED)
    except ValueError:
        pass
    else:
        raise AssertionError("One passing case must not satisfy two-test gate")
    print("PASS: instrumentation success/skip/failure/identity gates")

if __name__ == "__main__":
    if sys.argv[1:]==["--self-test"]:
        self_test()
    elif len(sys.argv)==3 and sys.argv[2] in EXPECTED:
        validate(Path(sys.argv[1]).read_text(errors="replace"),{sys.argv[2]})
        print("PASS: real Chrome test "+sys.argv[2])
    elif len(sys.argv)==2:
        validate(Path(sys.argv[1]).read_text(errors="replace"))
        print("PASS: both real Chrome instrumentation tests completed successfully")
    else:
        raise SystemExit("Usage: check-chrome-instrumentation.py FILE [METHOD]|--self-test")
