package com.rgbblocks.mixin.client;

import com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Dynamic;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mod.chiselsandbits.block.entities.ChiseledBlockEntity", remap = false)
public abstract class CnbChiseledBlockEntityMixin {
   @Inject(method = "setLevel(Lnet/minecraft/world/level/Level;)V", at = @At("TAIL"), require = 0, remap = false)
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockEntity#setLevel")
   private void rgbblocks$refreshCnbSourceAfterLevelAttach(Level level, CallbackInfo ci) {
      try {
         RGBRealLightEngine.refreshCnbBlockEntity(this);
      } catch (Throwable var4) {
      }
   }

   @Inject(method = "receivePayload(Lmod/chiselsandbits/block/entities/ChiseledBlockEntity$Payload;)V", at = @At("HEAD"), require = 0, remap = false)
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockEntity#receivePayload")
   private void rgbblocks$markLivePayloadBeforeModelUpdate(CallbackInfo ci) {
      try {
         RGBCnbGeometryBakeDebouncer.markPayloadModelUpdate(this);
      } catch (Throwable var3) {
      }
   }

   @Inject(method = "receivePayload(Lmod/chiselsandbits/block/entities/ChiseledBlockEntity$Payload;)V", at = @At("TAIL"), require = 0, remap = false)
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockEntity#receivePayload")
   private void rgbblocks$refreshCnbSourceAfterPayload(CallbackInfo ci) {
      try {
         RGBRealLightEngine.refreshCnbBlockEntity(this);
      } catch (Throwable var3) {
      }
   }

   @Inject(method = "setChanged()V", at = @At("TAIL"), require = 0, remap = false)
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockEntity#setChanged")
   private void rgbblocks$refreshCnbSourceAfterChanged(CallbackInfo ci) {
      try {
         RGBRealLightEngine.refreshCnbBlockEntity(this);
      } catch (Throwable var3) {
      }
   }

   @Inject(method = "setRemoved()V", at = @At("HEAD"), require = 0, remap = false)
   @Dynamic("Chisels & Bits 26.1.2 ChiseledBlockEntity#setRemoved")
   private void rgbblocks$removeCnbSourceOnRemoved(CallbackInfo ci) {
      try {
         RGBRealLightEngine.removeCnbBlockEntity(this);
      } catch (Throwable var3) {
      }
   }
}
