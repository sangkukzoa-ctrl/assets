package com.twobornot.imageorder;

import android.content.ClipData;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Environment;
import android.provider.MediaStore;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import static org.junit.Assert.*;

/** Android-device contract test: real MediaStore streams, original-byte hashes, selection ordering, intent resolution. */
@RunWith(AndroidJUnit4.class)
public class OrderedAttachmentInstrumentedTest {
    @Test public void orderedOriginalUrisRetainEveryByteAndImageMime() throws Exception {
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        Uri media=MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY);
        ArrayList<Uri> inserted=new ArrayList<>();
        ArrayList<byte[]> expected=new ArrayList<>();
        try {
            for(int i=0;i<3;i++) {
                Bitmap b=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);
                b.eraseColor(0xff123400 | (i*0x10000)+i);
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,bytes)); b.recycle();
                byte[] original=bytes.toByteArray();
                ContentValues v=new ContentValues();
                v.put(MediaStore.Images.Media.DISPLAY_NAME,"imageorder_ci_"+System.nanoTime()+"_"+i+".png");
                v.put(MediaStore.Images.Media.MIME_TYPE,"image/png");
                v.put(MediaStore.Images.Media.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/ImageOrderStudioCI");
                v.put(MediaStore.Images.Media.IS_PENDING,1);
                Uri uri=cr.insert(media,v);
                assertNotNull(uri);inserted.add(uri);expected.add(original);
                try(OutputStream out=cr.openOutputStream(uri,"w")){assertNotNull(out);out.write(original);}
                ContentValues done=new ContentValues();done.put(MediaStore.Images.Media.IS_PENDING,0);
                assertEquals(1,cr.update(uri,done,null,null));
            }
            ArrayList<Uri> chosen=new ArrayList<>(Arrays.asList(inserted.get(2),inserted.get(0),inserted.get(1)));
            Intent result=MediaIntentResult.forSelection(cr,chosen);
            assertEquals("image/png",result.getType());
            assertEquals(0,result.getFlags()&Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            assertTrue((result.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            ClipData clip=result.getClipData();assertNotNull(clip);
            assertTrue(clip.getDescription().hasMimeType("image/*"));
            assertTrue(clip.getDescription().hasMimeType("image/png"));
            assertEquals(3,clip.getItemCount());
            int[] selectedOriginalIndexes={2,0,1};
            for(int i=0;i<3;i++) {
                Uri uri=clip.getItemAt(i).getUri();
                assertEquals(chosen.get(i),uri);
                assertEquals("image/png",cr.getType(uri));
                assertArrayEquals(expected.get(selectedOriginalIndexes[i]),readAll(cr,uri));
            }
            Intent share=MediaIntentResult.forShare(cr,chosen);
            assertEquals(Intent.ACTION_SEND_MULTIPLE,share.getAction());
            assertEquals(chosen,share.getParcelableArrayListExtra(Intent.EXTRA_STREAM));
        } finally {
            for(Uri uri:inserted)cr.delete(uri,null,null);
        }
    }
    @Test public void singleResultHasReadableImageTypeAndOriginalUri() {
        Uri original=Uri.parse("content://media/external/images/media/12345");
        ArrayList<Uri> originals=new ArrayList<>(Arrays.asList(original));
        Intent result=MediaIntentResult.forSelection(originals,Arrays.asList("image/jpeg"));
        assertEquals(original,result.getData());
        assertEquals("image/jpeg",result.getType());
        assertEquals(1,result.getClipData().getItemCount());
        assertEquals(original,result.getClipData().getItemAt(0).getUri());
        assertTrue(result.getClipData().getDescription().hasMimeType("image/jpeg"));
        Intent share=MediaIntentResult.forShare(originals,Arrays.asList("image/jpeg"));
        assertEquals(Intent.ACTION_SEND,share.getAction());
        assertEquals(original,share.getParcelableExtra(Intent.EXTRA_STREAM));
    }
    @Test public void theImagePickerIsAdvertisedToNormalAndroidCallers() {
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        Intent get=new Intent(Intent.ACTION_GET_CONTENT);
        get.setType("image/jpeg");get.addCategory(Intent.CATEGORY_OPENABLE);
        List<ResolveInfo> activities=ctx.getPackageManager().queryIntentActivities(get,0);
        boolean found=false;
        for(ResolveInfo info:activities){
            if(info.activityInfo!=null && ctx.getPackageName().equals(info.activityInfo.packageName)
                && MainActivity.class.getName().equals(info.activityInfo.name))found=true;
        }
        assertTrue("Image Order Studio must resolve for image/jpeg GET_CONTENT",found);
    }
    private static byte[] readAll(ContentResolver cr,Uri uri) throws Exception {
        try(InputStream in=cr.openInputStream(uri);ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            assertNotNull(in);byte[] b=new byte[4096];int n;
            while((n=in.read(b))!=-1)out.write(b,0,n);
            return out.toByteArray();
        }
    }
}
