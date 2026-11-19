package com.twobornot.imageorder;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ImageDecoder;
import android.graphics.Matrix;
import android.os.Build;
import java.io.File;

/** Thumbnail decoding only: source images are never written, transformed or re-encoded. */
final class ThumbnailDecoder {
    private ThumbnailDecoder() {}
    static Bitmap decode(File file,int maxDim,int maxPixels) throws Exception {
        BitmapFactory.Options bound=new BitmapFactory.Options();bound.inJustDecodeBounds=true;
        BitmapFactory.decodeFile(file.getAbsolutePath(),bound);
        if(bound.outWidth<=0 || bound.outHeight<=0) return null;
        int sample=1;
        while(Math.max(bound.outWidth/sample,bound.outHeight/sample)>maxDim ||
            ((long)(bound.outWidth/sample)*(bound.outHeight/sample))>maxPixels) sample*=2;
        BitmapFactory.Options opt=new BitmapFactory.Options();opt.inSampleSize=sample;
        Bitmap bitmap=BitmapFactory.decodeFile(file.getAbsolutePath(),opt);
        if(bitmap==null) return null;
        // EXIF orientation is applied using Android's built-in ImageDecoder when available.
        if(Build.VERSION.SDK_INT>=28) {
            try {
                ImageDecoder.Source s=ImageDecoder.createSource(file);
                final int scale=sample;
                Bitmap oriented=ImageDecoder.decodeBitmap(s,(d,info,source)->{
                    d.setTargetSampleSize(scale);
                    d.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);
                });
                if(oriented!=null) { bitmap.recycle();return oriented; }
            } catch(Exception ignored) { /* BitmapFactory result still usable */ }
        }
        int orientation=orientation(file);
        Matrix matrix=new Matrix();
        switch(orientation) {
            case 2:matrix.setScale(-1,1);break;
            case 3:matrix.setRotate(180);break;
            case 4:matrix.setScale(1,-1);break;
            case 5:matrix.setRotate(90);matrix.postScale(-1,1);break;
            case 6:matrix.setRotate(90);break;
            case 7:matrix.setRotate(270);matrix.postScale(-1,1);break;
            case 8:matrix.setRotate(270);break;
            default:return bitmap;
        }
        Bitmap rotated=Bitmap.createBitmap(bitmap,0,0,bitmap.getWidth(),bitmap.getHeight(),matrix,true);
        if(rotated!=bitmap)bitmap.recycle();
        return rotated;
    }
    private static int orientation(File file) {
        try {
            android.media.ExifInterface exif=new android.media.ExifInterface(file.getAbsolutePath());
            return exif.getAttributeInt(android.media.ExifInterface.TAG_ORIENTATION,1);
        } catch(Exception ignored) { return 1; }
    }
}
