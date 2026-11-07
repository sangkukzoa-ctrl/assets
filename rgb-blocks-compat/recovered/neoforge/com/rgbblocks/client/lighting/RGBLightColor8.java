package com.rgbblocks.client.lighting;

public record RGBLightColor8(int r, int g, int b) {
   public static final RGBLightColor8 BLACK = new RGBLightColor8(0, 0, 0);

   public RGBLightColor8 {
      r = clamp8(r);
      g = clamp8(g);
      b = clamp8(b);
   }

   public boolean active() {
      return this.r > 0 || this.g > 0 || this.b > 0;
   }

   public static RGBLightColor8 from4(RGBLightColor4 c) {
      return c != null && c.active() ? new RGBLightColor8(c.r() * 17, c.g() * 17, c.b() * 17) : BLACK;
   }

   public static RGBLightColor8 lerp(RGBLightColor8 a, RGBLightColor8 b, double t) {
      double u = Math.max(0.0, Math.min(1.0, t));
      return new RGBLightColor8((int)Math.round(a.r + (b.r - a.r) * u), (int)Math.round(a.g + (b.g - a.g) * u), (int)Math.round(a.b + (b.b - a.b) * u));
   }

   private static int clamp8(int v) {
      return v < 0 ? 0 : Math.min(v, 255);
   }
}
