# -*- coding: utf-8 -*-
"""Pure smoke tests for Test Result Export on Windows and other platforms."""
from datetime import date
from pathlib import Path
import ast
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_export_v0373 import (
    default_test_result_filename,export_payload,VERSION,
)

assert VERSION=="0.4.10",VERSION
assert default_test_result_filename(date(2026,11,6)) == (
    "ChatLensOCR_v0.4.10-테스트결과-2026-11-06.txt"
)
assert default_test_result_filename(date(2027,1,2)) == (
    "ChatLensOCR_v0.4.10-테스트결과-2027-01-02.txt"
)
assert default_test_result_filename().endswith(".txt")

class FakeText:
    def __init__(self,payload):self.payload=payload
    def get(self,start,finish):
        assert (start,finish)==("1.0","end-1c")
        return self.payload

payload="--- 카카오톡.png [카카오톡] ---\n달팽이: 나빴어\n--- FFXIV.png [파판14] ---\n(현자)현시완: 안녕하세요\n"
assert export_payload(FakeText(payload))==payload
assert export_payload(FakeText(""))==""
source=(Path(__file__).resolve().parent/"app.py").read_text(encoding="utf-8")
assert "def save(ext, suggested_name=None):" in source
assert '"initialfile"' in source
debug_position=source.index('button(actions,"🐞 디버그 로그",show_debug_log)')
export_position=source.index('button(actions,"📄 테스트결과 내보내기",')
assert export_position>debug_position and export_position-debug_position<280
assert 'lambda:save("txt",default_test_result_filename())' in source
assert 'if ext=="txt":content=fields[0].get("1.0","end-1c")' in source
for name in ("app.py","test_export_v0373.py","debuglog_v0372.py"):
    ast.parse((Path(__file__).resolve().parent/name).read_text(encoding="utf-8"))
print("v0.4.10 default filename, UI adjacency, TXT payload and syntax tests PASSED",flush=True)
