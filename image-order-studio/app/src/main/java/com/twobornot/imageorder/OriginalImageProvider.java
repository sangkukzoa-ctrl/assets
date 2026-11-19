package com.twobornot.imageorder;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;
import java.util.*;
import org.json.JSONArray;
import org.json.JSONObject;

/** Read-only, grantable original byte streams with the user's *original* display names. */
public final class OriginalImageProvider extends ContentProvider {
    private static final String UUID="[0-9a-fA-F-]{36}";
    private static final String SESSION="session-"+UUID;
    private static final int MAX_META=8*1024*1024;
    private static final class Entry {
        final File file;
        final String name,mime;
        Entry(File file,String name,String mime){this.file=file;this.name=name;this.mime=mime;}
    }
    static Uri uriFor(Context ctx,GalleryStore store,GalleryStore.Item item){
        return new Uri.Builder().scheme("content")
            .authority(ctx.getPackageName()+".originals")
            .appendPath(store.sessionId()).appendPath(item.id).build();
    }
    @Override public boolean onCreate(){return true;}
    private Entry resolve(Uri uri) throws FileNotFoundException {
        Context ctx=getContext();
        if(ctx==null || !"content".equals(uri.getScheme()) ||
           !(ctx.getPackageName()+".originals").equals(uri.getAuthority()) ||
           uri.getPathSegments().size()!=2)throw new FileNotFoundException("Invalid image URI");
        String session=uri.getPathSegments().get(0),id=uri.getPathSegments().get(1);
        if(!id.matches(UUID) || !("main".equals(session)||session.matches(SESSION)))
            throw new FileNotFoundException("Invalid original ID");
        File home="main".equals(session)?ctx.getFilesDir():new File(new File(ctx.getFilesDir(),"picker-sessions"),session);
        File metadata=new File(home,"gallery.json");
        if(!metadata.isFile()||metadata.length()>MAX_META)throw new FileNotFoundException("Missing gallery metadata");
        try(FileInputStream input=new FileInputStream(metadata)){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            byte[] b=new byte[8192];int n;
            while((n=input.read(b))!=-1){bytes.write(b,0,n);if(bytes.size()>MAX_META)throw new IOException("Gallery metadata too large");}
            JSONArray images=new JSONObject(bytes.toString("UTF-8")).getJSONArray("images");
            for(int i=0;i<images.length();i++){
                JSONObject row=images.getJSONObject(i);
                if(!id.equals(row.getString("id")))continue;
                String rel=row.getString("path");
                if(!rel.matches(UUID+"\\.[a-zA-Z0-9]{1,8}"))throw new FileNotFoundException("Invalid stored path");
                File f=new File(new File(home,"library"),rel);
                if(!f.isFile())throw new FileNotFoundException("Original bytes no longer available");
                String mime=row.getString("mime"), name=row.getString("name");
                if(!mime.startsWith("image/"))throw new FileNotFoundException("Not an image");
                return new Entry(f,name,mime);
            }
        }catch(Exception e){throw new FileNotFoundException("Cannot open original image: "+e.getMessage());}
        throw new FileNotFoundException("Image not found");
    }
    @Override public String getType(Uri uri){try{return resolve(uri).mime;}catch(FileNotFoundException e){return null;}}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String sortOrder) {
        try {
            Entry entry=resolve(uri);
            String[] fields=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;
            MatrixCursor cursor=new MatrixCursor(fields);
            MatrixCursor.RowBuilder row=cursor.newRow();
            for(String field:fields){
                if(OpenableColumns.DISPLAY_NAME.equals(field))row.add(entry.name);
                else if(OpenableColumns.SIZE.equals(field))row.add(entry.file.length());
                else if("mime_type".equals(field))row.add(entry.mime);
                else row.add(null);
            }
            return cursor;
        } catch(FileNotFoundException e){return null;}
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        if(!"r".equals(mode))throw new FileNotFoundException("Read-only originals");
        return ParcelFileDescriptor.open(resolve(uri).file,ParcelFileDescriptor.MODE_READ_ONLY);
    }
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException("Read-only");}
    @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException("Read-only");}
    @Override public int update(Uri uri,ContentValues values,String sel,String[] args){throw new UnsupportedOperationException("Read-only");}
}
