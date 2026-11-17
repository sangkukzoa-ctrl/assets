#!/usr/bin/env python3
"""CI-only dual-loader, actual Nether / overworld / Nether colored-light probe.

Inject AFTER regular, two-client and mixed C&B probes. Shipping RGB engine
source and all original 1.3.1 bit/light semantics remain unchanged.
"""
from pathlib import Path
import sys
assert len(sys.argv)==2 and sys.argv[1] in ("neoforge1211","forge1201")
platform=sys.argv[1]
root=Path("port-work/mc1211-neoforge" if platform=="neoforge1211" else "port-work/mc1201-forge")
p=root/"src/main/java/com/rgbblocks/ci/RgbPortLightProbe.java"
s=p.read_text(encoding="utf-8")
def only(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a))
    s=s.replace(a,b,1)
only("private static int tickCallbackCount = 0;",
'''private static int tickCallbackCount = 0;
private static boolean dimNetherEntered=false;
private static boolean dimNetherBluePassed=false;
private static boolean dimOverworldReturned=false;
private static boolean dimNetherReentered=false;
private static int dimBlueSamples=0;
private static int dimOverworldSamples=0;
private static String dimWorldId="";''')

anchor=" net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
logic=r'''
 // Real dimension keys from the active client Level, never mocked.
 if(Boolean.getBoolean("rgbport.ci.dimension")) {
   String dimId=mc.level.dimension().location().toString();
   String worldId=com.rgbblocks.runtime.RGBRuntime.clientWorldId();
   if("minecraft:the_nether".equals(dimId)) {
     if(!dimNetherEntered && !worldId.isBlank()) {
       dimNetherEntered=true;
       dimWorldId=worldId;
       System.out.println("RGB_PORT_DIM_NETHER_ENTER_PASS worldId="+worldId+" ticks="+ticks);
     }
     var bluePos=new net.minecraft.core.BlockPos(0,202,7);
     if(dimNetherEntered && mc.level.isLoaded(bluePos)) {
       var blueState=mc.level.getBlockState(bluePos);
       int blueValue=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(blueState);
       int r=(blueValue>>16)&255,g=(blueValue>>8)&255,b=blueValue&255;
       var blueEmitter=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,bluePos);
       var blueNeighbor=new net.minecraft.core.BlockPos(0,202,6);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,blueNeighbor);
       var blueLight=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(blueNeighbor,0.5f,0.5f,0.5f);
       boolean blue=blueValue>=0 && b>r && b>g && b>=180
         && blueEmitter.active() && blueEmitter.b()>blueEmitter.r() && blueEmitter.b()>blueEmitter.g()
         && blueLight.active() && blueLight.b()>blueLight.r() && blueLight.b()>blueLight.g()
         && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()
         && worldId.equals(dimWorldId);
       if(blue && ++dimBlueSamples>=3) {
         if(!dimNetherBluePassed) {
           dimNetherBluePassed=true;
           System.out.println("RGB_PORT_DIM_NETHER_BLUE_PASS worldId="+worldId
             +" emitter="+blueEmitter+" near="+blueLight+" ticks="+ticks);
         }
         if(dimOverworldReturned && !dimNetherReentered) {
           dimNetherReentered=true;
           System.out.println("RGB_PORT_DIM_NETHER_REENTRY_PASS worldId="+worldId
             +" emitter="+blueEmitter+" near="+blueLight+" ticks="+ticks);
         }
       } else if(!blue) {
         dimBlueSamples=0;
         if(ticks%120==0) System.out.println("RGB_PORT_DIM_NETHER_WAIT block="+blueState
             +" direct="+blueEmitter+" near="+blueLight+" worldId="+worldId);
       }
     }
     // Prevent the original reconnect oracle from sampling overworld source
     // positions from the actual Nether dimension.
     return;
   }
   if("minecraft:overworld".equals(dimId) && dimNetherBluePassed && !dimOverworldReturned) {
     var cnb=new net.minecraft.core.BlockPos(4,121,7);
     var mixed=new net.minecraft.core.BlockPos(6,121,7);
     if(mc.level.isLoaded(src) && mc.level.isLoaded(cnb) && mc.level.isLoaded(mixed)) {
       var green=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
       var greenNeighbor=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       var redCnb=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,cnb);
       var mixedCnb=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,mixed);
       boolean good=green.active() && green.g()>green.r() && green.g()>green.b()
          && greenNeighbor.active() && greenNeighbor.g()>greenNeighbor.r()
          && redCnb.active() && redCnb.r()>redCnb.g()
          && mixedCnb.active() && mixedCnb.r()>mixedCnb.g()
          && mixedCnb.g()>=redCnb.g() && mixedCnb.b()>=redCnb.b()
          && worldId.equals(dimWorldId);
       if(good && ++dimOverworldSamples>=3) {
         dimOverworldReturned=true;
         System.out.println("RGB_PORT_DIM_OVERWORLD_RETURN_PASS worldId="+worldId
           +" green="+green+" neighbor="+greenNeighbor+" cnb="+redCnb
           +" mixedCnb="+mixedCnb+" ticks="+ticks);
       } else if(!good) {
         dimOverworldSamples=0;
         if(ticks%120==0)System.out.println("RGB_PORT_DIM_OVERWORLD_WAIT green="
           +green+" neighbor="+greenNeighbor+" cnb="+redCnb
           +" mixedCnb="+mixedCnb+" worldId="+worldId);
       }
     }
   }
 }
'''
only(anchor,anchor+"\n"+logic)
p.write_text(s,encoding="utf-8")
print("CI_ONLY_TWO_DIMENSIONS_REAL_BLUE_RGB",platform,len(s),flush=True)
