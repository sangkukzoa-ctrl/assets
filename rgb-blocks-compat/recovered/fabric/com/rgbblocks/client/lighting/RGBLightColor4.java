package com.rgbblocks.client.lighting;

public record RGBLightColor4(int r, int g, int b) {
   public static final RGBLightColor4 BLACK = new RGBLightColor4(0, 0, 0);

   public RGBLightColor4 {
      r = clamp4(r);
      g = clamp4(g);
      b = clamp4(b);
   }

   public boolean active() {
      return this.r > 0 || this.g > 0 || this.b > 0;
   }

   public int maxChannel() {
      return Math.max(this.r, Math.max(this.g, this.b));
   }

   public RGBLightColor4 max(RGBLightColor4 other) {
      return other == null ? this : new RGBLightColor4(Math.max(this.r, other.r), Math.max(this.g, other.g), Math.max(this.b, other.b));
   }

   public RGBLightColor4 attenuate(int amount) {
      int a = Math.max(1, amount);
      return new RGBLightColor4(Math.max(0, this.r - a), Math.max(0, this.g - a), Math.max(0, this.b - a));
   }

   public static RGBLightColor4 fromRgbAndEmission(int rgb, int emission) {
      int e = clamp4(emission);
      if (e > 0 && rgb >= 0) {
         int rr = rgb >>> 16 & 0xFF;
         int gg = rgb >>> 8 & 0xFF;
         int bb = rgb & 0xFF;
         int max = Math.max(rr, Math.max(gg, bb));
         return max <= 0 ? BLACK : new RGBLightColor4(Math.round((float)rr / max * e), Math.round((float)gg / max * e), Math.round((float)bb / max * e));
      } else {
         return BLACK;
      }
   }

   public static int clamp4(int v) {
      return v < 0 ? 0 : Math.min(v, 15);
   }
}
