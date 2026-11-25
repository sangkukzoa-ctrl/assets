package com.twobornot.imageorder;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;

/** Debug-only original fixtures; scoped media on Q+, public media paths on Oreo/Pie. */
final class TestMediaFixture {
    private TestMediaFixture(){}
    static Uri insert(Context context,String name,String mime,String relative,byte[] bytes) throws IOException {
        ContentResolver cr=context.getContentResolver();
        ContentValues values=new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME,name);
        values.put(MediaStore.Images.Media.MIME_TYPE,mime);
        if(Build.VERSION.SDK_INT>=29){
            values.put(MediaStore.Images.Media.RELATIVE_PATH,relative);
            values.put(MediaStore.Images.Media.IS_PENDING,1);
            Uri uri=cr.insert(MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY),values);
            if(uri==null)throw new IOException("MediaStore insert failed");
            boolean published=false;
            try{
                try(OutputStream out=cr.openOutputStream(uri,"w")){
                    if(out==null)throw new IOException("MediaStore stream missing");
                    out.write(bytes);
                }
                ContentValues ready=new ContentValues();ready.put(MediaStore.Images.Media.IS_PENDING,0);
                if(cr.update(uri,ready,null,null)!=1)throw new IOException("MediaStore publish failed");
                published=true;return uri;
            }finally{if(!published)cr.delete(uri,null,null);}
        }
        File directory=new File(Environment.getExternalStorageDirectory(),relative);
        if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create test album "+directory);
        File file=new File(directory,name);
        if(!file.createNewFile())throw new IOException("Test fixture already exists "+file);
        boolean inserted=false;
        try{
            try(FileOutputStream out=new FileOutputStream(file)){out.write(bytes);}
            values.put(MediaStore.Images.Media.DATA,file.getAbsolutePath());
            values.put(MediaStore.Images.Media.SIZE,bytes.length);
            values.put(MediaStore.Images.Media.DATE_ADDED,System.currentTimeMillis()/1000);
            values.put(MediaStore.Images.Media.DATE_MODIFIED,file.lastModified()/1000);
            values.put(MediaStore.Images.Media.TITLE,name);
            Uri uri=cr.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,values);
            if(uri==null)throw new IOException("Legacy MediaStore insert failed");
            inserted=true;return uri;
        }finally{if(!inserted)file.delete();}
    }
}
