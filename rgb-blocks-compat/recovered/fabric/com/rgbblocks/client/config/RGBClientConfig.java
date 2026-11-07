package com.rgbblocks.client.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import net.fabricmc.loader.api.FabricLoader;

public final class RGBClientConfig {
   private static final long CACHE_REFRESH_INTERVAL_NANOS = 250000000L;
   private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
   private static final Path CONFIG_PATH = FabricLoader.getInstance().getConfigDir().resolve("rgbblocks-client.json");
   public static volatile boolean ENABLED_CACHED = true;
   public static volatile int RADIUS_CACHED = 9;
   public static volatile float STRENGTH_CACHED = 1.35F;
   public static volatile boolean ENABLE_CNB_SOURCE_TRACKING_CACHED = true;
   public static volatile boolean ENABLE_GLOBAL_LIGHTMAP_TINT_CACHED = false;
   private static volatile boolean initialized;
   private static volatile long lastRefreshNanos;
   private static volatile long lastModifiedMillis = Long.MIN_VALUE;

   private RGBClientConfig() {
   }

   public static synchronized void initialize() {
      if (!initialized) {
         try {
            Files.createDirectories(CONFIG_PATH.getParent());
            if (Files.notExists(CONFIG_PATH)) {
               writeDefaults();
            }

            reloadFromDisk();
         } catch (IOException | RuntimeException exception) {
            System.err.println("RGB Blocks could not load " + CONFIG_PATH + "; client defaults will be used.");
            exception.printStackTrace();
         }

         initialized = true;
      }
   }

   public static void refreshCache() {
      if (!initialized) {
         initialize();
      }

      long now = System.nanoTime();
      if (now - lastRefreshNanos >= 250000000L) {
         lastRefreshNanos = now;

         try {
            long modified = Files.getLastModifiedTime(CONFIG_PATH).toMillis();
            if (modified != lastModifiedMillis) {
               synchronized (RGBClientConfig.class) {
                  reloadFromDisk();
               }
            }
         } catch (IOException | RuntimeException var7) {
         }
      }
   }

   public static boolean rgbEnabled() {
      refreshCache();
      return ENABLED_CACHED;
   }

   private static void reloadFromDisk() throws IOException {
      try (BufferedReader reader = Files.newBufferedReader(CONFIG_PATH, StandardCharsets.UTF_8)) {
         JsonElement parsed = JsonParser.parseReader(reader);
         JsonObject root = parsed.isJsonObject() ? parsed.getAsJsonObject() : new JsonObject();
         ENABLED_CACHED = booleanValue(root, "enabled", true);
         RADIUS_CACHED = clamp(intValue(root, "rgbLightRadius", 9), 3, 12);
         STRENGTH_CACHED = clamp(floatValue(root, "rgbLightStrength", 1.35F), 0.0F, 3.0F);
         ENABLE_CNB_SOURCE_TRACKING_CACHED = booleanValue(root, "enableCnbRgbSources", true);
         ENABLE_GLOBAL_LIGHTMAP_TINT_CACHED = booleanValue(root, "enableGlobalLightmapTint", false);
      }

      lastModifiedMillis = Files.getLastModifiedTime(CONFIG_PATH).toMillis();
   }

   private static void writeDefaults() throws IOException {
      JsonObject root = new JsonObject();
      root.addProperty("enabled", true);
      root.addProperty("rgbLightRadius", 9);
      root.addProperty("rgbLightStrength", 1.35);
      root.addProperty("enableCnbRgbSources", true);
      root.addProperty("enableGlobalLightmapTint", false);

      try (BufferedWriter writer = Files.newBufferedWriter(CONFIG_PATH, StandardCharsets.UTF_8)) {
         GSON.toJson(root, writer);
      }
   }

   private static boolean booleanValue(JsonObject root, String name, boolean fallback) {
      try {
         JsonElement value = root.get(name);
         return value == null ? fallback : value.getAsBoolean();
      } catch (RuntimeException ignored) {
         return fallback;
      }
   }

   private static int intValue(JsonObject root, String name, int fallback) {
      try {
         JsonElement value = root.get(name);
         return value == null ? fallback : value.getAsInt();
      } catch (RuntimeException ignored) {
         return fallback;
      }
   }

   private static float floatValue(JsonObject root, String name, float fallback) {
      try {
         JsonElement value = root.get(name);
         return value == null ? fallback : value.getAsFloat();
      } catch (RuntimeException ignored) {
         return fallback;
      }
   }

   private static int clamp(int value, int min, int max) {
      return Math.max(min, Math.min(max, value));
   }

   private static float clamp(float value, float min, float max) {
      return !Float.isFinite(value) ? 1.35F : Math.max(min, Math.min(max, value));
   }
}
