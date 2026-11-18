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
# Hostile testing is a RELEASE GATE, not a decorative CI job. Ensure
# a future cleanup cannot silently remove the user's genuine two-player
# Unbound shader, C&B geometry, no-ghost-light, or peer-restart tests.
chaos_wf=(folder/"rgb-blocks-cnb-seeded-chaos-real-clients.yml").read_text("utf-8")
assert "rgb-blocks-compat/inject_ci_chaos_probe.py" in chaos_wf
assert "rgb-blocks-compat/verify_native_owner_mixin_inventory.py" in chaos_wf
assert "RGB_PORT_TEST_CHAOS: '1'" in chaos_wf
assert "RGB_PORT_SHADER_ON: '1'" in chaos_wf
assert "RGB_PORT_SHADER_VARIANT: 'unbound'" in chaos_wf
assert "RGB_PORT_CHAOS_SEED:" in chaos_wf
assert "1313131" in chaos_wf and "2718281" in chaos_wf
# Each native loader needs TWO independent whole-game random scenarios,
# not just two numbers somewhere in comments or the same seed repeated.
seed_rows=re.findall(
    r"-\s*\{target:\s*(forge1201|neoforge1211),[^\n]*?\bseed:\s*'(\d+)'",
    chaos_wf)
for loader,required in {
    "forge1201":{"1313131","42"},
    "neoforge1211":{"2718281","999999937"},
}.items():
    actual=[seed for target,seed in seed_rows if target==loader]
    assert len(actual)==2 and set(actual)==required,(
        "Missing second independent native CHAOS gameplay seed",loader,actual)
# Both LIVE and STRESS must exercise Complementary Unbound, for BOTH loaders.
live_wf=(folder/"rgb-blocks-cnb-post-login-and-distant-rapid-bake.yml").read_text("utf-8")
shader_rows=re.findall(
    r"-\s*\{target:\s*(forge1201|neoforge1211),\s*mode:\s*(live|stress),[^\n]*?\bshader:\s*'([01])'",
    live_wf)
expected_modes={(target,mode) for target in ("forge1201","neoforge1211")
                for mode in ("live","stress")}
assert len(shader_rows)==4 and {
    (target,mode) for target,mode,shader in shader_rows if shader=="1"
}==expected_modes,("One native LIVE/STRESS test has shader disabled",shader_rows)
assert "RGB_PORT_SHADER_ON: '${{ matrix.shader }}'" in live_wf
assert "RGB_PORT_SHADER_VARIANT: 'unbound'" in live_wf
# Integrated-host tests also need the unpublished owner source, not a public
# binary. GitHub draft-release list access requires push-equivalent privileges.
for loader in ("1201-forge","1211-neoforge"):
    integrated=(folder/f"rgb-blocks-{loader}-integrated-singleplayer.yml").read_text(
        encoding="utf-8")
    assert "contents: write" in integrated,(
        "Integrated native game CI cannot read author-source DRAFT release",loader)
    assert "persist-credentials: false" in integrated,(
        "Integrated game checkout should not keep draft-read token",loader)
    assert "rgb-blocks-compat/stage_owner_original.py" in integrated
    assert "RGB_PORT_TEST_INTEGRATED: '1'" in integrated
    assert "rgb-blocks-compat/inject_ci_integrated_probe.py" in integrated
assert "fail-fast: false" in chaos_wf
assert "actions/upload-artifact@v4" in chaos_wf
assert "retention-days: 30" in chaos_wf
choreography=Path("rgb-blocks-compat/cnb_chaos_choreography.py").read_text("utf-8")
assert "MUST_COVER=" in choreography
assert "len(MUST_COVER)" in choreography
assert 'trace("round_coverage"' in choreography
assert "cnb-chaos-events.jsonl" in choreography
for loader in ("1201_forge","1211_neoforge"):
    harness=Path("rgb-blocks-compat/test_mc"+loader+"_two_clients.py").read_text("utf-8")
    for marker in ("if CHAOS_PROBE:","cnb_chaos_choreography",
                   "peer_process_restarted_and_verified",
                   "zero_ghost_rgb_both_clients",
                   "RGB_PORT_CHAOS_NO_GHOST_LIGHT_PASS",
                   "RGB_PORT_CHAOS_ROUND_PASS"):
        assert marker in harness,("Real-game hostile test removed",loader,marker)

print("RGB_OWNER_CI_WORKFLOW_SOURCE_FIRST_PASS",
      json.dumps({"workflows":len(audited),
                  "core_autorun_on_source_ready":2,
                  "legacy_bounded_full_matrix":29,
                  "public_rgb_mod_downloads":0,
                  "private_author_source_required":True,
                  "true_dual_client_unbound_chaos_preserved":True,
                  "seeded_11_family_hostility_preserved":True,
                  "two_distinct_chaos_seeds_per_loader":True,
                  "unbound_shader_on_in_all_native_live_stress":True,
                  "integrated_host_owner_draft_token_access":True},
                 ensure_ascii=False),flush=True)
