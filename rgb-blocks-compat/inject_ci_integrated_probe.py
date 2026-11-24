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
# Only the new LAN scenario retains this probe after prior checks finish.
guard_start=code.index("if (passed && cnbPassed && ")
guard_end=code.index(") return;",guard_start)
code=code[:guard_end]+' && !Boolean.getBoolean("rgbport.ci.lanHost") && !Boolean.getBoolean("rgbport.ci.lanGuest")'+code[guard_end:]
logic += r'''
 if(Boolean.getBoolean("rgbport.ci.lanHost") || Boolean.getBoolean("rgbport.ci.lanGuest")) {
   boolean host=Boolean.getBoolean("rgbport.ci.lanHost");
   var server=mc.getSingleplayerServer();
   if(host && integratedChecked && server!=null && !lanPublished) {
     lanPublished=server.publishServer(net.minecraft.world.level.GameType.SURVIVAL,true,25569);
     if(!lanPublished)throw new IllegalStateException("Actual integrated server LAN publish failed");
     System.out.println("RGB_PORT_LAN_PUBLISHED port=25569");
   }
   if(host && lanPublished && server!=null && !lanCommandsFinished
       && java.nio.file.Files.isRegularFile(mc.gameDirectory.toPath().resolve("rgbport-lan-guest-ready"))) {
     // Execute actual registered commands on the logical server thread,
     // not synthetic client state changes. One step per sample (30 ticks).
     server.execute(()->{
       if(server.getPlayerList().getPlayerByName("RGBPortTester")==null)return;
       if(lanStep==0) {
          System.out.println("RGB_PORT_LAN_SERVER_GUEST_PRESENT player=RGBPortTester");
          server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),"rgb manual");
          server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),"rgb setbake all");
       }else if(lanStep==2) {
          server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),
              "setblock 0 121 7 rgbblocks:rgb_blue_8_85_209_glow");
       }else if(lanStep>=4 && lanStep<12) {
          server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),"rgb bake");
          System.out.println("RGB_PORT_LAN_BAKE_ISSUED index="+(lanStep-3));
       }else if(lanStep==12) {
          server.getCommands().performPrefixedCommand(server.createCommandSourceStack(),
              "setblock 0 120 9 minecraft:gold_block");
          lanCommandsFinished=true;
          System.out.println("RGB_PORT_LAN_BAKE_SEQUENCE_DONE count=8");
       }
       lanStep++;
     });
   }
   var pos=new net.minecraft.core.BlockPos(6,121,7);
   var marker=new net.minecraft.core.BlockPos(0,120,9);
   if(!lanPassed && (host?server!=null:server==null) && mc.level.isLoaded(pos)
       && mc.level.isLoaded(src) && mc.level.isLoaded(marker)
       && mc.level.getBlockState(marker).is(net.minecraft.world.level.block.Blocks.GOLD_BLOCK)
       && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
     try{
       var tile=mc.level.getBlockEntity(pos);
       if(tile!=null) {
         var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
         var getter=stats.getClass().getMethod("getStateCounts");getter.setAccessible(true);
         int total=0;
         for(var en:((java.util.Map<?,?>)getter.invoke(stats)).entrySet())total+=((Number)en.getValue()).intValue();
         var rgb=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,pos);
         var direct=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
         var data=tile.getClass().getMethod("getBlockModelData").invoke(tile);
         var keyType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IModelDataKey");
         var known=Class.forName("mod.chiselsandbits.registrars.ModModelProperties").getField("KNOWN_LAYER_MODEL_PROPERTY").get(null);
         var dataType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IBlockModelData");
         var models=dataType.getMethod("getData",keyType).invoke(data,known);
         int quads=0;
         if(models instanceof java.util.Map<?,?> map)for(var value:map.values()){
           if(value instanceof net.minecraft.client.resources.model.BakedModel baked){
             for(var face:net.minecraft.core.Direction.values())
               quads+=baked.getQuads(null,face,net.minecraft.util.RandomSource.create()).size();
             quads+=baked.getQuads(null,null,net.minecraft.util.RandomSource.create()).size();
           }
         }
         var light=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
         String worldId=com.rgbblocks.runtime.RGBRuntime.clientWorldId();
         boolean okay=total==4095 && quads>0 && rgb.active() && direct.active()
           && direct.b()>direct.r() && direct.b()>direct.g()
           && light.active() && light.b()>light.r() && light.b()>light.g() && !worldId.isBlank();
         if(okay) {
           if(++lanStableSamples>=3){
             lanPassed=true;
             System.out.println("RGB_PORT_LAN_POST_BAKE_PASS role="+(host?"HOST":"GUEST")
                 +" worldId="+worldId+" bits="+total+" actualQuads="+quads+" cnbRgb="+rgb
                 +" direct="+direct+" neighbor="+light);
           }
         }else{
           lanStableSamples=0;
           if(ticks%120==0)System.out.println("RGB_PORT_LAN_WAIT bits="+total+" quads="+quads
                +" cnb="+rgb+" direct="+direct+" light="+light+" worldId="+worldId);
         }
       }
     }catch(Throwable err){
       if(ticks%120==0)System.out.println("RGB_PORT_LAN_WAIT_EXCEPTION "+err);
     }
   }
 }
'''
code=code.replace("private static boolean integratedChecked = false;",
    "private static boolean integratedChecked = false;\nprivate static boolean lanPublished=false,lanPassed=false;\nprivate static volatile boolean lanCommandsFinished=false;\nprivate static int lanStep=0,lanStableSamples=0;",1)
assert code.count(anchor)==1
code=code.replace(anchor,anchor+"\n"+logic,1)
path.write_text(code,encoding="utf-8")
print("RGB_PORT_CI_INTEGRATED_REAL_WORLD_PROBE",loader,path,len(code),flush=True)
