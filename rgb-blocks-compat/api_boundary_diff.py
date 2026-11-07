#!/usr/bin/env python3
"""Cross-version direct symbol check of original RGB Blocks -> Chisels & Bits API.

Compares class/method references in the public RGB Blocks 1.3.1 Java
bytecode (MC 26.1.2) with public C&B compiled classes for 1.21.1 Fabric and
1.20.1 Forge. This is *not* a loader runtime, RGB port, or Mixin validation.
We do not publish decompiled/private source code.
"""
import io,json,struct,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
from collections import defaultdict

SOURCE_URL="https://mediafilez.forgecdn.net/files/8426/251/RgbBlocksmod-26.1.2-1.3.1.jar"
TARGETS={
"1.21.1 Fabric C&B 21.1.40":"https://mediafilez.forgecdn.net/files/9455/172/chisels-and-bits-fabric-21.1.40.jar",
"1.20.1 Forge C&B 20.1.20":"https://mediafilez.forgecdn.net/files/7620/767/chisels-and-bits-forge-20.1.20.jar",
"1.21.1 NeoForge C&B 21.1.33 (known loading issue)":"https://mediafilez.forgecdn.net/files/7441/123/chisels-and-bits-neoforge-21.1.33.jar"
}
OUT=Path("audit-output");OUT.mkdir(exist_ok=True)

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"RGBBlocks-Bytecode-API-Compare/1.0"})
    with urllib.request.urlopen(req,timeout=120) as resp: return resp.read()

def clsfile(data):
    if data[:4]!=b"\xca\xfe\xba\xbe": raise ValueError("not classfile")
    n=len(data); off=8
    def u1():
        nonlocal off
        a=data[off];off+=1;return a
    def u2():
        nonlocal off
        v=struct.unpack_from(">H",data,off)[0];off+=2;return v
    def u4():
        nonlocal off
        v=struct.unpack_from(">I",data,off)[0];off+=4;return v
    cp=[None]*u2(); i=1
    while i<len(cp):
        t=u1()
        if t==1:
            size=u2(); cp[i]=(t,data[off:off+size].decode("utf-8","replace"));off+=size
        elif t in (3,4): off+=4;cp[i]=(t,None)
        elif t in (5,6): off+=8;cp[i]=(t,None);i+=1
        elif t in (7,8,16,19,20): cp[i]=(t,u2())
        elif t in (9,10,11,12,17,18): cp[i]=(t,u2(),u2())
        elif t==15: cp[i]=(t,u1(),u2())
        else: raise ValueError(f"Unknown CP tag {t}")
        i+=1
    def utf(idx):
        p=cp[idx]
        return p[1] if p and p[0]==1 else ""
    def cname(idx):
        p=cp[idx]
        return utf(p[1]) if p and p[0]==7 else ""
    def nt(idx):
        p=cp[idx]
        return (utf(p[1]),utf(p[2])) if p and p[0]==12 else ("","")
    def attrs():
        count=u2()
        for _ in range(count):
            u2(); offsz=u4()
            nonlocal_off[0] = offsz # see skip below
            skip(offsz)
    def skip(n):
        nonlocal off
        off+=n
    # class header: access, this, super, interfaces
    u2();selfclass=cname(u2()); u2()
    for _ in range(u2()):u2()
    fields=set();methods=set()
    for collection in (fields,methods):
        for _ in range(u2()):
            u2();name=utf(u2());desc=utf(u2());collection.add((name,desc))
            for _ in range(u2()): u2();skip(u4())
    for _ in range(u2()):u2();skip(u4())
    classrefs=set();methodrefs=set();fieldrefs=set()
    for p in cp[1:]:
        if p is None: continue
        if p[0]==7: classrefs.add(cname(cp.index(p))) # avoid if duplicate pointer index but same name
        elif p[0] in (10,11): methodrefs.add((cname(p[1]),*nt(p[2])))
        elif p[0]==9: fieldrefs.add((cname(p[1]),*nt(p[2])))
    return {"self":selfclass,"classes":classrefs,"methodrefs":methodrefs,"fieldrefs":fieldrefs,
            "methods":methods,"fields":fields,
            "all_utf8":[p[1] for p in cp if p is not None and p[0]==1]}

def jarclasses(b):
    result={}
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        for name in z.namelist():
            if name.endswith(".class"):
                try: c=clsfile(z.read(name)); result[c["self"]]=c
                except Exception as exc:
                    print("parse failed",name,str(exc))
    return result

def main():
    original=jarclasses(get(SOURCE_URL))
    rgb=[v for k,v in original.items() if k.startswith("com/rgbblocks/")]
    boundary_refs=set()
    owners=defaultdict(list)
    for c in rgb:
        for target in c["classes"]:
            if "chiselsandbits" in target.lower():
                boundary_refs.add(target)
        for owner,method,desc in c["methodrefs"]:
            if "chiselsandbits" in owner.lower():
                owners[owner].append({"method":method,"descriptor":desc,"original_rgb_class":c["self"]})
    boundary_refs.update(owners)
    textual=[]
    for c in rgb:
        for s in c["all_utf8"]:
            if "chiselsandbits" in s.lower() or "scena" in s.lower():
                textual.append({"original_rgb_class":c["self"],"utf8_value":s[:1000]})
    print("Original RGB classes successfully parsed",len(rgb),
          "direct C&B class references",len(boundary_refs),
          "textual or reflective strings",len(textual),flush=True)
    for entry in textual[:55]:
        print("  reflective or string:",entry,flush=True)
    result={"source":"Public original 1.3.1 NeoForge released binary",
            "original_minecraft":"26.1.2",
            "timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "rgb_class_count":len(rgb),
            "cnb_textual_or_reflective_strings":textual,
            "cnb_referenced_class_count":len(boundary_refs),
            "cnb_classes_referenced":sorted(boundary_refs),
            "cnb_target_comparisons":{},
            "limitations":"Static direct symbols only. Does not check Mixin string-injection target descriptors, inherited methods, ABI remapping or actual game runtime."}
    for name,url in TARGETS.items():
        classes=jarclasses(get(url))
        missing_classes=sorted(boundary_refs-set(classes))
        found_classes=sorted(boundary_refs&set(classes))
        missing_direct_methods=[]
        for owner,methods in owners.items():
            if owner not in classes:continue
            available=classes[owner]["methods"]
            for m in methods:
                if (m["method"],m["descriptor"]) not in available:
                    missing_direct_methods.append({"owner":owner,**m})
        entry={"target_url":url,"target_compiled_classes":len(classes),
               "original_cnb_boundary_classes_found":len(found_classes),
               "original_cnb_boundary_classes_missing":len(missing_classes),
               "missing_class_names":missing_classes,
               "direct_declaration_method_misses":missing_direct_methods,
               "note":"Direct method declaration misses can be inherited, renamed, mapped differently or otherwise valid; a recompile is required."}
        result["cnb_target_comparisons"][name]=entry
        print(name, "matched",len(found_classes),"missing classes",len(missing_classes),
              "potential direct method mismatches",len(missing_direct_methods),flush=True)
        if missing_classes:print("First class misses:",missing_classes[:20],flush=True)
        if missing_direct_methods:print("First method misses:",missing_direct_methods[:8],flush=True)
    (OUT/"chisels-and-bits-api-symbol-diff.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Target API diff complete; an actual RGB source recompile and gameplay tests remain necessary.",flush=True)

if __name__=="__main__":
    main()
