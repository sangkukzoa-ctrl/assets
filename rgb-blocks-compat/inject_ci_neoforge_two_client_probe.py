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
private static boolean dualRemovalPassed = false;
private static int manualHoldSamples = 0;
private static boolean manualDeferredPassed = false;
private static int manualBakedSamples = 0;
private static boolean manualBakedPassed = false;
private static boolean reconnectLightPassed = false;
private static boolean reconnectSawUnload = false;
private static boolean reconnectReturnPassed = false;
private static int reconnectStableSamples = 0;"""
)
replace_once(
    "if (passed && cnbPassed) return;",
    "if (passed && cnbPassed && dualManualSeen && dualAutoSeen && dualGreenPassed && dualRemovalPassed && manualDeferredPassed && manualBakedPassed) return;"
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

   if(dualRemovalPassed && !manualDeferredPassed && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
      var state=mc.level.getBlockState(src);
      int color=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(state);
      int r=(color>>16)&255,g=(color>>8)&255,b=color&255;
      if(color>=0 && g>r && g>b && g>=180) {
         var direct=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
         var held=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
         if(direct.active() && direct.g()>direct.r() && held.active() && held.r()>held.g()) {
            if(++manualHoldSamples>=6) {
               manualDeferredPassed=true;
               System.out.println("RGB_PORT_NEO_MANUAL_DEFER_PASS emitter="+direct
                 +" held="+held+" stableSamples="+manualHoldSamples+" ticks="+ticks);
            }
         } else {
            manualHoldSamples=0;
            if(ticks%120==0) System.out.println("RGB_PORT_NEO_MANUAL_DEFER_WAIT direct="+direct+" held="+held);
         }
      }
   }
   if(manualDeferredPassed && !manualBakedPassed && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
      var light=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
      if(light.active() && light.g()>light.r() && light.g()>light.b()) {
         if(++manualBakedSamples>=3) {
            manualBakedPassed=true;
            System.out.println("RGB_PORT_NEO_MANUAL_BAKE_PASS neighbor="+light
              +" stableSamples="+manualBakedSamples+" ticks="+ticks);
         }
      } else {
         manualBakedSamples=0;
         if(ticks%120==0) System.out.println("RGB_PORT_NEO_MANUAL_BAKE_WAIT light="+light+" ticks="+ticks);
      }
   } }
'''
reconnect = r'''
 // Reconnected client JVM: original source has been replaced with GREEN,
 // so never reuse the initial RED scene oracle for this fresh process.
 if(Boolean.getBoolean("rgbport.ci.reconnect")) {
   boolean far=Math.abs(mc.player.getX())>160.0;
   if(far && !mc.level.isLoaded(src) && !reconnectSawUnload) {
      reconnectSawUnload=true; reconnectStableSamples=0;
      System.out.println("RGB_PORT_NEO_CHUNK_UNLOAD_PASS pos="+mc.player.blockPosition()
         +" sourceLoaded="+mc.level.isLoaded(src)+" ticks="+ticks);
   }
   var cnb=new net.minecraft.core.BlockPos(4,121,7);
   if(!far && mc.level.isLoaded(src) && mc.level.isLoaded(cnb)) {
      int color=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(mc.level.getBlockState(src));
      int red=(color>>16)&255,green=(color>>8)&255,blue=color&255;
      var direct=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
      com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
      var nearLight=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
      var cnbState=mc.level.getBlockState(cnb);
      var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(cnbState.getBlock());
      boolean isChiseled=id!=null && "chiselsandbits".equals(id.getNamespace())
         && "chiseled".equals(id.getPath());
      if(isChiseled) com.rgbblocks.client.lighting.RGBRealLightEngine.refreshCnbBlockEntity(mc.level.getBlockEntity(cnb));
      var cnbDirect=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,cnb);
      var cnbNear=new net.minecraft.core.BlockPos(4,121,6);
      com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,cnbNear);
      var cnbLight=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(cnbNear,0.5f,0.5f,0.5f);
      boolean okay=color>=0 && green>red && green>blue && green>=180
         && direct.active() && direct.g()>direct.r()
         && nearLight.active() && nearLight.g()>nearLight.r() && nearLight.g()>nearLight.b()
         && isChiseled && cnbDirect.active() && cnbDirect.r()>cnbDirect.g()
         && cnbLight.active() && cnbLight.r()>cnbLight.g()
         && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()
         && !com.rgbblocks.runtime.RGBRuntime.clientWorldId().isBlank();
      if(okay) {
         if(++reconnectStableSamples>=3) {
            if(!reconnectLightPassed) {
               reconnectLightPassed=true;
               System.out.println("RGB_PORT_NEO_RECONNECT_LIGHT_PASS worldId="
                  +com.rgbblocks.runtime.RGBRuntime.clientWorldId()+" direct="+direct
                  +" neighbor="+nearLight+" cnb="+cnbDirect+" cnbNear="+cnbLight+" ticks="+ticks);
            }
            if(reconnectSawUnload && !reconnectReturnPassed) {
               reconnectReturnPassed=true;
               System.out.println("RGB_PORT_NEO_CHUNK_RETURN_PASS worldId="
                  +com.rgbblocks.runtime.RGBRuntime.clientWorldId()+" direct="+direct
                  +" neighbor="+nearLight+" cnb="+cnbDirect+" cnbNear="+cnbLight+" ticks="+ticks);
            }
         }
      } else {
         reconnectStableSamples=0;
         if(ticks%120==0) System.out.println("RGB_PORT_NEO_RECONNECT_WAIT block="+mc.level.getBlockState(src)
           +" direct="+direct+" neighbor="+nearLight+" cnb="+String.valueOf(id)+" cnbDirect="+cnbDirect
           +" cnbNear="+cnbLight+" auto="+com.rgbblocks.runtime.RGBRuntime.clientTargetAuto());
      }
   } else if(ticks%120==0) {
      System.out.println("RGB_PORT_NEO_RECONNECT_CHUNK_WAIT player="+mc.player.blockPosition()
        +" srcLoaded="+mc.level.isLoaded(src)+" sawUnload="+reconnectSawUnload);
   }
   return;
 }
'''
replace_once(point,point+"\n"+reconnect+"\n"+additional)
target.write_text(code,encoding="utf-8")
print("CI_ONLY_NEOFORGE_TWO_PEER_LIGHT_PROBE", target, len(code),flush=True)
