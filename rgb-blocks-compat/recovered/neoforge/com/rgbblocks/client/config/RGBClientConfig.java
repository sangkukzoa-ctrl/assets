package com.rgbblocks.client.config;

import net.neoforged.neoforge.common.ModConfigSpec;
import net.neoforged.neoforge.common.ModConfigSpec.BooleanValue;
import net.neoforged.neoforge.common.ModConfigSpec.Builder;
import net.neoforged.neoforge.common.ModConfigSpec.DoubleValue;
import net.neoforged.neoforge.common.ModConfigSpec.IntValue;

public final class RGBClientConfig {
   private static final long CACHE_REFRESH_INTERVAL_NANOS = 250000000L;
   public static final Builder BUILDER = new Builder();
   public static final BooleanValue ENABLED = BUILDER.comment(new String[]{"Enable RGB parallel light layer.", "Client-side only."}).define("enabled", true);
   public static final IntValue RADIUS = BUILDER.comment(new String[]{"RGB light sampling radius.", "Lower values improve performance."})
      .defineInRange("rgbLightRadius", 9, 3, 12);
   public static final DoubleValue STRENGTH = BUILDER.comment(
         new String[]{
            "RGB light intensity multiplier.",
            "This now scales single-source color energy only; identical sources are luminance-capped like vanilla block light."
         }
      )
      .defineInRange("rgbLightStrength", 1.35, 0.0, 3.0);
   public static final BooleanValue ENABLE_CNB_SOURCE_TRACKING = BUILDER.comment("Enable Chisels & Bits voxel RGB source tracking.")
      .define("enableCnbRgbSources", true);
   public static final BooleanValue ENABLE_GLOBAL_LIGHTMAP_TINT = BUILDER.comment(
         new String[]{"Apply RGB light tint through the client lightmap.", "This is the Sodium/Iris-safe global RGB light perception layer."}
      )
      .define("enableGlobalLightmapTint", false);
   public static final ModConfigSpec SPEC = BUILDER.build();
   public static volatile boolean ENABLED_CACHED = true;
   public static volatile int RADIUS_CACHED = 9;
   public static volatile float STRENGTH_CACHED = 1.35F;
   public static volatile boolean ENABLE_CNB_SOURCE_TRACKING_CACHED = true;
   public static volatile boolean ENABLE_GLOBAL_LIGHTMAP_TINT_CACHED = false;
   private static volatile long lastRefreshNanos = 0L;

   private RGBClientConfig() {
   }

   public static void refreshCache() {
      long now = System.nanoTime();
      if (now - lastRefreshNanos >= 250000000L) {
         lastRefreshNanos = now;

         try {
            ENABLED_CACHED = (Boolean)ENABLED.get();
            RADIUS_CACHED = (Integer)RADIUS.get();
            STRENGTH_CACHED = ((Double)STRENGTH.get()).floatValue();
            ENABLE_CNB_SOURCE_TRACKING_CACHED = (Boolean)ENABLE_CNB_SOURCE_TRACKING.get();
            ENABLE_GLOBAL_LIGHTMAP_TINT_CACHED = (Boolean)ENABLE_GLOBAL_LIGHTMAP_TINT.get();
         } catch (Throwable var3) {
         }
      }
   }

   public static boolean rgbEnabled() {
      refreshCache();
      return ENABLED_CACHED;
   }
}
