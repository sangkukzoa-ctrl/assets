package com.rgbblocks.client.cnb;

import java.lang.ref.WeakReference;
import java.lang.reflect.Method;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.world.level.block.entity.BlockEntity;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;

public final class RGBCnbGeometryBakeDebouncer {
   private static final long RAPID_WINDOW_MS = 70L;
   private static final long MAX_SUPPRESS_MS = 90L;
   private static final long PAYLOAD_ACTIVE_WINDOW_MS = 350L;
   private static final Map<Long, RGBCnbGeometryBakeDebouncer.Entry> ENTRIES = new ConcurrentHashMap<>();
   private static final ThreadLocal<Boolean> BYPASS = ThreadLocal.withInitial(() -> Boolean.FALSE);
   // C&B model compilation is asynchronous. Suppressing bursts without
   // replaying their LAST request can leave the old or empty mesh on screen,
   // while the actual C&B voxels and RGB light are still intact.
   private static final AtomicLong WORLD_EPOCH = new AtomicLong();
   private static final ScheduledExecutorService TRAILING_BAKES = Executors.newSingleThreadScheduledExecutor(task -> {
      Thread worker = new Thread(task, "RGB Blocks last C&B model bake");
      worker.setDaemon(true);
      return worker;
   });

   private RGBCnbGeometryBakeDebouncer() {
   }

   public static void reset() {
      WORLD_EPOCH.incrementAndGet();
      ENTRIES.clear();
      BYPASS.remove();
   }

   public static void runUndebounced(Runnable action) {
      if (action != null) {
         boolean previous = Boolean.TRUE.equals(BYPASS.get());
         BYPASS.set(Boolean.TRUE);

         try {
            action.run();
         } finally {
            if (previous) {
               BYPASS.set(Boolean.TRUE);
            } else {
               BYPASS.remove();
            }
         }
      }
   }

   public static void markPayloadModelUpdate(Object tileEntity) {
      if (tileEntity != null && isRemoteClientWorld(tileEntity)) {
         BlockPos pos = getBlockPos(tileEntity);
         if (pos != null) {
            long now = System.currentTimeMillis();
            RGBCnbGeometryBakeDebouncer.Entry entry = ENTRIES.computeIfAbsent(key(pos), ignored -> new RGBCnbGeometryBakeDebouncer.Entry());
            entry.lastPayloadMillis = now;
         }
      }
   }

   public static boolean shouldDelayModelBake(Object tileEntity, boolean force) {
      if (!force && !Boolean.TRUE.equals(BYPASS.get()) && tileEntity != null && isRemoteClientWorld(tileEntity)) {
         BlockPos pos = getBlockPos(tileEntity);
         if (pos == null) {
            return false;
         }

         long now = System.currentTimeMillis();
         RGBCnbGeometryBakeDebouncer.Entry entry = ENTRIES.computeIfAbsent(key(pos), ignored -> new RGBCnbGeometryBakeDebouncer.Entry());
         long lastPayload = entry.lastPayloadMillis;
         if (lastPayload != 0L && now - lastPayload <= 350L) {
            long previousRequest = entry.lastRequestMillis;
            long previousAllowed = entry.lastAllowedBakeMillis;
            entry.lastRequestMillis = now;
            long requestSerial = ++entry.requestSerial;
            if (previousRequest == 0L || now - previousRequest > 70L) {
               entry.lastAllowedBakeMillis = now;
               return false;
            }

            if (previousAllowed != 0L && now - previousAllowed < 90L) {
               scheduleTrailingBake(tileEntity, pos, entry, requestSerial);
               return true;
            }

            entry.lastAllowedBakeMillis = now;
            return false;
         } else {
            entry.lastRequestMillis = now;
            entry.lastAllowedBakeMillis = now;
            return false;
         }
      } else {
         return false;
      }
   }

   private static void scheduleTrailingBake(Object tileEntity, BlockPos pos, Entry entry, long serial) {
      Minecraft mc = Minecraft.getInstance();
      if (mc == null || mc.level == null || !(tileEntity instanceof BlockEntity blockEntity)) {
         return;
      }
      WeakReference<BlockEntity> captured = new WeakReference<>(blockEntity);
      WeakReference<Level> expectedWorld = new WeakReference<>(mc.level);
      long epoch = WORLD_EPOCH.get();
      TRAILING_BAKES.schedule(() -> {
         Minecraft client = Minecraft.getInstance();
         if (client == null || epoch != WORLD_EPOCH.get()) {
            return;
         }
         client.execute(() -> {
            if (epoch != WORLD_EPOCH.get() || entry.requestSerial != serial) {
               return;
            }
            Level level = expectedWorld.get();
            BlockEntity live = captured.get();
            if (level == null || client.level != level || live == null
                || !level.isLoaded(pos) || level.getBlockEntity(pos) != live || live.isRemoved()) {
               return;
            }
            // The latest C&B tile payload has settled. Force exactly ONE
            // non-debounced model build so an obsolete async future cannot
            // permanently keep the mesh invisible after rapid bakes.
            runUndebounced(() -> {
               try {
                  Method update = live.getClass().getMethod("updateModelData");
                  update.invoke(live);
                  level.sendBlockUpdated(pos, level.getBlockState(pos), level.getBlockState(pos), 3);
               } catch (Throwable failure) {
                  System.err.println("[RGB Blocks] C&B trailing mesh rebuild failed: " + failure);
               }
            });
         });
      }, 180L, TimeUnit.MILLISECONDS);
   }

   private static boolean isRemoteClientWorld(Object tileEntity) {
      try {
         Method hasLevel = tileEntity.getClass().getMethod("hasLevel");
         Object hasLevelResult = hasLevel.invoke(tileEntity);
         if (hasLevelResult instanceof Boolean && (Boolean)hasLevelResult) {
            Method getLevel = tileEntity.getClass().getMethod("getLevel");
            if (getLevel.invoke(tileEntity) instanceof Level level && level.isClientSide()) {
               Minecraft minecraft = Minecraft.getInstance();
               return minecraft != null && minecraft.getSingleplayerServer() == null;
            } else {
               return false;
            }
         } else {
            return false;
         }
      } catch (Throwable ignored) {
         return false;
      }
   }

   private static BlockPos getBlockPos(Object tileEntity) {
      try {
         Method method = tileEntity.getClass().getMethod("getBlockPos");
         Object result = method.invoke(tileEntity);
         return result instanceof BlockPos ? ((BlockPos)result).immutable() : null;
      } catch (Throwable ignored) {
         return null;
      }
   }

   private static long key(BlockPos pos) {
      long x = (pos.getX() & 67108863L) << 38;
      long z = (pos.getZ() & 67108863L) << 12;
      long y = pos.getY() & 4095L;
      return x | z | y;
   }

   private static final class Entry {
      private volatile long requestSerial;
      private volatile long lastPayloadMillis;
      private volatile long lastRequestMillis;
      private volatile long lastAllowedBakeMillis;
   }
}
