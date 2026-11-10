package com.twobornot.imageorder;

import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.*;
import android.os.Build;
import android.provider.DocumentsContract;
import android.net.Uri;
import android.content.ContentResolver;
import java.io.*;
import java.util.*;

/** Exports rendered evidence of order; sites cannot remove sequence labels by sorting files. */
final class ImageExporter {
    private static final int MAX_DIM=4096;
    private final Context ctx;
    ImageExporter(Context c) {ctx=c;}
    private File newExportDirectory() throws IOException {
        File root=new File(ctx.getCacheDir(),"exports");
        if(!root.exists() && !root.mkdirs()) throw new IOException("Could not create export root");
        File dir=new File(root,"batch-"+UUID.randomUUID());
        if(!dir.mkdirs()) throw new IOException("Could not create export batch");
        return dir;
    }
    List<File> renderNumbered(GalleryStore store,List<String> ids,boolean compact) throws Exception {
        if(ids.isEmpty()) throw new IllegalArgumentException("No selected images");
        File folder=newExportDirectory(); ArrayList<File> files=new ArrayList<>();
        for(int i=0;i<ids.size();i++) {
            GalleryStore.Item item=store.find(ids.get(i));
            if(item==null) throw new IOException("Missing image at position "+(i+1));
            Bitmap source=decode(store.source(item),compact?2560:MAX_DIM,compact?8_000_000:16_000_000);
            if(source==null) throw new IOException("Unsupported image format: "+item.name);
            try {
                int width=Math.max(700,source.getWidth());
                int header=170;
                Bitmap image=Bitmap.createBitmap(width,source.getHeight()+header,Bitmap.Config.ARGB_8888);
                try {
                    Canvas c=new Canvas(image); c.drawColor(Color.WHITE);
                    drawHeader(c,width,header,i+1,ids.size(),item.name);
                    c.drawBitmap(source,(width-source.getWidth())/2f,header,null);
                    File output=new File(folder,String.format(Locale.ROOT,"%04d_of_%04d_%s.%s",
                        i+1,ids.size(),safeName(item.name),compact?"jpg":"png"));
                    if(compact)writeJpeg(image,output);else writePng(image,output);
                    files.add(output);
                } finally { image.recycle(); }
            } finally { source.recycle(); }
        }
        return files;
    }
    File renderCombined(GalleryStore store,List<String> ids) throws Exception {
        if(ids.isEmpty()) throw new IllegalArgumentException("No selected images");
        if(ids.size()>12) throw new IllegalArgumentException("Combined mode supports up to 12 images. Use numbered images for larger batches.");
        final int width=900, header=145, maxHeight=14000;
        ArrayList<Integer> heights=new ArrayList<>();
        int total=0;
        // Measure first, without keeping a single decoded photo in memory.
        for(String id:ids) {
            GalleryStore.Item item=store.find(id);
            if(item==null) throw new IOException("Missing image");
            BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;
            BitmapFactory.decodeFile(store.source(item).getPath(),bounds);
            if(bounds.outWidth<=0||bounds.outHeight<=0) throw new IOException("Unsupported image format: "+item.name);
            int logicalWidth=bounds.outWidth, logicalHeight=bounds.outHeight;
            int orientation=orientation(store.source(item));
            if(orientation==6||orientation==8||orientation==5||orientation==7) {
                logicalWidth=bounds.outHeight;logicalHeight=bounds.outWidth;
            }
            int h=Math.max(1,(int)Math.ceil((double)logicalHeight*width/logicalWidth));
            total+=header+h;heights.add(h);
            if(total>maxHeight) throw new IllegalArgumentException("Combined image would be too tall. Use numbered export.");
        }
        Bitmap combined=Bitmap.createBitmap(width,total,Bitmap.Config.ARGB_8888);
        try {
            Canvas c=new Canvas(combined);c.drawColor(Color.WHITE);
            Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
            int y=0;
            for(int i=0;i<ids.size();i++) {
                GalleryStore.Item item=store.find(ids.get(i));
                Bitmap b=decode(store.source(item),2048,5_000_000);
                if(b==null) throw new IOException("Unsupported image format: "+item.name);
                try {
                    c.save();c.translate(0,y);
                    drawHeader(c,width,header,i+1,ids.size(),item.name);
                    c.drawBitmap(b,null,new Rect(0,header,width,header+heights.get(i)),paint);
                    c.restore();y+=header+heights.get(i);
                } finally {b.recycle();}
            }
            File folder=newExportDirectory();File out=new File(folder,"ORDERED_"+ids.size()+"_IMAGES.png");
            writePng(combined,out);return out;
        } finally {combined.recycle();}
    }
    private static String safeName(String name) {
        String s=name.replaceFirst("\\.[^.]*$","").replaceAll("[^\\p{L}\\p{N}._-]+","_");
        if(s.length()>42) s=s.substring(0,42);
        return s.isEmpty()?"image":s;
    }
    private static void drawHeader(Canvas c,int width,int height,int index,int count,String name) {
        Paint bg=new Paint();bg.setColor(Color.rgb(24,32,45));c.drawRect(0,0,width,height,bg);
        Paint t=new Paint(Paint.ANTI_ALIAS_FLAG);t.setColor(Color.WHITE);t.setTypeface(Typeface.create("sans-serif",Typeface.BOLD));
        t.setTextSize(54);c.drawText(String.format(Locale.ROOT,"ORDER  %04d / %04d",index,count),28,70,t);
        t.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));t.setTextSize(27);
        String safe=name.replaceAll("[\\r\\n]"," ");
        while(t.measureText(safe)>width-55 && safe.length()>3) safe=safe.substring(0,safe.length()-2);
        c.drawText(safe,29,Math.min(height-22,127),t);
    }
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
    private static void writePng(Bitmap b,File out) throws IOException {
        try(FileOutputStream fos=new FileOutputStream(out)) {
            if(!b.compress(Bitmap.CompressFormat.PNG,100,fos)) throw new IOException("PNG encoder failed");
        }
    }
    private static void writeJpeg(Bitmap b,File out) throws IOException {
        try(FileOutputStream fos=new FileOutputStream(out)) {
            if(!b.compress(Bitmap.CompressFormat.JPEG,90,fos)) throw new IOException("JPG encoder failed");
        }
    }
    void saveToTree(Uri tree,List<File> files) throws Exception {
        ContentResolver cr=ctx.getContentResolver();
        Uri parent=DocumentsContract.buildDocumentUriUsingTree(tree,DocumentsContract.getTreeDocumentId(tree));
        for(File source:files) {
            Uri destination=DocumentsContract.createDocument(cr,parent,source.getName().endsWith(".jpg")?"image/jpeg":"image/png",source.getName());
            if(destination==null) throw new IOException("Document provider could not create "+source.getName());
            try(InputStream in=new FileInputStream(source);OutputStream out=cr.openOutputStream(destination,"w")) {
                if(out==null) throw new IOException("Cannot write to selected folder");
                byte[] buffer=new byte[65536];int n;
                while((n=in.read(buffer))!=-1) out.write(buffer,0,n);
            }
        }
    }
}
