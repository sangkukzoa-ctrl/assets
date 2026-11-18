#!/usr/bin/env python3
"""CI-only real integrated SingleplayerServer test.

Inject after the original RGB probe + two-client + mixed C&B probe.
The Java source only exists in an instrumented CI workspace; never in
the distributable/native release JAR.
"""
from pathlib import Path
import sys
assert len(sys.argv)==2 and sys.argv[1] in ("neoforge1211","forge1201")
loader=sys.argv[1]
root=Path("port-work/mc1211-neoforge" if loader=="neoforge1211" else "port-work/mc1201-forge")
path=root/"src/main/java/com/rgbblocks/ci/RgbPortLightProbe.java"
code=path.read_text(encoding="utf-8")
assert code.count("private static int tickCallbackCount = 0;")==1
code=code.replace("private static int tickCallbackCount = 0;",
    "private static int tickCallbackCount = 0;\nprivate static boolean integratedChecked = false;",1)
anchor=" net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
logic=r'''
 if(Boolean.getBoolean("rgbport.ci.integrated") && !integratedChecked && ticks%30==0) {
   var server=mc.getSingleplayerServer();
   var cnb=new net.minecraft.core.BlockPos(4,121,7);
   var mixed=new net.minecraft.core.BlockPos(6,121,7);
   if(server!=null && mc.player!=null && mc.level!=null
       && "minecraft:overworld".equals(mc.level.dimension().location().toString())
       && mc.level.isLoaded(src) && mc.level.isLoaded(cnb) && mc.level.isLoaded(mixed)) {
      var srcColor=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
      com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
      var neighbors=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
      var red=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,cnb);
      var mixedColor=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,mixed);
      var chiseledState=mc.level.getBlockState(mixed);
      var chiseledId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(chiseledState.getBlock());
      var be=mc.level.getBlockEntity(mixed);
      boolean actualMixed=chiseledId!=null && "chiselsandbits".equals(chiseledId.getNamespace())
        && "chiseled".equals(chiseledId.getPath()) && be!=null;
      boolean lanHostCnbModelRepair=false;
      if(actualMixed) {
         try {
            var method=com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer.class
                 .getDeclaredMethod("isRemoteClientWorld",Object.class);
            method.setAccessible(true);
            lanHostCnbModelRepair=Boolean.TRUE.equals(method.invoke(null,be));
         } catch (ReflectiveOperationException | SecurityException diagnostic) {
            if(ticks%120==0)System.err.println(
               "RGB_PORT_INTEGRATED_LAN_MESH_DIAGNOSTIC "+diagnostic);
         }
      }
      boolean realRgb=srcColor.active() && srcColor.g()>srcColor.r()
        && srcColor.g()>srcColor.b() && neighbors.active()
        && neighbors.g()>neighbors.r() && neighbors.g()>neighbors.b()
        && red.active() && red.r()>red.g()
        && mixedColor.active() && mixedColor.r()>mixedColor.g()
        && mixedColor.g()>=red.g() && mixedColor.b()>=red.b();
      String worldId=com.rgbblocks.runtime.RGBRuntime.clientWorldId();
      if(actualMixed && lanHostCnbModelRepair && realRgb && !worldId.isBlank()
          && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()) {
         integratedChecked=true;
         System.out.println("RGB_PORT_INTEGRATED_LAN_HOST_MESH_GUARD_PASS"+
            " actualCnbTile="+be.getClass().getName()+
            " clientLevel="+mc.level.dimension().location()+
            " integratedServer="+server.getClass().getName());
         System.out.println("RGB_PORT_INTEGRATED_SINGLEPLAYER_PASS worldId="+worldId
            +" logicalServer="+server.getClass().getName()
            +" direct="+srcColor+" near="+neighbors+" redCnb="+red
            +" mixedCnb="+mixedColor+" ticks="+ticks);
      } else if(ticks%120==0) {
         System.out.println("RGB_PORT_INTEGRATED_WAIT server="+server.getClass().getName()
           +" source="+srcColor+" neighbor="+neighbors+" red="+red
           +" mixed="+mixedColor+" realMixedTile="+actualMixed+" world="+worldId
           +" auto="+com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()
           +" cnbLanHostMeshRepair="+lanHostCnbModelRepair);
      }
   } else if(ticks%120==0) {
      System.out.println("RGB_PORT_INTEGRATED_WAIT server="+(server==null?"NULL":server.getClass().getName())
          +" player="+(mc.player==null?"NULL":mc.player.blockPosition())
          +" world="+(mc.level==null?"NULL":mc.level.dimension().location().toString())
          +" ticks="+ticks);
   }
 }
'''
assert code.count(anchor)==1
code=code.replace(anchor,anchor+"\n"+logic,1)
path.write_text(code,encoding="utf-8")
print("RGB_PORT_CI_INTEGRATED_REAL_WORLD_PROBE",loader,path,len(code),flush=True)
