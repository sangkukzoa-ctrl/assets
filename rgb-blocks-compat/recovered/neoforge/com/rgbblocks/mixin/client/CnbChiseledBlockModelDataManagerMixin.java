package com.rgbblocks.mixin.client;

import com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mod.chiselsandbits.client.model.data.ChiseledBlockModelDataManager", remap = false)
public abstract class CnbChiseledBlockModelDataManagerMixin {
   @Inject(
      method = "updateModelData(Lmod/chiselsandbits/block/entities/ChiseledBlockEntity;Ljava/lang/Runnable;Z)V",
      at = @At("HEAD"),
      cancellable = true,
      require = 0,
      remap = false
   )
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockModelDataManager#updateModelData")
   private void rgbblocks$debounceRapidServerMicrobitModelBake(@Coerce Object tileEntity, Runnable onCompleteCallback, boolean force, CallbackInfo ci) {
      try {
         if (RGBCnbGeometryBakeDebouncer.shouldDelayModelBake(tileEntity, force)) {
            ci.cancel();
         }
      } catch (Throwable var6) {
      }
   }
}
