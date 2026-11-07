package com.rgbblocks.client.lighting;

import java.util.ArrayDeque;
import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Queue;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.SectionPos;
import net.minecraft.core.BlockPos.MutableBlockPos;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.level.block.state.BlockState;

public final class RGBLightEngine {
   private static final RGBLightStorage STORAGE = new RGBLightStorage();
   private static final Set<Long> READY_SECTIONS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final Map<Long, Long> RETRY_AFTER_NANOS = new ConcurrentHashMap<>();
   private static final Queue<RGBLightEngine.RefreshRequest> REFRESH_QUEUE = new ConcurrentLinkedQueue<>();
   private static final Queue<BlockPos> SOURCE_BOOTSTRAP_QUEUE = new ConcurrentLinkedQueue<>();
   private static final int MAX_RADIUS = 15;
   private static final int MIN_RADIUS = 4;
   private static final int MAX_PROPAGATION_NODES = 120000;
   private static final int MAX_REFRESHES_PER_SAMPLE = 2;
   private static final long EMPTY_RETRY_NANOS = 350000000L;
   private static volatile int lastLevelIdentity = 0;
   private static volatile boolean CLIENT_DISCONNECTING = false;

   private RGBLightEngine() {
   }

   public static void invalidateAll() {
      STORAGE.clear();
      READY_SECTIONS.clear();
      RETRY_AFTER_NANOS.clear();
      REFRESH_QUEUE.clear();
      SOURCE_BOOTSTRAP_QUEUE.clear();
      RGBSourceIndex.clear();
   }

   public static void onClientDisconnect() {
      CLIENT_DISCONNECTING = true;
      invalidateAll();
   }

   static Map<Long, byte[]> snapshotPersistedSections() {
      return STORAGE.snapshotActiveSections();
   }

   static int persistedSectionCount() {
      return STORAGE.activeSectionCount();
   }

   static void restorePersistedSections(Map<Long, byte[]> sections) {
      STORAGE.restoreActiveSections(sections);
      READY_SECTIONS.clear();
      if (sections != null) {
         READY_SECTIONS.addAll(sections.keySet());
      }

      RETRY_AFTER_NANOS.clear();
      REFRESH_QUEUE.clear();
      SOURCE_BOOTSTRAP_QUEUE.clear();
      RGBSourceIndex.clear();
      CLIENT_DISCONNECTING = false;

      try {
         Minecraft minecraft = Minecraft.getInstance();
         if (minecraft != null && minecraft.level != null) {
            lastLevelIdentity = System.identityHashCode(minecraft.level);
            RGBRenderInvalidator.onClientWorldReady();
         }
      } catch (Throwable var2) {
      }
   }

   public static void invalidateAround(BlockAndTintGetter level, BlockPos pos) {
      if (RGBRealLightEngine.enabled() && level != null && pos != null) {
         rememberLevel(level);
         if (!CLIENT_DISCONNECTING) {
            int radius = radius();
            int clearRadius = radius + 2;
            int sourceScanRadius = radius + clearRadius;
            STORAGE.clearCube(pos, clearRadius);
            clearReadySectionsAround(pos, clearRadius);
            queueRefreshAround(pos, radius);
            MutableBlockPos scan = new MutableBlockPos();

            for (int y = pos.getY() - sourceScanRadius; y <= pos.getY() + sourceScanRadius; y++) {
               for (int z = pos.getZ() - sourceScanRadius; z <= pos.getZ() + sourceScanRadius; z++) {
                  for (int x = pos.getX() - sourceScanRadius; x <= pos.getX() + sourceScanRadius; x++) {
                     scan.set(x, y, z);
                     RGBLightColor4 source = RGBRealLightEngine.sourceColorAt(level, scan);
                     if (source.active()) {
                        propagateFrom(level, scan.immutable(), source, clearRadius, pos);
                     }
                  }
               }
            }
         }
      }
   }

   public static void invalidateChunk(BlockAndTintGetter level, int chunkX, int chunkZ) {
      if (RGBRealLightEngine.enabled() && level != null) {
         rememberLevel(level);
         if (!CLIENT_DISCONNECTING) {
            int minX = chunkX << 4;
            int minZ = chunkZ << 4;

            for (int y = -64; y <= 384; y += 16) {
               invalidateAround(level, new BlockPos(minX + 8, y + 8, minZ + 8));
            }
         }
      }
   }

   private static void propagateFrom(BlockAndTintGetter level, BlockPos sourcePos, RGBLightColor4 sourceColor, int affectedRadius, BlockPos affectedCenter) {
      ArrayDeque<RGBLightEngine.Node> queue = new ArrayDeque<>();
      Set<Long> visited = new HashSet<>();
      queue.add(new RGBLightEngine.Node(sourcePos, sourceColor));
      int processed = 0;

      while (!queue.isEmpty() && processed++ < 120000) {
         RGBLightEngine.Node node = queue.poll();
         if (node.color != null && node.color.active() && affectedCenter.distManhattan(node.pos) <= affectedRadius + radius()) {
            long key = node.pos.asLong();
            RGBLightColor4 old = STORAGE.get(node.pos);
            RGBLightColor4 merged = old.max(node.color);
            if (merged.r() != old.r() || merged.g() != old.g() || merged.b() != old.b() || visited.add(key)) {
               STORAGE.set(node.pos, merged);

               for (Direction direction : Direction.values()) {
                  BlockPos next = node.pos.relative(direction);
                  if (isRgbPropagationBarrier(level, next)) {
                     RGBLightColor4 surfaceColor = node.color.attenuate(1);
                     if (surfaceColor.active()) {
                        STORAGE.setMax(next, surfaceColor);
                     }
                  } else {
                     RGBLightColor4 nextColor = attenuateThrough(level, next, node.color);
                     if (nextColor.active()) {
                        queue.add(new RGBLightEngine.Node(next, nextColor));
                     }
                  }
               }
            }
         }
      }
   }

   private static RGBLightColor4 attenuateThrough(BlockAndTintGetter level, BlockPos pos, RGBLightColor4 incoming) {
      int dampening = 1;

      try {
         BlockState state = level.getBlockState(pos);
         dampening = Math.max(1, state.getLightDampening());
      } catch (Throwable ignored) {
         dampening = 1;
      }

      return incoming.attenuate(dampening);
   }

   public static boolean shouldInvalidateForOccluder(BlockAndTintGetter level, BlockPos pos, BlockState state) {
      if (!RGBRealLightEngine.enabled() || level == null || pos == null || state == null) {
         return false;
      } else {
         return !isOpaqueSolidBarrierState(state) ? false : STORAGE.hasActiveNear(pos, radius() + 1);
      }
   }

   private static boolean isRgbPropagationBarrier(BlockAndTintGetter level, BlockPos pos) {
      if (level != null && pos != null) {
         BlockState state;
         try {
            state = level.getBlockState(pos);
         } catch (Throwable ignored) {
            return false;
         }

         if (!isOpaqueSolidBarrierState(state)) {
            return false;
         }

         try {
            return !RGBRealLightEngine.rgbEmitterAt(level, pos);
         } catch (Throwable ignored) {
            return false;
         }
      } else {
         return false;
      }
   }

   private static boolean isOpaqueSolidBarrierState(BlockState state) {
      if (state == null) {
         return false;
      }

      try {
         return state.getLightDampening() >= 15 && state.canOcclude() && state.isSolidRender();
      } catch (Throwable ignored) {
         return false;
      }
   }

   public static void ensureBootstrapped(BlockAndTintGetter level, BlockPos pos) {
      if (RGBRealLightEngine.bootstrapAllowedAt(pos)) {
         if (RGBRealLightEngine.enabled() && level != null && pos != null) {
            rememberLevel(level);
            if (!CLIENT_DISCONNECTING) {
               int sx = pos.getX() >> 4;
               int sy = pos.getY() >> 4;
               int sz = pos.getZ() >> 4;
               long key = sectionKey(sx, sy, sz);
               if (!READY_SECTIONS.contains(key)) {
                  long now = System.nanoTime();
                  Long retryAfter = RETRY_AFTER_NANOS.get(key);
                  if (retryAfter == null || now >= retryAfter) {
                     BlockPos sectionCenter = sectionCenter(sx, sy, sz);
                     boolean found = refreshSection(level, sx, sy, sz);
                     if (found) {
                        READY_SECTIONS.add(key);
                        RETRY_AFTER_NANOS.remove(key);
                        RGBRenderInvalidator.dirtyAfterBootstrap(sectionCenter, radius());
                     } else {
                        RETRY_AFTER_NANOS.put(key, now + 350000000L);
                     }
                  }
               }

               drainRefreshQueue(level, 2);
            }
         }
      }
   }

   static void processPendingBootstrap(BlockAndTintGetter level, int budget) {
      if (level != null && budget > 0 && !CLIENT_DISCONNECTING) {
         rememberLevel(level);
         if (!CLIENT_DISCONNECTING) {
            drainRefreshQueue(level, Math.max(1, budget));
         }
      }
   }

   static boolean hasPendingBootstrapWork() {
      return !SOURCE_BOOTSTRAP_QUEUE.isEmpty() || !REFRESH_QUEUE.isEmpty();
   }

   static void clearPendingBootstrapWork() {
      RETRY_AFTER_NANOS.clear();
      REFRESH_QUEUE.clear();
      SOURCE_BOOTSTRAP_QUEUE.clear();
   }

   public static void scheduleSourceBootstrap(BlockPos pos) {
      if (!CLIENT_DISCONNECTING) {
         if (pos != null) {
            SOURCE_BOOTSTRAP_QUEUE.add(pos.immutable());
         }
      }
   }

   private static void rememberLevel(BlockAndTintGetter level) {
      int identity;
      try {
         Minecraft minecraft = Minecraft.getInstance();
         if (minecraft != null && minecraft.level != null) {
            CLIENT_DISCONNECTING = false;
            RGBRenderInvalidator.onClientWorldReady();
            identity = System.identityHashCode(minecraft.level);
         } else {
            identity = System.identityHashCode(level);
         }
      } catch (Throwable ignored) {
         identity = System.identityHashCode(level);
      }

      int previous = lastLevelIdentity;
      if (previous != identity) {
         lastLevelIdentity = identity;
         invalidateAll();
      }
   }

   private static void queueRefreshAround(BlockPos pos, int radius) {
      int minX = pos.getX() - radius >> 4;
      int maxX = pos.getX() + radius >> 4;
      int minY = pos.getY() - radius >> 4;
      int maxY = pos.getY() + radius >> 4;
      int minZ = pos.getZ() - radius >> 4;
      int maxZ = pos.getZ() + radius >> 4;

      for (int sx = minX; sx <= maxX; sx++) {
         for (int sy = minY; sy <= maxY; sy++) {
            for (int sz = minZ; sz <= maxZ; sz++) {
               long key = sectionKey(sx, sy, sz);
               READY_SECTIONS.remove(key);
               RETRY_AFTER_NANOS.remove(key);
               REFRESH_QUEUE.add(new RGBLightEngine.RefreshRequest(new BlockPos((sx << 4) + 8, (sy << 4) + 8, (sz << 4) + 8), key));
            }
         }
      }
   }

   private static void drainRefreshQueue(BlockAndTintGetter level, int budget) {
      for (int i = 0; i < budget; i++) {
         BlockPos bootstrapPos = SOURCE_BOOTSTRAP_QUEUE.poll();
         if (bootstrapPos == null) {
            break;
         }

         int sx = bootstrapPos.getX() >> 4;
         int sy = bootstrapPos.getY() >> 4;
         int sz = bootstrapPos.getZ() >> 4;
         long key = sectionKey(sx, sy, sz);
         READY_SECTIONS.remove(key);
         RETRY_AFTER_NANOS.remove(key);
         REFRESH_QUEUE.add(new RGBLightEngine.RefreshRequest(sectionCenter(sx, sy, sz), key));
      }

      for (int i = 0; i < budget; i++) {
         RGBLightEngine.RefreshRequest request = REFRESH_QUEUE.poll();
         if (request == null) {
            return;
         }

         if (!READY_SECTIONS.contains(request.sectionKey)) {
            boolean found = refreshAround(level, request.center, radius() + 2, true);
            if (found) {
               READY_SECTIONS.add(request.sectionKey);
               RETRY_AFTER_NANOS.remove(request.sectionKey);
               RGBRenderInvalidator.dirtyAfterBootstrap(request.center, radius());
            } else {
               RETRY_AFTER_NANOS.put(request.sectionKey, System.nanoTime() + 350000000L);
            }
         }
      }
   }

   private static boolean refreshSection(BlockAndTintGetter level, int sx, int sy, int sz) {
      BlockPos center = sectionCenter(sx, sy, sz);
      int sourceScanRadius = Math.min(40, radius() + 22);
      return refreshAround(level, center, sourceScanRadius, false);
   }

   private static boolean refreshAround(BlockAndTintGetter level, BlockPos center, int scanRadius, boolean allowFallbackScan) {
      boolean[] indexedFound = new boolean[]{false};
      RGBSourceIndex.forEachSourceAround(center, scanRadius, (sourcePosx, sourceColor) -> {
         indexedFound[0] = true;
         propagateFrom(level, sourcePosx, sourceColor, scanRadius, center);
      });
      if (indexedFound[0]) {
         return true;
      }

      if (!allowFallbackScan) {
         return false;
      }

      boolean foundAny = false;
      MutableBlockPos scan = new MutableBlockPos();

      for (int y = center.getY() - scanRadius; y <= center.getY() + scanRadius; y++) {
         for (int z = center.getZ() - scanRadius; z <= center.getZ() + scanRadius; z++) {
            for (int x = center.getX() - scanRadius; x <= center.getX() + scanRadius; x++) {
               scan.set(x, y, z);
               RGBLightColor4 source = RGBRealLightEngine.sourceColorAt(level, scan);
               if (source.active()) {
                  BlockPos sourcePos = scan.immutable();
                  RGBSourceIndex.update(sourcePos, source);
                  foundAny = true;
                  propagateFrom(level, sourcePos, source, scanRadius, center);
               }
            }
         }
      }

      return foundAny;
   }

   private static void clearReadySectionsAround(BlockPos pos, int radius) {
      int minX = pos.getX() - radius >> 4;
      int maxX = pos.getX() + radius >> 4;
      int minY = pos.getY() - radius >> 4;
      int maxY = pos.getY() + radius >> 4;
      int minZ = pos.getZ() - radius >> 4;
      int maxZ = pos.getZ() + radius >> 4;

      for (int sx = minX; sx <= maxX; sx++) {
         for (int sy = minY; sy <= maxY; sy++) {
            for (int sz = minZ; sz <= maxZ; sz++) {
               long key = sectionKey(sx, sy, sz);
               READY_SECTIONS.remove(key);
               RETRY_AFTER_NANOS.remove(key);
            }
         }
      }
   }

   public static int packedLightAt(BlockAndTintGetter level, BlockPos blockPos, float localX, float localY, float localZ, int vanillaPackedLight) {
      if (RGBRealLightEngine.enabled() && blockPos != null) {
         ensureBootstrapped(level, blockPos);
         RGBLightColor8 color = sampleTrilinear(sampleX(blockPos, localX), sampleY(blockPos, localY), sampleZ(blockPos, localZ));
         if (!color.active()) {
            return vanillaPackedLight;
         }

         int sky = LightCoordsUtil.sky(vanillaPackedLight);
         int vanillaBlock = LightCoordsUtil.block(vanillaPackedLight);
         int rgbBlock = Math.max(color.r(), Math.max(color.g(), color.b())) / 17;
         return LightCoordsUtil.pack(Math.max(vanillaBlock, rgbBlock), sky);
      } else {
         return vanillaPackedLight;
      }
   }

   public static RGBLightColor8 lightColorAt(BlockPos blockPos, float localX, float localY, float localZ) {
      if (RGBRealLightEngine.enabled() && blockPos != null) {
         double x = sampleX(blockPos, localX);
         double y = sampleY(blockPos, localY);
         double z = sampleZ(blockPos, localZ);
         return sampleTrilinear(x, y, z);
      } else {
         return RGBLightColor8.BLACK;
      }
   }

   private static double sampleX(BlockPos blockPos, float localX) {
      return blockPos.getX() + clamp(localX, 0.0F, 1.0F) - 0.5;
   }

   private static double sampleY(BlockPos blockPos, float localY) {
      return blockPos.getY() + clamp(localY, 0.0F, 1.0F) - 0.5;
   }

   private static double sampleZ(BlockPos blockPos, float localZ) {
      return blockPos.getZ() + clamp(localZ, 0.0F, 1.0F) - 0.5;
   }

   public static RGBLightColor8 sampleTrilinear(double x, double y, double z) {
      int x0 = (int)Math.floor(x);
      int y0 = (int)Math.floor(y);
      int z0 = (int)Math.floor(z);
      double tx = x - x0;
      double ty = y - y0;
      double tz = z - z0;
      RGBLightColor8 c000 = sampleCellContinuous(x0, y0, z0);
      RGBLightColor8 c100 = sampleCellContinuous(x0 + 1, y0, z0);
      RGBLightColor8 c010 = sampleCellContinuous(x0, y0 + 1, z0);
      RGBLightColor8 c110 = sampleCellContinuous(x0 + 1, y0 + 1, z0);
      RGBLightColor8 c001 = sampleCellContinuous(x0, y0, z0 + 1);
      RGBLightColor8 c101 = sampleCellContinuous(x0 + 1, y0, z0 + 1);
      RGBLightColor8 c011 = sampleCellContinuous(x0, y0 + 1, z0 + 1);
      RGBLightColor8 c111 = sampleCellContinuous(x0 + 1, y0 + 1, z0 + 1);
      RGBLightColor8 c00 = RGBLightColor8.lerp(c000, c100, tx);
      RGBLightColor8 c10 = RGBLightColor8.lerp(c010, c110, tx);
      RGBLightColor8 c01 = RGBLightColor8.lerp(c001, c101, tx);
      RGBLightColor8 c11 = RGBLightColor8.lerp(c011, c111, tx);
      RGBLightColor8 c0 = RGBLightColor8.lerp(c00, c10, ty);
      RGBLightColor8 c1 = RGBLightColor8.lerp(c01, c11, ty);
      return RGBLightColor8.lerp(c0, c1, tz);
   }

   private static RGBLightColor8 sampleCellContinuous(int x, int y, int z) {
      RGBLightColor4 direct = STORAGE.get(x, y, z);
      if (!direct.active()) {
         return RGBLightColor8.BLACK;
      }

      RGBLightColor4 adjacent = RGBLightColor4.BLACK;
      adjacent = adjacent.max(STORAGE.get(x + 1, y, z));
      adjacent = adjacent.max(STORAGE.get(x - 1, y, z));
      adjacent = adjacent.max(STORAGE.get(x, y + 1, z));
      adjacent = adjacent.max(STORAGE.get(x, y - 1, z));
      adjacent = adjacent.max(STORAGE.get(x, y, z + 1));
      adjacent = adjacent.max(STORAGE.get(x, y, z - 1));
      RGBLightColor4 softenedAdjacent = adjacent.active() ? adjacent.attenuate(1) : RGBLightColor4.BLACK;
      return RGBLightColor8.from4(direct.max(softenedAdjacent));
   }

   private static long sectionKey(int sx, int sy, int sz) {
      return SectionPos.asLong(sx, sy, sz);
   }

   private static BlockPos sectionCenter(int sx, int sy, int sz) {
      return new BlockPos((sx << 4) + 8, (sy << 4) + 8, (sz << 4) + 8);
   }

   private static int radius() {
      return Math.max(4, Math.min(15, RGBRealLightEngine.radiusCached()));
   }

   private static float clamp(float v, float min, float max) {
      if (!Float.isFinite(v)) {
         return 0.5F;
      } else {
         return v < min ? min : Math.min(v, max);
      }
   }

   private record Node(BlockPos pos, RGBLightColor4 color) {
   }

   private record RefreshRequest(BlockPos center, long sectionKey) {
   }
}
