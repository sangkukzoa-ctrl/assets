package com.rgbblocks.mixin.client;

import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.client.lighting.RGBLightEngine;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ClientLevel.class)
public abstract class ClientLevelMixin {
   @Inject(method = "setBlock", at = @At("TAIL"))
   private void rgbblocks$updateRgbStorageAfterSetBlock(BlockPos pos, BlockState state, int flags, int recursionLeft, CallbackInfoReturnable<Boolean> cir) {
      if (Boolean.TRUE.equals(cir.getReturnValue()) && pos != null) {
         boolean lightRelevant = rgbblocks$isLightRelevant(state);
         boolean occluderRelevant = !lightRelevant && RGBLightEngine.shouldInvalidateForOccluder((ClientLevel)this, pos, state);
         if (lightRelevant || occluderRelevant) {
            if (rgbblocks$isRemoteMultiplayer()) {
               RGBRealLightEngine.settleAfterServerSync(pos);
            } else {
               RGBRealLightEngine.invalidateAround(pos);
            }
         }
      }
   }

   @Inject(method = "sendBlockUpdated", at = @At("TAIL"))
   private void rgbblocks$updateRgbStorageAfterBlockUpdate(BlockPos pos, BlockState oldState, BlockState newState, int flags, CallbackInfo ci) {
      if (pos != null) {
         boolean changed = oldState != newState && (oldState == null || !oldState.equals(newState));
         boolean relevant = rgbblocks$isLightRelevant(oldState) || rgbblocks$isLightRelevant(newState);
         boolean occluderRelevant = !relevant
            && (
               RGBLightEngine.shouldInvalidateForOccluder((ClientLevel)this, pos, oldState)
                  || RGBLightEngine.shouldInvalidateForOccluder((ClientLevel)this, pos, newState)
            );
         if (relevant || occluderRelevant) {
            if (rgbblocks$isRemoteMultiplayer()) {
               if (changed) {
                  RGBRealLightEngine.invalidateAround(pos);
               } else {
                  RGBRealLightEngine.settleAfterServerSync(pos);
               }
            } else {
               if (changed) {
                  RGBRealLightEngine.invalidateAround(pos);
               } else {
                  RGBRealLightEngine.settleAfterServerSync(pos);
               }
            }
         }
      }
   }

   @Inject(method = "onBlockEntityAdded", at = @At("TAIL"))
   private void rgbblocks$updateRgbStorageAfterBlockEntityAdded(BlockEntity blockEntity, CallbackInfo ci) {
      if (blockEntity != null) {
         try {
            RGBCnbReloadWakeup.onBlockEntityAdded(blockEntity);
         } catch (Throwable var7) {
         }

         BlockPos pos = blockEntity.getBlockPos();
         BlockState state = null;

         try {
            state = blockEntity.getBlockState();
         } catch (Throwable var6) {
         }

         if (rgbblocks$isLightRelevant(state)) {
            if (rgbblocks$isRemoteMultiplayer()) {
               RGBRealLightEngine.settleAfterServerSync(pos);
            } else {
               RGBRealLightEngine.invalidateAround(pos);
            }
         }
      }
   }

   private static boolean rgbblocks$isRemoteMultiplayer() {
      try {
         Minecraft minecraft = Minecraft.getInstance();
         return minecraft != null
            && minecraft.level != null
            && minecraft.getCurrentServer() != null
            && !minecraft.hasSingleplayerServer()
            && !minecraft.isLocalServer();
      } catch (Throwable ignored) {
         return false;
      }
   }

   private static boolean rgbblocks$isLightRelevant(BlockState state) {
      if (state == null) {
         return false;
      }

      try {
         if (state.getLightEmission() > 0) {
            return true;
         }
      } catch (Throwable var2) {
      }

      try {
         String id = String.valueOf(BuiltInRegistries.BLOCK.getKey(state.getBlock()));
         return id.contains("rgbblocks:") || id.contains("chiselsandbits:");
      } catch (Throwable ignored) {
         return false;
      }
   }
}
