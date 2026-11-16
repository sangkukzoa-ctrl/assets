#!/usr/bin/env python3
"""Strict CI-only NeoForge 1.21.1 dual-client RGB source/mode checks.

Run AFTER inject_ci_only_light_probe.py neoforge1211. The generated Java class
exists only in the isolated test workspace and is never used for releases.
"""
from pathlib import Path

target = Path("port-work/mc1211-neoforge/src/main/java/com/rgbblocks/ci/RgbPortLightProbe.java")
code = target.read_text(encoding="utf-8")

def replace_once(old, new):
    global code
    assert code.count(old) == 1, ("NeoForge two-peer CI probe drift", old, code.count(old))
    code = code.replace(old, new, 1)

replace_once(
    "private static int tickCallbackCount = 0;",
    """private static int tickCallbackCount = 0;
private static boolean dualManualSeen = false;
private static boolean dualAutoSeen = false;
private static boolean dualGreenPassed = false;
private static boolean dualRemovalPassed = false;"""
)
replace_once(
    "if (passed && cnbPassed) return;",
    "if (passed && cnbPassed && dualManualSeen && dualAutoSeen && dualGreenPassed && dualRemovalPassed) return;"
)
point = " net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
additional = r'''
 // All tests below are gated on actual initial RED source and sculpted
 // 4095-bit C&B colored emission. No synthetic light values are injected.
 if (passed && cnbPassed) {
   if(!dualManualSeen && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
     dualManualSeen=true;
     System.out.println("RGB_PORT_NEO_PEER_MANUAL_PASS worldId="
       +com.rgbblocks.runtime.RGBRuntime.clientWorldId());
   }
   if(dualManualSeen && !dualAutoSeen && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()) {
     dualAutoSeen=true;
     System.out.println("RGB_PORT_NEO_PEER_AUTO_PASS worldId="
       +com.rgbblocks.runtime.RGBRuntime.clientWorldId());
   }
   if(dualAutoSeen && !dualGreenPassed) {
     var liveState=mc.level.getBlockState(src);
     int changed=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(liveState);
     int cr=(changed>>16)&255, cg=(changed>>8)&255, cb=changed&255;
     if(changed>=0 && cg>cr && cg>cb && cg>=180) {
       var emitterNow=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
       var nearNow=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       if(emitterNow.active() && emitterNow.g()>emitterNow.r()
             && emitterNow.g()>emitterNow.b() && nearNow.active()
             && nearNow.g()>nearNow.r() && nearNow.g()>nearNow.b()) {
         dualGreenPassed=true;
         System.out.println("RGB_PORT_NEO_PEER_GREEN_PASS"
           +" direct="+emitterNow+" near="+nearNow+" ticks="+ticks);
       } else if(ticks%120==0) {
         System.out.println("RGB_PORT_NEO_PEER_GREEN_WAIT direct="+emitterNow
           +" near="+nearNow+" block="+liveState+" ticks="+ticks);
       }
     } else if(ticks%120==0) {
       System.out.println("RGB_PORT_NEO_PEER_GREEN_WAIT block="+liveState
         +" rgb="+Integer.toHexString(changed)+" ticks="+ticks);
     }
   }
   if(dualGreenPassed && !dualRemovalPassed && mc.level.getBlockState(src).isAir()) {
     var vanished=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
     com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
     var remain=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
     // The separate 4095-bit RED C&B sculpture still shines after removing GREEN.
     if(!vanished.active() && remain.active() && remain.r()>remain.g()) {
       dualRemovalPassed=true;
       System.out.println("RGB_PORT_NEO_PEER_REMOVAL_PASS"
         +" direct="+vanished+" near="+remain+" ticks="+ticks);
     } else if(ticks%120==0) {
       System.out.println("RGB_PORT_NEO_PEER_REMOVAL_WAIT"
         +" direct="+vanished+" near="+remain+" ticks="+ticks);
     }
   }
 }
'''
replace_once(point,point+"\n"+additional)
target.write_text(code,encoding="utf-8")
print("CI_ONLY_NEOFORGE_TWO_PEER_LIGHT_PROBE", target, len(code),flush=True)
