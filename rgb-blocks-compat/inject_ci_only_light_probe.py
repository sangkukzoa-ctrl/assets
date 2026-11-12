#!/usr/bin/env python3
"""CI-only light propagation telemetry (not part of release JAR artifacts).
Injects a client tick probe into the staged source to confirm RGB per-channel
lighting actually reaches a neighboring AIR/stone voxel in a running world.
The downloadable release JARs remain uninstrumented/original gameplay logic.
"""
import sys,pathlib
TARGET=sys.argv[1]
assert TARGET in ("fabric1211","forge1201","neoforge1211")
base=pathlib.Path({"fabric1211":"port-work/mc1211-fabric","forge1201":"port-work/mc1201-forge","neoforge1211":"port-work/mc1211-neoforge"}[TARGET])
code=base/"src/main/java/com/rgbblocks"
probe=code/"ci/RgbPortLightProbe.java";probe.parent.mkdir(parents=True,exist_ok=True)
logic=r'''private static int ticks = 0;
private static boolean passed = false;
private static boolean cnbPassed = false;
private static int tickCallbackCount = 0;
public static void sample() {
 if (passed && cnbPassed) return;
 net.minecraft.client.Minecraft mc=net.minecraft.client.Minecraft.getInstance();
 if (mc==null || mc.level==null || mc.player==null) return;
 ticks++;
 if(ticks==1) System.out.println("RGB_PORT_PROBE_CLIENT_TICK_ACTIVE level="+mc.level.dimension().location());
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
 if(ok && !passed){
    passed=true;
    System.out.println("RGB_PORT_LIGHT_PROBE_PASS source="+Integer.toHexString(packed)
      +" emitted=["+emitter.r()+","+emitter.g()+","+emitter.b()+"]"
      +" neighboringLight=["+glow.r()+","+glow.g()+","+glow.b()+"] ticks="+ticks);
 }else if(ticks%120==0){
    System.out.println("RGB_PORT_LIGHT_PROBE_WAIT source="+Integer.toHexString(packed)
      +" emitted=["+emitter.r()+","+emitter.g()+","+emitter.b()+"]"
      +" neighboringLight=["+glow.r()+","+glow.g()+","+glow.b()+"] ticks="+ticks
      +" enabled="+com.rgbblocks.client.lighting.RGBRealLightEngine.enabled()
      +" bootstrap="+com.rgbblocks.client.lighting.RGBRealLightEngine.bootstrapAllowedAt(near)
      +" worldId="+com.rgbblocks.runtime.RGBRuntime.clientWorldId()
      +" stateVersion="+com.rgbblocks.runtime.RGBRuntime.clientStateVersion()
      +" targetAuto="+com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()
      +" sourceCell="+com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(src,0.5f,0.5f,0.5f));
 }

 // Chisels & Bits 16^3 micro-voxel block: 4095 RGB bits + one carved air bit.
 // Original 1.3.1 C&B cache must discover and propagate its glow separately.
 if (!cnbPassed) {
   net.minecraft.core.BlockPos cnb=new net.minecraft.core.BlockPos(4,121,7);
   net.minecraft.core.BlockPos nearCnb=new net.minecraft.core.BlockPos(4,121,6);
   var chiseled=mc.level.getBlockState(cnb);
   var id=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(chiseled.getBlock());
   if(id!=null && "chiselsandbits".equals(id.getNamespace()) && "chiseled".equals(id.getPath())){
      com.rgbblocks.client.lighting.RGBRealLightEngine.refreshCnbBlockEntity(mc.level.getBlockEntity(cnb));
      com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,nearCnb);
      var cnbColor=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,cnb);
      var around=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(nearCnb,0.5f,0.5f,0.5f);
      if(cnbColor.active() && cnbColor.r()>cnbColor.g() && cnbColor.r()>cnbColor.b()
           && around.active() && around.r()>around.g() && around.r()>around.b()){
         cnbPassed=true;
         System.out.println("RGB_PORT_CNB_LIGHT_PROBE_PASS emitter=["+cnbColor.r()+","+cnbColor.g()+","+cnbColor.b()+"]"
            +" nearby=["+around.r()+","+around.g()+","+around.b()+"] ticks="+ticks);
      }else if(ticks%120==0){
         System.out.println("RGB_PORT_CNB_LIGHT_PROBE_WAIT emitter=["+cnbColor.r()+","+cnbColor.g()+","+cnbColor.b()+"]"
            +" nearby=["+around.r()+","+around.g()+","+around.b()+"] ticks="+ticks);
      }
   } else if(ticks%120==0){
     System.out.println("RGB_PORT_CNB_ID_WAIT block="+id+" state="+chiseled
         +" hasEntity="+(mc.level.getBlockEntity(cnb)!=null));
   }
 }
}
'''
# Forge-only CI diagnostics. In the real C&B 20.1.20 production client,
# distinguish absent block entity, empty/unreadable statistics, wrong bit
# states and a missing RGB engine cache. Never instrument the release JAR.
if TARGET=="forge1201":
    probe_line='''      com.rgbblocks.client.lighting.RGBRealLightEngine.refreshCnbBlockEntity(mc.level.getBlockEntity(cnb));'''
    assert probe_line in logic
    debug=r'''       if(ticks%120==0 && ticks<=360){
          Object tile=mc.level.getBlockEntity(cnb);
          System.out.println("RGB_PORT_CNB_CLIENT_DETAILS tick="+ticks+" tile="+(tile==null?"null":tile.getClass().getName())
            +" tracking="+com.rgbblocks.client.config.RGBClientConfig.ENABLE_CNB_SOURCE_TRACKING_CACHED);
          if(tile!=null){
            try{
              java.lang.reflect.Method getStatistics=tile.getClass().getMethod("getStatistics");
              getStatistics.setAccessible(true);
              Object statistics=getStatistics.invoke(tile);
              java.lang.reflect.Method getCounts=statistics.getClass().getMethod("getStateCounts");
              getCounts.setAccessible(true);
              Object counts=getCounts.invoke(statistics);
              if(counts instanceof java.util.Map<?,?> m){
                System.out.println("RGB_PORT_CNB_CLIENT_COUNTS count="+m.size());
                int logged=0;
                for(var item:m.entrySet()){
                  if(logged++>=4)break;
                  Object info=item.getKey();
                  try{
                    java.lang.reflect.Method stateMethod=info.getClass().getMethod("getBlockState");
                    stateMethod.setAccessible(true);
                    Object blockState=stateMethod.invoke(info);
                    System.out.println("RGB_PORT_CNB_CLIENT_ENTRY class="+info.getClass().getName()
                       +" state="+blockState+" count="+item.getValue());
                  }catch(Throwable e){
                    System.out.println("RGB_PORT_CNB_CLIENT_ENTRY_ERROR "+e);
                  }
                }
              }else{
                System.out.println("RGB_PORT_CNB_CLIENT_COUNTS unexpected="+counts);
              }
            }catch(Throwable e){
              System.out.println("RGB_PORT_CNB_CLIENT_STATISTICS_ERROR "+e);
            }
          }
          try{
            Class<?> engine=com.rgbblocks.client.lighting.RGBRealLightEngine.class;
            for(String name:new String[]{"CNB_PENDING","CNB_CACHE","MANUAL_CNB_SHADOW"}){
              java.lang.reflect.Field f=engine.getDeclaredField(name);
              f.setAccessible(true);
              Object value=f.get(null);
              if(value instanceof java.util.Map<?,?> m)
                System.out.println("RGB_PORT_CNB_ENGINE_MAP "+name+" size="+m.size()
                  +" fixture="+m.get(cnb.asLong()));
            }
          }catch(Throwable e){System.out.println("RGB_PORT_CNB_ENGINE_DIAGNOSTIC_ERROR "+e);}
       }
'''
    logic=logic.replace(probe_line,debug+probe_line,1)
    post=r'''       if(ticks%120==0 && ticks<=360){
          Object tile=mc.level.getBlockEntity(cnb);
          try{
            Class<?> engine=com.rgbblocks.client.lighting.RGBRealLightEngine.class;
            Object directPos=tile.getClass().getMethod("getBlockPos").invoke(tile);
            java.lang.reflect.Method posReader=engine.getDeclaredMethod("cnbBlockEntityPos",Object.class);
            posReader.setAccessible(true);
            Object enginePos=posReader.invoke(null,tile);
            java.lang.reflect.Method compute=engine.getDeclaredMethod("computeCnbSourceFromStatistics",Object.class);
            compute.setAccessible(true);
            Object source=compute.invoke(null,tile);
            java.lang.reflect.Field rgbField=source.getClass().getDeclaredField("rgb");
            java.lang.reflect.Field energyField=source.getClass().getDeclaredField("energy");
            rgbField.setAccessible(true); energyField.setAccessible(true);
            java.lang.reflect.Method activeMethod=source.getClass().getDeclaredMethod("active");
            activeMethod.setAccessible(true);
            System.out.println("RGB_PORT_CNB_DIRECT_SOURCE tilePos="+directPos+" enginePos="+enginePos
              +" active="+activeMethod.invoke(source)+" rgb="+rgbField.get(source)+" energy="+energyField.get(source));
          }catch(Throwable e){System.out.println("RGB_PORT_CNB_DIRECT_SOURCE_ERROR "+e);}
          try{
            Object tileStats=tile.getClass().getMethod("getStatistics").invoke(tile);
            Object counts=tileStats.getClass().getMethod("getStateCounts").invoke(tileStats);
            if(counts instanceof java.util.Map<?,?> m){
              for(Object info:m.keySet()){
                Object state=info.getClass().getMethod("getBlockState").invoke(info);
                int parsed=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState((net.minecraft.world.level.block.state.BlockState)state);
                System.out.println("RGB_PORT_CNB_DIRECT_STATE state="+state+" parsedRgb="+parsed);
              }
            }
          }catch(Throwable e){System.out.println("RGB_PORT_CNB_DIRECT_STATE_ERROR "+e);}
          try{
            Class<?> engine=com.rgbblocks.client.lighting.RGBRealLightEngine.class;
            for(String name:new String[]{"CNB_PENDING","CNB_CACHE","MANUAL_CNB_SHADOW"}){
              java.lang.reflect.Field f=engine.getDeclaredField(name);
              f.setAccessible(true);
              Object value=f.get(null);
              if(value instanceof java.util.Map<?,?> m)
                System.out.println("RGB_PORT_CNB_AFTER_REFRESH "+name+" size="+m.size()+" fixture="+m.get(cnb.asLong()));
            }
            java.lang.reflect.Field mode=engine.getDeclaredField("EFFECTIVE_MODE");
            mode.setAccessible(true);
            System.out.println("RGB_PORT_CNB_EFFECTIVE_MODE "+mode.get(null));
          }catch(Throwable e){System.out.println("RGB_PORT_CNB_AFTER_REFRESH_ERROR "+e);}
       }
'''
    logic=logic.replace(probe_line,probe_line+"\n"+post,1)

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
elif TARGET=="forge1201":
    probe.write_text('''package com.rgbblocks.ci;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.event.TickEvent;
@Mod.EventBusSubscriber(modid="rgbblocks", value=Dist.CLIENT)
public final class RgbPortLightProbe {
 private RgbPortLightProbe(){}
 @SubscribeEvent public static void tick(TickEvent.ClientTickEvent e){
   if(e.phase==TickEvent.Phase.END){
     if(++tickCallbackCount==1) System.out.println("RGB_PORT_FORGE_TICK_EVENT_RECEIVED");
     sample();
   }
 }
'''+logic+"}\n",encoding="utf-8")

else:
    # NeoForge 1.21.1 GAME bus events. Test-only class is not in release JAR.
    probe.write_text('''package com.rgbblocks.ci;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
@EventBusSubscriber(modid="rgbblocks",value=Dist.CLIENT)
public final class RgbPortLightProbe {
 private RgbPortLightProbe(){}
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){sample();}
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
elif TARGET=="forge1201":
    server_logic=server_logic.replace('net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("rgbblocks","rgb_red_186_72_96_glow")','new net.minecraft.resources.ResourceLocation("rgbblocks","rgb_red_186_72_96_glow")')
    server_logic=server_logic.replace("FABRICINFOCLASS","mod.chiselsandbits.blockinformation.BlockInformation").replace(
        "FABRICCONTRACT","mod.chiselsandbits.api.blockinformation.IBlockInformation")
    # C&B auto-restores a fully homogeneous 4096-bit chiseled block to its
    # ordinary full block when an initializeWith() batch closes. The old
    # fixture initialized 4096 bits and then cut one bit AFTER that collapse,
    # leaving a detached tile: client saw a normal rgbblocks:*_glow block.
    # Hold an OUTER mutation batch across both operations, then verify the
    # final real server block is still chiselsandbits:chiseled with a tile.
    old_work='''  tile.getClass().getMethod("initializeWith",contract).invoke(tile,info);
  tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
    .invoke(tile,new net.minecraft.world.phys.Vec3(0.11,0.11,0.11));
  tile.setChanged();
  made=true;
  System.out.println("RGB_PORT_CNB_FIXTURE_PASS tile="+tile.getClass().getName()
      +" rgb="+net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(rgb.getBlock())
      +" microcut=0.11x0.11x0.11");'''
    new_work='''  try (java.lang.AutoCloseable batch = (java.lang.AutoCloseable) tile.getClass()
      .getMethod("batch").invoke(tile)) {
    tile.getClass().getMethod("initializeWith",contract).invoke(tile,info);
    tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
      .invoke(tile,new net.minecraft.world.phys.Vec3(0.11,0.11,0.11));
  }
  var resultingState=level.getBlockState(pos);
  var resultingId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(resultingState.getBlock());
  var survivingTile=level.getBlockEntity(pos);
  if(resultingId==null || !"chiselsandbits".equals(resultingId.getNamespace())
     || !"chiseled".equals(resultingId.getPath()) || survivingTile!=tile){
    System.err.println("RGB_PORT_CNB_FIXTURE_RETRY actualBlock="+resultingId
        +" blockEntity="+survivingTile+" preserved="+(survivingTile==tile));
    return;
  }
  made=true;
  System.out.println("RGB_PORT_CNB_FIXTURE_PASS tile="+tile.getClass().getName()
      +" rgb="+net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(rgb.getBlock())
      +" microcut=0.11x0.11x0.11 actualBlock="+resultingId);'''
    if old_work not in server_logic:
        raise AssertionError("C&B fixture template drift")
    server_logic=server_logic.replace(old_work,new_work)
    # CI-only heartbeat in the original tick engine, separate from the
    # dedicated client-event probe. Distinguishes missing Mixin tick callbacks
    # from a network-state/persistence initialization failure.
    engine=code/"client/lighting/RGBRealLightEngine.java"
    engine_code=engine.read_text(encoding="utf-8")
    needle="         RGBLightPersistence.tick();"
    if needle not in engine_code:
        raise AssertionError("Forge original RGB engine tick call moved")
    engine_code=engine_code.replace(needle,'''         if (!RGBPortCiTickHeartbeat.seen) {
            RGBPortCiTickHeartbeat.seen=true;
            System.out.println("RGB_PORT_REAL_ENGINE_TICK_ACTIVE world="+com.rgbblocks.runtime.RGBRuntime.clientWorldId());
         }
'''+needle,1)
    # Use a compact private helper to preserve the original 1.3.1 engine logic.
    marker="public final class RGBRealLightEngine {"
    if marker not in engine_code:
        raise AssertionError("Forge RGB engine class definition changed")
    engine_code=engine_code.replace(marker,marker+'''
   private static final class RGBPortCiTickHeartbeat {
      private static boolean seen = false;
   }
''',1)
    engine.write_text(engine_code,encoding="utf-8")
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

else:
    # NeoForge 1.21.1 has the BlockInformation record (unlike Forge 1.20.1).
    # Reflective fixture keeps the production source free of a C&B compile dependency.
    server_logic=server_logic.replace("FABRICINFOCLASS","mod.chiselsandbits.api.blockinformation.BlockInformation").replace(
        "FABRICCONTRACT","mod.chiselsandbits.api.blockinformation.BlockInformation")
    # C&B auto-restores a fully homogeneous 4096-bit chiseled block to its
    # ordinary full block when an initializeWith() batch closes. The old
    # fixture initialized 4096 bits and then cut one bit AFTER that collapse,
    # leaving a detached tile: client saw a normal rgbblocks:*_glow block.
    # Hold an OUTER mutation batch across both operations, then verify the
    # final real server block is still chiselsandbits:chiseled with a tile.
    old_work='''  tile.getClass().getMethod("initializeWith",contract).invoke(tile,info);
  tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
    .invoke(tile,new net.minecraft.world.phys.Vec3(0.11,0.11,0.11));
  tile.setChanged();
  made=true;
  System.out.println("RGB_PORT_CNB_FIXTURE_PASS tile="+tile.getClass().getName()
      +" rgb="+net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(rgb.getBlock())
      +" microcut=0.11x0.11x0.11");'''
    new_work='''  try (java.lang.AutoCloseable batch = (java.lang.AutoCloseable) tile.getClass()
      .getMethod("batch").invoke(tile)) {
    tile.getClass().getMethod("initializeWith",contract).invoke(tile,info);
    tile.getClass().getMethod("clearInAreaTarget",net.minecraft.world.phys.Vec3.class)
      .invoke(tile,new net.minecraft.world.phys.Vec3(0.11,0.11,0.11));
  }
  var resultingState=level.getBlockState(pos);
  var resultingId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(resultingState.getBlock());
  var survivingTile=level.getBlockEntity(pos);
  if(resultingId==null || !"chiselsandbits".equals(resultingId.getNamespace())
     || !"chiseled".equals(resultingId.getPath()) || survivingTile!=tile){
    System.err.println("RGB_PORT_CNB_FIXTURE_RETRY actualBlock="+resultingId
        +" blockEntity="+survivingTile+" preserved="+(survivingTile==tile));
    return;
  }
  made=true;
  System.out.println("RGB_PORT_CNB_FIXTURE_PASS tile="+tile.getClass().getName()
      +" rgb="+net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(rgb.getBlock())
      +" microcut=0.11x0.11x0.11 actualBlock="+resultingId);'''
    if old_work not in server_logic:
        raise AssertionError("C&B fixture template drift")
    server_logic=server_logic.replace(old_work,new_work)
    fixture=code/"ci/RgbPortCnbFixture.java"
    fixture.write_text('''package com.rgbblocks.ci;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
@EventBusSubscriber(modid="rgbblocks")
public final class RgbPortCnbFixture {
 private RgbPortCnbFixture(){}
 @SubscribeEvent public static void onServerTick(ServerTickEvent.Post event) {
   create(event.getServer());
 }
'''+server_logic+"}\n",encoding="utf-8")

print("CI_ONLY_CNB_FIXTURE",TARGET,fixture,flush=True)

print("CI_ONLY_RGB_LIGHT_PROBE",TARGET,probe,flush=True)
