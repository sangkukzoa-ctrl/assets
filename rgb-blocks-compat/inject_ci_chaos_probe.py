#!/usr/bin/env python3
"""CI-ONLY chaos oracle: repeatedly rebuilt C&B RGB bits, actual source light and Scena baked mesh.

Never included in owner release JAR. Invoked only by dedicated chaotic game workflow.
"""
from pathlib import Path
import sys
assert len(sys.argv)==2 and sys.argv[1] in ("forge1201","neoforge1211")
neo=sys.argv[1]=="neoforge1211"
root=Path("port-work/mc1211-neoforge" if neo else "port-work/mc1201-forge")
ci=root/"src/main/java/com/rgbblocks/ci"
assert (ci/"RgbPortLightProbe.java").exists(), "Install real client probe first"
server=r'''package com.rgbblocks.ci;
{{SERVER_IMPORTS}}
@{{SERVER_ANNOTATION}}
public final class RgbPortChaosCnbFixture {
 private static Object lastTile=null;
 private static int ticks=0;
 @{{SUBSCRIBE}} public static void tick({{SERVER_EVENT}} event){
   {{SERVER_GUARD}}
   if(++ticks%2!=0)return;
   var server={{SERVER_OBJECT}};
   if(server==null)return;
   var world=server.overworld();
   var pos=new net.minecraft.core.BlockPos(166,121,7);
   var key=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(world.getBlockState(pos).getBlock());
   if(key==null || !"chiselsandbits".equals(key.getNamespace()) || !"chiseled".equals(key.getPath()))return;
   var tile=world.getBlockEntity(pos);
   if(tile==null || tile==lastTile)return;
   try {
      var marker=world.getBlockState(new net.minecraft.core.BlockPos(166,120,10));
      String colorName=marker.is(net.minecraft.world.level.block.Blocks.DIAMOND_BLOCK)
             ? "rgb_blue_8_85_209_glow"
             : marker.is(net.minecraft.world.level.block.Blocks.EMERALD_BLOCK)
               ? "rgb_green_59_209_25_glow" : "rgb_red_186_72_96_glow";
      var rgb=net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(
          {{BLOCK_ID}}("rgbblocks",colorName)).defaultBlockState();
      var info=Class.forName("{{INFO}}");
      var contract=Class.forName("{{CONTRACT}}");
      var state=info.getConstructor(net.minecraft.world.level.block.state.BlockState.class,
                      java.util.Optional.class).newInstance(rgb,java.util.Optional.empty());
      try(java.lang.AutoCloseable batch=(java.lang.AutoCloseable)tile.getClass().getMethod("batch").invoke(tile)){
         tile.getClass().getMethod("initializeWith",contract).invoke(tile,state);
         tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
             .invoke(tile,new net.minecraft.world.phys.Vec3(15.5/16.0,15.5/16.0,15.5/16.0));
      }
      tile.setChanged();
      var finalId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(world.getBlockState(pos).getBlock());
      if(!"chiselsandbits:chiseled".equals(String.valueOf(finalId)) || world.getBlockEntity(pos)!=tile)
          throw new IllegalStateException("C&B collapsed after sculpture: "+finalId);
      var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
      var getter=stats.getClass().getMethod("getStateCounts"); getter.setAccessible(true);
      int total=0;
      for(var entry:((java.util.Map<?,?>)getter.invoke(stats)).entrySet())
         total+=((Number)entry.getValue()).intValue();
      if(total!=4095)throw new IllegalStateException("Expected 4095 real microbits, got "+total);
      lastTile=tile;
      System.out.println("RGB_PORT_CHAOS_SCULPT_PASS color="+colorName+" bits="+total+" pos="+pos);
   }catch(Throwable error) {
      if(ticks%20==0){System.err.println("RGB_PORT_CHAOS_SCULPT_RETRY "+error);error.printStackTrace();}
   }
 }
}'''
client=r'''package com.rgbblocks.ci;
{{CLIENT_IMPORTS}}
@{{CLIENT_ANNOTATION}}
public final class RgbPortChaosOracle {
 private static int ticks=0;
 private static final int[] stable=new int[4];
 private static final boolean[] verified=new boolean[4];
 @{{SUBSCRIBE}} public static void tick({{CLIENT_EVENT}} event){
   {{CLIENT_GUARD}}
   if(++ticks%12!=0)return;
   var mc=net.minecraft.client.Minecraft.getInstance();
   if(mc==null || mc.level==null || mc.player==null)return;
   var pos=new net.minecraft.core.BlockPos(166,121,7);
   if(!mc.level.isLoaded(pos))return;
   var tile=mc.level.getBlockEntity(pos);
   if(tile==null)return;
   for(int round=0;round<4;round++){
      if(verified[round])continue;
      var markerPos=new net.minecraft.core.BlockPos(166,120,11+round);
      if(!mc.level.isLoaded(markerPos) ||
          !mc.level.getBlockState(markerPos).is(net.minecraft.world.level.block.Blocks.GOLD_BLOCK))continue;
      try{
         var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
         var counts=stats.getClass().getMethod("getStateCounts");
         counts.setAccessible(true);
         int total=0;int expected=0;
         String wanted=(round%3==0?"rgb_red_186_72_96_glow":
                     round%3==1?"rgb_blue_8_85_209_glow":"rgb_green_59_209_25_glow");
         for(var entry:((java.util.Map<?,?>)counts.invoke(stats)).entrySet()){
            var info=entry.getKey();
            java.lang.reflect.Method method;
            try{method=info.getClass().getMethod("getBlockState");}
            catch(NoSuchMethodException absent){method=info.getClass().getMethod("blockState");}
            var state=(net.minecraft.world.level.block.state.BlockState)method.invoke(info);
            var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock());
            int amount=((Number)entry.getValue()).intValue();
            total+=amount;
            if(("rgbblocks:"+wanted).equals(String.valueOf(id)))expected+=amount;
         }
         var source=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,pos);
         var neighbor=new net.minecraft.core.BlockPos(166,121,6);
         com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,neighbor);
         var adjacent=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(neighbor,0.5f,0.5f,0.5f);
         boolean color=(round%3==0?source.r()>source.g() && source.r()>source.b() &&
                   adjacent.r()>adjacent.g() && adjacent.r()>adjacent.b():
                   round%3==1?source.b()>source.r() && source.b()>source.g() &&
                   adjacent.b()>adjacent.r() && adjacent.b()>adjacent.g():
                   source.g()>source.r() && source.g()>source.b() &&
                   adjacent.g()>adjacent.r() && adjacent.g()>adjacent.b());
         var modelData=tile.getClass().getMethod("getBlockModelData").invoke(tile);
         var keyType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IModelDataKey");
         var props=Class.forName("mod.chiselsandbits.registrars.ModModelProperties");
         var known=props.getField("KNOWN_LAYER_MODEL_PROPERTY").get(null);
         var dataType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IBlockModelData");
         var models=dataType.getMethod("getData",keyType).invoke(modelData,known);
         int quads=0;
         if(models instanceof java.util.Map<?,?> layers){
            for(var model:layers.values()){
               if(model instanceof net.minecraft.client.resources.model.BakedModel baked){
                  for(var face:net.minecraft.core.Direction.values())
                     quads+=baked.getQuads(null,face,net.minecraft.util.RandomSource.create()).size();
                  quads+=baked.getQuads(null,null,net.minecraft.util.RandomSource.create()).size();
               }
            }
         }
         boolean okay=total==4095 && expected==4095 && source.active() && adjacent.active() &&
                   color && quads>0;
         stable[round]=okay?stable[round]+1:0;
         if(stable[round]>=3){
            verified[round]=true;
            System.out.println("RGB_PORT_CHAOS_ROUND_PASS round="+round+" color="+wanted+
                 " bits="+total+" actualBakedQuads="+quads+" source="+source+" adjacent="+adjacent);
         }else if(ticks%120==0){
            System.out.println("RGB_PORT_CHAOS_WAIT round="+round+" expected="+expected+
                 " bits="+total+" quads="+quads+" source="+source+" adjacent="+adjacent);
         }
      }catch(Throwable err){
         stable[round]=0;
         if(ticks%120==0)System.err.println("RGB_PORT_CHAOS_ORACLE_ERROR round="+round+" "+err);
      }
   }
 }
}'''
if neo:
    args={
        "SERVER_IMPORTS":"import net.neoforged.bus.api.SubscribeEvent;\nimport net.neoforged.fml.common.EventBusSubscriber;\nimport net.neoforged.neoforge.event.tick.ServerTickEvent;",
        "SERVER_ANNOTATION":'EventBusSubscriber(modid="rgbblocks")',
        "SERVER_EVENT":"ServerTickEvent.Post","SUBSCRIBE":"SubscribeEvent","SERVER_GUARD":"","SERVER_OBJECT":"event.getServer()",
        "BLOCK_ID":"net.minecraft.resources.ResourceLocation.fromNamespaceAndPath",
        "INFO":"mod.chiselsandbits.api.blockinformation.BlockInformation",
        "CONTRACT":"mod.chiselsandbits.api.blockinformation.BlockInformation",
        "CLIENT_IMPORTS":"import net.neoforged.api.distmarker.Dist;\nimport net.neoforged.bus.api.SubscribeEvent;\nimport net.neoforged.fml.common.EventBusSubscriber;\nimport net.neoforged.neoforge.client.event.ClientTickEvent;",
        "CLIENT_ANNOTATION":'EventBusSubscriber(modid="rgbblocks",value=Dist.CLIENT)',
        "CLIENT_EVENT":"ClientTickEvent.Post","CLIENT_GUARD":""}
else:
    args={
        "SERVER_IMPORTS":"import net.minecraftforge.eventbus.api.SubscribeEvent;\nimport net.minecraftforge.event.TickEvent;\nimport net.minecraftforge.fml.common.Mod;\nimport net.minecraftforge.server.ServerLifecycleHooks;",
        "SERVER_ANNOTATION":'Mod.EventBusSubscriber(modid="rgbblocks")',
        "SERVER_EVENT":"TickEvent.ServerTickEvent","SUBSCRIBE":"SubscribeEvent","SERVER_GUARD":"if(event.phase!=TickEvent.Phase.END)return;",
        "SERVER_OBJECT":"ServerLifecycleHooks.getCurrentServer()",
        "BLOCK_ID":"new net.minecraft.resources.ResourceLocation",
        "INFO":"mod.chiselsandbits.blockinformation.BlockInformation",
        "CONTRACT":"mod.chiselsandbits.api.blockinformation.IBlockInformation",
        "CLIENT_IMPORTS":"import net.minecraftforge.api.distmarker.Dist;\nimport net.minecraftforge.eventbus.api.SubscribeEvent;\nimport net.minecraftforge.event.TickEvent;\nimport net.minecraftforge.fml.common.Mod;",
        "CLIENT_ANNOTATION":'Mod.EventBusSubscriber(modid="rgbblocks",value=Dist.CLIENT)',
        "CLIENT_EVENT":"TickEvent.ClientTickEvent","CLIENT_GUARD":"if(event.phase!=TickEvent.Phase.END)return;"}
for key,value in args.items():
    server=server.replace("{{"+key+"}}",value)
    client=client.replace("{{"+key+"}}",value)
assert "{{" not in server and "{{" not in client
(ci/"RgbPortChaosCnbFixture.java").write_text(server,encoding="utf-8")
(ci/"RgbPortChaosOracle.java").write_text(client,encoding="utf-8")
print("RGB_PORT_CHAOS_CI_ONLY_REAL_CNB_4095_BITS_MESH_AND_LIGHT",sys.argv[1],flush=True)
