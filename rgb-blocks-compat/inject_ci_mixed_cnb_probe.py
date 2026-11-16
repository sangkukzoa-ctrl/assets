#!/usr/bin/env python3
"""Test-only C&B 16^3 RGB GLOW, ordinary RGB and transparent RGB GLASS mixture.

Inject only after inject_ci_only_light_probe.py and the target-specific
two-client probe. Zero changes to any original RGB Blocks production class.
A genuine C&B ChiseledBlockEntity is mutated using its public voxel API.
"""
from pathlib import Path
import json
import sys

assert len(sys.argv) == 2 and sys.argv[1] in ("neoforge1211", "forge1201")
target = sys.argv[1]
root = Path("port-work/mc1211-neoforge" if target == "neoforge1211" else "port-work/mc1201-forge")
palette = json.loads((root/"src/main/resources/assets/rgbblocks/palette.json").read_text())
blue = next(c for c in palette if c["blue"] >= 200 and c["red"] <= 85 and c["green"] <= 85)
blue_block = "rgb_%s_%s_%s_%s_glow" % (blue["group"], blue["red"], blue["green"], blue["blue"])
assert len(palette) == 16687
print("RGB_PORT_CNB_MIXED_BLUE_CHOICE",blue_block,flush=True)
folder = root/"src/main/java/com/rgbblocks/ci"
folder.mkdir(parents=True,exist_ok=True)

blockinfo = ("mod.chiselsandbits.api.blockinformation.BlockInformation"
    if target == "neoforge1211" else "mod.chiselsandbits.blockinformation.BlockInformation")
iface = ("mod.chiselsandbits.api.blockinformation.BlockInformation"
    if target == "neoforge1211" else "mod.chiselsandbits.api.blockinformation.IBlockInformation")
getter = "blockState" if target == "neoforge1211" else "getBlockState"

server = r'''package com.rgbblocks.ci;
{{EVENT_IMPORTS}}
@{{ANNOTATION}}
public final class RgbPortMixedCnbFixture {
 private static boolean attempted=false;
 private static int ticks=0;
 private RgbPortMixedCnbFixture(){}
 @{{SUBSCRIBE}} public static void tick({{EVENT_CLASS}} event) {
   if(!attempted && ++ticks%40==0) create({{SERVER_ACCESS}});
 }
 private static void create(net.minecraft.server.MinecraftServer server) {
   if(server==null)return;
   var level=server.overworld();
   var pos=new net.minecraft.core.BlockPos(6,121,7);
   var initial=level.getBlockState(pos);
   var initialId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(initial.getBlock());
   if(initialId==null || !"chiselsandbits".equals(initialId.getNamespace())
       || !"chiseled".equals(initialId.getPath()))return;
   var tile=level.getBlockEntity(pos);
   if(tile==null)return;
   attempted=true;
   try {
      Class<?> infoClass=Class.forName("{{BLOCKINFO}}");
      Class<?> contract=Class.forName("{{CONTRACT}}");
      var ctor=infoClass.getConstructor(net.minecraft.world.level.block.state.BlockState.class,java.util.Optional.class);
      String[] names={"rgb_red_186_72_96_glow","rgb_green_59_209_25_glow",
         "{{BLUE_BLOCK}}","rgb_green_59_209_25","rgb_green_59_209_25_glass"};
      Object[] infos=new Object[names.length];
      for(int i=0;i<names.length;i++) {
         var id=net.minecraft.resources.ResourceLocation.{{ID_CREATE}}("rgbblocks",names[i]);
         var block=net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(id);
         if(!String.valueOf(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(block)).endsWith(names[i]))
            throw new IllegalStateException("Absent RGB material "+names[i]);
         infos[i]=ctor.newInstance(block.defaultBlockState(),java.util.Optional.empty());
      }
      var initialize=tile.getClass().getMethod("initializeWith",contract);
      var clear=tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class);
      var set=tile.getClass().getMethod("setInAreaTarget",contract,net.minecraft.world.phys.Vec3.class);
      // 16^3 original RGB red GLOW, then four 1x16x16 voxel stripes:
      // 256 GREEN GLOW, 256 BLUE GLOW, 256 ordinary GREEN, 256 GREEN GLASS.
      // One real RED voxel removed. Expected remaining RED=3071.
      try(java.lang.AutoCloseable batch=(java.lang.AutoCloseable)tile.getClass().getMethod("batch").invoke(tile)) {
         initialize.invoke(tile,infos[0]);
         for(int x=0;x<4;x++) for(int y=0;y<16;y++) for(int z=0;z<16;z++) {
            var at=new net.minecraft.world.phys.Vec3((x+0.5)/16.0,(y+0.5)/16.0,(z+0.5)/16.0);
            clear.invoke(tile,at);
            set.invoke(tile,infos[x+1],at);
         }
         clear.invoke(tile,new net.minecraft.world.phys.Vec3(15.5/16.0,15.5/16.0,15.5/16.0));
      }
      tile.setChanged();
      var after=level.getBlockState(pos);
      var afterId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(after.getBlock());
      if(afterId==null || !"chiselsandbits".equals(afterId.getNamespace())
         || !"chiseled".equals(afterId.getPath()) || level.getBlockEntity(pos)!=tile)
         throw new IllegalStateException("Mixed C&B tile collapsed: "+afterId);
      var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
      var getCounts=stats.getClass().getMethod("getStateCounts");
       getCounts.setAccessible(true);
       var counts=(java.util.Map<?,?>)getCounts.invoke(stats);
      int[] byMaterial=new int[5];
      int other=0;
      for(var e:counts.entrySet()) {
         var state=(net.minecraft.world.level.block.state.BlockState)e.getKey().getClass()
            .getMethod("{{GETTER}}").invoke(e.getKey());
         String id=String.valueOf(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock()));
         int n=((Number)e.getValue()).intValue();
         boolean found=false;
         for(int i=0;i<names.length;i++) if(id.equals("rgbblocks:"+names[i])) {
            byMaterial[i]+=n;found=true;break;
         }
         if(!found) other+=n;
      }
      if(byMaterial[0]!=3071 || byMaterial[1]!=256 || byMaterial[2]!=256
            || byMaterial[3]!=256 || byMaterial[4]!=256 || other>1)
         throw new IllegalStateException("Real bit counts don't match required mixed sculpture: "
              +java.util.Arrays.toString(byMaterial)+" others="+other);
      System.out.println("RGB_PORT_CNB_MIXED_FIXTURE_PASS block="+afterId
         +" voxelCounts="+java.util.Arrays.toString(byMaterial)
         +" other="+other+" blue="+names[2]+" tilePreserved=true");
   }catch(Throwable err) {
      System.err.println("RGB_PORT_CNB_MIXED_FIXTURE_FAIL "+err);
      err.printStackTrace();
   }
 }
}
'''
if target=="neoforge1211":
    imports="""import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;"""
    subs={"EVENT_IMPORTS":imports,"ANNOTATION":'EventBusSubscriber(modid="rgbblocks")',
        "SUBSCRIBE":"SubscribeEvent","EVENT_CLASS":"ServerTickEvent.Post",
        "SERVER_ACCESS":"event.getServer()","ID_CREATE":"fromNamespaceAndPath"}
else:
    imports="""import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.server.ServerLifecycleHooks;"""
    subs={"EVENT_IMPORTS":imports,"ANNOTATION":'Mod.EventBusSubscriber(modid="rgbblocks")',
        "SUBSCRIBE":"SubscribeEvent","EVENT_CLASS":"TickEvent.ServerTickEvent",
        "SERVER_ACCESS":"net.minecraftforge.server.ServerLifecycleHooks.getCurrentServer()",
        "ID_CREATE":"forge1201FromTwoArgs"}
    # ResourceLocation(String,String) is used by the Forge 1.20.1 port.
    server=server.replace('net.minecraft.resources.ResourceLocation.{{ID_CREATE}}("rgbblocks",names[i])',
                          'new net.minecraft.resources.ResourceLocation("rgbblocks",names[i])')
for k,v in {**subs,"BLOCKINFO":blockinfo,"CONTRACT":iface,"BLUE_BLOCK":blue_block,"GETTER":getter}.items():
    server=server.replace("{{"+k+"}}",v)
assert "{{" not in server
if target=="forge1201":
    server=server.replace("if(!attempted && ++ticks%40==0) create(", 
                          "if(event.phase==TickEvent.Phase.END && !attempted && ++ticks%40==0) create(")
(folder/"RgbPortMixedCnbFixture.java").write_text(server,encoding="utf-8")

probe_path=folder/"RgbPortLightProbe.java"
probe=probe_path.read_text(encoding="utf-8")
def change(old,new):
    global probe
    assert probe.count(old)==1,(old,probe.count(old))
    probe=probe.replace(old,new,1)
change("private static int tickCallbackCount = 0;",
       "private static int tickCallbackCount = 0;\nprivate static boolean mixedPassed = false;")
# Existing dual-client probe must not terminate before the mixed fixture test.
guard="if (passed && cnbPassed && "
idx=probe.find(guard)
assert idx!=-1
end=probe.find(") return;",idx)
assert end!=-1
probe=probe[:end]+ " && mixedPassed" +probe[end:]
# Inject directly after src/near declarations in sample, before all existing
# actual-game probe logic; do not fake any direct light or C&B statistics.
anchor=" net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
mixed=r'''
 if(!mixedPassed && ticks%30==0 && mc.level.isLoaded(new net.minecraft.core.BlockPos(6,121,7))) {
   try {
     var p=new net.minecraft.core.BlockPos(6,121,7);
     var s=mc.level.getBlockState(p);
     var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(s.getBlock());
     var tile=mc.level.getBlockEntity(p);
     if(id!=null && "chiselsandbits".equals(id.getNamespace()) && "chiseled".equals(id.getPath()) && tile!=null) {
       var stats=tile.getClass().getMethod("getStatistics").invoke(tile);
       var getCounts=stats.getClass().getMethod("getStateCounts");
       getCounts.setAccessible(true);
       var counts=(java.util.Map<?,?>)getCounts.invoke(stats);
       int[] byMaterial=new int[5];
       String[] expected={"rgb_red_186_72_96_glow","rgb_green_59_209_25_glow",
            "{{BLUE_BLOCK}}","rgb_green_59_209_25","rgb_green_59_209_25_glass"};
       int other=0;
       for(var en:counts.entrySet()) {
         var block=(net.minecraft.world.level.block.state.BlockState)
             en.getKey().getClass().getMethod("{{GETTER}}").invoke(en.getKey());
         String name=String.valueOf(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(block.getBlock()));
         int amount=((Number)en.getValue()).intValue();
         boolean found=false;
         for(int i=0;i<expected.length;i++) if(name.equals("rgbblocks:"+expected[i])) {
           byMaterial[i]+=amount;found=true;break;
         }
         if(!found)other+=amount;
       }
       boolean bits=byMaterial[0]==3071 && byMaterial[1]==256
         && byMaterial[2]==256 && byMaterial[3]==256 && byMaterial[4]==256 && other<=1;
       com.rgbblocks.client.lighting.RGBRealLightEngine.refreshCnbBlockEntity(tile);
       var mixedEmitter=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,p);
       var pureEmitter=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(
          mc.level,new net.minecraft.core.BlockPos(4,121,7));
       var neighborPos=new net.minecraft.core.BlockPos(6,121,6);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,neighborPos);
       var mixedLight=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(neighborPos,0.5f,0.5f,0.5f);
       if(bits && mixedEmitter.active() && pureEmitter.active()
          && (mixedEmitter.g()>pureEmitter.g() || mixedEmitter.b()>pureEmitter.b())
          && mixedLight.active()) {
          mixedPassed=true;
          System.out.println("RGB_PORT_CNB_MIXED_PROBE_PASS counts="+java.util.Arrays.toString(byMaterial)
            +" pure="+pureEmitter+" mixed="+mixedEmitter
            +" neighbor="+mixedLight+" ticks="+ticks);
       } else if(ticks%120==0) {
          System.out.println("RGB_PORT_CNB_MIXED_WAIT counts="+java.util.Arrays.toString(byMaterial)
            +" other="+other+" pure="+pureEmitter+" mixed="+mixedEmitter
            +" neighbor="+mixedLight+" ticks="+ticks);
       }
     }
   } catch(Throwable err) {
     if(ticks%120==0)System.out.println("RGB_PORT_CNB_MIXED_WAIT_EXCEPTION "+err);
   }
 }
'''
mixed=mixed.replace("{{BLUE_BLOCK}}",blue_block).replace("{{GETTER}}",getter)
change(anchor,anchor+"\n"+mixed)
probe_path.write_text(probe,encoding="utf-8")
print("CI_ONLY_MIXED_CNB_RGB_GLASS",target,len(server),len(probe),flush=True)
