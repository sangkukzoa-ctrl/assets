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
print("CI_ONLY_RGB_LIGHT_PROBE",TARGET,probe,flush=True)
