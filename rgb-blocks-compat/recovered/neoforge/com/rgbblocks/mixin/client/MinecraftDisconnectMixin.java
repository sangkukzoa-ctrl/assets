package com.rgbblocks.mixin.client;

import com.rgbblocks.client.cnb.RGBCnbGeometryBakeDebouncer;
import com.rgbblocks.client.cnb.RGBCnbReloadWakeup;
import com.rgbblocks.client.lighting.RGBRealLightEngine;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Minecraft.class)
public abstract class MinecraftDisconnectMixin {
   @Inject(method = "tick", at = @At("TAIL"))
   private void rgbblocks$processCnbDeferredRefreshes(CallbackInfo ci) {
      RGBRealLightEngine.processClientTick();
   }

   @Inject(method = "disconnectWithSavingScreen", at = @At("HEAD"))
   private void rgbblocks$beforeDisconnectWithSavingScreen(CallbackInfo ci) {
      RGBRealLightEngine.onClientDisconnect();
      RGBCnbGeometryBakeDebouncer.reset();
      RGBCnbReloadWakeup.reset();
   }

   @Inject(method = "disconnectWithProgressScreen()V", at = @At("HEAD"))
   private void rgbblocks$beforeDisconnectWithProgressScreen(CallbackInfo ci) {
      RGBRealLightEngine.onClientDisconnect();
      RGBCnbGeometryBakeDebouncer.reset();
      RGBCnbReloadWakeup.reset();
   }

   @Inject(method = "disconnect(Lnet/minecraft/client/gui/screens/Screen;ZZ)V", at = @At("HEAD"))
   private void rgbblocks$beforeDisconnect(Screen screen, boolean bl, boolean bl2, CallbackInfo ci) {
      RGBRealLightEngine.onClientDisconnect();
      RGBCnbGeometryBakeDebouncer.reset();
      RGBCnbReloadWakeup.reset();
   }

   @Inject(method = "disconnectFromWorld", at = @At("HEAD"))
   private void rgbblocks$beforeDisconnectFromWorld(Component component, CallbackInfo ci) {
      RGBRealLightEngine.onClientDisconnect();
      RGBCnbGeometryBakeDebouncer.reset();
      RGBCnbReloadWakeup.reset();
   }
}
