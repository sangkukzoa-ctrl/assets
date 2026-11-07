package com.rgbblocks.mixin.client;

import net.minecraft.client.renderer.LightmapRenderStateExtractor;
import net.minecraft.client.renderer.state.LightmapRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(LightmapRenderStateExtractor.class)
public abstract class LightmapRenderStateExtractorMixin {
   @Inject(method = "extract", at = @At("TAIL"))
   private void rgbblocks$doNotTintGlobalLightmap(LightmapRenderState state, float partialTicks, CallbackInfo ci) {
   }
}
