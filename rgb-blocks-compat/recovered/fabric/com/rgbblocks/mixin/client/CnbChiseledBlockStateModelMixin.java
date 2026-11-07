package com.rgbblocks.mixin.client;

import com.rgbblocks.client.lighting.RGBRealLightEngine;
import java.util.List;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mod.chiselsandbits.client.model.block.ChiseledBlockStateModel", remap = false)
public abstract class CnbChiseledBlockStateModelMixin {
   @Inject(
      method = "collectParts(Lnet/minecraft/client/renderer/block/BlockAndTintGetter;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/util/RandomSource;Ljava/util/List;)V",
      at = @At("TAIL"),
      require = 0,
      remap = false
   )
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockStateModel#collectParts")
   private void rgbblocks$captureCnbPartSources(BlockAndTintGetter level, BlockPos pos, BlockState state, RandomSource random, List<?> parts, CallbackInfo ci) {
      try {
         RGBRealLightEngine.registerCnbModelPartSources(pos, parts);
      } catch (Throwable var8) {
      }
   }
}
