package com.rgbblocks.client.cnb;

import java.lang.ref.WeakReference;
import java.lang.reflect.Method;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.ScheduledThreadPoolExecutor;
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
   private static final ScheduledThreadPoolExecutor TRAILING_BAKES = createTrailingScheduler();

   private static ScheduledThreadPoolExecutor createTrailingScheduler() {
      ScheduledThreadPoolExecutor scheduler = new ScheduledThreadPoolExecutor(1, task -> {
         Thread worker = new Thread(task, "RGB Blocks last C&B model bake");
         worker.setDaemon(true);
         return worker;
      });
      // Cancelling a superseded bake must actually remove it from the queue:
      // rapid /rgb bake storms otherwise accumulate thousands of inert tasks.
      scheduler.setRemoveOnCancelPolicy(true);
      return scheduler;
   }

   private RGBCnbGeometryBakeDebouncer() {
   }

   public static void reset() {
      WORLD_EPOCH.incrementAndGet();
      // On disconnect/dimension change, delete queued work instead of merely
      // failing its epoch check after the scheduler eventually wakes it.
      for (Entry entry : ENTRIES.values()) {
         cancelTrailingBake(entry);
      }
      ENTRIES.clear();
      BYPASS.remove();
   }

   private static void cancelTrailingBake(Entry entry) {
      synchronized (entry) {
         ScheduledFuture<?> future = entry.pendingFuture;
         entry.pendingFuture = null;
         if (future != null) {
            future.cancel(false);
         }
      }
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
         if (pos != null && !isReplacedClientTile(tileEntity, pos)) {
            long now = System.currentTimeMillis();
            RGBCnbGeometryBakeDebouncer.Entry entry = ENTRIES.computeIfAbsent(key(pos), ignored -> new RGBCnbGeometryBakeDebouncer.Entry());
            entry.lastPayloadMillis = now;
         }
      }
   }

   public static boolean shouldDelayModelBake(Object tileEntity, boolean force) {
      // A forced or deliberate undebounced C&B rebuild supersedes ANY
      // earlier delayed bake for the same current client tile. Returning
      // false without cancelling leaves the old 180ms future to issue a
      // second asynchronous model build after the newer authoritative one.
      if (force || Boolean.TRUE.equals(BYPASS.get())) {
         if (tileEntity != null && isRemoteClientWorld(tileEntity)) {
            BlockPos pos = getBlockPos(tileEntity);
            if (pos != null && !isReplacedClientTile(tileEntity, pos)) {
               Entry pending = ENTRIES.get(key(pos));
               if (pending != null) {
                  pending.requestSerial.incrementAndGet();
                  cancelTrailingBake(pending);
               }
            }
         }
         return false;
      }
      if (tileEntity != null && isRemoteClientWorld(tileEntity)) {
         BlockPos pos = getBlockPos(tileEntity);
         if (pos == null || isReplacedClientTile(tileEntity, pos)) {
            // An old C&B block entity can still receive a late Scena
            // callback after AIR -> new C&B at the same packed position.
            // Reject BEFORE incrementing the live tile's request serial or
            // cancelling its ONLY pending last-mesh refresh.
            return false;
         }

         long now = System.currentTimeMillis();
         RGBCnbGeometryBakeDebouncer.Entry entry = ENTRIES.computeIfAbsent(key(pos), ignored -> new RGBCnbGeometryBakeDebouncer.Entry());
         long lastPayload = entry.lastPayloadMillis;
         if (lastPayload != 0L && now - lastPayload <= 350L) {
            long previousRequest = entry.lastRequestMillis;
            long previousAllowed = entry.lastAllowedBakeMillis;
            entry.lastRequestMillis = now;
            long requestSerial = entry.requestSerial.incrementAndGet();
            if (previousRequest == 0L || now - previousRequest > 70L) {
               entry.lastAllowedBakeMillis = now;
               cancelTrailingBake(entry);
               return false;
            }

            if (previousAllowed != 0L && now - previousAllowed < 90L) {
               scheduleTrailingBake(tileEntity, pos, entry, requestSerial);
               return true;
            }

            entry.lastAllowedBakeMillis = now;
            cancelTrailingBake(entry);
            return false;
         } else {
            entry.lastRequestMillis = now;
            entry.lastAllowedBakeMillis = now;
            cancelTrailingBake(entry);
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
      synchronized (entry) {
         // Only one trailing future per position. The request serial AND
         // world epoch remain the final on-main-thread correctness guards.
         // Cancel before replacing so hostile bursts do not queue O(bakes).
         if (entry.pendingFuture != null) {
            entry.pendingFuture.cancel(false);
         }
         entry.pendingFuture = TRAILING_BAKES.schedule(() -> {
         Minecraft client = Minecraft.getInstance();
         if (client == null || epoch != WORLD_EPOCH.get()) {
            return;
         }
         client.execute(() -> {
            if (epoch != WORLD_EPOCH.get() || entry.requestSerial.get() != serial) {
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
                  // C&B ships its actual native block entity behind loader
                  // implementation classes that may be package-private or
                  // inherit a protected model callback. A public-only
                  // getMethod() reflection probe can silently miss its LAST
                  // baked geometry update even when the voxel data is valid.
                  Method update = findModelUpdateMethod(live.getClass());
                  update.invoke(live);
                  level.sendBlockUpdated(pos, level.getBlockState(pos), level.getBlockState(pos), 3);
               } catch (Throwable failure) {
                  System.err.println("[RGB Blocks] C&B trailing mesh rebuild failed: " + failure);
               }
            });
         });
         }, 180L, TimeUnit.MILLISECONDS);
      }
   }

   private static Method findModelUpdateMethod(Class<?> entityType) throws NoSuchMethodException {
      try {
         Method method = entityType.getMethod("updateModelData");
         method.setAccessible(true);
         return method;
      } catch (NoSuchMethodException missingPublic) {
         for (Class<?> cursor = entityType; cursor != null; cursor = cursor.getSuperclass()) {
            try {
               Method declared = cursor.getDeclaredMethod("updateModelData");
               declared.setAccessible(true);
               return declared;
            } catch (NoSuchMethodException next) {
               // A class may inherit its C&B model callback from its superclass.
            }
         }
         throw missingPublic;
      }
   }

   private static boolean isReplacedClientTile(Object tileEntity, BlockPos pos) {
      if (tileEntity instanceof BlockEntity tile) {
         if (tile.isRemoved()) {
            return true;
         }
         Level world = tile.getLevel();
         if (world != null && world.isLoaded(pos)) {
            // During first attachment this can legitimately be null;
            // reject only when a DIFFERENT entity owns the live position.
            BlockEntity current = world.getBlockEntity(pos);
            return current != null && current != tile;
         }
      }
      return false;
   }

   private static boolean isRemoteClientWorld(Object tileEntity) {
      // Native BlockEntity names are loader-remapped in Forge/NeoForge.
      // Reflection on getLevel() can miss inherited runtime-mapped methods.
      if (tileEntity instanceof BlockEntity tile) {
         Level world = tile.getLevel();
         Minecraft mc = Minecraft.getInstance();
         // The host of a LAN multiplayer world owns an integrated server,
         // but still has a fully separate CLIENT Level and must receive
         // its own C&B trailing mesh updates. Reject server-side or stale
         // levels; never reject a live client because a server exists.
         return world != null && world.isClientSide() && mc != null
               && mc.level == world;
      }
      try {
         Method hasLevel = tileEntity.getClass().getMethod("hasLevel");
         Object hasLevelResult = hasLevel.invoke(tileEntity);
         if (hasLevelResult instanceof Boolean && (Boolean)hasLevelResult) {
            Method getLevel = tileEntity.getClass().getMethod("getLevel");
            if (getLevel.invoke(tileEntity) instanceof Level level && level.isClientSide()) {
               Minecraft minecraft = Minecraft.getInstance();
               return minecraft != null && minecraft.level == level;
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
      if (tileEntity instanceof BlockEntity tile) {
         BlockPos pos = tile.getBlockPos();
         return pos == null ? null : pos.immutable();
      }
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
      private final AtomicLong requestSerial = new AtomicLong();
      private volatile long lastPayloadMillis;
      private volatile long lastRequestMillis;
      private volatile long lastAllowedBakeMillis;
      private ScheduledFuture<?> pendingFuture;
   }
}
