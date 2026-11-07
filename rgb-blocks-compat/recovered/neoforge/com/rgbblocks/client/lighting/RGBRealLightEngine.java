package com.rgbblocks.client.lighting;

import com.mojang.blaze3d.vertex.QuadInstance;
import com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer;
import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.client.config.RGBClientConfig;
import com.rgbblocks.runtime.RGBRuntime;
import java.lang.reflect.Method;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ARGB;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3fc;

public final class RGBRealLightEngine {
   public static final String MOD_ID = "rgbblocks";
   private static final Pattern RGB_PATTERN = Pattern.compile(".*?(\\d{1,3})_(\\d{1,3})_(\\d{1,3})(?:_\\d+)?(?:_glow|_glass)?$");
   private static final int RGB_CACHE_LIMIT = 65536;
   private static final int CNB_CACHE_LIMIT = 65536;
   private static final int MAX_CNB_ENTRIES = 1024;
   private static final int CNB_EMPTY_CONFIRMATIONS = 4;
   private static final int CNB_WEAK_CONFIRMATIONS = 3;
   private static final int CNB_REFRESH_ATTEMPTS = 16;
   private static final int BAKE_COLLECTION_MIN_TICKS = 6;
   private static final int BAKE_COLLECTION_MAX_TICKS = 32;
   private static final Map<Block, Integer> RGB_BY_BLOCK = new ConcurrentHashMap<>();
   private static final Map<Long, RGBRealLightEngine.CnbSource> CNB_CACHE = new ConcurrentHashMap<>();
   private static final Map<Long, RGBRealLightEngine.PendingCnbRefresh> CNB_PENDING = new ConcurrentHashMap<>();
   private static final Map<Long, Integer> CNB_EMPTY_STRIKES = new ConcurrentHashMap<>();
   private static final Map<Long, Integer> CNB_WEAK_STRIKES = new ConcurrentHashMap<>();
   private static final Map<Long, RGBRealLightEngine.PendingCnbRemoval> CNB_REMOVE_PENDING = new ConcurrentHashMap<>();
   private static final Set<Long> UNVERIFIED_PERSISTED_CNB = ConcurrentHashMap.newKeySet();
   private static final Set<Long> STALE_CNB_CLEANUP = ConcurrentHashMap.newKeySet();
   private static final Set<Long> CNB_VALIDATION_REQUESTS = ConcurrentHashMap.newKeySet();
   private static final Set<Long> PERSISTED_CNB_RECOVERY_CANDIDATES = ConcurrentHashMap.newKeySet();
   private static final Map<String, ArrayDeque<RGBRealLightEngine.DeferredRgbEvent>> DEFERRED_EVENTS = new ConcurrentHashMap<>();
   private static final ArrayDeque<RGBRealLightEngine.DeferredRgbEvent> REPLAY_EVENTS = new ArrayDeque<>();
   private static final Map<Long, RGBRealLightEngine.CnbSource> MANUAL_CNB_SHADOW = new ConcurrentHashMap<>();
   private static final Map<Long, Integer> MANUAL_CNB_EMPTY_STRIKES = new ConcurrentHashMap<>();
   private static final Map<Long, Integer> MANUAL_CNB_WEAK_STRIKES = new ConcurrentHashMap<>();
   private static final Set<Long> MANUAL_BOOTSTRAP_SECTIONS = ConcurrentHashMap.newKeySet();
   private static RGBRealLightEngine.EffectiveMode EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.AUTO;
   private static long OBSERVED_RUNTIME_VERSION = Long.MIN_VALUE;
   private static int STABILIZATION_TICKS;
   private static boolean REPLAY_TO_AUTO;
   private static int REPLAY_PROCESSED;
   private static int REPLAY_FAILED;
   private static final int REPLAY_STABILIZATION_TICKS = 40;
   private static boolean BAKE_COLLECTING;
   private static boolean ACTIVE_BAKE_ALL;
   private static int ACTIVE_BAKE_RADIUS = 32;
   private static BlockPos ACTIVE_BAKE_CENTER = BlockPos.ZERO;
   private static int BAKE_COLLECTION_TICKS;
   private static final Map<String, Map<Long, Long>> DIRTY_LEDGER = new ConcurrentHashMap<>();
   private static final ArrayDeque<RGBRealLightEngine.DirtyBatchEntry> ACTIVE_BATCH = new ArrayDeque<>();
   private static final Set<Long> BATCH_INTERNAL_CNB_REFRESH = ConcurrentHashMap.newKeySet();
   private static long DIRTY_GENERATION;
   private static int BATCH_PROCESSED;
   private static int BATCH_FAILED;
   private static int BATCH_SKIPPED_UNLOADED;
   private static final int BATCH_CNB_WAIT_TICKS = 64;
   private static final int BATCH_STABILIZATION_TICKS = 24;

   private RGBRealLightEngine() {
   }

   public static boolean enabled() {
      try {
         return RGBClientConfig.rgbEnabled();
      } catch (Throwable ignored) {
         return true;
      }
   }

   public static int radiusCached() {
      RGBClientConfig.refreshCache();
      return clampInt(RGBClientConfig.RADIUS_CACHED, 4, 15);
   }

   public static float strengthCached() {
      RGBClientConfig.refreshCache();
      return clamp(RGBClientConfig.STRENGTH_CACHED, 0.0F, 2.0F);
   }

   public static void invalidateAll() {
      RGBClientConfig.refreshCache();
      RGBLightEngine.invalidateAll();
      RGBSourceIndex.clear();
      CNB_CACHE.clear();
      CNB_PENDING.clear();
      CNB_EMPTY_STRIKES.clear();
      CNB_WEAK_STRIKES.clear();
      CNB_REMOVE_PENDING.clear();
      UNVERIFIED_PERSISTED_CNB.clear();
      STALE_CNB_CLEANUP.clear();
      CNB_VALIDATION_REQUESTS.clear();
      PERSISTED_CNB_RECOVERY_CANDIDATES.clear();
   }

   public static void onClientDisconnect() {
      RGBLightPersistence.saveCurrentBlocking();
      CNB_CACHE.clear();
      CNB_PENDING.clear();
      CNB_EMPTY_STRIKES.clear();
      CNB_WEAK_STRIKES.clear();
      CNB_REMOVE_PENDING.clear();
      UNVERIFIED_PERSISTED_CNB.clear();
      STALE_CNB_CLEANUP.clear();
      CNB_VALIDATION_REQUESTS.clear();
      PERSISTED_CNB_RECOVERY_CANDIDATES.clear();
      DEFERRED_EVENTS.clear();
      REPLAY_EVENTS.clear();
      DIRTY_LEDGER.clear();
      ACTIVE_BATCH.clear();
      BATCH_INTERNAL_CNB_REFRESH.clear();
      DIRTY_GENERATION = 0L;
      BATCH_PROCESSED = 0;
      BATCH_FAILED = 0;
      BATCH_SKIPPED_UNLOADED = 0;
      MANUAL_CNB_SHADOW.clear();
      MANUAL_CNB_EMPTY_STRIKES.clear();
      MANUAL_CNB_WEAK_STRIKES.clear();
      MANUAL_BOOTSTRAP_SECTIONS.clear();
      EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.AUTO;
      OBSERVED_RUNTIME_VERSION = Long.MIN_VALUE;
      STABILIZATION_TICKS = 0;
      REPLAY_TO_AUTO = false;
      BAKE_COLLECTING = false;
      BAKE_COLLECTION_TICKS = 0;
      ACTIVE_BAKE_CENTER = BlockPos.ZERO;
      RGBRuntime.resetClientState();
      RGBLightPersistence.reset();
      RGBCnbGeometryBakeDebouncer.reset();
      RGBLightEngine.onClientDisconnect();
      RGBRenderInvalidator.onClientDisconnect();
   }

   public static void invalidateAround(BlockPos pos) {
      if (shouldDeferNewEvent()) {
         markDirty(pos);
      } else {
         executeInvalidateAround(pos);
         markClean(pos);
      }
   }

   private static void executeInvalidateAround(BlockPos pos) {
      RGBClientConfig.refreshCache();
      BlockAndTintGetter level = clientLevel();
      if (level != null) {
         RGBSourceIndex.refresh(level, pos);
         RGBLightEngine.invalidateAround(level, pos);
      }

      if (CNB_CACHE.size() > 65536) {
         CNB_CACHE.clear();
         RGBSourceIndex.clear();
      }

      RGBRenderInvalidator.dirtyAround(pos, radiusCached());
   }

   public static void invalidateChunk(int chunkX, int chunkZ) {
      RGBClientConfig.refreshCache();
      BlockAndTintGetter level = clientLevel();
      if (level != null) {
         RGBLightEngine.invalidateChunk(level, chunkX, chunkZ);
      }

      if (CNB_CACHE.size() > 65536) {
         CNB_CACHE.clear();
         RGBSourceIndex.clear();
      }

      RGBRenderInvalidator.dirtyChunk(chunkX, chunkZ);
   }

   public static void settleAfterServerSync(BlockPos pos) {
      if (shouldDeferNewEvent()) {
         markDirty(pos);
      } else {
         executeSettleAfterServerSync(pos);
      }
   }

   private static void executeSettleAfterServerSync(BlockPos pos) {
      if (enabled() && pos != null) {
         RGBClientConfig.refreshCache();
         BlockAndTintGetter level = clientLevel();
         if (level != null) {
            RGBSourceIndex.refresh(level, pos);
         }

         RGBLightEngine.scheduleSourceBootstrap(pos);
         RGBRenderInvalidator.dirtyAfterServerSync(pos, radiusCached());
      }
   }

   public static RGBLightColor4 sourceColorAt(BlockAndTintGetter level, BlockPos pos) {
      if (enabled() && level != null && pos != null) {
         BlockState state;
         try {
            state = level.getBlockState(pos);
         } catch (Throwable ignored) {
            return RGBLightColor4.BLACK;
         }

         RGBLightColor4 direct = directSource(state);
         RGBRealLightEngine.CnbSource cnb = cnbSource(pos);
         if (!cnb.active()) {
            return direct;
         }

         RGBLightColor4 cnbColor = RGBLightColor4.fromRgbAndEmission(cnb.rgb, Math.round(cnb.energy * 15.0F));
         return !direct.active()
            ? cnbColor
            : new RGBLightColor4(Math.max(direct.r(), cnbColor.r()), Math.max(direct.g(), cnbColor.g()), Math.max(direct.b(), cnbColor.b()));
      } else {
         return RGBLightColor4.BLACK;
      }
   }

   public static boolean directEmitterAt(BlockAndTintGetter level, BlockPos pos) {
      if (enabled() && level != null && pos != null) {
         try {
            return directSource(level.getBlockState(pos)).active();
         } catch (Throwable ignored) {
            return false;
         }
      } else {
         return false;
      }
   }

   public static boolean rgbEmitterAt(BlockAndTintGetter level, BlockPos pos) {
      if (enabled() && level != null && pos != null) {
         try {
            if (directSource(level.getBlockState(pos)).active()) {
               return true;
            }
         } catch (Throwable var4) {
         }

         try {
            return cnbSource(pos).active();
         } catch (Throwable ignored) {
            return false;
         }
      } else {
         return false;
      }
   }

   private static RGBLightColor4 directSource(BlockState state) {
      if (state == null) {
         return RGBLightColor4.BLACK;
      }

      int emission;
      try {
         emission = state.getLightEmission();
      } catch (Throwable ignored) {
         emission = 0;
      }

      if (emission <= 0) {
         return RGBLightColor4.BLACK;
      }

      int rgb = rgbForState(state);
      return rgb < 0 ? RGBLightColor4.BLACK : RGBLightColor4.fromRgbAndEmission(rgb, emission);
   }

   public static int applyPackedLight(BlockAndTintGetter level, BlockPos pos, float localX, float localY, float localZ, int vanillaPackedLight) {
      int packed = RGBLightEngine.packedLightAt(level, pos, localX, localY, localZ, vanillaPackedLight);
      return rgbEmitterAt(level, pos) ? LightCoordsUtil.pack(15, LightCoordsUtil.sky(packed)) : packed;
   }

   public static void applyToVanillaQuad(BlockAndTintGetter level, BlockPos pos, BlockState state, BakedQuad quad, QuadInstance instance) {
      if (enabled() && level != null && pos != null && quad != null && instance != null) {
         for (int vertex = 0; vertex < 4; vertex++) {
            Vector3fc p = quad.position(vertex);
            float x = p == null ? 0.5F : p.x();
            float y = p == null ? 0.5F : p.y();
            float z = p == null ? 0.5F : p.z();
            int oldLight = instance.getLightCoords(vertex);
            int newLight = applyPackedLight(level, pos, x, y, z, oldLight);
            RGBLightEngine.ensureBootstrapped(level, pos);
            RGBLightColor8 rgb = RGBLightEngine.lightColorAt(pos, x, y, z);
            instance.setLightCoords(vertex, newLight);
            if (rgb.active()) {
               instance.setColor(vertex, applyColor(instance.getColor(vertex), newLight, rgb, rgbEmitterAt(level, pos)));
            }
         }
      }
   }

   public static int applyColor(BlockAndTintGetter level, BlockPos pos, float localX, float localY, float localZ, int color, int packedLight) {
      if (enabled() && level != null && pos != null) {
         RGBLightEngine.ensureBootstrapped(level, pos);
         boolean emitter = rgbEmitterAt(level, pos);
         RGBLightColor8 rgb = RGBLightEngine.lightColorAt(pos, localX, localY, localZ);
         if (emitter) {
            RGBLightColor4 source = sourceColorAt(level, pos);
            if (source.active()) {
               RGBLightColor8 source8 = RGBLightColor8.from4(source);
               if (!rgb.active() || maxChannel(source8) >= maxChannel(rgb)) {
                  rgb = source8;
               }
            }
         }

         return !rgb.active() ? color : applyColor(color, packedLight, rgb, emitter);
      } else {
         return color;
      }
   }

   public static int applyColor(int color, int packedLight, RGBLightColor8 rgb, boolean emitter) {
      if (rgb != null && rgb.active()) {
         int a = ARGB.alpha(color);
         int r = ARGB.red(color);
         int g = ARGB.green(color);
         int b = ARGB.blue(color);
         if (emitter) {
            float cr = rgb.r() / 255.0F;
            float cg = rgb.g() / 255.0F;
            float cb = rgb.b() / 255.0F;
            return ARGB.color(a, lightChannel(r, cr, 1.0F), lightChannel(g, cg, 1.0F), lightChannel(b, cb, 1.0F));
         }

         int block = LightCoordsUtil.block(packedLight);
         int sky = LightCoordsUtil.sky(packedLight);
         float cr = rgb.r() / 255.0F;
         float cg = rgb.g() / 255.0F;
         float cb = rgb.b() / 255.0F;
         float rgbEnergy = Math.max(cr, Math.max(cg, cb));
         float rgbMin = Math.min(cr, Math.min(cg, cb));
         float chroma = rgbEnergy - rgbMin;
         float blockGate = Math.max(block / 15.0F, rgbEnergy * 0.98F);
         float skyGate = 1.0F - Math.min(0.56F, sky / 15.0F * 0.38F);
         float amount = rgbEnergy * blockGate * skyGate * strengthCached() * 1.5F;
         if (chroma < 0.18F) {
            float neutral = 1.0F - clamp(chroma / 0.18F, 0.0F, 1.0F);
            amount *= 1.0F - neutral * 0.48F;
         }

         float edgeFill = rgbEnergy * skyGate * strengthCached() * 0.055F;
         amount = Math.max(amount, Math.min(0.075F, edgeFill));
         amount = clamp(amount, 0.0F, 0.91F);
         return amount <= 8.0E-4F ? color : applySoftColoredLight(a, r, g, b, cr, cg, cb, amount, rgbEnergy);
      } else {
         return color;
      }
   }

   private static int maxChannel(RGBLightColor8 color) {
      return Math.max(color.r(), Math.max(color.g(), color.b()));
   }

   private static int lightChannel(int base, float light, float amount) {
      float albedo = base / 255.0F;
      float direct = light * amount * (0.88F - albedo * 0.28F);
      float bleed = light * amount * 0.22F;
      float lit = albedo + direct + bleed;
      return clamp255(Math.round(softClamp01(lit) * 255.0F));
   }

   private static int applySoftColoredLight(int a, int r, int g, int b, float cr, float cg, float cb, float amount, float rgbEnergy) {
      float ar = litChannelFloat(r, cr, amount);
      float ag = litChannelFloat(g, cg, amount);
      float ab = litChannelFloat(b, cb, amount);
      float max = Math.max(ar, Math.max(ag, ab));
      if (max > 1.0F) {
         float compressedMax = softClamp01(max);
         float scale = compressedMax / max;
         ar *= scale;
         ag *= scale;
         ab *= scale;
      }

      float shadowLift = rgbShadowLift(amount, rgbEnergy, ar, ag, ab);
      if (shadowLift > 0.0F) {
         ar += shadowLift * (1.0F - ar) * (0.58F + cr * 0.42F);
         ag += shadowLift * (1.0F - ag) * (0.58F + cg * 0.42F);
         ab += shadowLift * (1.0F - ab) * (0.58F + cb * 0.42F);
      }

      return ARGB.color(
         a,
         clamp255(Math.round(clamp(ar, 0.0F, 1.0F) * 255.0F)),
         clamp255(Math.round(clamp(ag, 0.0F, 1.0F) * 255.0F)),
         clamp255(Math.round(clamp(ab, 0.0F, 1.0F) * 255.0F))
      );
   }

   private static float rgbShadowLift(float amount, float rgbEnergy, float ar, float ag, float ab) {
      if (!(amount <= 8.0E-4F) && !(rgbEnergy <= 0.0F)) {
         float brightest = Math.max(ar, Math.max(ag, ab));
         float darkness = 1.0F - clamp(brightest, 0.0F, 1.0F);
         if (darkness <= 0.0F) {
            return 0.0F;
         }

         float presence = clamp(amount * 1.35F + rgbEnergy * 0.16F, 0.0F, 1.0F);
         return 0.085F * presence * darkness * darkness;
      } else {
         return 0.0F;
      }
   }

   private static float litChannelFloat(int base, float light, float amount) {
      float albedo = base / 255.0F;
      float direct = light * amount * (0.88F - albedo * 0.28F);
      float bleed = light * amount * 0.22F;
      return albedo + direct + bleed;
   }

   private static float softClamp01(float v) {
      if (v <= 1.0F) {
         return Math.max(0.0F, v);
      }

      float over = v - 1.0F;
      return 1.0F - 0.16F / (over + 0.16F) * 0.16F;
   }

   public static int rgbForState(BlockState state) {
      if (state == null) {
         return -1;
      }

      Block block = state.getBlock();
      Integer cached = RGB_BY_BLOCK.get(block);
      if (cached != null) {
         return cached;
      }

      int rgb = parseRgbBlock(block);
      if (RGB_BY_BLOCK.size() > 65536) {
         RGB_BY_BLOCK.clear();
      }

      RGB_BY_BLOCK.put(block, rgb);
      return rgb;
   }

   private static int parseRgbBlock(Block block) {
      try {
         Identifier id = BuiltInRegistries.BLOCK.getKey(block);
         if (id != null && "rgbblocks".equals(id.getNamespace())) {
            String path = id.getPath();
            if (!path.endsWith("_glow")) {
               return -1;
            }

            Matcher matcher = RGB_PATTERN.matcher(path);
            if (!matcher.matches()) {
               return -1;
            }

            int r = clamp255(Integer.parseInt(matcher.group(1)));
            int g = clamp255(Integer.parseInt(matcher.group(2)));
            int b = clamp255(Integer.parseInt(matcher.group(3)));
            return r << 16 | g << 8 | b;
         } else {
            return -1;
         }
      } catch (Throwable ignored) {
         return -1;
      }
   }

   public static void registerCnbModelPartSources(BlockPos pos, List<?> parts) {
      if (enabled() && pos != null) {
         if (shouldDeferNewEvent()) {
            markDirty(pos);
         } else {
            RGBRenderInvalidator.dirtyAround(pos, radiusCached());
         }
      }
   }

   public static void refreshCnbBlockEntity(Object blockEntity) {
      scheduleCnbBlockEntity(blockEntity, 2, 16);
   }

   public static void processClientTick() {
      if (enabled()) {
         try {
            Minecraft minecraft = Minecraft.getInstance();
            if (minecraft == null || !minecraft.isSameThread()) {
               return;
            }
         } catch (Throwable ignored) {
            return;
         }

         RGBLightPersistence.tick();
         syncRuntimeState();
         if (RGBLightPersistence.readyForCurrentDimension()) {
            if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.AUTO
               && RGBRuntime.clientTargetAuto()
               && ACTIVE_BATCH.isEmpty()
               && hasLoadedDirtyForCurrentDimension()) {
               startCatchUp();
            }

            RGBRuntime.BakeRequest request = RGBRuntime.consumeBakeRequest();
            if (request != null && EFFECTIVE_MODE != RGBRealLightEngine.EffectiveMode.AUTO) {
               startManualBake(request.all(), request.radius());
            }

            processCnbValidationAndCleanup();
            processPendingCnbRemovals();
            int processed = 0;
            Iterator<Entry<Long, RGBRealLightEngine.PendingCnbRefresh>> iterator = CNB_PENDING.entrySet().iterator();

            while (iterator.hasNext() && processed++ < 128) {
               Entry<Long, RGBRealLightEngine.PendingCnbRefresh> entry = iterator.next();
               RGBRealLightEngine.PendingCnbRefresh pending = entry.getValue();
               if (pending == null || pending.blockEntity == null || pending.pos == null) {
                  iterator.remove();
               } else if (pending.delayTicks > 0) {
                  entry.setValue(new RGBRealLightEngine.PendingCnbRefresh(pending.pos, pending.blockEntity, pending.delayTicks - 1, pending.attemptsLeft));
               } else {
                  boolean shadow = usesShadowCnbState();
                  Map<Long, RGBRealLightEngine.CnbSource> cache = shadow ? MANUAL_CNB_SHADOW : CNB_CACHE;
                  Map<Long, Integer> empty = shadow ? MANUAL_CNB_EMPTY_STRIKES : CNB_EMPTY_STRIKES;
                  Map<Long, Integer> weak = shadow ? MANUAL_CNB_WEAK_STRIKES : CNB_WEAK_STRIKES;
                  long key = cnbKey(pending.pos);
                  RGBRealLightEngine.CnbSource previous = sourceFrom(cache, pending.pos);
                  RGBRealLightEngine.CnbSource source = computeCnbSourceFromAccessor(pending.blockEntity);
                  RGBRealLightEngine.CnbCommit commit = putCnbSourceInto(pending.pos, source, cache, empty, weak, !shadow);
                  if (commit == RGBRealLightEngine.CnbCommit.CONFIRMED_EMPTY) {
                     iterator.remove();
                     PERSISTED_CNB_RECOVERY_CANDIDATES.remove(key);
                     if (shadow) {
                        deferShadowRemoval(pending.pos);
                     } else {
                        executeRealCnbRemoval(pending.pos, true);
                        markClean(pending.pos);
                     }
                  } else if (commit.committed()) {
                     iterator.remove();
                     RGBRealLightEngine.CnbSource current = sourceFrom(cache, pending.pos);
                     if (!shadow) {
                        UNVERIFIED_PERSISTED_CNB.remove(key);
                        CNB_VALIDATION_REQUESTS.remove(key);
                        STALE_CNB_CLEANUP.remove(key);
                        PERSISTED_CNB_RECOVERY_CANDIDATES.remove(key);
                     } else {
                        RGBRealLightEngine.CnbSource baked = sourceFrom(CNB_CACHE, pending.pos);
                        if (UNVERIFIED_PERSISTED_CNB.contains(key) && equivalentCnbSourceForValidation(baked, current)) {
                           UNVERIFIED_PERSISTED_CNB.remove(key);
                           CNB_VALIDATION_REQUESTS.remove(key);
                           STALE_CNB_CLEANUP.remove(key);
                        }

                        if (PERSISTED_CNB_RECOVERY_CANDIDATES.remove(key) && current.active()) {
                           CNB_CACHE.put(key, current);
                           CNB_EMPTY_STRIKES.remove(key);
                           CNB_WEAK_STRIKES.remove(key);
                           UNVERIFIED_PERSISTED_CNB.remove(key);
                           CNB_VALIDATION_REQUESTS.remove(key);
                           STALE_CNB_CLEANUP.remove(key);
                           BlockAndTintGetter level = clientLevel();
                           if (level != null) {
                              RGBSourceIndex.refresh(level, pending.pos);
                           } else {
                              RGBSourceIndex.update(pending.pos, RGBLightColor4.fromRgbAndEmission(current.rgb, Math.round(current.energy * 15.0F)));
                           }

                           RGBCnbReloadWakeup.onPersistedSourceRecovered(pending.pos);
                        }
                     }

                     boolean internalBatchRefresh = BATCH_INTERNAL_CNB_REFRESH.remove(key);
                     if (!sameCnbSource(previous, current)) {
                        if (shadow) {
                           if (!internalBatchRefresh) {
                              markDirty(pending.pos);
                           }
                        } else {
                           executeCommittedCnbChange(pending.pos);
                           markClean(pending.pos);
                        }
                     }
                  } else if (pending.attemptsLeft <= 0) {
                     iterator.remove();
                     BATCH_INTERNAL_CNB_REFRESH.remove(cnbKey(pending.pos));
                  } else {
                     entry.setValue(new RGBRealLightEngine.PendingCnbRefresh(pending.pos, pending.blockEntity, 2, pending.attemptsLeft - 1));
                  }
               }
            }

            collectActiveBakeEvents();
            processReplayTick();
         }
      }
   }

   private static void scheduleCnbBlockEntity(Object blockEntity, int delayTicks, int attemptsLeft) {
      if (enabled() && RGBClientConfig.ENABLE_CNB_SOURCE_TRACKING_CACHED && blockEntity != null) {
         BlockPos pos = cnbBlockEntityPos(blockEntity);
         if (pos != null) {
            long key = cnbKey(pos);
            if (CNB_PENDING.size() > 65536) {
               CNB_PENDING.clear();
            }

            RGBRealLightEngine.PendingCnbRefresh old = CNB_PENDING.get(key);
            int delay = Math.max(0, delayTicks);
            int attempts = Math.max(0, attemptsLeft);
            if (old != null) {
               delay = Math.min(old.delayTicks, delay);
               attempts = Math.max(old.attemptsLeft, attempts);
            }

            CNB_PENDING.put(key, new RGBRealLightEngine.PendingCnbRefresh(pos, blockEntity, delay, attempts));
         }
      }
   }

   public static void removeCnbBlockEntity(Object blockEntity) {
      if (blockEntity != null) {
         BlockPos pos = cnbBlockEntityPos(blockEntity);
         if (pos != null) {
            long key = cnbKey(pos);
            CNB_REMOVE_PENDING.put(key, new RGBRealLightEngine.PendingCnbRemoval(pos, 3, 8));
         }
      }
   }

   public static void removeCnbSource(BlockPos pos, boolean invalidate) {
      if (pos != null) {
         if (usesShadowCnbState()) {
            long key = cnbKey(pos);
            CNB_PENDING.remove(key);
            CNB_REMOVE_PENDING.remove(key);
            MANUAL_CNB_EMPTY_STRIKES.remove(key);
            MANUAL_CNB_WEAK_STRIKES.remove(key);
            MANUAL_CNB_SHADOW.put(key, RGBRealLightEngine.CnbSource.NONE);
            if (invalidate && !BATCH_INTERNAL_CNB_REFRESH.remove(key)) {
               markDirty(pos);
            }
         } else {
            executeRealCnbRemoval(pos, invalidate);
            if (invalidate) {
               markClean(pos);
            }
         }
      }
   }

   private static void executeRealCnbRemoval(BlockPos pos, boolean invalidate) {
      if (pos != null) {
         long key = cnbKey(pos);
         CNB_PENDING.remove(key);
         CNB_REMOVE_PENDING.remove(key);
         CNB_EMPTY_STRIKES.remove(key);
         CNB_WEAK_STRIKES.remove(key);
         CNB_CACHE.remove(key);
         UNVERIFIED_PERSISTED_CNB.remove(key);
         CNB_VALIDATION_REQUESTS.remove(key);
         STALE_CNB_CLEANUP.remove(key);
         PERSISTED_CNB_RECOVERY_CANDIDATES.remove(key);
         BlockAndTintGetter level = clientLevel();
         if (level != null) {
            RGBSourceIndex.refresh(level, pos);
         } else {
            RGBSourceIndex.remove(pos);
         }

         if (invalidate) {
            if (level != null) {
               RGBLightEngine.invalidateAround(level, pos);
            }

            RGBRenderInvalidator.dirtyAround(pos, radiusCached());
         }
      }
   }

   private static void executeCommittedCnbChange(BlockPos pos) {
      BlockAndTintGetter level = clientLevel();
      if (level != null) {
         RGBLightEngine.invalidateAround(level, pos);
      }

      RGBRenderInvalidator.dirtyAround(pos, radiusCached());
   }

   private static RGBRealLightEngine.CnbSource cnbSource(BlockPos pos) {
      if (RGBClientConfig.ENABLE_CNB_SOURCE_TRACKING_CACHED && pos != null) {
         long key = cnbKey(pos);
         RGBRealLightEngine.CnbSource source = CNB_CACHE.get(key);
         if (source == null || !source.active()) {
            return RGBRealLightEngine.CnbSource.NONE;
         }

         if (isPositionLoaded(pos) && !isStillChiseledBlock(pos)) {
            STALE_CNB_CLEANUP.add(key);
            return RGBRealLightEngine.CnbSource.NONE;
         }

         if (UNVERIFIED_PERSISTED_CNB.contains(key) && isPositionLoaded(pos)) {
            CNB_VALIDATION_REQUESTS.add(key);
         }

         return source;
      } else {
         return RGBRealLightEngine.CnbSource.NONE;
      }
   }

   private static RGBRealLightEngine.CnbCommit putCnbSource(BlockPos pos, RGBRealLightEngine.CnbSource source) {
      return putCnbSourceInto(pos, source, CNB_CACHE, CNB_EMPTY_STRIKES, CNB_WEAK_STRIKES, true);
   }

   private static RGBRealLightEngine.CnbCommit putCnbSourceInto(
      BlockPos pos,
      RGBRealLightEngine.CnbSource source,
      Map<Long, RGBRealLightEngine.CnbSource> cache,
      Map<Long, Integer> emptyStrikes,
      Map<Long, Integer> weakStrikes,
      boolean realCache
   ) {
      if (pos == null) {
         return RGBRealLightEngine.CnbCommit.HELD;
      }

      long key = cnbKey(pos);
      RGBRealLightEngine.CnbSource previous = cache.get(key);
      if (source != null && source.active()) {
         emptyStrikes.remove(key);
         if (previous != null && previous.active()) {
            float prevEnergy = previous.energy;
            float newEnergy = source.energy;
            if (isSuspiciousWeakening(previous, source)) {
               int strikes = weakStrikes.merge(key, 1, Integer::sum);
               if (strikes < 3) {
                  return RGBRealLightEngine.CnbCommit.HELD;
               }

               source = smoothCnbSource(previous, source, 0.42F);
            } else {
               weakStrikes.remove(key);
               if (Math.abs(newEnergy - prevEnergy) < 0.18F && previous.rgb == source.rgb) {
                  source = smoothCnbSource(previous, source, 0.65F);
               }
            }
         } else {
            weakStrikes.remove(key);
         }

         if (cache.size() > 65536) {
            cache.clear();
            emptyStrikes.clear();
            weakStrikes.clear();
            if (realCache) {
               RGBSourceIndex.clear();
            }
         }

         cache.put(key, source);
         if (realCache) {
            BlockAndTintGetter level = clientLevel();
            if (level != null) {
               RGBSourceIndex.refresh(level, pos);
            } else {
               RGBSourceIndex.update(pos, RGBLightColor4.fromRgbAndEmission(source.rgb, Math.round(source.energy * 15.0F)));
            }
         }

         return RGBRealLightEngine.CnbCommit.COMMITTED;
      } else if (previous != null && previous.active()) {
         int strikes = emptyStrikes.merge(key, 1, Integer::sum);
         return strikes >= 4 ? RGBRealLightEngine.CnbCommit.CONFIRMED_EMPTY : RGBRealLightEngine.CnbCommit.HELD;
      } else {
         return RGBRealLightEngine.CnbCommit.HELD;
      }
   }

   private static void processPendingCnbRemovals() {
      if (!CNB_REMOVE_PENDING.isEmpty()) {
         Iterator<Entry<Long, RGBRealLightEngine.PendingCnbRemoval>> iterator = CNB_REMOVE_PENDING.entrySet().iterator();
         int processed = 0;

         while (iterator.hasNext() && processed++ < 128) {
            Entry<Long, RGBRealLightEngine.PendingCnbRemoval> entry = iterator.next();
            RGBRealLightEngine.PendingCnbRemoval pending = entry.getValue();
            if (pending == null || pending.pos == null) {
               iterator.remove();
            } else if (pending.delayTicks > 0) {
               entry.setValue(new RGBRealLightEngine.PendingCnbRemoval(pending.pos, pending.delayTicks - 1, pending.attemptsLeft));
            } else if (isStillChiseledBlock(pending.pos)) {
               iterator.remove();
               Object be = currentBlockEntity(pending.pos);
               if (be != null) {
                  scheduleCnbBlockEntity(be, 1, 16);
               }
            } else if (pending.attemptsLeft <= 0) {
               iterator.remove();
               removeCnbSource(pending.pos, true);
            } else {
               entry.setValue(new RGBRealLightEngine.PendingCnbRemoval(pending.pos, 2, pending.attemptsLeft - 1));
            }
         }
      }
   }

   public static void deferCnbReloadRender(BlockPos pos) {
      if (pos != null) {
         if (shouldDeferNewEvent()) {
            markDirty(pos);
         } else {
            RGBRenderInvalidator.dirtyChunk(pos.getX() >> 4, pos.getZ() >> 4);
         }
      }
   }

   private static boolean shouldDeferNewEvent() {
      return !RGBLightPersistence.readyForCurrentDimension()
         || EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_IDLE
         || EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING;
   }

   private static boolean usesShadowCnbState() {
      return EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_IDLE || EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING;
   }

   public static boolean bootstrapAllowedAt(BlockPos pos) {
      if (!RGBLightPersistence.readyForCurrentDimension()) {
         return false;
      } else if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.AUTO || EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.CATCHING_UP) {
         return true;
      } else {
         return EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING && pos != null
            ? MANUAL_BOOTSTRAP_SECTIONS.contains(SectionPos.asLong(pos.getX() >> 4, pos.getY() >> 4, pos.getZ() >> 4))
            : false;
      }
   }

   private static void allowBootstrapAround(BlockPos pos) {
      if (pos != null && EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING) {
         int blockRadius = radiusCached() * 2 + 6;
         int minX = pos.getX() - blockRadius >> 4;
         int maxX = pos.getX() + blockRadius >> 4;
         int minY = pos.getY() - blockRadius >> 4;
         int maxY = pos.getY() + blockRadius >> 4;
         int minZ = pos.getZ() - blockRadius >> 4;
         int maxZ = pos.getZ() + blockRadius >> 4;

         for (int sx = minX; sx <= maxX; sx++) {
            for (int sy = minY; sy <= maxY; sy++) {
               for (int sz = minZ; sz <= maxZ; sz++) {
                  MANUAL_BOOTSTRAP_SECTIONS.add(SectionPos.asLong(sx, sy, sz));
               }
            }
         }
      }
   }

   private static void syncRuntimeState() {
      long version = RGBRuntime.clientStateVersion();
      if (version != OBSERVED_RUNTIME_VERSION) {
         OBSERVED_RUNTIME_VERSION = version;
         if (RGBRuntime.clientTargetManual()) {
            cancelActiveBatch();
            if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.AUTO) {
               initializeManualShadow();
               RGBLightPersistence.saveCurrentIfReady();
            }

            EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.MANUAL_IDLE;
            MANUAL_BOOTSTRAP_SECTIONS.clear();
            RGBLightEngine.clearPendingBootstrapWork();
            RGBRuntime.setClientBootstrapAllowed(false);
         } else if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.AUTO) {
            RGBRuntime.setClientBootstrapAllowed(true);
         } else {
            startCatchUp();
         }
      }
   }

   private static void initializeManualShadow() {
      MANUAL_CNB_SHADOW.clear();
      MANUAL_CNB_SHADOW.putAll(CNB_CACHE);
      MANUAL_CNB_EMPTY_STRIKES.clear();
      MANUAL_CNB_EMPTY_STRIKES.putAll(CNB_EMPTY_STRIKES);
      MANUAL_CNB_WEAK_STRIKES.clear();
      MANUAL_CNB_WEAK_STRIKES.putAll(CNB_WEAK_STRIKES);
   }

   private static void startManualBake(boolean all, int radius) {
      if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_IDLE && ACTIVE_BATCH.isEmpty()) {
         Minecraft minecraft = Minecraft.getInstance();
         BlockPos center = minecraft != null && minecraft.player != null ? minecraft.player.blockPosition().immutable() : BlockPos.ZERO;
         if (!buildFixedBatch(all, radius, center, false)) {
            System.out.println("[RGB Blocks] Bake skipped: no dirty positions in scope.");
         } else {
            EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.MANUAL_BAKING;
            REPLAY_TO_AUTO = false;
            STABILIZATION_TICKS = 0;
            BATCH_PROCESSED = 0;
            BATCH_FAILED = 0;
            BATCH_SKIPPED_UNLOADED = 0;
            MANUAL_BOOTSTRAP_SECTIONS.clear();
            RGBLightEngine.clearPendingBootstrapWork();

            for (RGBRealLightEngine.DirtyBatchEntry entry : ACTIVE_BATCH) {
               allowBootstrapAround(BlockPos.of(entry.packedPos));
            }

            RGBRuntime.setClientBootstrapAllowed(true);
         }
      }
   }

   private static void startCatchUp() {
      if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_IDLE || EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING) {
         CNB_EMPTY_STRIKES.clear();
         CNB_EMPTY_STRIKES.putAll(MANUAL_CNB_EMPTY_STRIKES);
         CNB_WEAK_STRIKES.clear();
         CNB_WEAK_STRIKES.putAll(MANUAL_CNB_WEAK_STRIKES);
      }

      cancelActiveBatch();
      if (!buildFixedBatch(true, 256, BlockPos.ZERO, true) && CNB_PENDING.isEmpty() && CNB_REMOVE_PENDING.isEmpty()) {
         finishToAuto();
      } else {
         EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.CATCHING_UP;
         REPLAY_TO_AUTO = true;
         STABILIZATION_TICKS = 0;
         BATCH_PROCESSED = 0;
         BATCH_FAILED = 0;
         BATCH_SKIPPED_UNLOADED = 0;
         MANUAL_BOOTSTRAP_SECTIONS.clear();
         RGBLightEngine.clearPendingBootstrapWork();
         RGBRuntime.setClientBootstrapAllowed(true);
      }
   }

   private static void collectActiveBakeEvents() {
   }

   private static boolean hasPendingCnbWorkInActiveBakeScope() {
      if (!ACTIVE_BAKE_ALL) {
         for (RGBRealLightEngine.PendingCnbRefresh pending : CNB_PENDING.values()) {
            if (pending != null && pending.pos != null && isInsideActiveBakeScope(pending.pos)) {
               return true;
            }
         }

         for (RGBRealLightEngine.PendingCnbRemoval pending : CNB_REMOVE_PENDING.values()) {
            if (pending != null && pending.pos != null && isInsideActiveBakeScope(pending.pos)) {
               return true;
            }
         }

         return false;
      } else {
         return !CNB_PENDING.isEmpty() || !CNB_REMOVE_PENDING.isEmpty();
      }
   }

   private static boolean isInsideActiveBakeScope(BlockPos pos) {
      if (!ACTIVE_BAKE_ALL && pos != null) {
         long dx = (long)pos.getX() - ACTIVE_BAKE_CENTER.getX();
         long dy = (long)pos.getY() - ACTIVE_BAKE_CENTER.getY();
         long dz = (long)pos.getZ() - ACTIVE_BAKE_CENTER.getZ();
         long radius = ACTIVE_BAKE_RADIUS;
         return dx * dx + dy * dy + dz * dz <= radius * radius;
      } else {
         return true;
      }
   }

   private static void processReplayTick() {
      if (EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING || EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.CATCHING_UP) {
         BlockAndTintGetter level = clientLevel();
         if (level != null) {
            RGBLightEngine.processPendingBootstrap(level, 2);
         }

         RGBRealLightEngine.DirtyBatchEntry entry = ACTIVE_BATCH.pollFirst();
         if (entry != null) {
            RGBRealLightEngine.BatchResult result;
            try {
               result = processBatchEntry(entry);
            } catch (Throwable error) {
               result = RGBRealLightEngine.BatchResult.FAILED;
               System.err.println("[RGB Blocks] Dirty-position Bake failed at " + BlockPos.of(entry.packedPos));
               error.printStackTrace();
            }

            switch (result) {
               case APPLIED:
                  clearDirtyIfGeneration(currentDimensionKey(), entry.packedPos, entry.generation);
                  BATCH_PROCESSED++;
                  break;
               case RETRY:
                  ACTIVE_BATCH.addLast(entry.nextWait(entry.cnbRefreshRequested || BATCH_INTERNAL_CNB_REFRESH.contains(entry.packedPos)));
                  break;
               case SKIPPED_UNLOADED:
                  BATCH_SKIPPED_UNLOADED++;
                  break;
               case FAILED:
                  BATCH_FAILED++;
            }

            STABILIZATION_TICKS = 0;
         } else if (!BATCH_INTERNAL_CNB_REFRESH.isEmpty()) {
            STABILIZATION_TICKS = 0;
         } else if (RGBLightEngine.hasPendingBootstrapWork()) {
            STABILIZATION_TICKS = 0;
         } else if (++STABILIZATION_TICKS >= 24) {
            if (REPLAY_TO_AUTO) {
               finishToAuto();
            } else {
               EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.MANUAL_IDLE;
               MANUAL_BOOTSTRAP_SECTIONS.clear();
               RGBLightEngine.clearPendingBootstrapWork();
               RGBRuntime.setClientBootstrapAllowed(false);
               RGBLightPersistence.saveCurrentBlocking();
               System.out
                  .println(
                     "[RGB Blocks] Bake complete: "
                        + BATCH_PROCESSED
                        + " applied, "
                        + BATCH_SKIPPED_UNLOADED
                        + " unloaded/kept dirty, "
                        + BATCH_FAILED
                        + " failed."
                  );
            }
         }
      }
   }

   private static void finishToAuto() {
      EFFECTIVE_MODE = RGBRealLightEngine.EffectiveMode.AUTO;
      ACTIVE_BATCH.clear();
      BATCH_INTERNAL_CNB_REFRESH.clear();
      MANUAL_BOOTSTRAP_SECTIONS.clear();
      REPLAY_TO_AUTO = false;
      STABILIZATION_TICKS = 0;
      RGBRuntime.setClientBootstrapAllowed(true);
      RGBLightPersistence.saveCurrentIfReady();
   }

   private static void replayEvent(RGBRealLightEngine.DeferredRgbEvent event) {
      BlockPos pos = BlockPos.of(event.packedPos);
      switch (event.type) {
         case INVALIDATE_AROUND:
            executeInvalidateAround(pos);
            break;
         case SETTLE_AFTER_SERVER_SYNC:
            executeSettleAfterServerSync(pos);
            break;
         case CNB_SOURCE_COMMITTED:
            if (event.cnbSnapshot != null) {
               CNB_CACHE.put(event.packedPos, event.cnbSnapshot);
               BlockAndTintGetter level = clientLevel();
               if (level != null) {
                  RGBSourceIndex.refresh(level, pos);
               }

               executeCommittedCnbChange(pos);
            }
            break;
         case CNB_SOURCE_REMOVED:
            executeRealCnbRemoval(pos, true);
            break;
         case CNB_MODEL_RENDER_REFRESH:
            RGBRenderInvalidator.dirtyAround(pos, radiusCached());
            break;
         case CNB_RELOAD_RENDER:
            RGBRenderInvalidator.dirtyChunk(pos.getX() >> 4, pos.getZ() >> 4);
      }
   }

   private static void deferEvent(RGBRealLightEngine.DeferredEventType type, BlockPos pos, RGBRealLightEngine.CnbSource snapshot) {
      markDirty(pos);
   }

   private static void deferShadowRemoval(BlockPos pos) {
      long key = cnbKey(pos);
      MANUAL_CNB_EMPTY_STRIKES.remove(key);
      MANUAL_CNB_WEAK_STRIKES.remove(key);
      MANUAL_CNB_SHADOW.put(key, RGBRealLightEngine.CnbSource.NONE);
      if (!BATCH_INTERNAL_CNB_REFRESH.remove(key)) {
         markDirty(pos);
      }
   }

   private static RGBRealLightEngine.CnbSource sourceFrom(Map<Long, RGBRealLightEngine.CnbSource> cache, BlockPos pos) {
      RGBRealLightEngine.CnbSource source = cache.get(cnbKey(pos));
      return source == null ? RGBRealLightEngine.CnbSource.NONE : source;
   }

   private static void selectDeferredEvents(boolean all, int radius) {
      Minecraft minecraft = Minecraft.getInstance();
      BlockPos center = minecraft != null && minecraft.player != null ? minecraft.player.blockPosition() : BlockPos.ZERO;
      selectDeferredEvents(all, radius, center);
   }

   private static void selectDeferredEvents(boolean all, int radius, BlockPos center) {
      String dimension = currentDimensionKey();
      ArrayDeque<RGBRealLightEngine.DeferredRgbEvent> queue = DEFERRED_EVENTS.get(dimension);
      if (queue != null && !queue.isEmpty()) {
         BlockPos origin = center == null ? BlockPos.ZERO : center;
         long clampedRadius = Math.max(4, Math.min(radius, 256));
         long radiusSq = clampedRadius * clampedRadius;
         ArrayDeque<RGBRealLightEngine.DeferredRgbEvent> keep = new ArrayDeque<>();

         while (!queue.isEmpty()) {
            RGBRealLightEngine.DeferredRgbEvent event = queue.removeFirst();
            BlockPos pos = BlockPos.of(event.packedPos);
            long dx = (long)pos.getX() - origin.getX();
            long dy = (long)pos.getY() - origin.getY();
            long dz = (long)pos.getZ() - origin.getZ();
            if (!all && dx * dx + dy * dy + dz * dz > radiusSq) {
               keep.addLast(event);
            } else {
               REPLAY_EVENTS.addLast(event);
            }
         }

         if (keep.isEmpty()) {
            DEFERRED_EVENTS.remove(dimension);
         } else {
            DEFERRED_EVENTS.put(dimension, keep);
         }
      }
   }

   private static void moveAllCurrentDimensionEventsToReplay() {
      selectDeferredEvents(true, 256);
   }

   private static void returnReplayToDeferredFront() {
      if (!REPLAY_EVENTS.isEmpty()) {
         ArrayList<RGBRealLightEngine.DeferredRgbEvent> list = new ArrayList<>(REPLAY_EVENTS);
         REPLAY_EVENTS.clear();

         for (int i = list.size() - 1; i >= 0; i--) {
            RGBRealLightEngine.DeferredRgbEvent event = list.get(i);
            DEFERRED_EVENTS.computeIfAbsent(event.dimension, ignored -> new ArrayDeque<>()).addFirst(event);
         }
      }
   }

   private static String currentDimensionKey() {
      try {
         Minecraft mc = Minecraft.getInstance();
         if (mc != null && mc.level != null) {
            return mc.level.dimension().identifier().toString();
         }
      } catch (Throwable var1) {
      }

      return "unknown";
   }

   static List<RGBLightPersistence.PersistedCnbSource> snapshotPersistedCnbSources() {
      List<RGBLightPersistence.PersistedCnbSource> snapshot = new ArrayList<>();

      for (Entry<Long, RGBRealLightEngine.CnbSource> entry : CNB_CACHE.entrySet()) {
         RGBRealLightEngine.CnbSource source = entry.getValue();
         if (entry.getKey() != null && source != null && source.active() && !STALE_CNB_CLEANUP.contains(entry.getKey())) {
            snapshot.add(new RGBLightPersistence.PersistedCnbSource(entry.getKey(), source.rgb, source.energy));
         }
      }

      return snapshot;
   }

   static void restorePersistedCnbSources(List<RGBLightPersistence.PersistedCnbSource> sources) {
      CNB_CACHE.clear();
      CNB_EMPTY_STRIKES.clear();
      CNB_WEAK_STRIKES.clear();
      UNVERIFIED_PERSISTED_CNB.clear();
      STALE_CNB_CLEANUP.clear();
      CNB_VALIDATION_REQUESTS.clear();
      PERSISTED_CNB_RECOVERY_CANDIDATES.clear();
      RGBSourceIndex.clear();
      List<BlockPos> stalePersistedSources = new ArrayList<>();
      if (sources != null) {
         for (RGBLightPersistence.PersistedCnbSource persisted : sources) {
            if (persisted != null && persisted.rgb() >= 0 && Float.isFinite(persisted.energy()) && !(persisted.energy() <= 0.0F)) {
               BlockPos pos = BlockPos.of(persisted.packedPos());
               if (isPositionLoaded(pos) && !isStillChiseledBlock(pos)) {
                  stalePersistedSources.add(pos);
               } else {
                  long key = persisted.packedPos();
                  CNB_CACHE.put(key, new RGBRealLightEngine.CnbSource(persisted.rgb(), clamp(persisted.energy(), 0.0F, 1.0F)));
                  UNVERIFIED_PERSISTED_CNB.add(key);
                  if (isPositionLoaded(pos)) {
                     CNB_VALIDATION_REQUESTS.add(key);
                  }
               }
            }
         }
      }

      BlockAndTintGetter level = clientLevel();
      if (level != null) {
         for (long packedPos : CNB_CACHE.keySet()) {
            RGBSourceIndex.refresh(level, BlockPos.of(packedPos));
         }
      }

      for (BlockPos stale : stalePersistedSources) {
         deferEvent(RGBRealLightEngine.DeferredEventType.INVALIDATE_AROUND, stale, null);
         deferEvent(RGBRealLightEngine.DeferredEventType.SETTLE_AFTER_SERVER_SYNC, stale, null);
      }

      if (EFFECTIVE_MODE != RGBRealLightEngine.EffectiveMode.AUTO) {
         initializeManualShadow();
      }
   }

   static void registerPersistedCnbRecoveryCandidates(Iterable<Long> packedPositions) {
      PERSISTED_CNB_RECOVERY_CANDIDATES.clear();
      if (packedPositions != null) {
         for (Long packedPos : packedPositions) {
            if (packedPos != null) {
               PERSISTED_CNB_RECOVERY_CANDIDATES.add(packedPos);
            }
         }
      }
   }

   static boolean isLoadedChiseledBlockForPersistence(BlockPos pos) {
      return pos != null && isPositionLoaded(pos) && isStillChiseledBlock(pos);
   }

   static void deferPersistedSourceCleanup(List<BlockPos> stalePositions) {
      if (stalePositions != null) {
         for (BlockPos pos : stalePositions) {
            if (pos != null) {
               deferEvent(RGBRealLightEngine.DeferredEventType.INVALIDATE_AROUND, pos, null);
               deferEvent(RGBRealLightEngine.DeferredEventType.SETTLE_AFTER_SERVER_SYNC, pos, null);
            }
         }
      }
   }

   static void prepareForPersistenceDimensionSwitch() {
      cancelActiveBatch();
      CNB_PENDING.clear();
      CNB_REMOVE_PENDING.clear();
      CNB_CACHE.clear();
      CNB_EMPTY_STRIKES.clear();
      CNB_WEAK_STRIKES.clear();
      UNVERIFIED_PERSISTED_CNB.clear();
      STALE_CNB_CLEANUP.clear();
      CNB_VALIDATION_REQUESTS.clear();
      MANUAL_CNB_SHADOW.clear();
      MANUAL_CNB_EMPTY_STRIKES.clear();
      MANUAL_CNB_WEAK_STRIKES.clear();
      MANUAL_BOOTSTRAP_SECTIONS.clear();
      STABILIZATION_TICKS = 0;
      REPLAY_TO_AUTO = false;
      EFFECTIVE_MODE = RGBRuntime.clientTargetManual() ? RGBRealLightEngine.EffectiveMode.MANUAL_IDLE : RGBRealLightEngine.EffectiveMode.AUTO;
      RGBRuntime.setClientBootstrapAllowed(EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.AUTO);
   }

   static int deferredEventCountForCurrentDimension() {
      Map<Long, Long> dirty = DIRTY_LEDGER.get(currentDimensionKey());
      return dirty == null ? 0 : dirty.size();
   }

   static int replayEventCount() {
      return ACTIVE_BATCH.size();
   }

   static String effectiveModeName() {
      return EFFECTIVE_MODE.name();
   }

   static List<Long> snapshotDirtyPositions() {
      return snapshotDirtyPositions(currentDimensionKey());
   }

   static List<Long> snapshotDirtyPositions(String dimension) {
      Map<Long, Long> dirty = DIRTY_LEDGER.get(dimension != null && !dimension.isBlank() ? dimension : currentDimensionKey());
      return dirty != null && !dirty.isEmpty() ? new ArrayList<>(dirty.keySet()) : List.of();
   }

   static void restoreDirtyPositions(List<Long> positions) {
      restoreDirtyPositions(currentDimensionKey(), positions);
   }

   static void restoreDirtyPositions(String dimension, List<Long> positions) {
      String key = dimension != null && !dimension.isBlank() ? dimension : currentDimensionKey();
      Map<Long, Long> dirty = DIRTY_LEDGER.computeIfAbsent(key, ignored -> new ConcurrentHashMap<>());
      if (positions != null) {
         for (Long packedPos : positions) {
            if (packedPos != null) {
               dirty.put(packedPos, ++DIRTY_GENERATION);
            }
         }
      }

      if (dirty.isEmpty()) {
         DIRTY_LEDGER.remove(key, dirty);
      }
   }

   private static void markDirty(BlockPos pos) {
      if (pos != null) {
         DIRTY_LEDGER.computeIfAbsent(currentDimensionKey(), ignored -> new ConcurrentHashMap<>()).put(pos.asLong(), ++DIRTY_GENERATION);
      }
   }

   private static void markClean(BlockPos pos) {
      if (pos != null) {
         Map<Long, Long> dirty = DIRTY_LEDGER.get(currentDimensionKey());
         if (dirty != null) {
            dirty.remove(pos.asLong());
            if (dirty.isEmpty()) {
               DIRTY_LEDGER.remove(currentDimensionKey(), dirty);
            }
         }
      }
   }

   private static void clearDirtyIfGeneration(String dimension, long packedPos, long generation) {
      Map<Long, Long> dirty = DIRTY_LEDGER.get(dimension);
      if (dirty != null) {
         dirty.remove(packedPos, generation);
         if (dirty.isEmpty()) {
            DIRTY_LEDGER.remove(dimension, dirty);
         }
      }
   }

   private static boolean hasLoadedDirtyForCurrentDimension() {
      Map<Long, Long> dirty = DIRTY_LEDGER.get(currentDimensionKey());
      if (dirty != null && !dirty.isEmpty()) {
         for (Long packedPos : dirty.keySet()) {
            if (packedPos != null && isPositionLoaded(BlockPos.of(packedPos))) {
               return true;
            }
         }

         return false;
      } else {
         return false;
      }
   }

   private static boolean buildFixedBatch(boolean all, int radius, BlockPos center, boolean loadedOnly) {
      ACTIVE_BATCH.clear();
      BATCH_INTERNAL_CNB_REFRESH.clear();
      String dimension = currentDimensionKey();
      Map<Long, Long> dirty = DIRTY_LEDGER.get(dimension);
      if (dirty != null && !dirty.isEmpty()) {
         BlockPos origin = center == null ? BlockPos.ZERO : center;
         long clampedRadius = Math.max(4, Math.min(radius, 256));
         long radiusSq = clampedRadius * clampedRadius;
         ArrayList<Entry<Long, Long>> selected = new ArrayList<>();

         for (Entry<Long, Long> entry : dirty.entrySet()) {
            if (entry.getKey() != null && entry.getValue() != null) {
               BlockPos pos = BlockPos.of(entry.getKey());
               if (!loadedOnly || isPositionLoaded(pos)) {
                  long dx = (long)pos.getX() - origin.getX();
                  long dy = (long)pos.getY() - origin.getY();
                  long dz = (long)pos.getZ() - origin.getZ();
                  if (all || dx * dx + dy * dy + dz * dz <= radiusSq) {
                     selected.add(entry);
                  }
               }
            }
         }

         selected.sort(Entry.comparingByValue());

         for (Entry<Long, Long> entry : selected) {
            ACTIVE_BATCH.addLast(new RGBRealLightEngine.DirtyBatchEntry(entry.getKey(), entry.getValue(), 0, false));
         }

         return !ACTIVE_BATCH.isEmpty();
      } else {
         return false;
      }
   }

   private static RGBRealLightEngine.BatchResult processBatchEntry(RGBRealLightEngine.DirtyBatchEntry entry) {
      BlockPos pos = BlockPos.of(entry.packedPos);
      if (!isPositionLoaded(pos)) {
         return RGBRealLightEngine.BatchResult.SKIPPED_UNLOADED;
      }

      long key = cnbKey(pos);
      boolean chiseled = isStillChiseledBlock(pos);
      if (chiseled && EFFECTIVE_MODE == RGBRealLightEngine.EffectiveMode.MANUAL_BAKING) {
         if (!entry.cnbRefreshRequested) {
            Object blockEntity = currentBlockEntity(pos);
            if (blockEntity != null) {
               BATCH_INTERNAL_CNB_REFRESH.add(key);
               scheduleCnbBlockEntity(blockEntity, 0, 16);
               return RGBRealLightEngine.BatchResult.RETRY;
            }

            if (entry.waitTicks < 12) {
               return RGBRealLightEngine.BatchResult.RETRY;
            }
         }

         if (CNB_PENDING.containsKey(key) || BATCH_INTERNAL_CNB_REFRESH.contains(key)) {
            if (entry.waitTicks < 64) {
               return RGBRealLightEngine.BatchResult.RETRY;
            }

            BATCH_INTERNAL_CNB_REFRESH.remove(key);
         }
      }

      if (chiseled) {
         RGBRealLightEngine.CnbSource desired = MANUAL_CNB_SHADOW.containsKey(key) ? MANUAL_CNB_SHADOW.get(key) : CNB_CACHE.get(key);
         if (desired != null && desired.active()) {
            CNB_CACHE.put(key, desired);
         } else {
            CNB_CACHE.remove(key);
         }

         CNB_EMPTY_STRIKES.remove(key);
         CNB_WEAK_STRIKES.remove(key);
         UNVERIFIED_PERSISTED_CNB.remove(key);
         CNB_VALIDATION_REQUESTS.remove(key);
         STALE_CNB_CLEANUP.remove(key);
         PERSISTED_CNB_RECOVERY_CANDIDATES.remove(key);
      } else {
         CNB_CACHE.remove(key);
         CNB_EMPTY_STRIKES.remove(key);
         CNB_WEAK_STRIKES.remove(key);
         MANUAL_CNB_SHADOW.remove(key);
         MANUAL_CNB_EMPTY_STRIKES.remove(key);
         MANUAL_CNB_WEAK_STRIKES.remove(key);
      }

      BlockAndTintGetter level = clientLevel();
      if (level == null) {
         return RGBRealLightEngine.BatchResult.FAILED;
      }

      RGBSourceIndex.refresh(level, pos);
      allowBootstrapAround(pos);
      executeInvalidateAround(pos);
      executeSettleAfterServerSync(pos);
      BATCH_INTERNAL_CNB_REFRESH.remove(key);
      return RGBRealLightEngine.BatchResult.APPLIED;
   }

   private static void cancelActiveBatch() {
      ACTIVE_BATCH.clear();
      BATCH_INTERNAL_CNB_REFRESH.clear();
      STABILIZATION_TICKS = 0;
      REPLAY_TO_AUTO = false;
      MANUAL_BOOTSTRAP_SECTIONS.clear();
      RGBLightEngine.clearPendingBootstrapWork();
   }

   private static void processCnbValidationAndCleanup() {
      int budget = 64;

      for (Long key : new ArrayList<>(STALE_CNB_CLEANUP)) {
         if (budget-- <= 0) {
            break;
         }

         BlockPos pos = BlockPos.of(key);
         if (isPositionLoaded(pos)) {
            if (!isStillChiseledBlock(pos)) {
               removeCnbSource(pos, true);
            } else {
               STALE_CNB_CLEANUP.remove(key);
            }
         }
      }

      budget = 64;

      for (Long key : new ArrayList<>(CNB_VALIDATION_REQUESTS)) {
         if (budget-- <= 0) {
            break;
         }

         CNB_VALIDATION_REQUESTS.remove(key);
         BlockPos pos = BlockPos.of(key);
         if (isPositionLoaded(pos)) {
            if (!isStillChiseledBlock(pos)) {
               removeCnbSource(pos, true);
            } else {
               Object blockEntity = currentBlockEntity(pos);
               if (blockEntity != null) {
                  scheduleCnbBlockEntity(blockEntity, 0, 16);
               }
            }
         }
      }
   }

   private static boolean isPositionLoaded(BlockPos pos) {
      try {
         Minecraft minecraft = Minecraft.getInstance();
         return minecraft != null && minecraft.level != null && pos != null && minecraft.level.isLoaded(pos);
      } catch (Throwable ignored) {
         return false;
      }
   }

   private static boolean isStillChiseledBlock(BlockPos pos) {
      try {
         BlockAndTintGetter level = clientLevel();
         if (level != null && pos != null) {
            BlockState state = level.getBlockState(pos);
            Identifier id = BuiltInRegistries.BLOCK.getKey(state.getBlock());
            return id != null && "chiselsandbits".equals(id.getNamespace()) && "chiseled".equals(id.getPath());
         } else {
            return false;
         }
      } catch (Throwable ignored) {
         return false;
      }
   }

   private static Object currentBlockEntity(BlockPos pos) {
      try {
         if (clientLevel() instanceof BlockGetter getter) {
            return getter.getBlockEntity(pos);
         }
      } catch (Throwable var3) {
      }

      return null;
   }

   private static boolean isSuspiciousWeakening(RGBRealLightEngine.CnbSource previous, RGBRealLightEngine.CnbSource source) {
      if (previous != null && source != null && previous.active() && source.active()) {
         float drop = previous.energy - source.energy;
         return drop >= 0.16F ? true : previous.rgb == source.rgb && previous.energy >= 0.5F && source.energy < previous.energy * 0.72F;
      } else {
         return false;
      }
   }

   private static RGBRealLightEngine.CnbSource smoothCnbSource(RGBRealLightEngine.CnbSource previous, RGBRealLightEngine.CnbSource source, float newWeight) {
      if (previous == null || !previous.active()) {
         return source;
      } else if (source != null && source.active()) {
         float oldWeight = 1.0F - clamp(newWeight, 0.0F, 1.0F);
         float nw = clamp(newWeight, 0.0F, 1.0F);
         int pr = previous.rgb >>> 16 & 0xFF;
         int pg = previous.rgb >>> 8 & 0xFF;
         int pb = previous.rgb & 0xFF;
         int nr = source.rgb >>> 16 & 0xFF;
         int ng = source.rgb >>> 8 & 0xFF;
         int nb = source.rgb & 0xFF;
         int r = clamp255(Math.round(pr * oldWeight + nr * nw));
         int g = clamp255(Math.round(pg * oldWeight + ng * nw));
         int b = clamp255(Math.round(pb * oldWeight + nb * nw));
         float energy = clamp(previous.energy * oldWeight + source.energy * nw, 0.0F, 1.0F);
         return new RGBRealLightEngine.CnbSource(r << 16 | g << 8 | b, energy);
      } else {
         return previous;
      }
   }

   private static RGBRealLightEngine.CnbSource computeCnbSourceFromAccessor(Object accessor) {
      if (accessor == null) {
         return RGBRealLightEngine.CnbSource.NONE;
      }

      RGBRealLightEngine.CnbSource fromStatistics = computeCnbSourceFromStatistics(accessor);
      if (fromStatistics.active()) {
         return fromStatistics;
      }

      if (!implementsCnbAccessor(accessor.getClass())) {
         return RGBRealLightEngine.CnbSource.NONE;
      }

      try {
         if (invokeNoArg(accessor, "stream") instanceof Stream<?> stream) {
            RGBRealLightEngine.CnbAccumulator acc = new RGBRealLightEngine.CnbAccumulator();
            stream.limit(1024L).forEach(entry -> addCnbEntry(entry, acc));
            return acc.toSource();
         } else {
            return RGBRealLightEngine.CnbSource.NONE;
         }
      } catch (Throwable ignored) {
         return RGBRealLightEngine.CnbSource.NONE;
      }
   }

   private static RGBRealLightEngine.CnbSource computeCnbSourceFromStatistics(Object accessor) {
      try {
         Object statistics = invokeNoArg(accessor, "getStatistics");
         if (statistics == null) {
            return RGBRealLightEngine.CnbSource.NONE;
         }

         if (invokeNoArg(statistics, "getStateCounts") instanceof Map<?, ?> counts && !counts.isEmpty()) {
            RGBRealLightEngine.CnbAccumulator acc = new RGBRealLightEngine.CnbAccumulator();
            int visited = 0;

            for (Entry<?, ?> entry : counts.entrySet()) {
               if (entry != null && entry.getKey() != null) {
                  int count = 0;
                  if (entry.getValue() instanceof Number number) {
                     count = number.intValue();
                  }

                  if (count > 0) {
                     float amount = clamp(count / 4096.0F, 2.4414062E-4F, 1.0F);
                     addCnbInformation(entry.getKey(), acc, amount);
                     if (++visited >= 1024) {
                        break;
                     }
                  }
               }
            }

            return acc.toSource();
         } else {
            return RGBRealLightEngine.CnbSource.NONE;
         }
      } catch (Throwable ignored) {
         return RGBRealLightEngine.CnbSource.NONE;
      }
   }

   private static void addCnbEntry(Object entry, RGBRealLightEngine.CnbAccumulator acc) {
      if (entry != null && acc != null) {
         try {
            Object information = invokeNoArg(entry, "getBlockInformation");
            float volume = 2.4414062E-4F;

            try {
               Object startObj = invokeNoArg(entry, "getStartPoint");
               Object endObj = invokeNoArg(entry, "getEndPoint");
               if (startObj instanceof Vec3 start && endObj instanceof Vec3 end) {
                  volume = (float)Math.max(2.4414062E-4F, Math.abs((end.x - start.x) * (end.y - start.y) * (end.z - start.z)));
               }
            } catch (Throwable ignored) {
               volume = 2.4414062E-4F;
            }

            addCnbInformation(information, acc, clamp(Math.max(volume * 42.0F, 0.22F), 0.12F, 1.0F));
         } catch (Throwable var9) {
         }
      }
   }

   private static void addCnbInformation(Object information, RGBRealLightEngine.CnbAccumulator acc, float amount) {
      if (information != null && acc != null) {
         try {
            if (!(invokeNoArg(information, "blockState") instanceof BlockState state)) {
               return;
            }

            int rgb = rgbForState(state);
            if (rgb < 0) {
               return;
            }

            acc.add(rgb, amount);
         } catch (Throwable var6) {
         }
      }
   }

   private static Object invokeNoArg(Object target, String methodName) throws ReflectiveOperationException {
      Class<?> type = target.getClass();

      try {
         Method method = type.getMethod(methodName);
         method.setAccessible(true);
         return method.invoke(target);
      } catch (NoSuchMethodException ignored) {
         for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
               Method method = current.getDeclaredMethod(methodName);
               method.setAccessible(true);
               return method.invoke(target);
            } catch (NoSuchMethodException var6) {
            }
         }

         throw ignored;
      }
   }

   private static BlockPos cnbBlockEntityPos(Object blockEntity) {
      try {
         return invokeNoArg(blockEntity, "getBlockPos") instanceof BlockPos blockPos ? blockPos.immutable() : null;
      } catch (Throwable ignored) {
         return null;
      }
   }

   private static boolean sameCnbSource(RGBRealLightEngine.CnbSource a, RGBRealLightEngine.CnbSource b) {
      RGBRealLightEngine.CnbSource aa = a == null ? RGBRealLightEngine.CnbSource.NONE : a;
      RGBRealLightEngine.CnbSource bb = b == null ? RGBRealLightEngine.CnbSource.NONE : b;
      return aa.rgb == bb.rgb && Math.abs(aa.energy - bb.energy) < 1.0E-4F;
   }

   private static boolean equivalentCnbSourceForValidation(RGBRealLightEngine.CnbSource a, RGBRealLightEngine.CnbSource b) {
      RGBRealLightEngine.CnbSource aa = a == null ? RGBRealLightEngine.CnbSource.NONE : a;
      RGBRealLightEngine.CnbSource bb = b == null ? RGBRealLightEngine.CnbSource.NONE : b;
      if (aa.active() && bb.active() && aa.rgb == bb.rgb) {
         int aLevel = Math.round(clamp(aa.energy, 0.0F, 1.0F) * 15.0F);
         int bLevel = Math.round(clamp(bb.energy, 0.0F, 1.0F) * 15.0F);
         return aLevel == bLevel || Math.abs(aa.energy - bb.energy) <= 0.02F;
      } else {
         return false;
      }
   }

   private static boolean implementsCnbAccessor(Class<?> type) {
      for (Class<?> current = type; current != null; current = current.getSuperclass()) {
         for (Class<?> iface : current.getInterfaces()) {
            if (isCnbAccessorInterface(iface)) {
               return true;
            }
         }
      }

      return false;
   }

   private static boolean isCnbAccessorInterface(Class<?> iface) {
      String name = iface.getName();
      if (!name.equals("mod.chiselsandbits.api.multistate.accessor.IAreaAccessor")
         && !name.equals("mod.chiselsandbits.api.multistate.accessor.ISingleBlockAxisAlignedAreaAccessor")
         && !name.equals("mod.chiselsandbits.api.multistate.accessor.world.IWorldAreaAccessor")) {
         for (Class<?> parent : iface.getInterfaces()) {
            if (isCnbAccessorInterface(parent)) {
               return true;
            }
         }

         return false;
      } else {
         return true;
      }
   }

   private static BlockAndTintGetter clientLevel() {
      try {
         return Minecraft.getInstance().level;
      } catch (Throwable ignored) {
         return null;
      }
   }

   private static long cnbKey(BlockPos pos) {
      return pos.asLong();
   }

   private static float clamp(float v, float min, float max) {
      return v < min ? min : Math.min(v, max);
   }

   private static int clampInt(int v, int min, int max) {
      return v < min ? min : Math.min(v, max);
   }

   private static int clamp255(int v) {
      return v < 0 ? 0 : Math.min(v, 255);
   }

   private enum BatchResult {
      APPLIED,
      RETRY,
      SKIPPED_UNLOADED,
      FAILED;
   }

   private static final class CnbAccumulator {
      private float r;
      private float g;
      private float b;
      private float weight;

      void add(int rgb, float amount) {
         float rr = (rgb >>> 16 & 0xFF) / 255.0F;
         float gg = (rgb >>> 8 & 0xFF) / 255.0F;
         float bb = (rgb & 0xFF) / 255.0F;
         float max = Math.max(rr, Math.max(gg, bb));
         if (!(max <= 0.0F) && !(amount <= 0.0F)) {
            this.r += rr / max * amount;
            this.g += gg / max * amount;
            this.b += bb / max * amount;
            this.weight += amount;
         }
      }

      RGBRealLightEngine.CnbSource toSource() {
         if (this.weight <= 0.0F) {
            return RGBRealLightEngine.CnbSource.NONE;
         }

         int rr = RGBRealLightEngine.clamp255(Math.round(this.r / this.weight * 255.0F));
         int gg = RGBRealLightEngine.clamp255(Math.round(this.g / this.weight * 255.0F));
         int bb = RGBRealLightEngine.clamp255(Math.round(this.b / this.weight * 255.0F));
         float fill = RGBRealLightEngine.clamp(this.weight, 0.0F, 1.0F);
         float energy = RGBRealLightEngine.clamp(0.66F + (float)Math.sqrt(fill) * 0.34F, 0.66F, 1.0F);
         return new RGBRealLightEngine.CnbSource(rr << 16 | gg << 8 | bb, energy);
      }
   }

   private enum CnbCommit {
      COMMITTED,
      HELD,
      CONFIRMED_EMPTY;

      boolean committed() {
         return this == COMMITTED;
      }
   }

   private record CnbSource(int rgb, float energy) {
      static final RGBRealLightEngine.CnbSource NONE = new RGBRealLightEngine.CnbSource(-1, 0.0F);

      boolean active() {
         return this.rgb >= 0 && this.energy > 0.0F;
      }
   }

   private enum DeferredEventType {
      INVALIDATE_AROUND,
      SETTLE_AFTER_SERVER_SYNC,
      CNB_SOURCE_COMMITTED,
      CNB_SOURCE_REMOVED,
      CNB_MODEL_RENDER_REFRESH,
      CNB_RELOAD_RENDER;
   }

   private record DeferredRgbEvent(RGBRealLightEngine.DeferredEventType type, String dimension, long packedPos, RGBRealLightEngine.CnbSource cnbSnapshot) {
   }

   private record DirtyBatchEntry(long packedPos, long generation, int waitTicks, boolean cnbRefreshRequested) {
      RGBRealLightEngine.DirtyBatchEntry nextWait(boolean requested) {
         return new RGBRealLightEngine.DirtyBatchEntry(this.packedPos, this.generation, this.waitTicks + 1, requested);
      }
   }

   private enum EffectiveMode {
      AUTO,
      MANUAL_IDLE,
      MANUAL_BAKING,
      CATCHING_UP;
   }

   private record PendingCnbRefresh(BlockPos pos, Object blockEntity, int delayTicks, int attemptsLeft) {
   }

   private record PendingCnbRemoval(BlockPos pos, int delayTicks, int attemptsLeft) {
   }
}
