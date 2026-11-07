package com.rgbblocks.client.lighting;

import java.util.Collections;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.core.BlockPos;

public final class RGBRenderInvalidator {
   private static final int EXTRA_MARGIN = 10;
   private static final int MAX_DIRTY_RADIUS = 32;
   private static final int MIN_SECTION_RADIUS = 2;
   private static final int MAX_SECTION_RADIUS = 4;
   private static final Set<Long> SETTLE_DIRTY_KEYS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final Set<Long> SERVER_SYNC_DIRTY_KEYS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final Set<Long> AROUND_DIRTY_KEYS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final Set<Long> CHUNK_DIRTY_KEYS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final AtomicLong DIRTY_EPOCH = new AtomicLong();
   private static volatile boolean CLIENT_DISCONNECTING = false;
   private static final ScheduledExecutorService DELAYED_DIRTY_EXECUTOR = Executors.newSingleThreadScheduledExecutor(runnable -> {
      Thread thread = new Thread(runnable, "RGB Blocks delayed render dirty");
      thread.setDaemon(true);
      return thread;
   });

   private RGBRenderInvalidator() {
   }

   public static void onClientDisconnect() {
      CLIENT_DISCONNECTING = true;
      DIRTY_EPOCH.incrementAndGet();
      SETTLE_DIRTY_KEYS.clear();
      SERVER_SYNC_DIRTY_KEYS.clear();
      AROUND_DIRTY_KEYS.clear();
      CHUNK_DIRTY_KEYS.clear();
   }

   public static void onClientWorldReady() {
      CLIENT_DISCONNECTING = false;
   }

   private static boolean canDirty() {
      if (CLIENT_DISCONNECTING) {
         return false;
      }

      try {
         Minecraft minecraft = Minecraft.getInstance();
         return minecraft != null && minecraft.level != null && minecraft.levelRenderer != null;
      } catch (Throwable ignored) {
         return false;
      }
   }

   public static void dirtyAround(BlockPos pos, int radius) {
      if (canDirty()) {
         if (pos != null) {
            int r = Math.max(10, Math.min(radius + 10, 32));
            int sectionRadius = Math.max(2, Math.min(4, (r >> 4) + 2));
            int sx = floorSection(pos.getX());
            int sy = floorSection(pos.getY());
            int sz = floorSection(pos.getZ());
            long key = sectionKey(sx, sy, sz) ^ (sectionRadius & 15L) << 56;
            if (AROUND_DIRTY_KEYS.add(key)) {
               dirtyAroundNow(pos, r, sectionRadius);
               dirtyAroundDelayed(pos, r, sectionRadius, 240L);
               releaseAroundKeyLater(key, 520L);
            }
         }
      }
   }

   public static void dirtyAfterBootstrap(BlockPos pos, int radius) {
      if (canDirty()) {
         if (pos != null) {
            int sx = floorSection(pos.getX());
            int sy = floorSection(pos.getY());
            int sz = floorSection(pos.getZ());
            long key = sectionKey(sx, sy, sz);
            if (SETTLE_DIRTY_KEYS.add(key)) {
               int r = Math.max(10, Math.min(radius + 10, 32));
               int sectionRadius = Math.max(2, Math.min(4, (r >> 4) + 2));
               BlockPos immutable = pos.immutable();
               scheduleSectionOnlyDirty(immutable, sectionRadius, 90L, key, false);
               scheduleSectionOnlyDirty(immutable, sectionRadius, 260L, key, false);
               scheduleSectionOnlyDirty(immutable, sectionRadius, 700L, key, true);
            }
         }
      }
   }

   public static void dirtyAfterServerSync(BlockPos pos, int radius) {
      if (canDirty() && pos != null) {
         int sx = floorSection(pos.getX());
         int sy = floorSection(pos.getY());
         int sz = floorSection(pos.getZ());
         long key = sectionKey(sx, sy, sz) ^ 6510615555426900570L;
         if (SERVER_SYNC_DIRTY_KEYS.add(key)) {
            int r = Math.max(10, Math.min(radius + 10, 32));
            int sectionRadius = Math.max(2, Math.min(4, (r >> 4) + 2));
            BlockPos immutable = pos.immutable();
            scheduleServerSyncDirty(immutable, sectionRadius, 120L, key, false);
            scheduleServerSyncDirty(immutable, sectionRadius, 360L, key, false);
            scheduleServerSyncDirty(immutable, sectionRadius, 900L, key, true);
         }
      }
   }

   public static void dirtyChunk(int chunkX, int chunkZ) {
      if (canDirty()) {
         long key = (chunkX & 4294967295L) << 32 | chunkZ & 4294967295L;
         if (CHUNK_DIRTY_KEYS.add(key)) {
            int minX = chunkX << 4;
            int minZ = chunkZ << 4;
            int maxX = minX + 15;
            int maxZ = minZ + 15;
            dirtyBlockRangeNow(minX, -128, minZ, maxX, 511, maxZ);
            dirtySectionRangeNow(chunkX - 1, -8, chunkZ - 1, chunkX + 1, 31, chunkZ + 1, true);
            dirtyChunkDelayed(chunkX, chunkZ, 450L);
            releaseChunkKeyLater(key, 1200L);
         }
      }
   }

   private static void releaseAroundKeyLater(long key, long delayMillis) {
      long epoch = DIRTY_EPOCH.get();
      DELAYED_DIRTY_EXECUTOR.schedule(() -> {
         if (epoch == DIRTY_EPOCH.get()) {
            AROUND_DIRTY_KEYS.remove(key);
         }
      }, delayMillis, TimeUnit.MILLISECONDS);
   }

   private static void releaseChunkKeyLater(long key, long delayMillis) {
      long epoch = DIRTY_EPOCH.get();
      DELAYED_DIRTY_EXECUTOR.schedule(() -> {
         if (epoch == DIRTY_EPOCH.get()) {
            CHUNK_DIRTY_KEYS.remove(key);
         }
      }, delayMillis, TimeUnit.MILLISECONDS);
   }

   private static void scheduleSectionOnlyDirty(BlockPos pos, int sectionRadius, long delayMillis, long key, boolean releaseKey) {
      long epoch = DIRTY_EPOCH.get();
      DELAYED_DIRTY_EXECUTOR.schedule(
         () -> {
            try {
               if (CLIENT_DISCONNECTING || epoch != DIRTY_EPOCH.get()) {
                  if (releaseKey) {
                     SETTLE_DIRTY_KEYS.remove(key);
                  }

                  return;
               }

               Minecraft minecraft = Minecraft.getInstance();
               if (minecraft == null) {
                  if (releaseKey) {
                     SETTLE_DIRTY_KEYS.remove(key);
                  }

                  return;
               }

               minecraft.execute(
                  () -> {
                     try {
                        if (CLIENT_DISCONNECTING || epoch != DIRTY_EPOCH.get()) {
                           return;
                        }

                        int sx = floorSection(pos.getX());
                        int sy = floorSection(pos.getY());
                        int sz = floorSection(pos.getZ());
                        dirtySectionRangeNow(
                           sx - sectionRadius, sy - sectionRadius, sz - sectionRadius, sx + sectionRadius, sy + sectionRadius, sz + sectionRadius, true
                        );
                     } finally {
                        if (releaseKey) {
                           SETTLE_DIRTY_KEYS.remove(key);
                        }
                     }
                  }
               );
            } catch (Throwable ignored) {
               if (releaseKey) {
                  SETTLE_DIRTY_KEYS.remove(key);
               }
            }
         },
         delayMillis,
         TimeUnit.MILLISECONDS
      );
   }

   private static void scheduleServerSyncDirty(BlockPos pos, int sectionRadius, long delayMillis, long key, boolean releaseKey) {
      long epoch = DIRTY_EPOCH.get();
      DELAYED_DIRTY_EXECUTOR.schedule(
         () -> {
            try {
               if (CLIENT_DISCONNECTING || epoch != DIRTY_EPOCH.get()) {
                  if (releaseKey) {
                     SERVER_SYNC_DIRTY_KEYS.remove(key);
                  }

                  return;
               }

               Minecraft minecraft = Minecraft.getInstance();
               if (minecraft == null) {
                  if (releaseKey) {
                     SERVER_SYNC_DIRTY_KEYS.remove(key);
                  }

                  return;
               }

               minecraft.execute(
                  () -> {
                     try {
                        if (CLIENT_DISCONNECTING || epoch != DIRTY_EPOCH.get()) {
                           return;
                        }

                        int sx = floorSection(pos.getX());
                        int sy = floorSection(pos.getY());
                        int sz = floorSection(pos.getZ());
                        dirtySectionRangeNow(
                           sx - sectionRadius, sy - sectionRadius, sz - sectionRadius, sx + sectionRadius, sy + sectionRadius, sz + sectionRadius, true
                        );
                     } finally {
                        if (releaseKey) {
                           SERVER_SYNC_DIRTY_KEYS.remove(key);
                        }
                     }
                  }
               );
            } catch (Throwable ignored) {
               if (releaseKey) {
                  SERVER_SYNC_DIRTY_KEYS.remove(key);
               }
            }
         },
         delayMillis,
         TimeUnit.MILLISECONDS
      );
   }

   private static long sectionKey(int sx, int sy, int sz) {
      long x = sx & 67108863L;
      long y = sy & 4095L;
      long z = sz & 67108863L;
      return x << 38 | z << 12 | y;
   }

   private static void dirtyAroundDelayed(BlockPos pos, int radius, int sectionRadius, long delayMillis) {
      BlockPos immutable = pos.immutable();
      long epoch = DIRTY_EPOCH.get();
      DELAYED_DIRTY_EXECUTOR.schedule(() -> {
         try {
            if (CLIENT_DISCONNECTING || epoch != DIRTY_EPOCH.get()) {
               return;
            }

            Minecraft minecraft = Minecraft.getInstance();
            if (minecraft == null) {
               return;
            }

            minecraft.execute(() -> {
               if (!CLIENT_DISCONNECTING && epoch == DIRTY_EPOCH.get()) {
                  dirtyAroundNow(immutable, radius, sectionRadius);
               }
            });
         } catch (Throwable var6x) {
         }
      }, delayMillis, TimeUnit.MILLISECONDS);
   }

   private static void dirtyChunkDelayed(int chunkX, int chunkZ, long delayMillis) {
      long epoch = DIRTY_EPOCH.get();
      DELAYED_DIRTY_EXECUTOR.schedule(() -> {
         try {
            if (CLIENT_DISCONNECTING || epoch != DIRTY_EPOCH.get()) {
               return;
            }

            Minecraft minecraft = Minecraft.getInstance();
            if (minecraft == null) {
               return;
            }

            minecraft.execute(() -> {
               if (!CLIENT_DISCONNECTING && epoch == DIRTY_EPOCH.get()) {
                  int minX = chunkX << 4;
                  int minZ = chunkZ << 4;
                  dirtyBlockRangeNow(minX, -128, minZ, minX + 15, 511, minZ + 15);
                  dirtySectionRangeNow(chunkX - 1, -8, chunkZ - 1, chunkX + 1, 31, chunkZ + 1, true);
               }
            });
         } catch (Throwable var5) {
         }
      }, delayMillis, TimeUnit.MILLISECONDS);
   }

   private static void dirtyAroundNow(BlockPos pos, int radius, int sectionRadius) {
      if (canDirty()) {
         int minX = pos.getX() - radius;
         int minY = pos.getY() - radius;
         int minZ = pos.getZ() - radius;
         int maxX = pos.getX() + radius;
         int maxY = pos.getY() + radius;
         int maxZ = pos.getZ() + radius;
         dirtyBlockRangeNow(minX, minY, minZ, maxX, maxY, maxZ);
         int sx = floorSection(pos.getX());
         int sy = floorSection(pos.getY());
         int sz = floorSection(pos.getZ());
         dirtySectionRangeNow(sx - sectionRadius, sy - sectionRadius, sz - sectionRadius, sx + sectionRadius, sy + sectionRadius, sz + sectionRadius, true);
      }
   }

   private static void dirtyBlockRangeNow(int minX, int minY, int minZ, int maxX, int maxY, int maxZ) {
      if (canDirty()) {
         try {
            Minecraft minecraft = Minecraft.getInstance();
            if (minecraft == null || minecraft.level == null) {
               return;
            }

            LevelRenderer renderer = minecraft.levelRenderer;
            if (renderer == null) {
               return;
            }

            renderer.setBlocksDirty(minX, minY, minZ, maxX, maxY, maxZ);
            renderer.setSectionRangeDirty(
               floorSection(minX), floorSection(minY), floorSection(minZ), floorSection(maxX), floorSection(maxY), floorSection(maxZ)
            );
         } catch (Throwable var8) {
         }
      }
   }

   private static void dirtySectionRangeNow(int minSx, int minSy, int minSz, int maxSx, int maxSy, int maxSz, boolean withNeighbors) {
      if (canDirty()) {
         try {
            Minecraft minecraft = Minecraft.getInstance();
            if (minecraft == null || minecraft.level == null) {
               return;
            }

            LevelRenderer renderer = minecraft.levelRenderer;
            if (renderer == null) {
               return;
            }

            renderer.setSectionRangeDirty(minSx, minSy, minSz, maxSx, maxSy, maxSz);
            if (withNeighbors) {
               for (int sx = minSx; sx <= maxSx; sx++) {
                  for (int sy = minSy; sy <= maxSy; sy++) {
                     for (int sz = minSz; sz <= maxSz; sz++) {
                        renderer.setSectionDirtyWithNeighbors(sx, sy, sz);
                     }
                  }
               }
            } else {
               for (int sx = minSx; sx <= maxSx; sx++) {
                  for (int sy = minSy; sy <= maxSy; sy++) {
                     for (int sz = minSz; sz <= maxSz; sz++) {
                        renderer.setSectionDirty(sx, sy, sz);
                     }
                  }
               }
            }
         } catch (Throwable var12) {
         }
      }
   }

   private static int floorSection(int blockCoord) {
      return Math.floorDiv(blockCoord, 16);
   }
}
