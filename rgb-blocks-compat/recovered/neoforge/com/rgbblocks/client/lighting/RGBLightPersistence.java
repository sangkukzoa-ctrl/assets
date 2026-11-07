package com.rgbblocks.client.lighting;

import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.runtime.RGBRuntime;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;

final class RGBLightPersistence {
   private static final int MAGIC = 1380401740;
   private static final int FORMAT_VERSION = 3;
   private static final long MAX_FILE_BYTES = 536870912L;
   private static final int MAX_SECTIONS = 262144;
   private static final int MAX_CNB_SOURCES = 65536;
   private static final int MAX_INDEXED_SOURCES = 65536;
   private static final int MAX_DIRTY_POSITIONS = 262144;
   private static String loadedWorldId = "";
   private static String loadedDimension = "";
   private static RGBLightPersistence.Status status = RGBLightPersistence.Status.NOT_LOADED;
   private static int persistedSections;
   private static int persistedCnbSources;
   private static int persistedIndexedSources;
   private static int persistedDirtyPositions;
   private static String lastError = "";

   private RGBLightPersistence() {
   }

   static void tick() {
      Minecraft minecraft = Minecraft.getInstance();
      if (minecraft != null && minecraft.level != null && minecraft.isSameThread()) {
         String worldId = RGBRuntime.clientWorldId();
         String dimension = currentDimension();
         if (worldId != null && !worldId.isBlank() && dimension != null && !dimension.isBlank() && !"unknown".equals(dimension)) {
            if (!worldId.equals(loadedWorldId) || !dimension.equals(loadedDimension)) {
               boolean switchingLoadedContext = !loadedWorldId.isBlank() || !loadedDimension.isBlank();
               if (switchingLoadedContext) {
                  RGBRealLightEngine.prepareForPersistenceDimensionSwitch();
               }

               loadedWorldId = worldId;
               loadedDimension = dimension;
               loadCurrentBlocking();
            }
         }
      }
   }

   static boolean readyForCurrentDimension() {
      if (status != RGBLightPersistence.Status.NOT_LOADED && status != RGBLightPersistence.Status.LOADING) {
         String worldId = RGBRuntime.clientWorldId();
         String dimension = currentDimension();
         return worldId != null
            && !worldId.isBlank()
            && dimension != null
            && !dimension.isBlank()
            && worldId.equals(loadedWorldId)
            && dimension.equals(loadedDimension);
      } else {
         return false;
      }
   }

   static void saveCurrentBlocking() {
      if (!loadedWorldId.isBlank() && !loadedDimension.isBlank()) {
         try {
            Map<Long, byte[]> sections = RGBLightEngine.snapshotPersistedSections();
            List<RGBLightPersistence.PersistedCnbSource> cnbSources = RGBRealLightEngine.snapshotPersistedCnbSources();
            Map<Long, RGBLightColor4> indexedSources = RGBSourceIndex.snapshotSources();
            List<Long> dirtyPositions = RGBRealLightEngine.snapshotDirtyPositions(loadedDimension);
            writeSnapshot(snapshotPath(loadedWorldId, loadedDimension), loadedDimension, sections, cnbSources, indexedSources, dirtyPositions);
            persistedSections = sections.size();
            persistedCnbSources = cnbSources.size();
            persistedIndexedSources = indexedSources.size();
            persistedDirtyPositions = dirtyPositions.size();
            status = RGBLightPersistence.Status.SAVED;
            lastError = "";
            System.out
               .println(
                  "[RGB Blocks] Saved RGB lightmap: "
                     + persistedSections
                     + " sections, "
                     + persistedCnbSources
                     + " C&B sources, "
                     + persistedIndexedSources
                     + " indexed sources, "
                     + persistedDirtyPositions
                     + " dirty positions ("
                     + loadedDimension
                     + ")."
               );
         } catch (Throwable error) {
            status = RGBLightPersistence.Status.ERROR;
            lastError = error.getClass().getSimpleName() + ": " + error.getMessage();
            System.err.println("[RGB Blocks] Failed to save RGB lightmap for " + loadedDimension + ".");
            error.printStackTrace();
         }
      }
   }

   static void saveCurrentIfReady() {
      if (status != RGBLightPersistence.Status.LOADING && status != RGBLightPersistence.Status.NOT_LOADED) {
         saveCurrentBlocking();
      }
   }

   static void reset() {
      loadedWorldId = "";
      loadedDimension = "";
      status = RGBLightPersistence.Status.NOT_LOADED;
      persistedSections = 0;
      persistedCnbSources = 0;
      persistedIndexedSources = 0;
      persistedDirtyPositions = 0;
      lastError = "";
   }

   static RGBLightPersistence.Diagnostics diagnostics() {
      return new RGBLightPersistence.Diagnostics(
         status.name(), persistedSections, persistedCnbSources, persistedIndexedSources, persistedDirtyPositions, loadedWorldId, loadedDimension, lastError
      );
   }

   private static void loadCurrentBlocking() {
      status = RGBLightPersistence.Status.LOADING;
      lastError = "";
      Path path = snapshotPath(loadedWorldId, loadedDimension);

      try {
         RGBLightPersistence.Snapshot snapshot = Files.isRegularFile(path) ? readSnapshot(path, loadedDimension) : RGBLightPersistence.Snapshot.empty();
         RGBLightEngine.restorePersistedSections(snapshot.sections());
         RGBRealLightEngine.restorePersistedCnbSources(snapshot.cnbSources());
         HashSet<Long> persistedCnbKeys = new HashSet<>();

         for (RGBLightPersistence.PersistedCnbSource source : snapshot.cnbSources()) {
            if (source != null) {
               persistedCnbKeys.add(source.packedPos());
            }
         }

         HashSet<Long> missingCnbCandidates = new HashSet<>();

         for (Long packedPos : snapshot.indexedSources().keySet()) {
            if (packedPos != null && !persistedCnbKeys.contains(packedPos)) {
               missingCnbCandidates.add(packedPos);
            }
         }

         RGBRealLightEngine.registerPersistedCnbRecoveryCandidates(missingCnbCandidates);
         List<BlockPos> staleSources = RGBSourceIndex.restorePersistedSources(snapshot.indexedSources());
         staleSources.removeIf(pos -> missingCnbCandidates.contains(pos.asLong()) && RGBRealLightEngine.isLoadedChiseledBlockForPersistence(pos));
         RGBRealLightEngine.deferPersistedSourceCleanup(staleSources);
         RGBRealLightEngine.restoreDirtyPositions(loadedDimension, snapshot.dirtyPositions());
         persistedSections = snapshot.sections().size();
         persistedCnbSources = snapshot.cnbSources().size();
         persistedIndexedSources = snapshot.indexedSources().size();
         persistedDirtyPositions = snapshot.dirtyPositions().size();
         status = Files.isRegularFile(path) ? RGBLightPersistence.Status.LOADED : RGBLightPersistence.Status.EMPTY;
         Minecraft minecraft = Minecraft.getInstance();
         if (minecraft != null && minecraft.levelRenderer != null) {
            minecraft.levelRenderer.allChanged();
         }

         List<BlockPos> restoredCnbPositions = new ArrayList<>();

         for (RGBLightPersistence.PersistedCnbSource source : snapshot.cnbSources()) {
            if (source != null) {
               restoredCnbPositions.add(BlockPos.of(source.packedPos()));
            }
         }

         RGBCnbReloadWakeup.onPersistedSourcesRestored(loadedDimension, restoredCnbPositions);
         System.out
            .println(
               "[RGB Blocks] Loaded RGB lightmap: "
                  + persistedSections
                  + " sections, "
                  + persistedCnbSources
                  + " C&B sources, "
                  + persistedIndexedSources
                  + " indexed sources, "
                  + persistedDirtyPositions
                  + " dirty positions ("
                  + loadedDimension
                  + ")."
            );
      } catch (Throwable error) {
         RGBLightEngine.restorePersistedSections(Map.of());
         RGBRealLightEngine.restorePersistedCnbSources(List.of());
         RGBSourceIndex.clear();
         persistedSections = 0;
         persistedCnbSources = 0;
         persistedIndexedSources = 0;
         persistedDirtyPositions = 0;
         RGBRealLightEngine.restoreDirtyPositions(loadedDimension, List.of());
         status = RGBLightPersistence.Status.ERROR;
         lastError = error.getClass().getSimpleName() + ": " + error.getMessage();
         System.err.println("[RGB Blocks] Failed to load RGB lightmap for " + loadedDimension + ". Starting empty.");
         error.printStackTrace();
      }
   }

   private static void writeSnapshot(
      Path path,
      String dimension,
      Map<Long, byte[]> sections,
      List<RGBLightPersistence.PersistedCnbSource> cnbSources,
      Map<Long, RGBLightColor4> indexedSources,
      List<Long> dirtyPositions
   ) throws IOException {
      Files.createDirectories(path.getParent());
      Path temporary = path.resolveSibling(path.getFileName() + ".tmp");

      try (DataOutputStream out = new DataOutputStream(new BufferedOutputStream(new GZIPOutputStream(Files.newOutputStream(temporary))))) {
         out.writeInt(1380401740);
         out.writeInt(3);
         out.writeUTF(dimension);
         out.writeInt(sections.size());

         for (Entry<Long, byte[]> entry : sections.entrySet()) {
            byte[] data = entry.getValue();
            if (data == null || data.length != 12288) {
               throw new IOException("Invalid RGB section snapshot length");
            }

            out.writeLong(entry.getKey());
            out.writeInt(data.length);
            out.write(data);
         }

         out.writeInt(cnbSources.size());

         for (RGBLightPersistence.PersistedCnbSource source : cnbSources) {
            out.writeLong(source.packedPos());
            out.writeInt(source.rgb());
            out.writeFloat(source.energy());
         }

         out.writeInt(indexedSources.size());

         for (Entry<Long, RGBLightColor4> entry : indexedSources.entrySet()) {
            RGBLightColor4 color = entry.getValue();
            if (entry.getKey() == null || color == null || !color.active()) {
               throw new IOException("Invalid persisted RGB source");
            }

            out.writeLong(entry.getKey());
            out.writeByte(color.r());
            out.writeByte(color.g());
            out.writeByte(color.b());
         }

         List<Long> safeDirty = dirtyPositions == null ? List.of() : dirtyPositions;
         if (safeDirty.size() > 262144) {
            throw new IOException("Too many dirty RGB positions: " + safeDirty.size());
         }

         out.writeInt(safeDirty.size());

         for (Long packedPos : safeDirty) {
            if (packedPos == null) {
               throw new IOException("Invalid dirty RGB position");
            }

            out.writeLong(packedPos);
         }
      }

      try {
         Files.move(temporary, path, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
      } catch (AtomicMoveNotSupportedException ignored) {
         Files.move(temporary, path, StandardCopyOption.REPLACE_EXISTING);
      }
   }

   private static RGBLightPersistence.Snapshot readSnapshot(Path path, String expectedDimension) throws IOException {
      long size = Files.size(path);
      if (size >= 1L && size <= 536870912L) {
         try (DataInputStream in = new DataInputStream(new BufferedInputStream(new GZIPInputStream(Files.newInputStream(path))))) {
            if (in.readInt() != 1380401740) {
               throw new IOException("Invalid RGB lightmap magic");
            }

            int version = in.readInt();
            if (version < 1 || version > 3) {
               throw new IOException("Unsupported RGB lightmap version: " + version);
            }

            String dimension = in.readUTF();
            if (!expectedDimension.equals(dimension)) {
               throw new IOException("RGB lightmap dimension mismatch: " + dimension);
            }

            int sectionCount = checkedCount(in.readInt(), 262144, "section");
            Map<Long, byte[]> sections = new HashMap<>(Math.min(sectionCount * 2, 262144));

            for (int i = 0; i < sectionCount; i++) {
               long key = in.readLong();
               int length = in.readInt();
               if (length != 12288) {
                  throw new IOException("Invalid RGB section length: " + length);
               }

               byte[] data = new byte[length];
               in.readFully(data);
               sections.put(key, data);
            }

            int cnbCount = checkedCount(in.readInt(), 65536, "C&B source");
            List<RGBLightPersistence.PersistedCnbSource> cnbSources = new ArrayList<>(cnbCount);

            for (int i = 0; i < cnbCount; i++) {
               long packedPos = in.readLong();
               int rgb = in.readInt();
               float energy = in.readFloat();
               if (rgb >= 0 && Float.isFinite(energy) && energy > 0.0F) {
                  cnbSources.add(new RGBLightPersistence.PersistedCnbSource(packedPos, rgb, Math.min(1.0F, energy)));
               }
            }

            Map<Long, RGBLightColor4> indexedSources = new HashMap<>();
            if (version >= 2) {
               int sourceCount = checkedCount(in.readInt(), 65536, "indexed source");

               for (int i = 0; i < sourceCount; i++) {
                  long packedPos = in.readLong();
                  RGBLightColor4 color = new RGBLightColor4(in.readUnsignedByte(), in.readUnsignedByte(), in.readUnsignedByte());
                  if (color.active()) {
                     indexedSources.put(packedPos, color);
                  }
               }
            }

            List<Long> dirtyPositions = new ArrayList<>();
            if (version >= 3) {
               int dirtyCount = checkedCount(in.readInt(), 262144, "dirty position");

               for (int i = 0; i < dirtyCount; i++) {
                  dirtyPositions.add(in.readLong());
               }
            } else {
               dirtyPositions.addAll(indexedSources.keySet());

               for (RGBLightPersistence.PersistedCnbSource source : cnbSources) {
                  if (source != null) {
                     dirtyPositions.add(source.packedPos());
                  }
               }
            }

            return new RGBLightPersistence.Snapshot(sections, cnbSources, indexedSources, dirtyPositions);
         } catch (EOFException error) {
            throw new IOException("Truncated RGB lightmap", error);
         }
      } else {
         throw new IOException("Invalid RGB lightmap file size: " + size);
      }
   }

   private static int checkedCount(int count, int max, String name) throws IOException {
      if (count >= 0 && count <= max) {
         return count;
      } else {
         throw new IOException("Invalid " + name + " count: " + count);
      }
   }

   private static Path snapshotPath(String worldId, String dimension) {
      Minecraft minecraft = Minecraft.getInstance();
      Path root = minecraft.gameDirectory.toPath().resolve("rgbblocks").resolve("lightmaps").resolve(safeComponent(worldId));
      String encodedDimension = Base64.getUrlEncoder().withoutPadding().encodeToString(dimension.getBytes(StandardCharsets.UTF_8));
      return root.resolve(encodedDimension + ".rgl.gz");
   }

   private static String safeComponent(String value) {
      return value == null ? "unknown" : value.replaceAll("[^A-Za-z0-9._-]", "_");
   }

   private static String currentDimension() {
      try {
         Minecraft minecraft = Minecraft.getInstance();
         if (minecraft != null && minecraft.level != null) {
            return minecraft.level.dimension().identifier().toString();
         }
      } catch (Throwable var1) {
      }

      return "unknown";
   }

   record Diagnostics(String status, int sections, int cnbSources, int indexedSources, int dirtyPositions, String worldId, String dimension, String lastError) {
   }

   record PersistedCnbSource(long packedPos, int rgb, float energy) {
   }

   private record Snapshot(
      Map<Long, byte[]> sections, List<RGBLightPersistence.PersistedCnbSource> cnbSources, Map<Long, RGBLightColor4> indexedSources, List<Long> dirtyPositions
   ) {
      static RGBLightPersistence.Snapshot empty() {
         return new RGBLightPersistence.Snapshot(Map.of(), List.of(), Map.of(), List.of());
      }
   }

   enum Status {
      NOT_LOADED,
      LOADING,
      EMPTY,
      LOADED,
      SAVED,
      ERROR;
   }
}
