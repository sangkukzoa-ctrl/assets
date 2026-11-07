package com.rgbblocks.client.lighting;

final class RGBLightSection {
   static final int DATA_LENGTH = 12288;
   private final byte[] data = new byte[12288];
   private int activeCells;

   RGBLightColor4 get(int x, int y, int z) {
      int i = index(x, y, z);
      return new RGBLightColor4(this.data[i] & 15, this.data[i + 1] & 15, this.data[i + 2] & 15);
   }

   boolean setMax(int x, int y, int z, RGBLightColor4 c) {
      int i = index(x, y, z);
      boolean wasActive = this.activeAt(i);
      int nr = Math.max(this.data[i] & 15, c.r());
      int ng = Math.max(this.data[i + 1] & 15, c.g());
      int nb = Math.max(this.data[i + 2] & 15, c.b());
      if (nr == (this.data[i] & 15) && ng == (this.data[i + 1] & 15) && nb == (this.data[i + 2] & 15)) {
         return false;
      }

      this.data[i] = (byte)nr;
      this.data[i + 1] = (byte)ng;
      this.data[i + 2] = (byte)nb;
      this.updateActiveCount(wasActive, this.activeAt(i));
      return true;
   }

   void set(int x, int y, int z, RGBLightColor4 c) {
      int i = index(x, y, z);
      boolean wasActive = this.activeAt(i);
      this.data[i] = (byte)c.r();
      this.data[i + 1] = (byte)c.g();
      this.data[i + 2] = (byte)c.b();
      this.updateActiveCount(wasActive, this.activeAt(i));
   }

   boolean isEmpty() {
      return this.activeCells <= 0;
   }

   byte[] copyData() {
      return (byte[])this.data.clone();
   }

   boolean loadData(byte[] source) {
      if (source != null && source.length == 12288) {
         System.arraycopy(source, 0, this.data, 0, 12288);
         this.activeCells = 0;

         for (int i = 0; i < 12288; i += 3) {
            if (this.activeAt(i)) {
               this.activeCells++;
            }
         }

         return true;
      } else {
         return false;
      }
   }

   private boolean activeAt(int index) {
      return (this.data[index] & 15) != 0 || (this.data[index + 1] & 15) != 0 || (this.data[index + 2] & 15) != 0;
   }

   private void updateActiveCount(boolean wasActive, boolean isActive) {
      if (wasActive != isActive) {
         this.activeCells += isActive ? 1 : -1;
      }
   }

   private static int index(int x, int y, int z) {
      return ((y & 15) << 8 | (z & 15) << 4 | x & 15) * 3;
   }
}
