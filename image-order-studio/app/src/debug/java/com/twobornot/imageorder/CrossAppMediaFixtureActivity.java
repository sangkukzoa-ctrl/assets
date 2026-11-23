package com.twobornot.imageorder;

import android.app.Activity;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.util.ArrayList;

/** TEST ONLY. Seeds photos owned by the target app, not by the third-party picker caller.
 * External test callers receive URI strings only (without any URI grant) so that the
 * cross-UID read grant made by the real picker can be tested independently. */
public final class CrossAppMediaFixtureActivity extends Activity {
    public static final String EXTRA_NAMES="test_names";
    public static final String EXTRA_URIS="test_uri_strings";
    public static final String EXTRA_HASHES="test_sha256";
    public static final String EXTRA_CLEAN="test_cleanup_uri_strings";
    private static final String PATH=Environment.DIRECTORY_PICTURES+"/ImageOrderStudioCrossAppCI";

    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        try {
            String[] toRemove=getIntent().getStringArrayExtra(EXTRA_CLEAN);
            if(toRemove!=null){
                for(String str:toRemove){
                    if(str==null)continue;
                    Uri uri=Uri.parse(str);
                    if("media".equals(uri.getAuthority()))getContentResolver().delete(uri,null,null);
                }
                setResult(RESULT_OK);
                finish();return;
            }
            ArrayList<String> names=new ArrayList<>(),uris=new ArrayList<>(),hashes=new ArrayList<>();
            Uri collection=MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY);
            long runId=System.nanoTime();
            for(int i=0;i<3;i++){
                Bitmap image=Bitmap.createBitmap(19,17,Bitmap.Config.ARGB_8888);
                image.eraseColor(0xff224466+(i*0x00070b0d));
                ByteArrayOutputStream data=new ByteArrayOutputStream();
                if(!image.compress(Bitmap.CompressFormat.PNG,100,data))throw new IllegalStateException("PNG fixture");
                image.recycle();byte[] bytes=data.toByteArray();
                String name="imageorder_crossuid_"+runId+"_"+i+".png";
                ContentValues meta=new ContentValues();
                meta.put(MediaStore.Images.Media.DISPLAY_NAME,name);
                meta.put(MediaStore.Images.Media.MIME_TYPE,"image/png");
                meta.put(MediaStore.Images.Media.RELATIVE_PATH,PATH);
                meta.put(MediaStore.Images.Media.IS_PENDING,1);
                Uri uri=getContentResolver().insert(collection,meta);
                if(uri==null)throw new IllegalStateException("MediaStore insert failed");
                uris.add(uri.toString()); names.add(name); hashes.add(hex(MessageDigest.getInstance("SHA-256").digest(bytes)));
                try(OutputStream os=getContentResolver().openOutputStream(uri,"w")){
                    if(os==null)throw new IllegalStateException("MediaStore stream missing");
                    os.write(bytes);
                }
                ContentValues ready=new ContentValues();ready.put(MediaStore.Images.Media.IS_PENDING,0);
                if(getContentResolver().update(uri,ready,null,null)!=1)throw new IllegalStateException("MediaStore publish failed");
            }
            Intent result=new Intent();
            result.putExtra(EXTRA_NAMES,names.toArray(new String[0]));
            result.putExtra(EXTRA_URIS,uris.toArray(new String[0]));
            result.putExtra(EXTRA_HASHES,hashes.toArray(new String[0]));
            // No data URI, ClipData, or FLAG_GRANT_READ_URI_PERMISSION here!
            setResult(RESULT_OK,result);
        }catch(Exception e){
            android.util.Log.e("ImageOrderCrossApp","Fixture failed",e);
            setResult(RESULT_CANCELED,new Intent().putExtra("error",e.toString()));
        }
        finish();
    }
    private static String hex(byte[] data){
        char[] alphabet="0123456789abcdef".toCharArray();
        StringBuilder sb=new StringBuilder(data.length*2);
        for(byte b:data){sb.append(alphabet[(b>>4)&15]);sb.append(alphabet[b&15]);}
        return sb.toString();
    }
}
