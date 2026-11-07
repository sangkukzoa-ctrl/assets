package com.rgbblocks.client.cnb;

import java.lang.reflect.Method;
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

   private RGBCnbGeometryBakeDebouncer() {
   }

   public static void reset() {
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
            if (previousRequest == 0L || now - previousRequest > 70L) {
               entry.lastAllowedBakeMillis = now;
               return false;
            }

            if (previousAllowed != 0L && now - previousAllowed < 90L) {
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
      private volatile long lastPayloadMillis;
      private volatile long lastRequestMillis;
      private volatile long lastAllowedBakeMillis;
   }
}
