package com.rgbblocks.mixin.client;

import java.util.Map;
import java.util.Map.Entry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "mod.chiselsandbits.block.entities.ChiseledBlockEntity$MutableStatistics", remap = false)
public abstract class CnbMutableStatisticsLightEmissionMixin {
   @Shadow(remap = false)
   @Final
   private Map<?, Integer> countMap;

   @Inject(method = "getLightEmissionFactor()F", at = @At("HEAD"), cancellable = true, require = 0, remap = false)
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockEntity.MutableStatistics#getLightEmissionFactor")
   private void rgbblocks$disableVanillaEmissionForRgbBits(CallbackInfoReturnable<Float> cir) {
      if (this.rgbblocks$containsRgbGlowBit()) {
         cir.setReturnValue(0.0F);
      }
   }

   private boolean rgbblocks$containsRgbGlowBit() {
      if (this.countMap != null && !this.countMap.isEmpty()) {
         for (Entry<?, Integer> entry : this.countMap.entrySet()) {
            Integer count = entry.getValue();
            if (count != null && count > 0) {
               Object information = entry.getKey();
               if (information != null) {
                  try {
                     if (information.getClass().getMethod("blockState").invoke(information) instanceof BlockState state && rgbblocks$isRgbGlowState(state)) {
                        return true;
                     }
                  } catch (Throwable var7) {
                  }
               }
            }
         }

         return false;
      } else {
         return false;
      }
   }

   private static boolean rgbblocks$isRgbGlowState(BlockState state) {
      if (state == null) {
         return false;
      }

      try {
         Identifier id = BuiltInRegistries.BLOCK.getKey(state.getBlock());
         if (id != null && "rgbblocks".equals(id.getNamespace())) {
            String path = id.getPath();
            return path.startsWith("rgb_") && path.endsWith("_glow");
         } else {
            return false;
         }
      } catch (Throwable ignored) {
         return false;
      }
   }
}
