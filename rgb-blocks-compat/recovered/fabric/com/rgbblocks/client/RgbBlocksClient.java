package com.rgbblocks.client;

import com.rgbblocks.client.config.RGBClientConfig;
import com.rgbblocks.runtime.RGBRuntime;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

public final class RgbBlocksClient implements ClientModInitializer {
   public void onInitializeClient() {
      RGBClientConfig.initialize();
      ClientPlayNetworking.registerGlobalReceiver(RGBRuntime.StatePayload.TYPE, (payload, context) -> RGBRuntime.acceptState(payload));
      ClientPlayNetworking.registerGlobalReceiver(RGBRuntime.BakePayload.TYPE, (payload, context) -> RGBRuntime.acceptBake(payload));
   }
}
