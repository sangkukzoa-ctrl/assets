#!/usr/bin/env python3
"""Exercise BOTH real integrated-world CI-probe injections without owner assets.

Run production inject_ci_integrated_probe.py on minimal, actual-style generated
probe fixtures; assert the LAN host's live C&B block entity must satisfy
isRemoteClientWorld even when an integrated server exists, and assert both
full-game harnesses refuse PASS if that Java marker was absent.

No game-result claims. True Minecraft runs still need original source in CI.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import ast
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
inject=HERE/"inject_ci_integrated_probe.py"
assert inject.is_file()
ast.parse(inject.read_text("utf-8"),filename=str(inject))
source='''package com.rgbblocks.ci;
public class RgbPortLightProbe {
 private static int tickCallbackCount = 0;
 public void run() {
 net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);
 }
}
'''
for loader,folder,harness in (
    ("forge1201","mc1201-forge","test_mc1201_forge_two_clients.py"),
    ("neoforge1211","mc1211-neoforge","test_mc1211_neoforge_two_clients.py")
):
    with TemporaryDirectory(prefix="rgb-lan-probe-"+loader+"-") as temp:
        dest=Path(temp)/"port-work"/folder/"src/main/java/com/rgbblocks/ci/RgbPortLightProbe.java"
        dest.parent.mkdir(parents=True)
        dest.write_text(source,encoding="utf-8")
        result=subprocess.run([sys.executable,str(inject),loader],
                              cwd=temp,capture_output=True,text=True,timeout=20)
        assert result.returncode==0,(loader,result.stdout,result.stderr)
        generated=dest.read_text("utf-8")
        assert generated.count("private static boolean integratedChecked = false;")==1
        assert generated.count("RGB_PORT_INTEGRATED_SINGLEPLAYER_PASS")==1
        assert generated.count("RGB_PORT_INTEGRATED_LAN_HOST_MESH_GUARD_PASS")==1
        assert generated.count('getDeclaredMethod("isRemoteClientWorld",Object.class)')==1
        assert 'Boolean.TRUE.equals(method.invoke(null,be))' in generated
        assert 'if(actualMixed && lanHostCnbModelRepair && realRgb' in generated
        assert generated.index("RGB_PORT_INTEGRATED_LAN_HOST_MESH_GUARD_PASS") < (
               generated.index("RGB_PORT_INTEGRATED_SINGLEPLAYER_PASS"))
        assert "getSingleplayerServer()" in generated, (
            "CI fixture must actually require the integrated LAN server")
        harness_path=HERE/harness
        harness_code=harness_path.read_text("utf-8")
        ast.parse(harness_code,filename=str(harness_path))
        assert harness_code.count(
            'result["integrated_host_cnb_mesh_guard_verified"]=')==1
        assert 'RGB_PORT_INTEGRATED_LAN_HOST_MESH_GUARD_PASS' in harness_code
        assert ('"integrated_host_cnb_mesh_guard_verified","integrated_same_world_id"'
                in harness_code),("LAN host probe omitted from final acceptance",loader)
        assert harness_code.index("RGB_PORT_INTEGRATED_LAN_HOST_MESH_GUARD_PASS") > (
               harness_code.index("RGB_PORT_INTEGRATED_SINGLEPLAYER_PASS"))
        for marker in ("RGB_PORT_LAN_PUBLISHED","RGB_PORT_LAN_SERVER_GUEST_PRESENT",
                       "RGB_PORT_LAN_BAKE_SEQUENCE_DONE","RGB_PORT_LAN_POST_BAKE_PASS"):
            assert marker in harness_code,(loader,marker)
        assert '"lan_host_post_bake_verified","lan_guest_post_bake_verified"' in harness_code
        print("RGB_PORT_INTEGRATED_LAN_CNB_PROBE_INJECTION_PASS",
              loader,"generator=true host_guard_required=true"
              " final_game_acceptance_required=true",flush=True)
