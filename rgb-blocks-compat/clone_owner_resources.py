#!/usr/bin/env python3
"""Efficient copy-on-write-safe staging of 233,627 original owner resources.

Immutable RGB textures/blockstates/ordinary models are hardlinked when the
runner filesystem permits. Every resource the legacy backports WRITE is copied
as a separate file so neither the original owner archive nor the intermediate
port can be accidentally mutated. A filesystem without hardlinks falls back
to shutil.copy2, preserving behavior.
"""
from pathlib import Path
import os
import shutil

MUTABLE_FILES={
    "pack.mcmeta",
    "fabric.mod.json",
    "rgbblocks.mixins.json",
    "rgbblocks.client.mixins.json",
    "mods.toml",
    "neoforge.mods.toml",
}
def must_copy(path):
    source=Path(path)
    return source.name in MUTABLE_FILES or (
        source.name.endswith("_glass.json")
        and "models" in source.parts and "block" in source.parts)

def copy_resource(src,dst):
    if must_copy(src):
        return shutil.copy2(src,dst)
    try:
        os.link(src,dst)
        return dst
    except (OSError,NotImplementedError):
        return shutil.copy2(src,dst)

def clone_resources(original,destination):
    original=Path(original)
    destination=Path(destination)
    if not original.is_dir():
        raise FileNotFoundError("Missing author-original resource tree: "+str(original))
    if destination.exists():
        raise FileExistsError("Refusing to merge stale resources: "+str(destination))
    shutil.copytree(original,destination,copy_function=copy_resource)
    return destination
