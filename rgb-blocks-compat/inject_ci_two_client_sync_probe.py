#!/usr/bin/env python3
"""Add extra CI-only two-peer live RGB synchronization checks to the Forge probe.

Call only after inject_ci_only_light_probe.py forge1201 in the dedicated
dual-client acceptance workflow. This never changes release source/JAR.
"""
from pathlib import Path

path = Path("port-work/mc1201-forge/src/main/java/com/rgbblocks/ci/RgbPortLightProbe.java")
source = path.read_text(encoding="utf-8")

def replace_once(old, new):
    global source
    if source.count(old) != 1:
        raise AssertionError(f"CI two-peer injection anchor changed: {old!r}, count={source.count(old)}")
    source = source.replace(old, new, 1)

replace_once(
    "private static int tickCallbackCount = 0;",
    """private static int tickCallbackCount = 0;
private static boolean syncManualSeen = false;
private static boolean syncAutoRestored = false;
private static boolean liveGreenPassed = false;
private static boolean liveRemovalPassed = false;
private static int manualFrozenTicks = 0;
private static boolean manualFrozenPassed = false;
private static boolean manualBakePassed = false;
private static boolean reconnectLightPassed = false;
private static boolean reconnectSawChunkUnload = false;
private static boolean reconnectReturnPassed = false;
private static int reconnectStableSamples = 0;"""
)
replace_once(
    "if (passed && cnbPassed) return;",
    "if (passed && cnbPassed && syncAutoRestored && liveGreenPassed && liveRemovalPassed && manualFrozenPassed && manualBakePassed) return;"
)
anchor = " net.minecraft.core.BlockPos near=new net.minecraft.core.BlockPos(0,121,6);"
extra = r'''
 if (passed && cnbPassed) {
   if (!syncManualSeen && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
     syncManualSeen=true;
     System.out.println("RGB_PORT_PEER_MANUAL_SYNC_PASS worldId="
       +com.rgbblocks.runtime.RGBRuntime.clientWorldId());
   }
   if (syncManualSeen && !syncAutoRestored && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()) {
     syncAutoRestored=true;
     System.out.println("RGB_PORT_PEER_AUTO_SYNC_PASS worldId="
       +com.rgbblocks.runtime.RGBRuntime.clientWorldId());
   }
   if (syncAutoRestored && !liveGreenPassed) {
     if(ticks%120==0) {
       var liveState=mc.level.getBlockState(src);
       var emittedNow=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       var neighborNow=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       System.out.println("RGB_PORT_PEER_LIVE_GREEN_DIAG tick="+ticks
         +" block="+liveState+" rgb="+Integer.toHexString(com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(liveState))
         +" emitted="+emittedNow+" near="+neighborNow
         +" auto="+com.rgbblocks.runtime.RGBRuntime.clientTargetAuto());
     }
     int changed=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(mc.level.getBlockState(src));
     int cr=(changed>>16)&255, cg=(changed>>8)&255, cb=changed&255;
     if(changed>=0 && cg>cr && cg>cb && cg>=180) {
       var emitted=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
       var light=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       if(emitted.active() && emitted.g()>emitted.r() && emitted.g()>emitted.b()
             && light.active() && light.g()>light.r() && light.g()>light.b()) {
         liveGreenPassed=true;
         System.out.println("RGB_PORT_PEER_LIVE_GREEN_SYNC_PASS color="+Integer.toHexString(changed)
           +" emitted=["+emitted.r()+","+emitted.g()+","+emitted.b()+"]"
           +" neighbor=["+light.r()+","+light.g()+","+light.b()+"] ticks="+ticks);
       } else if(ticks%120==0) {
         System.out.println("RGB_PORT_PEER_LIVE_GREEN_SYNC_WAIT emitted="+emitted
           +" neighbor="+light+" ticks="+ticks);
       }
     }
   }
   // Only examine removal AFTER both peers already proved GREEN propagation.
   // The nearby C&B sculpture is still a genuine RED source, so the expected
   // post-removal color is red-dominant rather than necessarily black.
   if (liveGreenPassed && !liveRemovalPassed) {
     var removedState=mc.level.getBlockState(src);
     if (removedState.isAir()) {
       var removedEmission=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
       var remaining=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       if (!removedEmission.active() && (!remaining.active() || remaining.r()>remaining.g())) {
         liveRemovalPassed=true;
         System.out.println("RGB_PORT_PEER_LIVE_SOURCE_REMOVAL_PASS"
           +" direct="+removedEmission+" near="+remaining+" ticks="+ticks);
       } else if (ticks%120==0) {
         System.out.println("RGB_PORT_PEER_LIVE_SOURCE_REMOVAL_WAIT"
           +" direct="+removedEmission+" near="+remaining+" ticks="+ticks);
       }
     }
   }
   // Reintroduce green emitter while MANUAL is active: the direct source
   // changes, but the existing baked RED C&B neighbor must remain unchanged.
   if (liveRemovalPassed && !manualFrozenPassed
         && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
     var state=mc.level.getBlockState(src);
     int directRGB=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(state);
     int rr=(directRGB>>16)&255, gg=(directRGB>>8)&255, bb=directRGB&255;
     if (directRGB>=0 && gg>rr && gg>bb && gg>=180) {
       var emitted=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
       var held=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
       if (emitted.active() && held.active() && held.r()>held.g()) {
         if (++manualFrozenTicks>=30) {
           manualFrozenPassed=true;
           System.out.println("RGB_PORT_PEER_MANUAL_DEFER_PASS direct="+emitted
             +" held="+held+" stableTicks="+manualFrozenTicks);
         }
       } else {
         manualFrozenTicks=0;
         if(ticks%100==0) System.out.println("RGB_PORT_PEER_MANUAL_DEFER_WAIT source="+emitted+" light="+held);
       }
     }
   }
   // /rgb bake is sent only after BOTH DEFER_PASS markers. Successful GREEN
   // neighbor afterward proves the original dirty-position replay executed.
   if (manualFrozenPassed && !manualBakePassed
         && com.rgbblocks.runtime.RGBRuntime.clientTargetManual()) {
     var baked=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
     if (baked.active() && baked.g()>baked.r() && baked.g()>baked.b()) {
       manualBakePassed=true;
       System.out.println("RGB_PORT_PEER_MANUAL_BAKE_PASS neighbor="+baked+" ticks="+ticks);
     } else if (ticks%120==0) {
       System.out.println("RGB_PORT_PEER_MANUAL_BAKE_WAIT neighbor="+baked+" ticks="+ticks);
     }
   }
 }
'''
# The second production client is deliberately disconnected, stopped and
# restarted with the SAME minecraft directory after MANUAL bake. This separate
# CI-only JVM flag tests persisted RGB/C&B lightmap restoration and a real
# client chunk eviction/reload, without depending on the original RED fixture
# that is now authoritatively GREEN.
reconnect_extra = r'''
 if (Boolean.getBoolean("rgbport.ci.reconnect")) {
   boolean far = Math.abs(mc.player.getX()) > 160.0;
   if (far && !mc.level.isLoaded(src) && !reconnectSawChunkUnload) {
     reconnectSawChunkUnload=true;
     reconnectStableSamples=0;
     System.out.println("RGB_PORT_PEER_CHUNK_UNLOAD_PASS pos="+mc.player.blockPosition()
       +" sourceLoaded="+mc.level.isLoaded(src)+" ticks="+ticks);
   }
   boolean loaded=mc.level.isLoaded(src) && mc.level.isLoaded(new net.minecraft.core.BlockPos(4,121,7));
   if (loaded && !far) {
     var live=mc.level.getBlockState(src);
     int actual=com.rgbblocks.client.lighting.RGBRealLightEngine.rgbForState(live);
     int r=(actual>>16)&255,g=(actual>>8)&255,b=actual&255;
     var emitter=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,src);
     com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,near);
     var nearLight=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(near,0.5f,0.5f,0.5f);
     var cnb=new net.minecraft.core.BlockPos(4,121,7);
     var nearCnb=new net.minecraft.core.BlockPos(4,121,6);
     var cnbState=mc.level.getBlockState(cnb);
     var cnbId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(cnbState.getBlock());
     if(cnbId!=null && "chiselsandbits".equals(cnbId.getNamespace()) && "chiseled".equals(cnbId.getPath())) {
       com.rgbblocks.client.lighting.RGBRealLightEngine.refreshCnbBlockEntity(mc.level.getBlockEntity(cnb));
     }
     com.rgbblocks.client.lighting.RGBLightEngine.ensureBootstrapped(mc.level,nearCnb);
     var cbEmitter=com.rgbblocks.client.lighting.RGBRealLightEngine.sourceColorAt(mc.level,cnb);
     var cbNear=com.rgbblocks.client.lighting.RGBLightEngine.lightColorAt(nearCnb,0.5f,0.5f,0.5f);
     boolean good=actual>=0 && g>r && g>b && g>=180
       && emitter.active() && emitter.g()>emitter.r()
       && nearLight.active() && nearLight.g()>nearLight.r() && nearLight.g()>nearLight.b()
       && cnbId!=null && "chiselsandbits".equals(cnbId.getNamespace())
       && "chiseled".equals(cnbId.getPath())
       && cbEmitter.active() && cbEmitter.r()>cbEmitter.g()
       && cbNear.active() && cbNear.r()>cbNear.g()
       && com.rgbblocks.runtime.RGBRuntime.clientTargetAuto()
       && !com.rgbblocks.runtime.RGBRuntime.clientWorldId().isBlank();
     if(good) {
       if(++reconnectStableSamples>=3) {
         if(!reconnectLightPassed) {
           reconnectLightPassed=true;
           System.out.println("RGB_PORT_PEER_RECONNECT_SOURCE_PASS worldId="
             +com.rgbblocks.runtime.RGBRuntime.clientWorldId()
             +" emitter="+emitter+" near="+nearLight+" cnb="+cbEmitter
             +" cnbNear="+cbNear+" ticks="+ticks);
         }
         if(reconnectSawChunkUnload && !reconnectReturnPassed) {
           reconnectReturnPassed=true;
           System.out.println("RGB_PORT_PEER_CHUNK_RETURN_PASS worldId="
             +com.rgbblocks.runtime.RGBRuntime.clientWorldId()
             +" emitter="+emitter+" near="+nearLight+" cnb="+cbEmitter
             +" cnbNear="+cbNear+" ticks="+ticks);
         }
       }
     } else {
       reconnectStableSamples=0;
       if(ticks%120==0) System.out.println("RGB_PORT_PEER_RECONNECT_WAIT state="+live
         +" direct="+emitter+" neighbor="+nearLight
         +" cnb="+cbId(cnbId)+" cnbLight="+cbEmitter+" aroundCnb="+cbNear
         +" auto="+com.rgbblocks.runtime.RGBRuntime.clientTargetAuto());
     }
   } else if(ticks%120==0) {
     System.out.println("RGB_PORT_PEER_RECONNECT_CHUNK_WAIT sourceLoaded="+mc.level.isLoaded(src)
       +" player="+mc.player.blockPosition()+" sawUnload="+reconnectSawChunkUnload);
   }
   return;
 }
'''
# No additional helpers are allowed in the injected method: Java's String.valueOf
# handles a nullable Registry key directly.
reconnect_extra = reconnect_extra.replace('cbId(cnbId)', 'String.valueOf(cnbId)')
replace_once(anchor, anchor + "\n" + reconnect_extra + "\n" + extra)
path.write_text(source, encoding="utf-8")
print("CI_ONLY_TWO_CLIENT_SYNC_PROBE", path, len(source), flush=True)

# CI-only trace: isolate the Forge 1.20.1 packet -> ClientLevel -> RGB
# invalidation path. Never patch the release builder with these print calls.
client_mixin = Path("port-work/mc1201-forge/src/main/java/com/rgbblocks/mixin/client/ClientLevelMixin.java")
mixin_source = client_mixin.read_text(encoding="utf-8")
def mixin_once(old, new):
    global mixin_source
    if mixin_source.count(old) != 1:
        raise AssertionError(f"CI Forge Mixin probe anchor moved: {old[:110]!r}; count={mixin_source.count(old)}")
    mixin_source = mixin_source.replace(old, new, 1)

mixin_once(
    '      if (Boolean.TRUE.equals(cir.getReturnValue()) && pos != null) {',
    '''      if (rgbblocks$ciSource(pos)) {
         System.out.println("RGB_PORT_DIAG_SETBLOCK_TAIL state=" + state
            + " ok=" + cir.getReturnValue()
            + " world=" + ((ClientLevel)(Object)this).getBlockState(pos)
            + " nearby=" + RGBLightEngine.lightColorAt(new BlockPos(0,121,6),0.5f,0.5f,0.5f));
      }
      if (Boolean.TRUE.equals(cir.getReturnValue()) && pos != null) {'''
)
mixin_once(
    '      if (pos != null) {\n         boolean changed = oldState != newState',
    '''      if (rgbblocks$ciSource(pos)) {
         System.out.println("RGB_PORT_DIAG_BLOCK_UPDATED old=" + oldState
            + " new=" + newState + " flags=" + flags
            + " nearby=" + RGBLightEngine.lightColorAt(new BlockPos(0,121,6),0.5f,0.5f,0.5f));
      }
      if (pos != null) {
         boolean changed = oldState != newState'''
)
mixin_once(
    '   private static boolean rgbblocks$isRemoteMultiplayer() {',
    '''   private static boolean rgbblocks$ciSource(BlockPos pos) {
      return pos != null && pos.getX() == 0 && pos.getY() == 121 && pos.getZ() == 7;
   }

   @Inject(method = "setServerVerifiedBlockState", at = @At("HEAD"))
   private void rgbblocks$ciServerBlockHead(BlockPos pos, BlockState state, int flags, CallbackInfo ci) {
      if (rgbblocks$ciSource(pos)) {
         System.out.println("RGB_PORT_DIAG_SERVER_BLOCK_HEAD incoming=" + state
            + " old=" + ((ClientLevel)(Object)this).getBlockState(pos)
            + " flags=" + flags);
      }
   }

   @Inject(method = "setServerVerifiedBlockState", at = @At("TAIL"))
   private void rgbblocks$ciServerBlockTail(BlockPos pos, BlockState state, int flags, CallbackInfo ci) {
      if (rgbblocks$ciSource(pos)) {
         System.out.println("RGB_PORT_DIAG_SERVER_BLOCK_TAIL incoming=" + state
            + " actual=" + ((ClientLevel)(Object)this).getBlockState(pos)
            + " nearby=" + RGBLightEngine.lightColorAt(new BlockPos(0,121,6),0.5f,0.5f,0.5f));
      }
   }

   @Inject(method = "syncBlockState", at = @At("TAIL"))
   private void rgbblocks$ciSyncBlockTail(BlockPos pos, BlockState state,
       net.minecraft.world.phys.Vec3 playerPos, CallbackInfo ci) {
      if (rgbblocks$ciSource(pos)) {
         System.out.println("RGB_PORT_DIAG_PREDICTION_BLOCK_TAIL incoming=" + state
            + " actual=" + ((ClientLevel)(Object)this).getBlockState(pos));
      }
   }

   private static boolean rgbblocks$isRemoteMultiplayer() {'''
)
client_mixin.write_text(mixin_source, encoding="utf-8")

real_engine = Path("port-work/mc1201-forge/src/main/java/com/rgbblocks/client/lighting/RGBRealLightEngine.java")
real_source = real_engine.read_text(encoding="utf-8")
engine_anchor = '''   public static void invalidateAround(BlockPos pos) {
      if (shouldDeferNewEvent()) {'''
engine_instrumented = '''   public static void invalidateAround(BlockPos pos) {
      if (pos != null && pos.getX() == 0 && pos.getY() == 121 && pos.getZ() == 7) {
         System.out.println("RGB_PORT_DIAG_INVALIDATE_CALLED mode=" + EFFECTIVE_MODE
            + " ready=" + RGBLightPersistence.readyForCurrentDimension()
            + " defer=" + shouldDeferNewEvent()
            + " direct=" + sourceColorAt(clientLevel(), pos)
            + " before=" + RGBLightEngine.lightColorAt(new BlockPos(0,121,6),0.5f,0.5f,0.5f));
      }
      if (shouldDeferNewEvent()) {'''
if real_source.count(engine_anchor) != 1:
    raise AssertionError("Forge CI real light invalidation probe anchor moved")
real_source = real_source.replace(engine_anchor, engine_instrumented, 1)
engine_anchor_end = '''      RGBRenderInvalidator.dirtyAround(pos, radiusCached());
   }

   public static void invalidateChunk'''
engine_end_instrumented = '''      RGBRenderInvalidator.dirtyAround(pos, radiusCached());
      if (pos != null && pos.getX() == 0 && pos.getY() == 121 && pos.getZ() == 7) {
         System.out.println("RGB_PORT_DIAG_INVALIDATE_EXECUTED mode=" + EFFECTIVE_MODE
            + " after=" + RGBLightEngine.lightColorAt(new BlockPos(0,121,6),0.5f,0.5f,0.5f));
      }
   }

   public static void invalidateChunk'''
if real_source.count(engine_anchor_end) != 1:
    raise AssertionError("Forge CI invalidate execution probe anchor moved")
real_source = real_source.replace(engine_anchor_end, engine_end_instrumented, 1)
real_engine.write_text(real_source, encoding="utf-8")
print("CI_ONLY_FORGE_BLOCK_PACKET_AND_INVALIDATION_TRACES", client_mixin, real_engine, flush=True)


