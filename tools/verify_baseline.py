#!/usr/bin/env python3
"""Verify immutable Siman handoff files by Git blob hash and byte count.
Run at baseline only; deliberately fail if a preserved file differs.
No network, credentials, or private records are needed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument("--working-tree",action="store_true",help="Check bytes on disk (default)")
parser.parse_args()
root=Path(__file__).resolve().parent.parent
data=json.loads((root/"HANDOFF/BASELINE_MANIFEST.json").read_text(encoding="utf-8"))
errors=[]
for row in data["files"]:
    p=root/row["path"]
    if not p.is_file():
        errors.append("MISSING "+row["path"]); continue
    raw=p.read_bytes()
    digest=hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\x00"+raw).hexdigest()
    if len(raw)!=row["bytes"] or digest!=row["git_blob_sha"]:
        errors.append("MISMATCH "+row["path"])
if errors:
    print("\n".join(errors),file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(data['files'])} exact Git blobs; development tree {data['development_tree']}")
