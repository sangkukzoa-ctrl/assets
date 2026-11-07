package com.rgbblocks.client.cnb;

import com.rgbblocks.client.lighting.RGBRenderInvalidator;
import java.lang.ref.WeakReference;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

public final class RGBCnbReloadWakeup {
   private static final long[] BOOTSTRAP_DELAYS_MS = new long[]{180L, 650L, 1450L};
   private static final Set<Long> PENDING_POSITIONS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final Map<Long, Long> LAST_BOOTSTRAP_MS = new ConcurrentHashMap<>();
   private static final long[] PERSISTED_REFRESH_DELAYS_MS = new long[]{0L, 180L, 650L, 1450L};
   private static final Set<Long> PERSISTED_SOURCE_POSITIONS = Collections.newSetFromMap(new ConcurrentHashMap<>());
   private static final AtomicLong PERSISTED_REFRESH_EPOCH = new AtomicLong();
   private static final ScheduledExecutorService EXECUTOR = Executors.newSingleThreadScheduledExecutor(runnable -> {
      Thread thread = new Thread(runnable, "RGB Blocks CNB reload bootstrap");
      thread.setDaemon(true);
      return thread;
   });

   private RGBCnbReloadWakeup() {
   }

   public static void reset() {
      PENDING_POSITIONS.clear();
      LAST_BOOTSTRAP_MS.clear();
      PERSISTED_SOURCE_POSITIONS.clear();
      PERSISTED_REFRESH_EPOCH.incrementAndGet();
   }

   public static void onPersistedSourcesRestored(String dimension, Iterable<BlockPos> positions) {
      long epoch = PERSISTED_REFRESH_EPOCH.incrementAndGet();
      PERSISTED_SOURCE_POSITIONS.clear();
      if (positions != null) {
         for (BlockPos pos : positions) {
            if (pos != null) {
               PERSISTED_SOURCE_POSITIONS.add(key(pos));
            }
         }
      }

      if (!PERSISTED_SOURCE_POSITIONS.isEmpty()) {
         String expectedDimension = dimension == null ? "" : dimension;
         schedulePersistedRefreshPasses(epoch, expectedDimension, PERSISTED_REFRESH_DELAYS_MS);
      }
   }

   public static void onPersistedSourceRecovered(BlockPos pos) {
      if (pos != null) {
         PERSISTED_SOURCE_POSITIONS.add(key(pos));
         long epoch = PERSISTED_REFRESH_EPOCH.get();
         String dimension = currentDimension();
         schedulePersistedRefreshPasses(epoch, dimension, new long[]{0L, 180L, 650L});
      }
   }

   public static void onBlockEntityAdded(BlockEntity blockEntity) {
      if (blockEntity != null && isRemoteMultiplayerClient() && isChiseledBlockEntity(blockEntity)) {
         BlockPos pos;
         try {
            pos = blockEntity.getBlockPos().immutable();
         } catch (Throwable ignored) {
            return;
         }

         long key = key(pos);
         if (PERSISTED_SOURCE_POSITIONS.contains(key)) {
            schedulePersistedRefreshPasses(PERSISTED_REFRESH_EPOCH.get(), currentDimension(), new long[]{0L, 180L, 650L});
         }

         long now = System.currentTimeMillis();
         Long last = LAST_BOOTSTRAP_MS.get(key);
         if (last == null || now - last >= 2500L) {
            if (PENDING_POSITIONS.add(key)) {
               WeakReference<BlockEntity> ref = new WeakReference<>(blockEntity);

               for (int i = 0; i < BOOTSTRAP_DELAYS_MS.length; i++) {
                  boolean release = i == BOOTSTRAP_DELAYS_MS.length - 1;
                  scheduleBootstrap(ref, pos, key, BOOTSTRAP_DELAYS_MS[i], release);
               }
            }
         }
      }
   }

   private static void scheduleBootstrap(WeakReference<BlockEntity> ref, BlockPos pos, long key, long delayMillis, boolean release) {
      EXECUTOR.schedule(() -> {
         Minecraft minecraft = Minecraft.getInstance();
         if (minecraft == null) {
            if (release) {
               release(key);
            }
         } else {
            minecraft.execute(() -> {
               try {
                  if (!isRemoteMultiplayerClient()) {
                     return;
                  }

                  Level level = minecraft.level;
                  if (level == null || !level.isClientSide()) {
                     return;
                  }

                  BlockEntity live = level.getBlockEntity(pos);
                  BlockEntity captured = ref.get();
                  if (live != null && (captured == null || live == captured) && isChiseledBlockEntity(live)) {
                     RGBCnbGeometryBakeDebouncer.runUndebounced(() -> invokeNoArg(live, "updateModelData"));
                     BlockState state = level.getBlockState(pos);
                     level.sendBlockUpdated(pos, state, state, 3);
                     RGBRenderInvalidator.dirtyChunk(pos.getX() >> 4, pos.getZ() >> 4);
                     return;
                  }
               } catch (Throwable var13) {
                  return;
               } finally {
                  if (release) {
                     release(key);
                  }
               }
            });
         }
      }, delayMillis, TimeUnit.MILLISECONDS);
   }

   private static void runPersistedRenderRefresh(long epoch, String expectedDimension, boolean release) {
      Minecraft minecraft = Minecraft.getInstance();
      if (minecraft != null) {
         minecraft.execute(() -> {
            try {
               if (epoch != PERSISTED_REFRESH_EPOCH.get()) {
                  return;
               }

               Level level = minecraft.level;
               if (level == null || !level.isClientSide()) {
                  return;
               }

               String currentDimension;
               try {
                  currentDimension = level.dimension().identifier().toString();
               } catch (Throwable ignored) {
                  currentDimension = "";
               }

               if (!expectedDimension.isBlank() && !expectedDimension.equals(currentDimension)) {
                  return;
               }

               Set<Long> dirtyChunks = new HashSet<>();
               Set<Long> completed = new HashSet<>();
               Set<Long> terminal = new HashSet<>();

               for (Long packedPos : PERSISTED_SOURCE_POSITIONS) {
                  if (packedPos != null) {
                     BlockPos pos = BlockPos.of(packedPos);
                     if (level.isLoaded(pos)) {
                        BlockEntity live = level.getBlockEntity(pos);
                        if (live != null) {
                           if (!isChiseledBlockEntity(live)) {
                              terminal.add(packedPos);
                           } else {
                              RGBCnbGeometryBakeDebouncer.runUndebounced(() -> invokeNoArg(live, "updateModelData"));
                              BlockState state = level.getBlockState(pos);
                              level.sendBlockUpdated(pos, state, state, 3);
                              long chunkKey = (long)(pos.getX() >> 4) << 32 ^ pos.getZ() >> 4 & 4294967295L;
                              dirtyChunks.add(chunkKey);
                              completed.add(packedPos);
                           }
                        }
                     }
                  }
               }

               for (Long chunkKey : dirtyChunks) {
                  int chunkX = (int)(chunkKey >> 32);
                  int chunkZ = (int)chunkKey.longValue();
                  RGBRenderInvalidator.dirtyChunk(chunkX, chunkZ);
               }

               PERSISTED_SOURCE_POSITIONS.removeAll(terminal);
               if (release) {
                  PERSISTED_SOURCE_POSITIONS.removeAll(completed);
               }
            } catch (Throwable var18) {
            }
         });
      }
   }

   private static void schedulePersistedRefreshPasses(long epoch, String expectedDimension, long[] delays) {
      if (delays != null && delays.length != 0) {
         String dimension = expectedDimension == null ? "" : expectedDimension;

         for (int i = 0; i < delays.length; i++) {
            boolean release = i == delays.length - 1;
            long delay = Math.max(0L, delays[i]);
            EXECUTOR.schedule(() -> runPersistedRenderRefresh(epoch, dimension, release), delay, TimeUnit.MILLISECONDS);
         }
      }
   }

   private static String currentDimension() {
      try {
         Minecraft minecraft = Minecraft.getInstance();
         if (minecraft != null && minecraft.level != null) {
            return minecraft.level.dimension().identifier().toString();
         }
      } catch (Throwable var1) {
      }

      return "";
   }

   private static void release(long key) {
      PENDING_POSITIONS.remove(key);
      LAST_BOOTSTRAP_MS.put(key, System.currentTimeMillis());
   }

   private static boolean isRemoteMultiplayerClient() {
      try {
         Minecraft minecraft = Minecraft.getInstance();
         return minecraft != null
            && minecraft.level != null
            && minecraft.getCurrentServer() != null
            && !minecraft.hasSingleplayerServer()
            && !minecraft.isLocalServer();
      } catch (Throwable ignored) {
         return false;
      }
   }

   private static boolean isChiseledBlockEntity(Object object) {
      try {
         String name = object.getClass().getName();
         return name.contains("chiselsandbits") && name.endsWith("ChiseledBlockEntity");
      } catch (Throwable ignored) {
         return false;
      }
   }

   private static void invokeNoArg(Object target, String methodName) {
      if (target != null && methodName != null) {
         Class<?> type = target.getClass();

         while (type != null) {
            try {
               Method method = type.getDeclaredMethod(methodName);
               method.setAccessible(true);
               method.invoke(target);
               return;
            } catch (NoSuchMethodException var5) {
               type = type.getSuperclass();
            } catch (Throwable ignored) {
               return;
            }
         }

         try {
            Method method = target.getClass().getMethod(methodName);
            method.invoke(target);
         } catch (Throwable var4) {
         }
      }
   }

   private static long key(BlockPos pos) {
      long x = (pos.getX() & 67108863L) << 38;
      long z = (pos.getZ() & 67108863L) << 12;
      long y = pos.getY() & 4095L;
      return x | z | y;
   }
}
