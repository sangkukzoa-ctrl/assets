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
private static boolean liveGreenPassed = false;"""
)
replace_once(
    "if (passed && cnbPassed) return;",
    "if (passed && cnbPassed && syncAutoRestored && liveGreenPassed) return;"
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
 }
'''
replace_once(anchor, anchor + "\n" + extra)
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


