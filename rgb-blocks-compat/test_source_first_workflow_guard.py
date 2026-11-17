#!/usr/bin/env python3
"""Audit EVERY original-source consumer CI workflow, fully offline.

Owner requires no Modrinth RGB Blocks JAR fetching, no unbounded repeated
game builds, and no silent reuse of decompiled source. This audit checks the
actual 31 native GitHub workflow definitions, not a synthetic single sample.
"""
from pathlib import Path
import re, json

folder=Path(".github/workflows")
assert folder.is_dir()
runtime_build=re.compile(
    r"^\s*(?:run:\s*)?python3?\s+rgb-blocks-compat/build_mc1211_fabric\.py(?:\s|$)",
    re.M)
root_jobs=re.compile(r"^  ([a-zA-Z][\w-]*):\s*$",re.M)
source_ready="vars.RGB_OWNER_SOURCE_READY == 'true'"
full_matrix="vars.RGB_FULL_MATRIX == 'true'"
core={
    "rgb-blocks-cnb-seeded-chaos-real-clients.yml",
    "rgb-blocks-cnb-post-login-and-distant-rapid-bake.yml",
}
audited=[]
for file in sorted(folder.glob("rgb-blocks-*.yml")):
    txt=file.read_text(encoding="utf-8")
    actual_calls=len(runtime_build.findall(txt))
    if not actual_calls:continue
    assert "\njobs:\n" in txt,("No jobs section",file.name)
    jobs=txt.split("\njobs:\n",1)[1]
    names=root_jobs.findall(jobs)
    assert names,(file.name,"No real runtime jobs")
    assert source_ready in txt,("Missing owner source-ready gate",file.name)
    assert "stage_owner_original.py" in txt,("Missing verified original source",file.name)
    assert "RGB_OWNER_SOURCE_RELEASE_TAG" in txt,("Missing nonpublic owner source location",file.name)
    assert "GITHUB_TOKEN" in txt,("Missing scoped GitHub release token",file.name)
    assert "verify_owner_runtime_migration.py" in txt,("Missing true Java SavedData gate",file.name)
    assert "cdn.modrinth.com/data/A48MxLWx" not in txt,("Original public download leaked",file.name)
    if file.name in core:
        assert full_matrix not in txt,("Critical regression should run automatically when source is ready",file.name)
        assert jobs.count(source_ready)==len(names),(file.name,"Core jobs without source-ready gate")
    else:
        assert jobs.count(full_matrix)==len(names),(file.name,"Legacy jobs require explicit bounded FULL_MATRIX opt-in")
    # One source-provisioning call per actual compatibility intermediate build.
    stage_calls=len(re.findall(r"^\s*.*python3?\s+rgb-blocks-compat/stage_owner_original\.py(?:\s|$)",txt,re.M))
    assert stage_calls>=actual_calls,(file.name,"Some runtime build can bypass author source",actual_calls,stage_calls)
    # Do not upload original development source to public Actions artifacts.
    assert not re.search(r"(?m)^\s*path:\s*rgb-blocks-compat/owner-source/?\s*$",txt)
    audited.append({"workflow":file.name,"jobs":names,"runtime_builds":actual_calls,
                    "source_stages":stage_calls,"mode":"CORE" if file.name in core else "FULL_MATRIX"})

assert len(audited)==31,("Expected exact 2 core + 29 legacy native workflows",len(audited))
assert sum(x["mode"]=="CORE" for x in audited)==2
assert sum(x["mode"]=="FULL_MATRIX" for x in audited)==29
print("RGB_OWNER_CI_WORKFLOW_SOURCE_FIRST_PASS",
      json.dumps({"workflows":len(audited),
                  "core_autorun_on_source_ready":2,
                  "legacy_bounded_full_matrix":29,
                  "public_rgb_mod_downloads":0,
                  "private_author_source_required":True},
                 ensure_ascii=False),flush=True)
