#!/usr/bin/env python3
"""Real post-login C&B chisel edit / RGB light on TWO real Minecraft clients.

CI ONLY; inject after original C&B and mixed 4096-bit probes. Unlike earlier
pre-login sculpture tests, these real voxel mutations happen AFTER both real
clients joined the game. No test-side RGB source refresh is invoked.
"""
from pathlib import Path
import sys
assert len(sys.argv)==2 and sys.argv[1] in ("neoforge1211","forge1201")
target=sys.argv[1]
root=Path("port-work/mc1211-neoforge" if target=="neoforge1211" else "port-work/mc1201-forge")
ci=root/"src/main/java/com/rgbblocks/ci"
assert (ci/"RgbPortLightProbe.java").exists()
isneo=target=="neoforge1211"
java=r'''package com.rgbblocks.ci;
{{IMPORTS}}
@{{SUBSCRIBER}}
public final class RgbPortLiveCnbEditFixture {
 private static boolean first=false,second=false,third=false;
 private static int ticks=0;
 @{{SUBSCRIBE}} public static void tick({{EVENT}} event){
   {{GUARD}}
   if(++ticks%5!=0)return;
   var server={{SERVER}};
   if(server==null)return;
   var level=server.overworld();
   var pos=new net.minecraft.core.BlockPos(10,121,7);
   try {
     if(!first && level.getBlockState(new net.minecraft.core.BlockPos(12,121,7))
                     .is(net.minecraft.world.level.block.Blocks.GOLD_BLOCK)){
       var id={{RGB_ID}}("chiselsandbits","chiseled");
       var cb=net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(id);
       level.setBlock(pos,cb.defaultBlockState(),3);
       sculpt(level,pos,"rgb_blue_8_85_209_glow");
       first=true;
       System.out.println("RGB_PORT_LIVE_CNB_SERVER_BLUE_PASS realClientJoined=true");
     }
     if(first && !second && level.getBlockState(new net.minecraft.core.BlockPos(13,121,7))
                        .is(net.minecraft.world.level.block.Blocks.GOLD_BLOCK)){
       sculpt(level,pos,"rgb_green_59_209_25_glow");
       second=true;
       System.out.println("RGB_PORT_LIVE_CNB_SERVER_GREEN_PASS sameTileAfterPacket=true");
     }
     if(second && !third && level.getBlockState(new net.minecraft.core.BlockPos(14,121,7))
                        .is(net.minecraft.world.level.block.Blocks.GOLD_BLOCK)){
       sculpt(level,pos,"rgb_red_186_72_96_glow");
       third=true;
       System.out.println("RGB_PORT_LIVE_CNB_SERVER_MANUAL_RED_PASS sameTileAfterPacket=true");
     }
   }catch(Throwable err){System.err.println("RGB_PORT_LIVE_CNB_SERVER_FAIL "+err);err.printStackTrace();}
 }
 private static void sculpt(net.minecraft.server.level.ServerLevel level,
                            net.minecraft.core.BlockPos pos,String name)throws Exception{
    var tile=level.getBlockEntity(pos);
    if(tile==null)throw new IllegalStateException("No real C&B block entity at "+pos);
    var id={{RGB_ID}}("rgbblocks",name);
    var color=net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(id);
    var infoClass=Class.forName("{{BLOCK_INFO}}");
    var contract=Class.forName("{{CONTRACT}}");
    var ctor=infoClass.getConstructor(net.minecraft.world.level.block.state.BlockState.class,java.util.Optional.class);
    var information=ctor.newInstance(color.defaultBlockState(),java.util.Optional.empty());
    try(java.lang.AutoCloseable batch=(java.lang.AutoCloseable)tile.getClass().getMethod("batch").invoke(tile)){
       tile.getClass().getMethod("initializeWith",contract).invoke(tile,information);
       tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class).invoke(
            tile,new net.minecraft.world.phys.Vec3(15.5/16.0,15.5/16.0,15.5/16.0));
    }
    tile.setChanged();
    var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
    var getter=stats.getClass().getMethod("getStateCounts");
    getter.setAccessible(true);
    int expected=0,other=0;
    for(var en:((java.util.Map<?,?>)getter.invoke(stats)).entrySet()){
       var actual=(net.minecraft.world.level.block.state.BlockState)en.getKey()
         .getClass().getMethod("{{GETTER}}").invoke(en.getKey());
       String material=String.valueOf(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(actual.getBlock()));
       int count=((Number)en.getValue()).intValue();
       if(material.equals("rgbblocks:"+name))expected+=count;else other+=count;
    }
    if(expected!=4095 || other>1)throw new IllegalStateException(
         "Actual after-mutation C&B voxel count="+expected+" other="+other+" material="+name);
    System.out.println("RGB_PORT_LIVE_CNB_VOXELS_PASS name="+name+" count="+expected+" other="+other);
 }
}'''
if isneo:
    spec={
       "IMPORTS":"import net.neoforged.bus.api.SubscribeEvent;\nimport net.neoforged.fml.common.EventBusSubscriber;\nimport net.neoforged.neoforge.event.tick.ServerTickEvent;",
       "SUBSCRIBER":'EventBusSubscriber(modid="rgbblocks")',
       "SUBSCRIBE":"SubscribeEvent","EVENT":"ServerTickEvent.Post",
       "GUARD":"","SERVER":"event.getServer()",
       "RGB_ID":"net.minecraft.resources.ResourceLocation.fromNamespaceAndPath",
       "BLOCK_INFO":"mod.chiselsandbits.api.blockinformation.BlockInformation",
       "CONTRACT":"mod.chiselsandbits.api.blockinformation.BlockInformation",
       "GETTER":"blockState"}
else:
    spec={
       "IMPORTS":"import net.minecraftforge.eventbus.api.SubscribeEvent;\nimport net.minecraftforge.fml.common.Mod;\nimport net.minecraftforge.event.TickEvent;\nimport net.minecraftforge.server.ServerLifecycleHooks;",
       "SUBSCRIBER":'Mod.EventBusSubscriber(modid="rgbblocks")',
       "SUBSCRIBE":"SubscribeEvent","EVENT":"TickEvent.ServerTickEvent",
       "GUARD":"if(event.phase!=TickEvent.Phase.END)return;",
       "SERVER":"ServerLifecycleHooks.getCurrentServer()",
       "RGB_ID":"new net.minecraft.resources.ResourceLocation",
       "BLOCK_INFO":"mod.chiselsandbits.blockinformation.BlockInformation",
       "CONTRACT":"mod.chiselsandbits.api.blockinformation.IBlockInformation",
       "GETTER":"getBlockState"}
for k,v in spec.items():java=java.replace("{{"+k+"}}",v)
assert "{{" not in java
(ci/"RgbPortLiveCnbEditFixture.java").write_text(java,encoding="utf-8")
probe=ci/"RgbPortLightProbe.java";s=probe.read_text(encoding="utf-8")
def change(a,b):
  global s
  assert s.count(a)==1,(a,s.count(a))
  s=s.replace(a,b,1)
change("private static int tickCallbackCount = 0;",'''private static int tickCallbackCount = 0;
private static boolean liveBluePassed = false;
private static boolean liveCnbGreenPassed = false;
private static boolean liveManualRedPassed = false;''')
needle="if (passed && cnbPassed && "
i=s.index(needle); end=s.index(") return;",i)
s=s[:end]+" && (!Boolean.getBoolean(\"rgbport.ci.liveCnb\") || liveManualRedPassed)"+s[end:]
anchor=" net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
logic=r'''
 if(Boolean.getBoolean("rgbport.ci.liveCnb") && ticks%30==0
     && !liveManualRedPassed && mc.level.isLoaded(new net.minecraft.core.BlockPos(10,121,7))){
   try{
     var p=new net.minecraft.core.BlockPos(10,121,7);
     var tile=mc.level.getBlockEntity(p);
     if(tile!=null){
       var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
       var countMethod=stats.getClass().getMethod("getStateCounts");countMethod.setAccessible(true);
       var counts=(java.util.Map<?,?>)countMethod.invoke(stats);
       String[] names={"rgb_blue_8_85_209_glow","rgb_green_59_209_25_glow",
                      "rgb_red_186_72_96_glow"};
       int[] materialCounts=new int[3];
       for(var ent:counts.entrySet()){
         var state=(net.minecraft.world.level.block.state.BlockState)
            ent.getKey().getClass().getMethod("{{GETTER}}").invoke(ent.getKey());
         var actual=String.valueOf(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock()));
         for(int k=0;k<3;k++)if(actual.equals("rgbblocks:"+names[k]))
            materialCounts[k]+=((Number)ent.getValue()).intValue();
       }
       var source=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,p);
       var nearCnb=new net.minecraft.core.BlockPos(10,121,6);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,nearCnb);
       var illumination=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(nearCnb,0.5f,0.5f,0.5f);
       if(!liveBluePassed && materialCounts[0]==4095 && source.active()
             && source.b()>source.r() && source.b()>source.g()
             && illumination.active() && illumination.b()>illumination.r()
             && illumination.b()>illumination.g()){
           liveBluePassed=true;
           System.out.println("RGB_PORT_LIVE_CNB_BLUE_PASS counts="+java.util.Arrays.toString(materialCounts)
             +" source="+source+" adjacent="+illumination);
       }
       if(liveBluePassed && !liveCnbGreenPassed && materialCounts[1]==4095 && source.active()
             && source.g()>source.r() && source.g()>source.b()
             && illumination.active() && illumination.g()>illumination.r()
             && illumination.g()>illumination.b()){
           liveCnbGreenPassed=true;
           System.out.println("RGB_PORT_LIVE_CNB_GREEN_PASS counts="+java.util.Arrays.toString(materialCounts)
             +" source="+source+" adjacent="+illumination);
       }
       if(liveCnbGreenPassed && !liveManualRedPassed && materialCounts[2]==4095
            && source.active() && source.r()>source.g() && source.r()>source.b()
            && illumination.active() && illumination.r()>illumination.g()
            && illumination.r()>illumination.b()){
          liveManualRedPassed=true;
          System.out.println("RGB_PORT_LIVE_CNB_MANUAL_RED_BAKE_PASS counts="+
              java.util.Arrays.toString(materialCounts)+" source="+source+" adjacent="+illumination);
       } else if(ticks%120==0) {
          System.out.println("RGB_PORT_LIVE_CNB_WAIT counts="+java.util.Arrays.toString(materialCounts)
            +" source="+source+" adjacent="+illumination+" blue="+liveBluePassed
            +" green="+liveCnbGreenPassed+" redBake="+liveManualRedPassed);
       }
     }
   }catch(Throwable err){if(ticks%120==0)System.out.println("RGB_PORT_LIVE_CNB_PROBE_ERROR "+err);}
 }
'''
logic=logic.replace("{{GETTER}}",spec["GETTER"])
change(anchor,anchor+"\n"+logic)
probe.write_text(s,encoding="utf-8")
print("CI_GENUINE_POST_LOGIN_CNB_LIVE_BLUE_TO_GREEN_AND_MANUAL_RED",target,len(s),flush=True)
