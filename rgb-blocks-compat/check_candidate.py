#!/usr/bin/env python3
"""Release-blocking preservation contract for RGB Blocks 1.3.1 backports.

Usage:
  python rgb-blocks-compat/check_candidate.py path/to/port.jar
  python rgb-blocks-compat/check_candidate.py --self-test

Self-test checks the contract against identical official source input; only a
candidate JAR can verify a real port. This script does not establish runtime
lighting, shader, client, or dedicated server compatibility.
"""
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

URL = "https://mediafilez.forgecdn.net/files/8426/251/RgbBlocksmod-26.1.2-1.3.1.jar"
EXPECTED = {"blockstates":50061,"block_models":50061,"item_models":50063,"png":33377}
OUT = Path("audit-output");OUT.mkdir(exist_ok=True)

def source_bytes():
    req=urllib.request.Request(URL,headers={"User-Agent":"RGBBlocks-Backport-Release-Gate/1.0"})
    with urllib.request.urlopen(req,timeout=120) as res:
        return res.read()

def categorize(name):
    if not name.startswith("assets/"):
        return None
    if name.endswith(".png"):
        return "png"
    if "/lang/" in name and name.endswith(".json"):
        return "language"
    if name.endswith("palette.json"):
        return "palette"
    if "/blockstates/" in name and name.endswith(".json"):
        return "blockstates"
    if "/models/block/" in name and name.endswith(".json"):
        return "block_models"
    if "/models/item/" in name and name.endswith(".json"):
        return "item_models"
    return None

def scan(z):
    result=defaultdict(dict)
    for name in z.namelist():
        group=categorize(name)
        if not group:
            continue
        data=z.read(name)
        result[group][name]={"sha":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
        if name.endswith(".json"):
            try:
                json.loads(data.decode("utf-8"))
            except Exception as e:
                raise AssertionError(f"INVALID_JSON {name}: {e}")
    return result

def compare(src, dst):
    issues=[]
    metrics={}
    for group in set(src)|set(dst):
        original=src.get(group,{})
        port=dst.get(group,{})
        missing=sorted(set(original)-set(port))
        extra=sorted(set(port)-set(original))
        changed=sorted(name for name in set(original)&set(port) if original[name]["sha"]!=port[name]["sha"])
        metrics[group]={"original":len(original),"candidate":len(port),
                        "missing_count":len(missing),"extra_count":len(extra),
                        "changed_count":len(changed),"missing_examples":missing[:15],
                        "extra_examples":extra[:15], "changed_examples":changed[:15]}
        if missing or extra:
            issues.append(f"{group}: {len(missing)} missing / {len(extra)} added paths")
        # Only legacy JSON shape may change. Text/images/palette must be byte-exact.
        if group in {"png","language","palette"} and changed:
            issues.append(f"{group}: {len(changed)} changed source files (must be byte-identical)")
    for group,count in EXPECTED.items():
        if len(src.get(group,{}))!=count:
            issues.append(f"BASELINE ERROR: expected {count} {group} files, got {len(src.get(group,{}))}")
    return issues,metrics

def main():
    base_bytes=source_bytes()
    srcfile="--self-test"
    if len(sys.argv)==2:
        srcfile=sys.argv[1]
    elif len(sys.argv)>2:
        raise ValueError("Usage: check_candidate.py <target-jar> | --self-test")
    if srcfile=="--self-test":
        cand_bytes=base_bytes
    else:
        cand_bytes=Path(srcfile).read_bytes()
    if not zipfile.is_zipfile(io.BytesIO(cand_bytes)):
        raise AssertionError("Candidate is not a ZIP/JAR archive")
    with zipfile.ZipFile(io.BytesIO(base_bytes)) as orig, zipfile.ZipFile(io.BytesIO(cand_bytes)) as candidate:
        if orig.testzip() is not None or candidate.testzip() is not None:
            raise AssertionError("One or more JARs failed complete CRC scan")
        issues,metrics=compare(scan(orig),scan(candidate))
    result={"mode":"SELF_TEST_NOT_PORT_VALIDATION" if srcfile=="--self-test" else "PORT_CANDIDATE_CHECK",
            "candidate":srcfile, "source_jar_sha256":hashlib.sha256(base_bytes).hexdigest(),
            "candidate_jar_sha256":hashlib.sha256(cand_bytes).hexdigest(),
            "preservation_pass":not issues,"issues":issues,"counts":metrics,
            "scope":"Static asset/name preservation only. Does not verify code, RGB light, chisel runtime, shader, SP or MP."}
    (OUT/"release-preservation-gate.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="counts"},indent=2,ensure_ascii=False))
    for group,vals in sorted(metrics.items()):
        print(group,{k:v for k,v in vals.items() if k.endswith("count") or k in ("original","candidate")})
    return 1 if issues else 0

if __name__=="__main__":
    sys.exit(main())
