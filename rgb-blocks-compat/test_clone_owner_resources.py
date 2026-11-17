#!/usr/bin/env python3
"""Real filesystem regression: a native port MUST NEVER mutate original RGB assets.

Makes a tiny synthetic RGB block/textures/Mixin resource tree, clones it with
the actual staging helper, then rewrites the generated glass, pack and Mixin
files exactly as the two native build scripts do. Original fingerprints must
remain byte-identical. This test does not need any network or Java tools.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
from clone_owner_resources import clone_resources, must_copy

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

with TemporaryDirectory(prefix="rgb-owner-resource-cow-") as temp:
    root=Path(temp)
    author=root/"author"
    mutable=[
        "assets/rgbblocks/models/block/rgb_red_186_72_96_glass.json",
        "rgbblocks.mixins.json",
        "rgbblocks.client.mixins.json",
        "fabric.mod.json",
        "pack.mcmeta",
        "META-INF/neoforge.mods.toml",
    ]
    immutable=[
        "assets/rgbblocks/models/block/rgb_red_186_72_96_glow.json",
        "assets/rgbblocks/blockstates/rgb_red_186_72_96_glow.json",
        "assets/rgbblocks/textures/block/rgb_red_186_72_96_glow.png",
        "assets/rgbblocks/palette.json",
    ]
    baseline={}
    for rel in mutable+immutable:
        p=author/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(("SOURCE OWNER RGB 1.3.1 ORIGINAL "+rel).encode("utf-8"))
        baseline[rel]=sha(p)
    for rel in mutable:assert must_copy(author/rel),rel
    for rel in immutable:assert not must_copy(author/rel),rel
    fabric=clone_resources(author,root/"fabric-port")
    for rel in mutable+immutable:
        assert sha(fabric/rel)==baseline[rel],("Clone lost bytes",rel)
    # The generated Fabric stage mutates glass, pack and Mixin files.
    for rel in mutable:
        (fabric/rel).write_bytes(("PATCHED FABRIC "+rel).encode("utf-8"))
        assert sha(author/rel)==baseline[rel],(
            "FATAL: writing port glass/Mixin/pack changed OWNER original source",rel)
    # The native loaders must each receive detached, writeable mutable copies
    # but may share immutable blockstates and textures.
    for name in ("forge-port","neoforge-port"):
        target=clone_resources(fabric,root/name)
        for rel in mutable:
            previous=sha(fabric/rel)
            (target/rel).write_bytes(("PATCHED "+name+" "+rel).encode("utf-8"))
            assert sha(fabric/rel)==previous,(
                "FATAL: native port changed Fabric intermediate source",name,rel)
            assert sha(author/rel)==baseline[rel]
        for rel in immutable:
            assert sha(target/rel)==baseline[rel],(
                "Immutable source resource changed",name,rel)

print("RGB_OWNER_COW_RESOURCE_CLONE_PASS",
      "original_sha_unchanged=10 distinct_native_copies=3 copy_on_write_safe=true",
      flush=True)
