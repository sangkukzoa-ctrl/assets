#!/usr/bin/env python3
"""Add extra CI-only two-peer live RGB synchronization checks to the Forge probe.

Call only after inject_ci_only_light_probe.py forge1201 in the dedicated
dual-client acceptance workflow. This never changes release source/JAR.
"""
from pathlib import Path

path = Path("port-work/mc1201-forge/src/main/java/com/rgbblocks/ci/RgbPortLightProbe.java")
source = path.read_text(encoding="utf-8")

def replace_once(old, new):
    global source
    if source.count(old) != 1:
        raise AssertionError(f"CI two-peer injection anchor changed: {old!r}, count={source.count(old)}")
    source = source.replace(old, new, 1)

replace_once(
    "private static int tickCallbackCount = 0;",
    """private static int tickCallbackCount = 0;
private static boolean syncManualSeen = false;
private static boolean syncAutoRestored = false;
private static boolean liveGreenPassed = false;"""
)
replace_once(
    "if (passed && cnbPassed) return;",
    "if (passed && cnbPassed && syncAutoRestored && liveGreenPassed) return;"
)
anchor = " net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
extra = r'''
 if (passed && cnbPassed) {
   if (!syncManualSeen && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
     syncManualSeen=true;
     System.out.println("RGB_PORT_PEER_MANUAL_SYNC_PASS worldId="
       +com.rgbblocks.runtime.RGBRuntime.clientWorldId());
   }
   if (syncManualSeen && !syncAutoRestored && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()) {
     syncAutoRestored=true;
     System.out.println("RGB_PORT_PEER_AUTO_SYNC_PASS worldId="
       +com.rgbblocks.runtime.RGBRuntime.clientWorldId());
   }
   if (syncAutoRestored && !liveGreenPassed) {
     int changed=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(mc.level.getBlockState(src));
     int cr=(changed>>16)&255, cg=(changed>>8)&255, cb=changed&255;
     if(changed>=0 && cg>cr && cg>cb && cg>=180) {
       var emitted=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
       var light=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       if(emitted.active() && emitted.g()>emitted.r() && emitted.g()>emitted.b()
             && light.active() && light.g()>light.r() && light.g()>light.b()) {
         liveGreenPassed=true;
         System.out.println("RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS color="+Integer.toHexString(changed)
           +" emitted=["+emitted.r()+","+emitted.g()+","+emitted.b()+"]"
           +" neighbor=["+light.r()+","+light.g()+","+light.b()+"] ticks="+ticks);
       } else if(ticks%120==0) {
         System.out.println("RGB_PORT_PEER_LIVE_GREEN_SYNC_WAIT emitted="+emitted
           +" neighbor="+light+" ticks="+ticks);
       }
     }
   }
 }
'''
replace_once(anchor, anchor + "\n" + extra)
path.write_text(source, encoding="utf-8")
print("CI_ONLY_TWO_CLIENT_SYNC_PROBE", path, len(source), flush=True)
