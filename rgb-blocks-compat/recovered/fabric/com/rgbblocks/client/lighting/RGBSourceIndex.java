package com.rgbblocks.client.lighting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;

public final class RGBSourceIndex {
   private static final int MAX_INDEXED_SOURCES = 65536;
   private static final Map<Long, RGBSourceIndex.SourceEntry> BY_POS = new ConcurrentHashMap<>();
   private static final Map<Long, Map<Long, RGBSourceIndex.SourceEntry>> BY_SECTION = new ConcurrentHashMap<>();

   private RGBSourceIndex() {
   }

   public static void clear() {
      BY_POS.clear();
      BY_SECTION.clear();
   }

   public static void refresh(BlockAndTintGetter level, BlockPos pos) {
      if (level != null && pos != null) {
         RGBLightColor4 source = RGBRealLightEngine.sourceColorAt(level, pos);
         update(pos, source);
      }
   }

   public static void update(BlockPos pos, RGBLightColor4 color) {
      if (pos != null && color != null && color.active()) {
         if (BY_POS.size() > 65536) {
            clear();
         } else {
            BlockPos immutable = pos.immutable();
            long posKey = immutable.asLong();
            RGBSourceIndex.SourceEntry next = new RGBSourceIndex.SourceEntry(immutable, color);
            RGBSourceIndex.SourceEntry old = BY_POS.put(posKey, next);
            if (old != null) {
               Map<Long, RGBSourceIndex.SourceEntry> oldSection = BY_SECTION.get(sectionKey(old.pos));
               if (oldSection != null) {
                  oldSection.remove(posKey);
                  if (oldSection.isEmpty()) {
                     BY_SECTION.remove(sectionKey(old.pos));
                  }
               }
            }

            BY_SECTION.computeIfAbsent(sectionKey(immutable), ignored -> new ConcurrentHashMap<>()).put(posKey, next);
         }
      } else {
         remove(pos);
      }
   }

   public static void remove(BlockPos pos) {
      if (pos != null) {
         long posKey = pos.asLong();
         RGBSourceIndex.SourceEntry old = BY_POS.remove(posKey);
         if (old != null) {
            long sectionKey = sectionKey(old.pos);
            Map<Long, RGBSourceIndex.SourceEntry> section = BY_SECTION.get(sectionKey);
            if (section != null) {
               section.remove(posKey);
               if (section.isEmpty()) {
                  BY_SECTION.remove(sectionKey);
               }
            }
         }
      }
   }

   static Map<Long, RGBLightColor4> snapshotSources() {
      Map<Long, RGBLightColor4> snapshot = new HashMap<>();

      for (Entry<Long, RGBSourceIndex.SourceEntry> entry : BY_POS.entrySet()) {
         RGBSourceIndex.SourceEntry source = entry.getValue();
         if (entry.getKey() != null && source != null && source.color != null && source.color.active()) {
            snapshot.put(entry.getKey(), source.color);
         }
      }

      return snapshot;
   }

   static List<BlockPos> restorePersistedSources(Map<Long, RGBLightColor4> snapshot) {
      clear();
      List<BlockPos> stale = new ArrayList<>();
      if (snapshot != null && !snapshot.isEmpty()) {
         Minecraft minecraft = Minecraft.getInstance();
         BlockAndTintGetter level = minecraft == null ? null : minecraft.level;
         Iterator var4 = snapshot.entrySet().iterator();

         while (true) {
            BlockPos pos;
            RGBLightColor4 color;
            while (true) {
               if (!var4.hasNext()) {
                  return stale;
               }

               Entry<Long, RGBLightColor4> entry = (Entry<Long, RGBLightColor4>)var4.next();
               if (entry.getKey() != null && entry.getValue() != null && entry.getValue().active()) {
                  pos = BlockPos.of(entry.getKey());
                  color = entry.getValue();

                  try {
                     if (minecraft != null && minecraft.level != null && minecraft.level.isLoaded(pos)) {
                        RGBLightColor4 current = RGBRealLightEngine.sourceColorAt(level, pos);
                        if (current.active()) {
                           color = current;
                           break;
                        }

                        stale.add(pos);
                     }
                  } catch (Throwable ignored) {
                  }
               }
            }

            update(pos, color);
         }
      } else {
         return stale;
      }
   }

   public static boolean forEachSourceAround(BlockPos center, int radius, RGBSourceIndex.SourceConsumer consumer) {
      if (center != null && consumer != null && !BY_SECTION.isEmpty()) {
         int r = Math.max(0, radius);
         int minX = center.getX() - r >> 4;
         int maxX = center.getX() + r >> 4;
         int minY = center.getY() - r >> 4;
         int maxY = center.getY() + r >> 4;
         int minZ = center.getZ() - r >> 4;
         int maxZ = center.getZ() + r >> 4;
         boolean found = false;

         for (int sx = minX; sx <= maxX; sx++) {
            for (int sy = minY; sy <= maxY; sy++) {
               for (int sz = minZ; sz <= maxZ; sz++) {
                  Map<Long, RGBSourceIndex.SourceEntry> section = BY_SECTION.get(SectionPos.asLong(sx, sy, sz));
                  if (section != null && !section.isEmpty()) {
                     for (RGBSourceIndex.SourceEntry entry : section.values()) {
                        if (entry != null
                           && entry.pos != null
                           && entry.color != null
                           && entry.color.active()
                           && Math.abs(entry.pos.getX() - center.getX()) <= r
                           && Math.abs(entry.pos.getY() - center.getY()) <= r
                           && Math.abs(entry.pos.getZ() - center.getZ()) <= r) {
                           found = true;
                           consumer.accept(entry.pos, entry.color);
                        }
                     }
                  }
               }
            }
         }

         return found;
      } else {
         return false;
      }
   }

   private static long sectionKey(BlockPos pos) {
      return SectionPos.asLong(pos.getX() >> 4, pos.getY() >> 4, pos.getZ() >> 4);
   }

   @FunctionalInterface
   public interface SourceConsumer {
      void accept(BlockPos var1, RGBLightColor4 var2);
   }

   private record SourceEntry(BlockPos pos, RGBLightColor4 color) {
   }
}
