package com.twobornot.imageorder.caller;

import android.Manifest;
import android.app.Activity;
import android.app.Instrumentation;
import android.content.ClipData;
import android.content.ComponentName;
import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;
import static org.junit.Assert.*;

/** Verifies grant propagation to a third-party app WITHOUT any media reading permission. */
@RunWith(AndroidJUnit4.class)
public final class CrossPackagePickerTest {
    private static final String TARGET="com.twobornot.imageorder";
    private static final String FIXTURE=TARGET+".CrossAppMediaFixtureActivity";
    private static final int[] TAP_ORDER={2,0,1};
    private static final int[] FIVE_ORDER={4,1,3,0,2};

    @Test public void actualExternalAppGetsReadableOriginalsInTapOrder() throws Exception {
        verifyCrossUidRoundTrip("image/png");
    }
    @Test public void genericWildcardUploadAlsoGrantsOriginalsInTapOrder() throws Exception {
        verifyCrossUidRoundTrip("*/*");
    }

    @Test public void genericImageWildcardAlsoPreservesTapOrder() throws Exception {
        verifyCrossUidRoundTrip("image/*");
    }
    @Test public void singleImageRequestReturnsOriginalWithReadGrant() throws Exception {
        verifyCrossUidRoundTrip("image/png",false);
    }
    @Test public void fiveMixedMimeOriginalsKeepExplicitTapOrderAcrossApps() throws Exception {
        verifyCrossUidRoundTrip("image/*",true,5,true);
    }
    @Test public void externalCallerKeepsVerifiedOrderThroughScreenRotation() throws Exception {
        // This invokes an independent application UID, not a same-process picker test.
        verifyCrossUidRoundTrip("image/png",true,3,false,Intent.ACTION_GET_CONTENT,false,true);
    }
    @Test public void duplicateNamesAcrossAlbumsAndReselectionPreserveOriginalIdentity() throws Exception {
        verifyCrossUidRoundTrip("image/png",true,3,false,Intent.ACTION_GET_CONTENT,false,false,true);
    }
    @Test public void actionPickWithMediaStoreUriAndMimeReturnsOneOriginal() throws Exception {
        verifyCrossUidRoundTrip("image/*",false,3,false,Intent.ACTION_PICK,false);
    }
    @Test public void actionPickWithUriOnlyReturnsOneOriginal() throws Exception {
        verifyCrossUidRoundTrip("image/*",false,3,false,Intent.ACTION_PICK,true);
    }
    private void verifyCrossUidRoundTrip(String requestedMime) throws Exception {
        verifyCrossUidRoundTrip(requestedMime,true);
    }
    private void verifyCrossUidRoundTrip(String requestedMime,boolean allowMultiple) throws Exception {
        verifyCrossUidRoundTrip(requestedMime,allowMultiple,3,false);
    }
    private void verifyCrossUidRoundTrip(String requestedMime,boolean allowMultiple,int fixtureCount,boolean mixed) throws Exception {
        verifyCrossUidRoundTrip(requestedMime,allowMultiple,fixtureCount,mixed,Intent.ACTION_GET_CONTENT,false);
    }
    private void verifyCrossUidRoundTrip(String requestedMime,boolean allowMultiple,int fixtureCount,boolean mixed,
            String pickerAction,boolean uriOnlyPick) throws Exception {
        verifyCrossUidRoundTrip(requestedMime,allowMultiple,fixtureCount,mixed,pickerAction,uriOnlyPick,false);
    }
    private void verifyCrossUidRoundTrip(String requestedMime,boolean allowMultiple,int fixtureCount,boolean mixed,
            String pickerAction,boolean uriOnlyPick,boolean rotateMidSelection) throws Exception {
        verifyCrossUidRoundTrip(requestedMime,allowMultiple,fixtureCount,mixed,pickerAction,uriOnlyPick,rotateMidSelection,false);
    }
    private void verifyCrossUidRoundTrip(String requestedMime,boolean allowMultiple,int fixtureCount,boolean mixed,
            String pickerAction,boolean uriOnlyPick,boolean rotateMidSelection,boolean duplicateNames) throws Exception {
        Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
        Context context=instrumentation.getTargetContext();
        PackageManager pm=context.getPackageManager();
        assertEquals("Caller must be a different package", "com.twobornot.imageorder.caller",context.getPackageName());
        assertEquals("Caller MUST lack read permission",PackageManager.PERMISSION_DENIED,
            pm.checkPermission((android.os.Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE),context.getPackageName()));
        assertNotEquals("Caller and picker must have different UIDs",
            pm.getApplicationInfo(TARGET,0).uid,pm.getApplicationInfo(context.getPackageName(),0).uid);
        instrumentation.getUiAutomation().grantRuntimePermission(TARGET,(android.os.Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE));
        AttachmentCallerActivity.reset();
        UiDevice device=UiDevice.getInstance(instrumentation);
        Intent start=new Intent(context,AttachmentCallerActivity.class);
        start.putExtra("requestedMime",requestedMime);
        start.putExtra("allowMultiple",allowMultiple);
        start.putExtra("testCount",fixtureCount);
        start.putExtra("testMixed",mixed);
        start.putExtra("testDuplicateNames",duplicateNames);
        start.putExtra("pickerAction",pickerAction);
        start.putExtra("uriOnlyPick",uriOnlyPick);
        // Every case must start a clean caller task. In API 34 a prior failed case can
        // leave its old Activity on the task stack, bypassing fixture onCreate.
        start.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        context.startActivity(start); // asynchronous cross-app launch: do not block test instrumentation idle
        try {
            UiObject2 tab=null;
            for(int attempt=0;attempt<20 && tab==null;attempt++){
                tab=device.wait(Until.findObject(By.desc("imageorder.photos")),2000);
                if(tab==null){
                    // API 34 emulator sometimes displays a crashed Pixel Launcher dialog
                    // *over* the already-open gallery. Do not misreport an OS ANR as
                    // a gallery defect. Dismiss only this known launcher dialog.
                    UiObject2 launcherAnr=device.findObject(By.textContains("Pixel Launcher"));
                    UiObject2 dismiss=device.findObject(By.text("Close app"));
                    if(launcherAnr!=null && dismiss!=null){
                        android.util.Log.w("ImageOrderFlow","Dismissing emulator Pixel Launcher ANR obstructing picker");
                        dismiss.click();
                    }
                }
            }
            if(tab==null)captureFailure(instrumentation,requestedMime,"gallery-not-found");
            assertNotNull("Picker gallery must appear for external "+pickerAction,tab);
            clickFresh(device,"imageorder.photos",15000);
            String[] names=AttachmentCallerActivity.names;
            for(int attempt=0;names==null && attempt<16;attempt++){
                Thread.sleep(250);
                names=AttachmentCallerActivity.names;
            }
            if(names==null)captureFailure(instrumentation,requestedMime,"fixture-metadata-missing");
            assertNotNull("Target-owned photo fixtures must be returned as metadata",names);
            assertEquals(fixtureCount,names.length);
            assertNotNull("Fixture must also supply real MIME types",AttachmentCallerActivity.mimes);
            assertEquals(fixtureCount,AttachmentCallerActivity.mimes.length);
            assertFalse("Before user selection caller must NOT be able to open target-owned files",
                AttachmentCallerActivity.hadAccessBeforeUserSelection);
            int[] selectedOrder=duplicateNames?new int[]{2,1,0}:!allowMultiple?new int[]{TAP_ORDER[0]}:fixtureCount==5?FIVE_ORDER:TAP_ORDER;
            int expectedCount=0;
            if(duplicateNames){
                assertEquals(names[0],names[1]);assertEquals(names[1],names[2]);
                assertNotEquals(AttachmentCallerActivity.hashes[0],AttachmentCallerActivity.hashes[1]);
                assertNotEquals(AttachmentCallerActivity.hashes[1],AttachmentCallerActivity.hashes[2]);
                // Every album contains one uniquely identified original with the SAME name.
                // Select 3,1,2, remove 1, then reselect 1. The final order must be 3,2,1.
                int[] taps={2,0,1,0,0};
                int[] counts={1,2,3,2,3};
                String prefix=names[0].replace("imageorder_crossuid_","").replace("_same.png","");
                for(int k=0;k<taps.length;k++){
                    clickFresh(device,"imageorder.albums",15000);
                    clickFresh(device,"imageorder.album:IO_"+prefix+"_"+taps[k],30000);
                    clickPhotoAndWaitForCount(device,"imageorder.photo:"+names[taps[k]],counts[k]);
                }
            }else for(int index:selectedOrder) {
                String desc="imageorder.photo:"+names[index];
                if(allowMultiple)clickPhotoAndWaitForCount(device,desc,++expectedCount);
                else clickFresh(device,desc,30000);
                if(rotateMidSelection && expectedCount==2) {
                    // The native picker has no configChanges override, so this exercises
                    // real Android Activity save/restore while the caller remains pending.
                    device.setOrientationLeft();
                    device.waitForIdle(10000);
                    assertTrue("Rotation must place the device in landscape",
                        device.getDisplayWidth()>device.getDisplayHeight());
                    assertTrue("Two ordered selections must survive landscape recreation",
                        waitForSelectionCount(device,2,12000));
                    device.setOrientationNatural();
                    device.waitForIdle(10000);
                    assertTrue("Two selections must survive portrait recreation",
                        waitForSelectionCount(device,2,12000));
                }
            }
            boolean returned;
            if(allowMultiple) {
            UiObject2 done=device.wait(Until.findObject(By.desc("imageorder.confirm")),15000);
            assertNotNull("Gallery Done button",done);
            assertTrue("All taps must be recognized before returning. Actual label: "+done.getText(),
                done.getText()!=null && done.getText().trim().endsWith(String.valueOf(selectedOrder.length)));
            // Distinguish input routing problems from cross-UID result/grant failures.
            android.graphics.Rect doneRect=done.getVisibleBounds();
            android.util.Log.i("ImageOrderFlow","Confirm probe: bounds="+doneRect
                +"; text="+done.getText()+"; display="+device.getDisplayWidth()+"x"+device.getDisplayHeight()
                +"; foreground="+device.getCurrentPackageName());
            done.click();
            returned=AttachmentCallerActivity.done.await(4,TimeUnit.SECONDS);
            if(!returned && device.hasObject(By.desc("imageorder.confirm"))){
                android.util.Log.w("ImageOrderFlow","Accessibility click did not deliver result; inject physical coordinates");
                assertTrue("Coordinate input must inject",device.click(doneRect.centerX(),doneRect.centerY()));
                returned=AttachmentCallerActivity.done.await(4,TimeUnit.SECONDS);
            }
            if(!returned && device.hasObject(By.desc("imageorder.confirm"))){
                android.util.Log.w("ImageOrderFlow","Shell-level physical tap as independent input route");
                try(android.os.ParcelFileDescriptor fd=instrumentation.getUiAutomation().executeShellCommand(
                    "input tap "+doneRect.centerX()+" "+doneRect.centerY())){}
                returned=AttachmentCallerActivity.done.await(6,TimeUnit.SECONDS);
            }
            if(!returned){
                java.io.File diagnostics=context.getExternalFilesDir(null);
                if(diagnostics!=null){
                    String label=requestedMime.equals("*/*")?"wildcard":"png";
                    try{device.takeScreenshot(new java.io.File(diagnostics,"imageorder-"+label+"-failure.png"));}
                    catch(Exception ex){android.util.Log.e("ImageOrderFlow","Screenshot capture failed",ex);}
                    try{device.dumpWindowHierarchy(new java.io.File(diagnostics,"imageorder-"+label+"-hierarchy.xml"));}
                    catch(Exception ex){android.util.Log.e("ImageOrderFlow","Hierarchy capture failed",ex);}
                }
                captureFailure(instrumentation,requestedMime,"done-not-returned");
                android.util.Log.e("ImageOrderFlow",
                    "No result after three input methods: currentPackage="+device.getCurrentPackageName()
                    +"; request="+requestedMime+"; bounds="+doneRect+"; error="+AttachmentCallerActivity.error);
            }
            } else {
                returned=AttachmentCallerActivity.done.await(15,TimeUnit.SECONDS);
                if(!returned)captureFailure(instrumentation,requestedMime,"single-auto-return");
            }
            assertTrue("Independent app must receive Activity RESULT_OK ("+AttachmentCallerActivity.error+")",returned);
            assertNull("Result path must not fail",AttachmentCallerActivity.error);
            assertEquals(Activity.RESULT_OK,AttachmentCallerActivity.resultCode);
            Intent result=AttachmentCallerActivity.resultData;
            assertNotNull(result);
            assertEquals("Intent MIME must describe the original collection",mixed?"image/*":"image/png",result.getType());
            assertTrue("Result must include URI grant",(result.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            assertEquals(0,result.getFlags()&Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            ClipData clip=result.getClipData();assertNotNull(clip);
            assertEquals(selectedOrder.length,clip.getItemCount());
            if(!allowMultiple)assertEquals("Single selection data URI",clip.getItemAt(0).getUri(),result.getData());
            ContentResolver cr=context.getContentResolver();
            for(int i=0;i<selectedOrder.length;i++) {
                int source=selectedOrder[i];
                Uri uri=clip.getItemAt(i).getUri();
                assertNotNull(uri);
                assertEquals("No image substitution or reordering",
                    android.content.ContentUris.parseId(Uri.parse(AttachmentCallerActivity.uriStrings[source])),
                    android.content.ContentUris.parseId(uri));
                assertEquals("Original MIME must not be substituted",AttachmentCallerActivity.mimes[source],cr.getType(uri));
                assertEquals("Temporary read grant must be received in foreign UID",
                    PackageManager.PERMISSION_GRANTED,
                    context.checkUriPermission(uri,android.os.Process.myPid(),android.os.Process.myUid(),Intent.FLAG_GRANT_READ_URI_PERMISSION));
                try(Cursor c=cr.query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){
                    assertNotNull(c);assertTrue(c.moveToFirst());
                    assertEquals(AttachmentCallerActivity.names[source],c.getString(0));
                }
                try(InputStream in=cr.openInputStream(uri)) {
                    assertNotNull("Cross-UID original stream must be readable",in);
                    MessageDigest digest=MessageDigest.getInstance("SHA-256");
                    byte[] buf=new byte[8192];int size;
                    while((size=in.read(buf))!=-1)digest.update(buf,0,size);
                    assertEquals("Original byte SHA-256 must be unchanged",AttachmentCallerActivity.hashes[source],hex(digest.digest()));
                }
            }
        }finally{
            // Restore emulator state so that subsequent cross-UID tests are independent.
            if(rotateMidSelection) {
                try{device.setOrientationNatural();}catch(Exception ignored){}
            }
            String[] saved=AttachmentCallerActivity.uriStrings;
            if(saved!=null) {
                Intent cleanup=new Intent();cleanup.setComponent(new ComponentName(TARGET,FIXTURE));
                cleanup.putExtra("test_cleanup_uri_strings",saved);
                cleanup.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try{context.startActivity(cleanup);}catch(Exception ignored){}
            }
            device.pressBack();
            device.pressBack();
            device.pressHome();
        }
    }
    /**
     * A successful UiAutomator click only guarantees input injection, not that a
     * rapidly re-rendered gallery registered a change. Check the VISIBLE
     * selection counter before sending the next, ordered user tap.
     */
    private static void clickPhotoAndWaitForCount(UiDevice device,String desc,int expected) throws Exception {
        for(int attempt=0;attempt<3;attempt++){
            clickFresh(device,desc,30000);
            if(waitForSelectionCount(device,expected,3500))return;
            android.util.Log.w("ImageOrderFlow",
                "Expected selected count "+expected+" after "+desc+"; resync attempt="+attempt);
        }
        fail("Gallery did not commit user tap #"+expected+" for "+desc);
    }
    private static boolean waitForSelectionCount(UiDevice device,int expected,long millis) throws Exception {
        long end=android.os.SystemClock.uptimeMillis()+millis;
        while(android.os.SystemClock.uptimeMillis()<end){
            UiObject2 count=device.wait(Until.findObject(By.desc("imageorder.confirm")),400);
            if(count!=null){
                try{
                    String value=count.getText();
                    if(value!=null && value.trim().endsWith(" "+expected))return true;
                }catch(androidx.test.uiautomator.StaleObjectException ignored){}
            }
            Thread.sleep(100);
        }
        return false;
    }
    /**
     * GridView replaces visible tile nodes after each numbered selection.
     * A UiObject2 from the preceding layout becomes stale mid-click on API 33/34.
     * Re-acquire each node by its unique content description, and only retry
     * the UiAutomator stale-node exception (not an app-level result failure).
     */
    private static void clickFresh(UiDevice device,String description,long timeoutMs) throws Exception {
        final long deadline=android.os.SystemClock.uptimeMillis()+timeoutMs;
        androidx.test.uiautomator.StaleObjectException stale=null;
        while(android.os.SystemClock.uptimeMillis()<deadline){
            UiObject2 current=device.wait(Until.findObject(By.desc(description)),2000);
            if(current==null)continue;
            try{
                current.click();
                return;
            }catch(androidx.test.uiautomator.StaleObjectException e){
                stale=e;
                android.util.Log.w("ImageOrderFlow","Recycler UI node stale during click: "+description+"; reacquiring");
                Thread.sleep(150);
            }
        }
        if(stale!=null)throw new AssertionError("UI never stabilized for "+description,stale);
        fail("Expected gallery item is missing: "+description);
    }

    /** Keep emulator evidence outside the instrumented APK's auto-removed app data. */
    private static void captureFailure(Instrumentation inst,String mime,String reason){
        String label=mime.equals("*/*")?"wildcard":"png";
        String path="/sdcard/Download/imageorder-"+label+"-"+reason+".png";
        try(android.os.ParcelFileDescriptor shell=inst.getUiAutomation().executeShellCommand(
                "screencap -p "+path);
            java.io.InputStream out=new android.os.ParcelFileDescriptor.AutoCloseInputStream(shell)){
            byte[] buffer=new byte[128];while(out.read(buffer)!=-1){}
            android.util.Log.i("ImageOrderFlow","Saved emulator screenshot: "+path);
        }catch(Exception ex){android.util.Log.e("ImageOrderFlow","Cannot save screenshot "+path,ex);}
    }

    private static String hex(byte[] bytes){
        char[] h="0123456789abcdef".toCharArray();StringBuilder o=new StringBuilder(bytes.length*2);
        for(byte b:bytes){o.append(h[(b>>>4)&15]);o.append(h[b&15]);}
        return o.toString();
    }
}
