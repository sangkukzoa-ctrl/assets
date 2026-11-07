package com.rgbblocks.mixin;

import java.util.function.Supplier;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Pseudo
@Mixin(targets = "mod.chiselsandbits.block.ChiseledBlock", remap = false)
public abstract class CnbChiseledBlockPickBlockServerConfigMixin {
   @Redirect(
      method = "getCloneItemStack(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/phys/HitResult;Lnet/minecraft/world/level/LevelReader;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/entity/player/Player;)Lnet/minecraft/world/item/ItemStack;",
      at = @At(value = "INVOKE", target = "Ljava/util/function/Supplier;get()Ljava/lang/Object;"),
      require = 0,
      remap = false
   )
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlock#getCloneItemStack client config read")
   private Object rgbblocks$safelyReadInvertPickBlockBehaviour(Supplier<?> supplier) {
      try {
         Object value = supplier.get();
         return value instanceof Boolean ? value : Boolean.FALSE;
      } catch (IllegalStateException exception) {
         return Boolean.FALSE;
      }
   }
}
