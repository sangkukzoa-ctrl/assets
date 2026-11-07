package com.rgbblocks.mixin.client;

import com.rgbblocks.client.lighting.SodiumQuadDataAccessor;
import com.rgbblocks.client.lighting.SodiumRgbBridge;
import net.minecraft.core.Direction;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "net.caffeinemc.mods.sodium.client.render.model.MutableQuadViewImpl", remap = false)
public abstract class SodiumMutableQuadViewImplMixin {
   private static final int RGBBLOCKS_VERTEX_STRIDE = 8;
   private static final int RGBBLOCKS_VERTEX_X = 4;
   private static final int RGBBLOCKS_VERTEX_Y = 5;
   private static final int RGBBLOCKS_VERTEX_Z = 6;
   private static final int RGBBLOCKS_VERTEX_COLOR = 7;
   private static final int RGBBLOCKS_VERTEX_LIGHTMAP = 10;

   @Inject(method = "setColor(II)Lnet/caffeinemc/mods/sodium/client/render/model/MutableQuadViewImpl;", at = @At("TAIL"), require = 0, remap = false)
   @Dynamic("Sodium 0.8.11 MutableQuadViewImpl#setColor")
   private void rgbblocks$doNotPaintAlbedo(int vertexIndex, int color, CallbackInfoReturnable<Object> cir) {
   }

   @Inject(method = "setLight(II)Lnet/caffeinemc/mods/sodium/client/render/model/MutableQuadViewImpl;", at = @At("TAIL"), require = 0, remap = false)
   @Dynamic("Sodium 0.8.11 MutableQuadViewImpl#setLight")
   private void rgbblocks$applyRgbLightField(int vertexIndex, int lightmap, CallbackInfoReturnable<Object> cir) {
      try {
         if (vertexIndex < 0 || vertexIndex > 3) {
            return;
         }

         SodiumQuadDataAccessor accessor = (SodiumQuadDataAccessor)this;
         int[] data = accessor.rgbblocks$getData();
         if (data == null) {
            return;
         }

         int base = accessor.rgbblocks$getBaseIndex();
         int vertexBase = base + vertexIndex * 8;
         int lightIndex = vertexBase + 10;
         int colorIndex = vertexBase + 7;
         int xIndex = vertexBase + 4;
         int yIndex = vertexBase + 5;
         int zIndex = vertexBase + 6;
         if (lightIndex < 0
            || lightIndex >= data.length
            || colorIndex < 0
            || colorIndex >= data.length
            || xIndex < 0
            || yIndex < 0
            || zIndex < 0
            || xIndex >= data.length
            || yIndex >= data.length
            || zIndex >= data.length) {
            return;
         }

         float x = Float.intBitsToFloat(data[xIndex]);
         float y = Float.intBitsToFloat(data[yIndex]);
         float z = Float.intBitsToFloat(data[zIndex]);
         Direction face = null;
         int newLight = SodiumRgbBridge.applyLight(data[lightIndex], x, y, z, face);
         data[lightIndex] = newLight;
         data[colorIndex] = SodiumRgbBridge.applyColorWithLight(data[colorIndex], newLight, x, y, z, face);
      } catch (Throwable var18) {
      }
   }
}
