package com.rgbblocks.mixin.client;

import com.mojang.blaze3d.vertex.QuadInstance;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.renderer.block.BlockQuadOutput;
import net.minecraft.client.renderer.block.ModelBlockRenderer;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ModelBlockRenderer.class)
public abstract class ModelBlockRendererMixin {
   @Shadow
   private QuadInstance quadInstance;

   @Inject(method = "putQuadWithTint", at = @At("HEAD"))
   private void rgbblocks$applyRgbPackedLight(
      BlockQuadOutput output,
      float red,
      float green,
      float blue,
      BlockAndTintGetter level,
      BlockState state,
      BlockPos pos,
      BakedQuad bakedQuad,
      CallbackInfo ci
   ) {
      try {
         if (this.quadInstance == null) {
            return;
         }

         RGBRealLightEngine.applyToVanillaQuad(level, pos, state, bakedQuad, this.quadInstance);
      } catch (Throwable var11) {
      }
   }
}
