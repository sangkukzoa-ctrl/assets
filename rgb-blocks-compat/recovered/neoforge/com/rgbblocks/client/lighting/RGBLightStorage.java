package com.rgbblocks.client.lighting;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;

public final class RGBLightStorage {
   private final Map<Long, RGBLightSection> sections = new ConcurrentHashMap<>();

   public RGBLightColor4 get(BlockPos pos) {
      return this.get(pos.getX(), pos.getY(), pos.getZ());
   }

   public RGBLightColor4 get(int x, int y, int z) {
      RGBLightSection section = this.sections.get(sectionKey(x, y, z));
      return section == null ? RGBLightColor4.BLACK : section.get(x & 15, y & 15, z & 15);
   }

   public boolean setMax(BlockPos pos, RGBLightColor4 color) {
      return this.setMax(pos.getX(), pos.getY(), pos.getZ(), color);
   }

   public boolean setMax(int x, int y, int z, RGBLightColor4 color) {
      return color != null && color.active()
         ? this.sections.computeIfAbsent(sectionKey(x, y, z), ignored -> new RGBLightSection()).setMax(x & 15, y & 15, z & 15, color)
         : false;
   }

   public void set(BlockPos pos, RGBLightColor4 color) {
      this.set(pos.getX(), pos.getY(), pos.getZ(), color);
   }

   public void set(int x, int y, int z, RGBLightColor4 color) {
      if (color == null) {
         color = RGBLightColor4.BLACK;
      }

      long key = sectionKey(x, y, z);
      if (color.active()) {
         this.sections.computeIfAbsent(key, ignored -> new RGBLightSection()).set(x & 15, y & 15, z & 15, color);
      } else {
         RGBLightSection section = this.sections.get(key);
         if (section != null) {
            section.set(x & 15, y & 15, z & 15, RGBLightColor4.BLACK);
            if (section.isEmpty()) {
               this.sections.remove(key, section);
            }
         }
      }
   }

   public boolean hasActiveNear(BlockPos center, int radius) {
      if (center == null) {
         return false;
      }

      int r = Math.max(1, radius);

      for (int y = center.getY() - r; y <= center.getY() + r; y++) {
         for (int z = center.getZ() - r; z <= center.getZ() + r; z++) {
            for (int x = center.getX() - r; x <= center.getX() + r; x++) {
               if (this.get(x, y, z).active()) {
                  return true;
               }
            }
         }
      }

      return false;
   }

   public void clear() {
      this.sections.clear();
   }

   public void clearCube(BlockPos center, int radius) {
      if (center == null) {
         this.clear();
      } else {
         int r = Math.max(1, radius);
         Set<Long> touched = new HashSet<>();

         for (int y = center.getY() - r; y <= center.getY() + r; y++) {
            for (int z = center.getZ() - r; z <= center.getZ() + r; z++) {
               for (int x = center.getX() - r; x <= center.getX() + r; x++) {
                  long key = sectionKey(x, y, z);
                  RGBLightSection section = this.sections.get(key);
                  if (section != null) {
                     section.set(x & 15, y & 15, z & 15, RGBLightColor4.BLACK);
                     touched.add(key);
                  }
               }
            }
         }

         for (long key : touched) {
            RGBLightSection section = this.sections.get(key);
            if (section != null && section.isEmpty()) {
               this.sections.remove(key, section);
            }
         }
      }
   }

   Map<Long, byte[]> snapshotActiveSections() {
      Map<Long, byte[]> snapshot = new HashMap<>();

      for (Entry<Long, RGBLightSection> entry : this.sections.entrySet()) {
         RGBLightSection section = entry.getValue();
         if (section != null && !section.isEmpty()) {
            snapshot.put(entry.getKey(), section.copyData());
         }
      }

      return snapshot;
   }

   void restoreActiveSections(Map<Long, byte[]> snapshot) {
      this.sections.clear();
      if (snapshot != null && !snapshot.isEmpty()) {
         for (Entry<Long, byte[]> entry : snapshot.entrySet()) {
            if (entry.getKey() != null && entry.getValue() != null) {
               RGBLightSection section = new RGBLightSection();
               if (section.loadData(entry.getValue()) && !section.isEmpty()) {
                  this.sections.put(entry.getKey(), section);
               }
            }
         }
      }
   }

   int activeSectionCount() {
      int count = 0;

      for (RGBLightSection section : this.sections.values()) {
         if (section != null && !section.isEmpty()) {
            count++;
         }
      }

      return count;
   }

   private static long sectionKey(int x, int y, int z) {
      return SectionPos.asLong(x >> 4, y >> 4, z >> 4);
   }
}
