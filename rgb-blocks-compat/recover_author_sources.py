#!/usr/bin/env python3
"""Deprecated compatibility entrypoint: author-provided original Java ONLY.

Deliberately does NOT fetch a Modrinth/CurseForge RGB Blocks release and
does NOT decompile a JAR. Existing backport deltas are preserved independently
in recovered/fabric until rebased file-by-file onto verified owner source.
"""
import os
import runpy
from pathlib import Path
os.environ["RGB_OWNER_CODE_ONLY"]="1"
runpy.run_path(str(Path(__file__).with_name("stage_owner_original.py")),run_name="__main__")
