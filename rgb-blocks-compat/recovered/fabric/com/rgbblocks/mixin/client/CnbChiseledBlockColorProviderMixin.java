package com.rgbblocks.mixin.client;

import it.unimi.dsi.fastutil.ints.IntList;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mod.chiselsandbits.client.colors.ChiseledBlockColorProvider", remap = false)
public abstract class CnbChiseledBlockColorProviderMixin {
   @Inject(
      method = "collect(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/client/renderer/block/BlockAndTintGetter;Lnet/minecraft/core/BlockPos;Lit/unimi/dsi/fastutil/ints/IntList;)V",
      at = @At("HEAD"),
      cancellable = true,
      require = 0,
      remap = false
   )
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockColorProvider#collect")
   private void rgbblocks$skipThreadUnsafeSodiumDynamicTint(
      BlockState blockState, BlockAndTintGetter blockAndTintGetter, BlockPos blockPos, IntList intList, CallbackInfo ci
   ) {
      if (rgbblocks$mustSkip(blockAndTintGetter)) {
         try {
            intList.clear();
         } catch (Throwable var7) {
         }

         ci.cancel();
      }
   }

   private static boolean rgbblocks$mustSkip(BlockAndTintGetter getter) {
      if (getter == null) {
         return false;
      }

      try {
         String name = getter.getClass().getName();
         if (name.equals("net.caffeinemc.mods.sodium.client.world.LevelSlice") || name.startsWith("net.caffeinemc.mods.sodium.client.world.")) {
            return true;
         }
      } catch (Throwable var3) {
      }

      try {
         Minecraft minecraft = Minecraft.getInstance();
         return minecraft != null && !minecraft.isSameThread();
      } catch (Throwable ignored) {
         return false;
      }
   }
}
