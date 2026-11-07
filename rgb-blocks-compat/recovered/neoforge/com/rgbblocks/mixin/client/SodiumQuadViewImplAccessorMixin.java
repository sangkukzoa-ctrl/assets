package com.rgbblocks.mixin.client;

import com.rgbblocks.client.lighting.SodiumQuadDataAccessor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;

@Pseudo
@Mixin(targets = "net.caffeinemc.mods.sodium.client.render.model.QuadViewImpl", remap = false)
public abstract class SodiumQuadViewImplAccessorMixin implements SodiumQuadDataAccessor {
   @Shadow(remap = false)
   public int[] data;
   @Shadow(remap = false)
   public int baseIndex;

   @Override
   public int[] rgbblocks$getData() {
      return this.data;
   }

   @Override
   public int rgbblocks$getBaseIndex() {
      return this.baseIndex;
   }
}
