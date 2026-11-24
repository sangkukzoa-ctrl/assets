#!/usr/bin/env python3
"""Offline test of exact owner source release bootstrap and SHA guard.

A GitHub unpublished DRAFT release may return 404 from GET /releases/tags;
authenticated GET /releases can still enumerate it. Simulate this without
network to prevent the owner being asked to upload the source twice.
Never publish or fetch the owner's Modrinth distribution.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib, importlib.util, io, json, os, urllib.error

SCRIPT=Path("rgb-blocks-compat/stage_owner_original.py")
spec=importlib.util.spec_from_file_location("rgb_owner_source_stager",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
TAG="rgbblocks-131-private-original-source"
PAYLOAD=b"RGB-Blocks-1.3.1-OWNER-SOURCE-COMPLETE.test-hash-only"
FILE_ID=27510
OWNER=module.CANONICAL_NAME
required_hash=hashlib.sha256(PAYLOAD).hexdigest()
module.EXPECTED_BUNDLE=required_hash

release={
  "id":52,
  "tag_name":TAG,
  "draft":True,
  "assets":[{"id":FILE_ID,"name":OWNER}],
}
hits=[]
class FakeResponse(io.BytesIO):
    pass

def fake_urlopen(request,timeout=0):
    url=request.full_url if hasattr(request,"full_url") else request
    hits.append(url)
    header=request.headers.get("Authorization") if hasattr(request,"headers") else None
    assert header=="Bearer fake-test-token",("Owner source request lost authenticated token",url)
    assert "modrinth" not in url and "forgecdn" not in url
    if "/releases/tags/" in url:
        raise urllib.error.HTTPError(url,404,"Draft release hidden from tag lookup",{},None)
    if "/releases?per_page=" in url:
        return FakeResponse(json.dumps([release]).encode("utf-8"))
    if "/releases/assets/" in url:
        return FakeResponse(PAYLOAD)
    raise AssertionError("Unexpected source URL: "+url)

env={
    "GH_TOKEN":"fake-test-token",
    "RGB_OWNER_SOURCE_RELEASE_TAG":TAG,
    "GITHUB_REPOSITORY":"sangkukzoa-ctrl/assets",
}
with TemporaryDirectory(prefix="rgb-private-source-release-test-") as temp:
    bundle=Path(temp)/OWNER
    with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",
                                                side_effect=fake_urlopen):
        assert module.private_owner_source_release(bundle)
        assert bundle.read_bytes()==PAYLOAD
        assert len(hits)==3,("Expected draft-tag 404 then draft list then asset",hits)
        assert "/releases/tags/" in hits[0]
        assert "/releases?per_page=100&page=1" in hits[1]
        assert "/releases/assets/" in hits[2]
    bundle.unlink()
    hits.clear()

    def fake_public(request,timeout=0):
        return FakeResponse(json.dumps({**release,"draft":False}).encode("utf-8"))
    with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",
                                                side_effect=fake_public):
        try:module.private_owner_source_release(bundle)
        except RuntimeError as err:
            assert "DRAFT" in str(err),str(err)
        else:raise AssertionError("Public author-source Release was accepted")
        assert not bundle.exists()

    def wrong_bytes(request,timeout=0):
        url=request.full_url
        if "/releases/tags/" in url:
            return FakeResponse(json.dumps(release).encode("utf-8"))
        if "/releases/assets/" in url:
            return FakeResponse(b"tampered author archive")
        raise AssertionError(url)
    with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",
                                                side_effect=wrong_bytes):
        try:module.private_owner_source_release(bundle)
        except RuntimeError as err:
            assert "SHA-256 mismatch" in str(err),str(err)
        else:raise AssertionError("Corrupt owner-source bytes were accepted")
        assert not bundle.exists() and not bundle.with_name(bundle.name+".partial").exists()

    def missing_release(request,timeout=0):
        url=request.full_url
        if "/releases/tags/" in url:
            raise urllib.error.HTTPError(url,404,"not found",{},None)
        if "/releases?per_page=" in url:
            return FakeResponse(b"[]")
        raise AssertionError(url)
    with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",
                                                side_effect=missing_release):
        try:module.private_owner_source_release(bundle)
        except RuntimeError as err:
            assert "not provisioned" in str(err),str(err)
        else:raise AssertionError("Missing author source Release silently bypassed")
        assert not bundle.exists()

# Direct original-pair path: simulate both original SHA-locked archive
# responses and verify the same private-release and fail-closed rules.
fabric_bytes=b"test owner-original Fabric TAR"
neo_bytes=b"test owner-original NeoForge ZIP"
module.EXPECTED_FABRIC=hashlib.sha256(fabric_bytes).hexdigest()
module.EXPECTED_NEO_RAW=hashlib.sha256(neo_bytes).hexdigest()
pair_assets=[{"id":30001,"name":module.FABRIC_NAME},
             {"id":30002,"name":module.NEO_RAW_NAME}]
pair_release={**release,"assets":pair_assets}
with TemporaryDirectory(prefix="rgb-owner-pair-") as temp:
    root=Path(temp)
    canonical=root/module.CANONICAL_NAME
    fabric=root/module.FABRIC_NAME
    neo=root/module.NEO_RAW_NAME
    requests=[]
    def pair_urlopen(request,timeout=0):
        url=request.full_url
        requests.append(url)
        assert request.headers.get("Authorization")=="Bearer fake-test-token"
        if "/releases/tags/" in url:
            return FakeResponse(json.dumps(pair_release).encode("utf-8"))
        if url.endswith("/30001"):
            return FakeResponse(fabric_bytes)
        if url.endswith("/30002"):
            return FakeResponse(neo_bytes)
        raise AssertionError("Unexpected request "+url)
    with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",side_effect=pair_urlopen):
        assert module.private_owner_source_release(canonical,(fabric,neo))=="raw_pair"
        assert fabric.read_bytes()==fabric_bytes and neo.read_bytes()==neo_bytes
        assert not canonical.exists() and len(requests)==3
    fabric.unlink()
    neo.unlink()
    for rejected in (
        {**pair_release,"draft":False},
        {**pair_release,"assets":pair_assets[:1]},
        {**pair_release,"assets":pair_assets+[pair_assets[0]]},
    ):
        requests.clear()
        with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",
                  return_value=FakeResponse(json.dumps(rejected).encode("utf-8"))) as call:
            try:module.private_owner_source_release(canonical,(fabric,neo))
            except RuntimeError:pass
            else:raise AssertionError("Unsafe or incomplete original pair accepted")
            assert call.call_count==1 and not fabric.exists() and not neo.exists()
    def corrupt_pair(request,timeout=0):
        if request.full_url.endswith("/30002"):
            return FakeResponse(b"corrupt NeoForge")
        return pair_urlopen(request,timeout)
    with patch.dict(os.environ,env),patch.object(module.urllib.request,"urlopen",side_effect=corrupt_pair):
        try:module.private_owner_source_release(canonical,(fabric,neo))
        except RuntimeError as error:assert "SHA-256 mismatch" in str(error)
        else:raise AssertionError("Unverified original pair was accepted")
        assert not neo.exists() and not neo.with_name(neo.name+".partial").exists()

# Real zipfile staging method with canonical and arbitrary nested source
# roots. Actual owner archives are verified separately by stage() SHA locks.
import zipfile
for prefix in ("neoforge/","owner project/NeoForge original/",""):
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,"w") as z:
        z.writestr(prefix+"src/main/java/com/rgbblocks/RgbBlocksMod.java",b"entrypoint")
        z.writestr(prefix+"src/main/java/com/rgbblocks/runtime/RGBRuntime.java",b"runtime")
        z.writestr(prefix+"src/main/resources/META-INF/neoforge.mods.toml",b"metadata")
        z.writestr(prefix+"src/main/resources/rgbblocks.mixins.json",b"mixin")
        z.writestr(prefix+"build/generated/noise.java",b"ignored")
    recorded={}
    stats={"neo_java":0}
    with zipfile.ZipFile(memory) as z:
        module.stage_neo_java(z,lambda root,rel,data:recorded.update({(root.name,rel):data}),stats)
    assert stats["neo_java"]==2 and len(recorded)==4
    assert recorded["neoforge","com/rgbblocks/RgbBlocksMod.java"]==b"entrypoint"
    assert recorded["resources","META-INF/neoforge.mods.toml"]==b"metadata"
print("RGB_OWNER_DIRECT_ORIGINAL_PAIR_TRANSPORT_PASS",json.dumps({
    "original_pair_draft_download":True,"both_sha_verified":True,
    "incomplete_duplicate_public_rejected":True,"corrupt_neo_rejected":True,
    "full_zip_root_and_core_zip_supported":True,"native_build_not_claimed":True
}),flush=True)

print("RGB_OWNER_PRIVATE_DRAFT_SOURCE_TRANSPORT_PASS",
      json.dumps({"draft_404_fallback":True,
                  "authenticated_source_download":True,
                  "public_draft_required":True,
                  "wrong_sha_rejected":True,
                  "missing_source_hard_fail":True,
                  "public_rgb_mod_requests":0}),flush=True)
