package com.rgbblocks.mixin.client;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.lighting.LevelLightEngine;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(LevelLightEngine.class)
public abstract class LevelLightEngineMixin {
   @Inject(method = "checkBlock", at = @At("TAIL"))
   private void rgbblocks$updateRgbStorageForLightPropertyChange(BlockPos pos, CallbackInfo ci) {
   }

   @Inject(method = "runLightUpdates", at = @At("TAIL"))
   private void rgbblocks$afterVanillaLightUpdates(CallbackInfoReturnable<Integer> cir) {
   }
}
