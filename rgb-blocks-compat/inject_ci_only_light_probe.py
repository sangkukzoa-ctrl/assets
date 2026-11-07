#!/usr/bin/env python3
"""CI-only light propagation telemetry (not part of release JAR artifacts).
Injects a client tick probe into the staged source to confirm RGB per-channel
lighting actually reaches a neighboring AIR/stone voxel in a running world.
The downloadable release JARs remain uninstrumented/original gameplay logic.
"""
import sys,pathlib
TARGET=sys.argv[1]
assert TARGET in ("fabric1211","forge1201")
base=pathlib.Path("port-work/mc1211-fabric" if TARGET=="fabric1211" else "port-work/mc1201-forge")
code=base/"src/main/java/com/rgbblocks"
probe=code/"ci/RgbPortLightProbe.java";probe.parent.mkdir(parents=True,exist_ok=True)
logic=r'''private static int ticks = 0;
private static boolean passed = false;
public static void sample() {
 if (passed) return;
 net.minecraft.client.Minecraft mc=net.minecraft.client.Minecraft.getInstance();
 if (mc==null || mc.level==null || mc.player==null) return;
 ticks++;
 if(ticks%30!=0)return;
 net.minecraft.core.BlockPos src=new net.minecraft.core.BlockPos(0,121,7);
 net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);
 int packed=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(mc.level.getBlockState(src));
 com.rgbblocks.client.lighting.RGBLightColor4 emitter=
   com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
 com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,src);
 com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
 com.rgbblocks.client.lighting.RGBLightColor8 glow=
   com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
 boolean sourceRed=packed>=0 && ((packed>>16)&255)>(packed&255)
          && ((packed>>16)&255)>((packed>>8)&255);
 boolean lightRed=glow.active() && glow.r()>glow.g() && glow.r()>glow.b();
 boolean ok=sourceRed && emitter.active() && lightRed;
 if(ok){
    passed=true;
    System.out.println("RGB_PORT_LIGHT_PROBE_PASS source="+Integer.toHexString(packed)
      +" emitted=["+emitter.r()+","+emitter.g()+","+emitter.b()+"]"
      +" neighboringLight=["+glow.r()+","+glow.g()+","+glow.b()+"] ticks="+ticks);
 }else if(ticks%120==0){
    System.out.println("RGB_PORT_LIGHT_PROBE_WAIT source="+Integer.toHexString(packed)
      +" emitted=["+emitter.r()+","+emitter.g()+","+emitter.b()+"]"
      +" neighboringLight=["+glow.r()+","+glow.g()+","+glow.b()+"] ticks="+ticks
      +" enabled="+com.rgbblocks.client.lighting.RGBRealLightEngine.enabled());
 }
}
'''
if TARGET=="fabric1211":
    probe.write_text('''package com.rgbblocks.ci;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
public final class RgbPortLightProbe {
 private RgbPortLightProbe(){}
 public static void register() {
    ClientTickEvents.END_CLIENT_TICK.register(client->sample());
 }
'''+logic+"}\n",encoding="utf-8")
    client=code/"client/RgbBlocksClient.java"
    src=client.read_text(encoding="utf-8")
    k="RGBClientConfig.initialize();"
    if k not in src:raise AssertionError("Client initializer location changed")
    src=src.replace(k,k+"\n      com.rgbblocks.ci.RgbPortLightProbe.register();")
    client.write_text(src,encoding="utf-8")
else:
    probe.write_text('''package com.rgbblocks.ci;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.event.TickEvent;
@Mod.EventBusSubscriber(modid="rgbblocks", value=Dist.CLIENT)
public final class RgbPortLightProbe {
 private RgbPortLightProbe(){}
 @SubscribeEvent public static void tick(TickEvent.ClientTickEvent e){
   if(e.phase==TickEvent.Phase.END)sample();
 }
'''+logic+"}\n",encoding="utf-8")

# A deliberately separate test-only C&B sculpted RGB block fixture: actual
# original mod class paths and the release source remain unchanged. C&B 20.1.20
# uses IBlockInformation; C&B 21.1.40 uses BlockInformation record.
server_logic=r'''
private static boolean made=false;
private static int count=0;
public static void create(net.minecraft.server.MinecraftServer server) {
 if(made || server==null)return;
 if((++count)%40!=0)return;
 try {
  var level=server.overworld();
  var pos=new net.minecraft.core.BlockPos(4,121,7);
  var state=level.getBlockState(pos);
  var reg=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(state.getBlock());
  if(reg==null || !("chiselsandbits".equals(reg.getNamespace()) && "chiseled".equals(reg.getPath()))) return;
  net.minecraft.resources.ResourceLocation id =
    net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("rgbblocks","rgb_red_186_72_96_glow");
  var rgb=net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(id).defaultBlockState();
  var tile=level.getBlockEntity(pos);
  if(tile==null)return;
  Class<?> infoClass=Class.forName(
    "FABRICINFOCLASS");
  Object info=infoClass.getConstructor(net.minecraft.world.level.block.state.BlockState.class,
    java.util.Optional.class).newInstance(rgb,java.util.Optional.empty());
  Class<?> contract=Class.forName("FABRICCONTRACT");
  tile.getClass().getMethod("initializeWith",contract).invoke(tile,info);
  tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
    .invoke(tile,new net.minecraft.world.phys.Vec3(0.11,0.11,0.11));
  tile.setChanged();
  made=true;
  System.out.println("RGB_PORT_CNB_FIXTURE_PASS tile="+tile.getClass().getName()
      +" rgb="+net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(rgb.getBlock())
      +" microcut=0.11x0.11x0.11");
 } catch(Throwable err){
    System.err.println("RGB_PORT_CNB_FIXTURE_FAIL "+err);
    err.printStackTrace();
    // no silent false positive; retry only after another tick.
 }
}
'''
if TARGET=="fabric1211":
    server_logic=server_logic.replace("FABRICINFOCLASS","mod.chiselsandbits.api.blockinformation.BlockInformation").replace(
        "FABRICCONTRACT","mod.chiselsandbits.api.blockinformation.BlockInformation")
    fixture=code/"ci/RgbPortCnbFixture.java"
    fixture.write_text('''package com.rgbblocks.ci;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
public final class RgbPortCnbFixture {
 private RgbPortCnbFixture(){}
 public static void register(){
    ServerTickEvents.END_SERVER_TICK.register(server->create(server));
 }
'''+server_logic+"}\n",encoding="utf-8")
    mod=code/"RgbBlocksMod.java"
    source=mod.read_text(encoding="utf-8")
    needle="int paletteSize = registerRGBBlocks();"
    if needle not in source:raise AssertionError("Original Fabric mod initializer changed")
    source=source.replace(needle,needle+"\n      com.rgbblocks.ci.RgbPortCnbFixture.register();")
    mod.write_text(source,encoding="utf-8")
else:
    server_logic=server_logic.replace("FABRICINFOCLASS","mod.chiselsandbits.blockinformation.BlockInformation").replace(
        "FABRICCONTRACT","mod.chiselsandbits.api.blockinformation.IBlockInformation")
    fixture=code/"ci/RgbPortCnbFixture.java"
    fixture.write_text('''package com.rgbblocks.ci;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.server.ServerLifecycleHooks;
@Mod.EventBusSubscriber(modid="rgbblocks")
public final class RgbPortCnbFixture {
 private RgbPortCnbFixture(){}
 @SubscribeEvent public static void onServerTick(TickEvent.ServerTickEvent e){
   if(e.phase==TickEvent.Phase.END)create(ServerLifecycleHooks.getCurrentServer());
 }
'''+server_logic+"}\n",encoding="utf-8")
print("CI_ONLY_CNB_FIXTURE",TARGET,fixture,flush=True)

print("CI_ONLY_RGB_LIGHT_PROBE",TARGET,probe,flush=True)
