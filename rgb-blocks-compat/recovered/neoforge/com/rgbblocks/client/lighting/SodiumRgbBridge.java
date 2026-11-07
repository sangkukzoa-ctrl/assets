package com.rgbblocks.client.lighting;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.state.BlockState;

public final class SodiumRgbBridge {
   private static final ThreadLocal<SodiumRgbBridge.Context> CURRENT = new ThreadLocal<>();

   private SodiumRgbBridge() {
   }

   public static void begin(Object levelObj, BlockState state, BlockPos pos) {
      if (RGBRealLightEngine.enabled() && state != null && pos != null) {
         BlockAndTintGetter level = null;

         try {
            Minecraft minecraft = Minecraft.getInstance();
            if (minecraft != null && minecraft.level != null) {
               level = minecraft.level;
            }
         } catch (Throwable ignored) {
            level = null;
         }

         if (level == null && levelObj instanceof BlockAndTintGetter getter) {
            level = getter;
         }

         if (level == null) {
            CURRENT.remove();
         } else {
            CURRENT.set(new SodiumRgbBridge.Context(level, pos.immutable()));
         }
      } else {
         CURRENT.remove();
      }
   }

   public static void end() {
      CURRENT.remove();
   }

   public static int applyColor(int color) {
      return color;
   }

   public static int applyColorWithLight(int color, int packedLight) {
      return applyColorWithLight(color, packedLight, 0.5F, 0.5F, 0.5F, null);
   }

   public static int applyColorWithLight(int color, int packedLight, float x, float y, float z, Direction face) {
      SodiumRgbBridge.Context context = CURRENT.get();
      return context == null
         ? color
         : RGBRealLightEngine.applyColor(context.level, context.pos, stableLocal(x), stableLocal(y), stableLocal(z), color, packedLight);
   }

   public static int applyLight(int packedLight) {
      return applyLight(packedLight, 0.5F, 0.5F, 0.5F, null);
   }

   public static int applyLight(int packedLight, float x, float y, float z, Direction face) {
      SodiumRgbBridge.Context context = CURRENT.get();
      return context == null
         ? packedLight
         : RGBRealLightEngine.applyPackedLight(context.level, context.pos, stableLocal(x), stableLocal(y), stableLocal(z), packedLight);
   }

   private static float stableLocal(float value) {
      if (!Float.isFinite(value)) {
         return 0.5F;
      }

      float v = value;
      if (v < -0.001F || v > 1.001F) {
         v -= (float)Math.floor(v);
      }

      if (v < 0.0F) {
         return 0.0F;
      } else {
         return v > 1.0F ? 1.0F : v;
      }
   }

   private record Context(BlockAndTintGetter level, BlockPos pos) {
   }
}
