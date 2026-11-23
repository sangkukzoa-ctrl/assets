package com.twobornot.imageorder;

import android.content.ClipData;
import android.content.ContentUris;
import android.Manifest;
import android.app.Activity;
import android.app.Instrumentation;
import android.widget.GridView;
import android.widget.TextView;
import java.lang.reflect.Field;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;
import android.database.Cursor;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.content.res.AssetFileDescriptor;
import java.io.FileNotFoundException;
import android.util.Size;
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
                v.put(MediaStore.Images.Media.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/ImageOrderCI");
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
    /** SAF root: original MediaStore bytes, name, MIME, thumbnail and read-only contract. */
    @Test public void safDocumentProviderExposesRealPhotosWithoutNumberedCopies() throws Exception {
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        String authority=ctx.getPackageName()+".documents";
        Uri mediaRoot=MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY);
        Bitmap bitmap=Bitmap.createBitmap(11,9,Bitmap.Config.ARGB_8888);
        bitmap.eraseColor(0xff335577);
        ByteArrayOutputStream buffer=new ByteArrayOutputStream();
        assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,buffer));bitmap.recycle();
        byte[] original=buffer.toByteArray();
        String name="saf_original_"+System.nanoTime()+".png";
        ContentValues cv=new ContentValues();
        cv.put(MediaStore.Images.Media.DISPLAY_NAME,name);
        cv.put(MediaStore.Images.Media.MIME_TYPE,"image/png");
        cv.put(MediaStore.Images.Media.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/ImageOrderCI");
        cv.put(MediaStore.Images.Media.IS_PENDING,1);
        Uri added=cr.insert(mediaRoot,cv);assertNotNull(added);
        try {
            try(OutputStream out=cr.openOutputStream(added,"w")){assertNotNull(out);out.write(original);}
            ContentValues done=new ContentValues();done.put(MediaStore.Images.Media.IS_PENDING,0);
            assertEquals(1,cr.update(added,done,null,null));
            try(Cursor roots=cr.query(DocumentsContract.buildRootsUri(authority),null,null,null,null)) {
                assertNotNull(roots);assertTrue(roots.moveToFirst());
                assertEquals("images",roots.getString(roots.getColumnIndexOrThrow(DocumentsContract.Root.COLUMN_ROOT_ID)));
                assertEquals("image/*",roots.getString(roots.getColumnIndexOrThrow(DocumentsContract.Root.COLUMN_MIME_TYPES)));
            }
            String id=SafDocumentIds.photo(ContentUris.parseId(added));
            boolean found=false;
            try(Cursor photos=cr.query(DocumentsContract.buildChildDocumentsUri(authority,"all"),null,null,null,null)) {
                assertNotNull(photos);
                while(photos.moveToNext()){
                    String row=photos.getString(photos.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DOCUMENT_ID));
                    if(id.equals(row)){
                        found=true;
                        assertEquals(name,photos.getString(photos.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME)));
                        assertEquals("image/png",photos.getString(photos.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_MIME_TYPE)));
                        assertEquals(original.length,photos.getLong(photos.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_SIZE)));
                        break;
                    }
                }
            }
            assertTrue("SAF must display the original photo",found);
            Uri document=DocumentsContract.buildDocumentUri(authority,id);
            assertArrayEquals(original,readAll(cr,document));
            assertEquals("image/png",cr.getType(document));
            try(Cursor file=cr.query(document,new String[]{DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE},null,null,null)){
                assertNotNull(file);assertTrue(file.moveToFirst());assertEquals(name,file.getString(0));
                assertEquals("image/png",file.getString(1));
            }
            android.graphics.Bitmap preview=DocumentsContract.getDocumentThumbnail(cr,document,new android.graphics.Point(80,80),null);
            assertNotNull("SAF thumbnail should decode",preview);
            preview.recycle();
            try {cr.openOutputStream(document,"w");fail("SAF must be read-only");}
            catch(FileNotFoundException | SecurityException | UnsupportedOperationException expected){}
            Uri traversal=DocumentsContract.buildDocumentUri(authority,"photo:../../etc/passwd");
            try {cr.openInputStream(traversal);fail("SAF ID traversal must be rejected");}
            catch(FileNotFoundException | SecurityException expected){}
        }finally{cr.delete(added,null,null);}
    }

    /** A real Activity sends GET_CONTENT, taps photos in the gallery and receives RESULT_OK. */
    @Test public void externalPickerRoundTripPreservesTapSequence() throws Exception {
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        inst.getUiAutomation().grantRuntimePermission(ctx.getPackageName(),Manifest.permission.READ_MEDIA_IMAGES);
        ArrayList<Uri> inserted=new ArrayList<>();
        ArrayList<byte[]> expected=new ArrayList<>();
        ArrayList<String> names=new ArrayList<>();
        Activity gallery=null;
        try {
            for(int i=0;i<3;i++){
                Bitmap bitmap=Bitmap.createBitmap(13,12,Bitmap.Config.ARGB_8888);
                bitmap.eraseColor(0xff112233+i*0x10000);
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));bitmap.recycle();
                byte[] data=out.toByteArray();
                String name="e2e_picker_"+System.nanoTime()+"_"+i+".png";
                ContentValues values=new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME,name);
                values.put(MediaStore.Images.Media.MIME_TYPE,"image/png");
                values.put(MediaStore.Images.Media.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/ImageOrderCI");
                values.put(MediaStore.Images.Media.IS_PENDING,1);
                Uri uri=cr.insert(MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY),values);
                assertNotNull(uri);inserted.add(uri);expected.add(data);names.add(name);
                try(OutputStream write=cr.openOutputStream(uri,"w")){assertNotNull(write);write.write(data);}
                ContentValues published=new ContentValues();published.put(MediaStore.Images.Media.IS_PENDING,0);
                assertEquals(1,cr.update(uri,published,null,null));
            }
            PickerHostActivity.receivedCode=Activity.RESULT_CANCELED;
            PickerHostActivity.receivedIntent=null;
            PickerHostActivity.completed=new CountDownLatch(1);
            Instrumentation.ActivityMonitor monitor=inst.addMonitor(NativeGalleryActivity.class.getName(),null,false);
            Intent host=new Intent(ctx,PickerHostActivity.class);
            host.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            inst.startActivitySync(host);
            gallery=inst.waitForMonitorWithTimeout(monitor,20000);
            assertNotNull("Native picker must open from external GET_CONTENT",gallery);
            final Activity selectedGallery=gallery;
            int[] indexes=null;
            for(int retry=0;retry<80;retry++){
                AtomicReference<int[]> found=new AtomicReference<>();
                inst.runOnMainSync(()->{
                    try{
                        TextView photosTab=(TextView)getField(selectedGallery,"photosTab");
                        photosTab.performClick();
                        ArrayList<?> displayed=(ArrayList<?>)getField(selectedGallery,"displayed");
                        int[] slots={-1,-1,-1};
                        for(int i=0;i<displayed.size();i++){
                            String n=(String)getField(displayed.get(i),"name");
                            for(int k=0;k<3;k++)if(names.get(k).equals(n))slots[k]=i;
                        }
                        if(slots[0]>=0&&slots[1]>=0&&slots[2]>=0)found.set(slots);
                    }catch(Exception e){throw new RuntimeException(e);}
                });
                indexes=found.get();if(indexes!=null)break;
                Thread.sleep(250);
            }
            assertNotNull("Inserted photos must appear in the native gallery",indexes);
            final int[] positions=indexes;
            inst.runOnMainSync(()->{
                try{
                    GridView grid=(GridView)getField(selectedGallery,"grid");
                    for(int index:new int[]{2,0,1}) {
                        int position=positions[index];
                        grid.performItemClick(null,position,position);
                    }
                    ((TextView)getField(selectedGallery,"confirm")).performClick();
                }catch(Exception e){throw new RuntimeException(e);}
            });
            assertTrue("Caller must receive picker result",PickerHostActivity.completed.await(20,TimeUnit.SECONDS));
            assertEquals(Activity.RESULT_OK,PickerHostActivity.receivedCode);
            Intent result=PickerHostActivity.receivedIntent;
            assertNotNull(result);assertTrue((result.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            ClipData clip=result.getClipData();assertNotNull(clip);assertEquals(3,clip.getItemCount());
            for(int i=0;i<3;i++){
                int source=new int[]{2,0,1}[i];
                Uri uri=clip.getItemAt(i).getUri();
                assertEquals(ContentUris.parseId(inserted.get(source)),ContentUris.parseId(uri));
                assertArrayEquals("Caller must get unchanged original bytes",expected.get(source),readAll(cr,uri));
                assertEquals("image/png",cr.getType(uri));
            }
        }finally{
            if(gallery!=null && !gallery.isFinishing()) {
                final Activity g=gallery;inst.runOnMainSync(g::finish);
            }
            for(Uri uri:inserted)cr.delete(uri,null,null);
        }
    }
    private static Object getField(Object target,String name) throws Exception {
        Field field=target.getClass().getDeclaredField(name);
        field.setAccessible(true);return field.get(target);
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
    /** Regression: Android 15+ edge-to-edge must not place Done under the system status bar. */
    @Test public void galleryDoneControlClearsAndroid15SystemBars() throws Exception {
        if(android.os.Build.VERSION.SDK_INT<35)return;
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        inst.getUiAutomation().grantRuntimePermission(ctx.getPackageName(),Manifest.permission.READ_MEDIA_IMAGES);
        Intent launch=new Intent(ctx,NativeGalleryActivity.class);
        launch.setAction(Intent.ACTION_GET_CONTENT);
        launch.setType("image/png");
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Activity gallery=inst.startActivitySync(launch);
        try{
            inst.waitForIdleSync();
            AtomicReference<android.graphics.Rect> bounds=new AtomicReference<>();
            AtomicReference<Integer> topSafe=new AtomicReference<>();
            AtomicReference<Integer> rootPadding=new AtomicReference<>();
            inst.runOnMainSync(()->{
                try{
                    android.view.ViewGroup content=gallery.findViewById(android.R.id.content);
                    android.view.View root=content.getChildAt(0);
                    android.view.WindowInsets insets=root.getRootWindowInsets();
                    android.graphics.Insets bars=insets.getInsets(
                        android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.displayCutout());
                    android.graphics.Rect confirmRect=new android.graphics.Rect();
                    assertTrue(((TextView)getField(gallery,"confirm")).getGlobalVisibleRect(confirmRect));
                    bounds.set(confirmRect);topSafe.set(bars.top);rootPadding.set(root.getPaddingTop());
                }catch(Exception e){throw new RuntimeException(e);}
            });
            assertNotNull(bounds.get());
            assertTrue("Gallery root must respect Android 15 status-bar inset",
                rootPadding.get()>=topSafe.get());
            assertTrue("Done button must begin below the status-bar obstruction: "+bounds.get(),
                bounds.get().top>=topSafe.get());
        }finally{
            inst.runOnMainSync(gallery::finish);
        }
    }

    @Test public void theImagePickerIsAdvertisedToNormalAndroidCallers() {
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        Intent get=new Intent(Intent.ACTION_GET_CONTENT);
        get.setType("image/jpeg");get.addCategory(Intent.CATEGORY_OPENABLE);
        List<ResolveInfo> activities=ctx.getPackageManager().queryIntentActivities(get,0);
        boolean found=false;
        for(ResolveInfo info:activities){
            if(info.activityInfo!=null && ctx.getPackageName().equals(info.activityInfo.packageName)
                && NativeGalleryActivity.class.getName().equals(info.activityInfo.name))found=true;
        }
        assertTrue("Image Order must resolve for image/jpeg GET_CONTENT",found);
        Intent generic=new Intent(Intent.ACTION_GET_CONTENT);
        generic.setType("*/*");generic.addCategory(Intent.CATEGORY_OPENABLE);
        generic.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/png","image/jpeg"});
        boolean genericFound=false;
        for(ResolveInfo info:ctx.getPackageManager().queryIntentActivities(generic,0)){
            if(info.activityInfo!=null && ctx.getPackageName().equals(info.activityInfo.packageName)
                && NativeGalleryActivity.class.getName().equals(info.activityInfo.name))genericFound=true;
        }
        assertTrue("Generic */* uploaders must also offer this image gallery",genericFound);
    }
    private static byte[] readAll(ContentResolver cr,Uri uri) throws Exception {
        try(InputStream in=cr.openInputStream(uri);ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            assertNotNull(in);byte[] b=new byte[4096];int n;
            while((n=in.read(b))!=-1)out.write(b,0,n);
            return out.toByteArray();
        }
    }
}
