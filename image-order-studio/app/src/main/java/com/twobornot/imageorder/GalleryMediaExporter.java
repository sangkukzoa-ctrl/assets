package com.twobornot.imageorder;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;

/** Publish deliberately numbered images into a normal, device-visible Gallery album.
 * This avoids requiring the destination website to offer a custom picker choice.
 */
final class GalleryMediaExporter {
    private GalleryMediaExporter() {}
    static final String ALBUM = "Image Order Studio";
    static String imageMime(File f) {
        String name=f.getName().toLowerCase(Locale.ROOT);
        return name.endsWith(".png")?"image/png":"image/jpeg";
    }
    static String mediaName(String batch,int index,int size,File file) {
        return MediaNaming.galleryFileName(batch,index,size,imageMime(file).equals("image/png"));
    }
    static List<Uri> publish(Context ctx,List<File> files) throws IOException {
        if(files.isEmpty())throw new IOException("No images to publish");
        ContentResolver cr=ctx.getContentResolver();
        List<Uri> published=new ArrayList<>();
        String batch=new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.ROOT).format(new Date());
        long stamp=System.currentTimeMillis();
        try {
            for(int i=0;i<files.size();i++) {
                File file=files.get(i);
                String mime=imageMime(file);
                ContentValues values=new ContentValues();
                values.put(MediaStore.MediaColumns.DISPLAY_NAME,mediaName(batch,i,files.size(),file));
                values.put(MediaStore.MediaColumns.MIME_TYPE,mime);
                // Most gallery apps show newest first; rank #1 is given the highest timestamp.
                values.put(MediaStore.Images.Media.DATE_TAKEN,stamp-i*1000L);
                if(Build.VERSION.SDK_INT>=29) {
                    values.put(MediaStore.MediaColumns.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/"+ALBUM);
                    values.put(MediaStore.MediaColumns.IS_PENDING,1);
                }
                Uri collection=Build.VERSION.SDK_INT>=29?
                    MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY):
                    MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
                Uri uri=cr.insert(collection,values);
                if(uri==null)throw new IOException("Gallery refused new image at #"+(i+1));
                try {
                    try(InputStream in=new FileInputStream(file);OutputStream out=cr.openOutputStream(uri,"w")) {
                        if(out==null)throw new IOException("Gallery output stream unavailable");
                        byte[] bytes=new byte[65536];int n;
                        while((n=in.read(bytes))!=-1)out.write(bytes,0,n);
                    }
                    if(Build.VERSION.SDK_INT>=29) {
                        ContentValues ready=new ContentValues();ready.put(MediaStore.MediaColumns.IS_PENDING,0);
                        if(cr.update(uri,ready,null,null)!=1)throw new IOException("Gallery could not finalize image");
                    }
                    published.add(uri);
                } catch(Exception e) { cr.delete(uri,null,null);throw e; }
            }
            return published;
        } catch(Exception failure) {
            // Avoid a half-published batch being mistaken for a complete upload set.
            for(Uri uri:published)try{cr.delete(uri,null,null);}catch(Exception ignored){}
            if(failure instanceof IOException)throw (IOException)failure;
            throw new IOException("Failed publishing images to Gallery",failure);
        }
    }
}
