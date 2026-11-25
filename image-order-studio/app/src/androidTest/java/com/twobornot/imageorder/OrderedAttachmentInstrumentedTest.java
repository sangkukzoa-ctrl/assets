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
    @org.junit.Before public void prepareMediaPermissions() throws Exception {
        TestMediaPermissions.grant(InstrumentationRegistry.getInstrumentation());
    }
    @Test public void orderedOriginalUrisRetainEveryByteAndImageMime() throws Exception {
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        ArrayList<Uri> inserted=new ArrayList<>();
        ArrayList<byte[]> expected=new ArrayList<>();
        try {
            for(int i=0;i<3;i++) {
                Bitmap b=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);
                b.eraseColor(0xff123400 | (i*0x10000)+i);
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,bytes)); b.recycle();
                byte[] original=bytes.toByteArray();
                Uri uri=TestMediaFixture.insert(ctx,"imageorder_ci_"+System.nanoTime()+"_"+i+".png","image/png",Environment.DIRECTORY_PICTURES+"/ImageOrderCI",original);
                inserted.add(uri);expected.add(original);
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
        Bitmap bitmap=Bitmap.createBitmap(11,9,Bitmap.Config.ARGB_8888);
        bitmap.eraseColor(0xff335577);
        ByteArrayOutputStream buffer=new ByteArrayOutputStream();
        assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,buffer));bitmap.recycle();
        byte[] original=buffer.toByteArray();
        String name="saf_original_"+System.nanoTime()+".png";
        Uri added=TestMediaFixture.insert(ctx,name,"image/png",Environment.DIRECTORY_PICTURES+"/ImageOrderCI",original);
        try {
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
                Uri uri=TestMediaFixture.insert(ctx,name,"image/png",Environment.DIRECTORY_PICTURES+"/ImageOrderCI",data);
                inserted.add(uri);expected.add(data);names.add(name);
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

    /**
     * Native GET_CONTENT round trip at the default 100-photo limit.
     * GridView item callbacks exercise actual selection logic, rather than injecting
     * a fabricated LinkedHashMap or ClipData. The debug host is same UID; the
     * smaller independent APK tests separately establish cross-UID grants.
     */
    @Test public void hundredOriginalsKeepOrderAtLimitAndAfterReselection() throws Exception {
        final int total=102,limit=100;
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        ArrayList<Uri> sources=new ArrayList<>();
        ArrayList<byte[]> originals=new ArrayList<>();
        ArrayList<String> names=new ArrayList<>();
        Activity gallery=null;
        long stamp=System.nanoTime();
        try {
            for(int i=0;i<total;i++){
                Bitmap bitmap=Bitmap.createBitmap(9,9,Bitmap.Config.ARGB_8888);
                bitmap.eraseColor(0xff123400+i);
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,bytes));bitmap.recycle();
                byte[] original=bytes.toByteArray();
                String name="imageorder_batch_"+stamp+"_"+i+".png";
                Uri uri=TestMediaFixture.insert(ctx,name,"image/png",Environment.DIRECTORY_PICTURES+"/ImageOrderBatchCI",original);
                sources.add(uri);originals.add(original);names.add(name);
            }
            PickerHostActivity.receivedCode=Activity.RESULT_CANCELED;
            PickerHostActivity.receivedIntent=null;
            PickerHostActivity.completed=new CountDownLatch(1);
            Instrumentation.ActivityMonitor monitor=inst.addMonitor(NativeGalleryActivity.class.getName(),null,false);
            Intent host=new Intent(ctx,PickerHostActivity.class);
            host.putExtra("testNativeGallery",true);
            host.putExtra("testRequestedMime","image/png");
            host.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            inst.startActivitySync(host);
            gallery=inst.waitForMonitorWithTimeout(monitor,20000);
            assertNotNull("Direct native gallery must open",gallery);
            final Activity target=gallery;
            AtomicReference<int[]> found=new AtomicReference<>();
            for(int retry=0;retry<100 && found.get()==null;retry++){
                inst.runOnMainSync(()->{
                    try {
                        ((TextView)getField(target,"photosTab")).performClick();
                        ArrayList<?> displayed=(ArrayList<?>)getField(target,"displayed");
                        int[] positions=new int[total];Arrays.fill(positions,-1);
                        int matches=0;
                        for(int p=0;p<displayed.size();p++){
                            int idx=names.indexOf((String)getField(displayed.get(p),"name"));
                            if(idx>=0 && positions[idx]<0){positions[idx]=p;matches++;}
                        }
                        if(matches==total)found.set(positions);
                    }catch(Exception ex){throw new RuntimeException(ex);}
                });
                if(found.get()==null)Thread.sleep(200);
            }
            int[] positions=found.get();assertNotNull("All 102 original fixtures must load",positions);
            // A non-monotonic permutation of the first hundred sources: gcd(37,100)=1.
            ArrayList<Integer> expected=new ArrayList<>();
            for(int i=0;i<limit;i++)expected.add((i*37)%limit);
            for(int i=0;i<limit;i++){
                final int pos=positions[expected.get(i)];
                inst.runOnMainSync(()->{
                    try{((GridView)getField(target,"grid")).performItemClick(null,pos,pos);}
                    catch(Exception ex){throw new RuntimeException(ex);}
                });
            }
            final int removed=expected.remove(31);
            expected.add(100);
            inst.runOnMainSync(()->{
                try {
                    GridView grid=(GridView)getField(target,"grid");
                    TextView confirm=(TextView)getField(target,"confirm");
                    assertTrue("Default limit reached",confirm.getText().toString().endsWith(" 100"));
                    grid.performItemClick(null,positions[100],positions[100]);
                    assertTrue("101st unique selection must be rejected",confirm.getText().toString().endsWith(" 100"));
                    grid.performItemClick(null,positions[removed],positions[removed]);
                    assertTrue("Deselect frees one slot",confirm.getText().toString().endsWith(" 99"));
                    grid.performItemClick(null,positions[100],positions[100]);
                    assertTrue("New photo fills the free slot",confirm.getText().toString().endsWith(" 100"));
                    grid.performItemClick(null,positions[101],positions[101]);
                    assertTrue("Another overflow must be rejected",confirm.getText().toString().endsWith(" 100"));
                    confirm.performClick();
                }catch(Exception ex){throw new RuntimeException(ex);}
            });
            assertTrue("Requester must receive full result",PickerHostActivity.completed.await(30,TimeUnit.SECONDS));
            assertEquals(Activity.RESULT_OK,PickerHostActivity.receivedCode);
            Intent result=PickerHostActivity.receivedIntent;
            assertNotNull(result);
            assertEquals("image/png",result.getType());
            assertTrue((result.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            assertEquals(0,result.getFlags()&Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            ClipData clip=result.getClipData();assertNotNull(clip);assertEquals(limit,clip.getItemCount());
            java.util.HashSet<Long> seen=new java.util.HashSet<>();
            for(int i=0;i<limit;i++){
                int source=expected.get(i);
                Uri uri=clip.getItemAt(i).getUri();
                long id=ContentUris.parseId(uri);
                assertEquals("Original sequence at index "+i,ContentUris.parseId(sources.get(source)),id);
                assertTrue("No duplicate original in result",seen.add(id));
                assertEquals("image/png",cr.getType(uri));
                assertArrayEquals("Untouched original at index "+i,originals.get(source),readAll(cr,uri));
                try(Cursor c=cr.query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){
                    assertNotNull(c);assertTrue(c.moveToFirst());assertEquals(names.get(source),c.getString(0));
                }
            }
        }finally{
            if(gallery!=null && !gallery.isFinishing()){
                Activity end=gallery;inst.runOnMainSync(end::finish);
            }
            for(Uri uri:sources)cr.delete(uri,null,null);
        }
    }

    private static Object getField(Object target,String name) throws Exception {
        Field field=target.getClass().getDeclaredField(name);
        field.setAccessible(true);return field.get(target);
    }

    @Test public void legacyChooserExcludesBothImageOrderActivities(){
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        Intent chooser=NativeGalleryActivity.newLegacyPickerIntent(context,10,"Photos");
        assertEquals(Intent.ACTION_CHOOSER,chooser.getAction());
        Intent inner=chooser.getParcelableExtra(Intent.EXTRA_INTENT);
        assertNotNull(inner);
        assertEquals(Intent.ACTION_GET_CONTENT,inner.getAction());
        assertEquals("image/*",inner.getType());
        assertTrue(inner.hasCategory(Intent.CATEGORY_OPENABLE));
        assertTrue(inner.getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false));
        android.os.Parcelable[] excluded=chooser.getParcelableArrayExtra(Intent.EXTRA_EXCLUDE_COMPONENTS);
        assertNotNull(excluded);
        assertTrue(Arrays.asList(excluded).contains(new android.content.ComponentName(context,NativeGalleryActivity.class)));
        assertTrue(Arrays.asList(excluded).contains(new android.content.ComponentName(context,MainActivity.class)));
        Intent single=NativeGalleryActivity.newLegacyPickerIntent(context,1,"Photos")
            .getParcelableExtra(Intent.EXTRA_INTENT);
        assertNotNull(single);
        assertFalse(single.getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false));
    }

    /** The fallback must opt into Android's ordered Photo Picker without re-encoding. */
    @Test public void systemPickerFallbackRequestsOrderedSelectionWhenSupported() {
        int api=android.os.Build.VERSION.SDK_INT;
        int extension=api>=30?android.os.ext.SdkExtensions.getExtensionVersion(android.os.Build.VERSION_CODES.R):0;
        assertEquals(PickerDecision.supportsPhotoPicker(api,extension),
            NativeGalleryActivity.supportsSystemPhotoPicker());
        if(!NativeGalleryActivity.supportsSystemPhotoPicker())return;
        Intent many=NativeGalleryActivity.newSystemPickerIntent(5);
        assertEquals(MediaStore.ACTION_PICK_IMAGES,many.getAction());
        assertEquals("image/*",many.getType());
        assertTrue("Maximum count must not drop below 1",
            many.getIntExtra(MediaStore.EXTRA_PICK_IMAGES_MAX,1)>=1);
        assertEquals("Ordered picker capability must match installed SDK/extensions",
            NativeGalleryActivity.supportsOrderedSystemPicker(),
            many.getBooleanExtra(MediaStore.EXTRA_PICK_IMAGES_IN_ORDER,false));
        Intent one=NativeGalleryActivity.newSystemPickerIntent(1);
        assertFalse("Android rejects max=1; single selection must omit this extra",
            one.hasExtra(MediaStore.EXTRA_PICK_IMAGES_MAX));
        assertFalse("Single-image picker should not require ordering extra",
            one.getBooleanExtra(MediaStore.EXTRA_PICK_IMAGES_IN_ORDER,false));
    }


    /** Restored selection numbers and ClipData must retain the exact prior tap order. */
    @Test public void nativeGalleryRecreationKeepsSelectionSequence() throws Exception {
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        ArrayList<Uri> sources=new ArrayList<>();
        ArrayList<String> names=new ArrayList<>();
        Activity first=null,restored=null;
        try{
            for(int i=0;i<3;i++){
                Bitmap bitmap=Bitmap.createBitmap(9,9,Bitmap.Config.ARGB_8888);
                bitmap.eraseColor(0xff19384a + i*0x2200);
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,bytes));bitmap.recycle();
                String name="imageorder_recreate_"+System.nanoTime()+"_"+i+".png";
                Uri uri=TestMediaFixture.insert(ctx,name,"image/png",Environment.DIRECTORY_PICTURES+"/ImageOrderCI",bytes.toByteArray());
                sources.add(uri);names.add(name);
            }
            Intent open=new Intent(ctx,NativeGalleryActivity.class);
            open.setAction(Intent.ACTION_GET_CONTENT);
            open.setType("image/png");
            open.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
            open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            first=inst.startActivitySync(open);
            final Activity initial=first;
            AtomicReference<int[]> positions=new AtomicReference<>();
            for(int retry=0;retry<80 && positions.get()==null;retry++){
                inst.runOnMainSync(()->{
                    try{
                        ((TextView)getField(initial,"photosTab")).performClick();
                        ArrayList<?> displayed=(ArrayList<?>)getField(initial,"displayed");
                        int[] slots={-1,-1,-1};
                        for(int p=0;p<displayed.size();p++){
                            String actual=(String)getField(displayed.get(p),"name");
                            for(int k=0;k<3;k++)if(names.get(k).equals(actual))slots[k]=p;
                        }
                        if(slots[0]>=0 && slots[1]>=0 && slots[2]>=0)positions.set(slots);
                    }catch(Exception ex){throw new RuntimeException(ex);}
                });
                if(positions.get()==null)Thread.sleep(120);
            }
            assertNotNull("All fixture photos must load",positions.get());
            final int[] slots=positions.get();
            inst.runOnMainSync(()->{
                try{
                    GridView grid=(GridView)getField(initial,"grid");
                    grid.performItemClick(null,slots[2],slots[2]);
                    grid.performItemClick(null,slots[0],slots[0]);
                    grid.performItemClick(null,slots[1],slots[1]);
                    assertTrue(((TextView)getField(initial,"confirm")).getText().toString().endsWith("3"));
                }catch(Exception ex){throw new RuntimeException(ex);}
            });
            inst.runOnMainSync(initial::recreate);
            AtomicReference<Activity> reloaded=new AtomicReference<>();
            for(int retry=0;retry<100 && reloaded.get()==null;retry++){
                inst.runOnMainSync(()->{
                    for(Activity a:androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance()
                            .getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED)){
                        if(a instanceof NativeGalleryActivity && a!=initial)reloaded.set(a);
                    }
                });
                if(reloaded.get()==null)Thread.sleep(120);
            }
            restored=reloaded.get();
            assertNotNull("Native gallery must recreate with saved state",restored);
            final Activity target=restored;
            inst.runOnMainSync(()->{
                try{
                    @SuppressWarnings("unchecked")
                    java.util.LinkedHashMap<String,Uri> picked=
                        (java.util.LinkedHashMap<String,Uri>)getField(target,"ordered");
                    assertEquals("All selected photos survive Activity recreation",3,picked.size());
                    assertTrue("Selected count remains visible",
                        ((TextView)getField(target,"confirm")).getText().toString().endsWith("3"));
                    int i=0;
                    for(Uri uri:picked.values()){
                        assertEquals("Recreated selection retains original tap order",
                            android.content.ContentUris.parseId(sources.get(new int[]{2,0,1}[i++])),
                            android.content.ContentUris.parseId(uri));
                    }
                }catch(Exception ex){throw new RuntimeException(ex);}
            });
        }finally{
            Activity end=restored!=null?restored:first;
            if(end!=null && !end.isFinishing())inst.runOnMainSync(end::finish);
            for(Uri uri:sources)cr.delete(uri,null,null);
        }
    }

    /** Android must not start another platform picker while a prior picker is pending. */
    @Test public void fallbackPickerPendingStateSurvivesActivityRecreation() throws Exception {
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context context=inst.getTargetContext();
        Intent start=new Intent(context,NativeGalleryActivity.class);
        start.setAction(Intent.ACTION_GET_CONTENT);
        start.setType("image/png");
        start.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
        start.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Activity initial=inst.startActivitySync(start),updated=null;
        java.lang.reflect.Field pending=NativeGalleryActivity.class.getDeclaredField("fallbackPickerPending");
        pending.setAccessible(true);
        try {
            inst.runOnMainSync(()->{
                try{pending.setBoolean(initial,true);}catch(Exception ex){throw new RuntimeException(ex);}
                initial.recreate();
            });
            AtomicReference<Activity> next=new AtomicReference<>();
            for(int attempt=0;attempt<100 && next.get()==null;attempt++){
                inst.runOnMainSync(()->{
                    for(Activity candidate:androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
                            .getInstance().getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED)){
                        if(candidate instanceof NativeGalleryActivity && candidate!=initial)next.set(candidate);
                    }
                });
                if(next.get()==null)Thread.sleep(120);
            }
            updated=next.get();
            assertNotNull("Pending platform chooser must not destroy external picker",updated);
            Activity target=updated;
            inst.runOnMainSync(()->{
                try {
                    assertTrue("Recreated gallery remembers an outstanding platform picker",
                        pending.getBoolean(target));
                    @SuppressWarnings("unchecked")
                    ArrayList<Object> photos=(ArrayList<Object>)getField(target,"photos");
                    assertTrue("Do not reload/reopen a new gallery over pending system chooser",
                        photos.isEmpty());
                }catch(Exception ex){throw new RuntimeException(ex);}
            });
        }finally {
            Activity end=updated!=null?updated:initial;
            if(!end.isFinishing())inst.runOnMainSync(end::finish);
        }
    }

    /**
     * Feed an OS-style ordered ClipData result through the ACTUAL gallery
     * onActivityResult and verify that the requesting host receives original
     * mixed-format streams in identical order. Synthetic platform response:
     * distinct from UI-driving a vendor's system Photo Picker.
     */
    @Test public void orderedSystemPhotoPickerFallbackDeliversUnchangedMixedOriginals() throws Exception {
        if(android.os.Build.VERSION.SDK_INT<35)return;
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        ContentResolver cr=ctx.getContentResolver();
        ArrayList<Uri> media=new ArrayList<>();
        ArrayList<byte[]> contents=new ArrayList<>();
        ArrayList<String> names=new ArrayList<>();
        Activity gallery=null;
        try {
            Bitmap.CompressFormat[] formats={
                Bitmap.CompressFormat.PNG,Bitmap.CompressFormat.JPEG,Bitmap.CompressFormat.WEBP_LOSSLESS
            };
            String[] mimes={"image/png","image/jpeg","image/webp"};
            String[] extensions={"png","jpg","webp"};
            for(int i=0;i<3;i++){
                Bitmap bitmap=Bitmap.createBitmap(12,14,Bitmap.Config.ARGB_8888);
                bitmap.eraseColor(0xff123456+i*0x13290a);
                ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                assertTrue(bitmap.compress(formats[i],90,bytes));bitmap.recycle();
                String name="imageorder_fallback_"+System.nanoTime()+"_"+i+"."+extensions[i];
                Uri uri=TestMediaFixture.insert(ctx,name,mimes[i],Environment.DIRECTORY_PICTURES+"/ImageOrderCI",bytes.toByteArray());
                media.add(uri);contents.add(bytes.toByteArray());names.add(name);
            }
            PickerHostActivity.receivedCode=Activity.RESULT_CANCELED;
            PickerHostActivity.receivedIntent=null;
            PickerHostActivity.completed=new CountDownLatch(1);
            Instrumentation.ActivityMonitor monitor=inst.addMonitor(NativeGalleryActivity.class.getName(),null,false);
            Intent host=new Intent(ctx,PickerHostActivity.class);
            host.putExtra("testNativeGallery",true);
            host.putExtra("testRequestedMime","image/*");
            host.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            inst.startActivitySync(host);
            gallery=inst.waitForMonitorWithTimeout(monitor,20000);
            assertNotNull("Debug caller must launch native Image Order directly",gallery);
            final Activity target=gallery;
            ClipData clip=new ClipData("Ordered platform selection",new String[]{"image/*"},
                new ClipData.Item(media.get(2)));
            clip.addItem(new ClipData.Item(media.get(0)));
            clip.addItem(new ClipData.Item(media.get(1)));
            Intent platformResult=new Intent();
            platformResult.setClipData(clip);
            platformResult.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            inst.runOnMainSync(()->{
                try {
                    Field ordered=NativeGalleryActivity.class.getDeclaredField("fallbackOrderedSelectionRequested");
                    ordered.setAccessible(true);
                    ordered.setBoolean(target,true);
                    ((NativeGalleryActivity)target).onActivityResult(28,Activity.RESULT_OK,platformResult);
                }catch(Exception ex){throw new RuntimeException(ex);}
            });
            assertTrue("Source caller must receive ordered fallback result",
                PickerHostActivity.completed.await(20,TimeUnit.SECONDS));
            assertEquals(Activity.RESULT_OK,PickerHostActivity.receivedCode);
            Intent returned=PickerHostActivity.receivedIntent;
            assertNotNull(returned);
            assertEquals("image/*",returned.getType());
            assertTrue((returned.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            ClipData received=returned.getClipData();
            assertNotNull(received);assertEquals(3,received.getItemCount());
            int[] indices={2,0,1};
            for(int i=0;i<3;i++){
                int original=indices[i];
                Uri uri=received.getItemAt(i).getUri();
                assertEquals("System picker URI order must not change",media.get(original),uri);
                assertArrayEquals("Original bytes must be untouched",contents.get(original),readAll(cr,uri));
                assertEquals(mimes[original],cr.getType(uri));
                try(Cursor c=cr.query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){
                    assertNotNull(c);assertTrue(c.moveToFirst());
                    assertEquals(names.get(original),c.getString(0));
                }
            }
        }finally{
            if(gallery!=null && !gallery.isFinishing()){
                Activity toFinish=gallery;
                inst.runOnMainSync(toFinish::finish);
            }
            for(Uri uri:media)cr.delete(uri,null,null);
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
    /** Regression: Android 15+ edge-to-edge must not place Done under the system status bar. */
    @Test public void galleryDoneControlClearsAndroid15SystemBars() throws Exception {
        if(android.os.Build.VERSION.SDK_INT<35)return;
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
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

    @Test public void actionPickUriOnlyResolvesNativeGallery() {
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        Intent pick=new Intent(Intent.ACTION_PICK,MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        pick.setPackage(ctx.getPackageName());
        boolean found=false;
        for(ResolveInfo info:ctx.getPackageManager().queryIntentActivities(pick,0)){
            if(info.activityInfo!=null && ctx.getPackageName().equals(info.activityInfo.packageName)
                && NativeGalleryActivity.class.getName().equals(info.activityInfo.name))found=true;
        }
        assertTrue("URI-only ACTION_PICK must resolve Image Order",found);
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
