#!/usr/bin/env python3
"""CI-only real two-distant-region repeated MANUAL bake + C&B MESH assertion.

Unlike prior colored-light-only tests, this examines C&B actual client-side
IBlockModelData KNOWN_LAYER_MODEL_PROPERTY BakedModel quads. A preserved
light source with an invisible/empty C&B mesh FAILS the test.
"""
from pathlib import Path
import sys
assert len(sys.argv)==2 and sys.argv[1] in ("neoforge1211","forge1201")
neo=sys.argv[1]=="neoforge1211"
root=Path("port-work/mc1211-neoforge" if neo else "port-work/mc1201-forge")
ci=root/"src/main/java/com/rgbblocks/ci"
server=r'''package com.rgbblocks.ci;
{{IMPORTS}}
@{{ANNOTATION}}
public final class RgbPortBakeStressFarCnbFixture {
 private static boolean done=false;
 private static int ticks=0;
 @{{SUBSCRIBE}} public static void tick({{EVENT}} e){
   {{GUARD}}
   if(done || ++ticks%20!=0)return;
   var server={{SERVER}};
   if(server==null)return;
   var world=server.overworld();
   var pos=new net.minecraft.core.BlockPos(134,121,7);
   var block=world.getBlockState(pos).getBlock();
   var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(block);
   if(id==null || !"chiselsandbits".equals(id.getNamespace())
             || !"chiseled".equals(id.getPath()))return;
   var tile=world.getBlockEntity(pos);
   if(tile==null)return;
   done=true;
   try{
      var color=net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(
          {{BLOCK_ID}}("rgbblocks","rgb_red_186_72_96_glow")).defaultBlockState();
      var info=Class.forName("{{INFO}}");
      var ctor=info.getConstructor(net.minecraft.world.level.block.state.BlockState.class,java.util.Optional.class);
      var state=ctor.newInstance(color,java.util.Optional.empty());
      var contract=Class.forName("{{CONTRACT}}");
      try(java.lang.AutoCloseable batch=(java.lang.AutoCloseable)tile.getClass().getMethod("batch").invoke(tile)){
         tile.getClass().getMethod("initializeWith",contract).invoke(tile,state);
         tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
             .invoke(tile,new net.minecraft.world.phys.Vec3(15.5/16.0,15.5/16.0,15.5/16.0));
      }
      tile.setChanged();
      var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
      var m=stats.getClass().getMethod("getStateCounts");m.setAccessible(true);
      int total=0;
      for(var entry:((java.util.Map<?,?>)m.invoke(stats)).entrySet())
        total+=((Number)entry.getValue()).intValue();
      if(total!=4095)throw new IllegalStateException("Far C&B bits="+total);
      System.out.println("RGB_PORT_BAKE_STRESS_FAR_SETUP_PASS pos="+pos+" bits="+total);
   }catch(Throwable err){
      System.err.println("RGB_PORT_BAKE_STRESS_FAR_SETUP_FAIL "+err);
      err.printStackTrace();
   }
 }
}'''
if neo:
  config={"IMPORTS":"import net.neoforged.bus.api.SubscribeEvent;\nimport net.neoforged.fml.common.EventBusSubscriber;\nimport net.neoforged.neoforge.event.tick.ServerTickEvent;",
    "ANNOTATION":'EventBusSubscriber(modid="rgbblocks")',"SUBSCRIBE":"SubscribeEvent",
    "EVENT":"ServerTickEvent.Post","GUARD":"","SERVER":"e.getServer()",
    "BLOCK_ID":"net.minecraft.resources.ResourceLocation.fromNamespaceAndPath",
    "INFO":"mod.chiselsandbits.api.blockinformation.BlockInformation",
    "CONTRACT":"mod.chiselsandbits.api.blockinformation.BlockInformation"}
else:
  config={"IMPORTS":"import net.minecraftforge.eventbus.api.SubscribeEvent;\nimport net.minecraftforge.fml.common.Mod;\nimport net.minecraftforge.event.TickEvent;\nimport net.minecraftforge.server.ServerLifecycleHooks;",
    "ANNOTATION":'Mod.EventBusSubscriber(modid="rgbblocks")',"SUBSCRIBE":"SubscribeEvent",
    "EVENT":"TickEvent.ServerTickEvent","GUARD":"if(e.phase!=TickEvent.Phase.END)return;",
    "SERVER":"ServerLifecycleHooks.getCurrentServer()",
    "BLOCK_ID":"new net.minecraft.resources.ResourceLocation",
    "INFO":"mod.chiselsandbits.blockinformation.BlockInformation",
    "CONTRACT":"mod.chiselsandbits.api.blockinformation.IBlockInformation"}
for key,value in config.items():server=server.replace("{{"+key+"}}",value)
assert "{{" not in server
(ci/"RgbPortBakeStressFarCnbFixture.java").write_text(server,encoding="utf-8")

p=ci/"RgbPortLightProbe.java";s=p.read_text(encoding="utf-8")
def replace(a,b):
  global s
  assert s.count(a)==1,(a,s.count(a))
  s=s.replace(a,b,1)
replace("private static int tickCallbackCount = 0;",'''private static int tickCallbackCount = 0;
private static boolean bakeStressNearVisible=false;
private static boolean bakeStressFarVisible=false;
private static int bakeStressNearSamples=0,bakeStressFarSamples=0;''')
anchor="if (passed && cnbPassed && "
i=s.index(anchor)
end=s.index(") return;",i)
s=s[:end]+' && (!Boolean.getBoolean("rgbport.ci.bakeStress") || (bakeStressNearVisible && bakeStressFarVisible))'+s[end:]
needle=" net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
code=r'''
 if(Boolean.getBoolean("rgbport.ci.bakeStress") && ticks%30==0 &&
   !(bakeStressNearVisible && bakeStressFarVisible)){
   try{
     var nearPos=new net.minecraft.core.BlockPos(6,121,7);
     var farPos=new net.minecraft.core.BlockPos(134,121,7);
     for(int region=0;region<2;region++){
       boolean isFar=region==1;
       var pos=isFar?farPos:nearPos;
       var marker=isFar?new net.minecraft.core.BlockPos(134,120,9):
                        new net.minecraft.core.BlockPos(0,120,9);
       if(!mc.level.isLoaded(pos) || !mc.level.isLoaded(marker) ||
           !mc.level.getBlockState(marker).is(net.minecraft.world.level.block.Blocks.GOLD_BLOCK))continue;
       if(isFar?bakeStressFarVisible:bakeStressNearVisible)continue;
       var tile=mc.level.getBlockEntity(pos);
       if(tile==null)continue;
       var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
       var getter=stats.getClass().getMethod("getStateCounts");
       getter.setAccessible(true);
       int total=0;
       for(var en:((java.util.Map<?,?>)getter.invoke(stats)).entrySet())
         total+=((Number)en.getValue()).intValue();
       var rgb=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,pos);
       var modelData=tile.getClass().getMethod("getBlockModelData").invoke(tile);
       var keyType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IModelDataKey");
       var props=Class.forName("mod.chiselsandbits.registrars.ModModelProperties");
       var known=props.getField("KNOWN_LAYER_MODEL_PROPERTY").get(null);
       var dataType=Class.forName("com.communi.suggestu.scena.core.client.models.data.IBlockModelData");
       var models=dataType.getMethod("getData",keyType).invoke(modelData,known);
       int nonempty=0,quads=0;
       if(models instanceof java.util.Map<?,?> modelMap){
         for(var value:modelMap.values()){
           if(value instanceof net.minecraft.client.resources.model.BakedModel baked){
             int rendered=0;
             for(var face:net.minecraft.core.Direction.values())
                rendered+=baked.getQuads(null,face,net.minecraft.util.RandomSource.create()).size();
             rendered+=baked.getQuads(null,null,net.minecraft.util.RandomSource.create()).size();
             if(rendered>0){nonempty++;quads+=rendered;}
           }
         }
       }
       boolean okay=total==4095 && rgb.active() && nonempty>0 && quads>0;
       if(okay) {
         if(isFar){
           if(++bakeStressFarSamples>=3){
             bakeStressFarVisible=true;
             System.out.println("RGB_PORT_BAKE_STRESS_FAR_MESH_PASS bits="+total
                 +" modelLayers="+nonempty+" actualQuads="+quads
                 +" rgb="+rgb+" chunk="+(pos.getX()>>4));
           }
         }else{
           if(++bakeStressNearSamples>=3){
             bakeStressNearVisible=true;
             System.out.println("RGB_PORT_BAKE_STRESS_NEAR_MESH_PASS bits="+total
                 +" modelLayers="+nonempty+" actualQuads="+quads
                 +" rgb="+rgb+" chunk="+(pos.getX()>>4));
           }
         }
       }else if(ticks%120==0){
         System.out.println("RGB_PORT_BAKE_STRESS_MESH_MISSING region="+(isFar?"FAR":"NEAR")
             +" bits="+total+" modelLayers="+nonempty+" quads="+quads
             +" rgb="+rgb+" ticks="+ticks+" player="+mc.player.blockPosition()
             +" manual="+com.rgbblocks.runtime.RGBRuntime.clientTargetManual());
       }
     }
   }catch(Throwable err){
      if(ticks%120==0){
        System.out.println("RGB_PORT_BAKE_STRESS_MODEL_EXCEPTION "+err);
        err.printStackTrace();
      }
   }
 }
'''
replace(needle,needle+"\n"+code)
p.write_text(s,encoding="utf-8")
print("RGB_PORT_CI_ACTUAL_CNB_MESH_QUADS_AFTER_REMOTE_BAKE_STRESS",("neo" if neo else "forge"),flush=True)
