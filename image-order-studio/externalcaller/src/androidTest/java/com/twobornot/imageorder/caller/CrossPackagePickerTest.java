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

    @Test public void actualExternalAppGetsReadableOriginalsInTapOrder() throws Exception {
        verifyCrossUidRoundTrip("image/png");
    }
    @Test public void genericWildcardUploadAlsoGrantsOriginalsInTapOrder() throws Exception {
        verifyCrossUidRoundTrip("*/*");
    }

    private void verifyCrossUidRoundTrip(String requestedMime) throws Exception {
        Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
        Context context=instrumentation.getTargetContext();
        PackageManager pm=context.getPackageManager();
        assertEquals("Caller must be a different package", "com.twobornot.imageorder.caller",context.getPackageName());
        assertEquals("Caller MUST lack read permission",PackageManager.PERMISSION_DENIED,
            pm.checkPermission(Manifest.permission.READ_MEDIA_IMAGES,context.getPackageName()));
        assertNotEquals("Caller and picker must have different UIDs",
            pm.getApplicationInfo(TARGET,0).uid,pm.getApplicationInfo(context.getPackageName(),0).uid);
        instrumentation.getUiAutomation().grantRuntimePermission(TARGET,Manifest.permission.READ_MEDIA_IMAGES);
        AttachmentCallerActivity.reset();
        UiDevice device=UiDevice.getInstance(instrumentation);
        Intent start=new Intent(context,AttachmentCallerActivity.class);
        start.putExtra("requestedMime",requestedMime);
        start.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        instrumentation.startActivitySync(start);
        try {
            UiObject2 tab=device.wait(Until.findObject(By.desc("imageorder.photos")),35000);
            assertNotNull("Picker gallery must appear in another app's GET_CONTENT",tab);
            tab.click();
            String[] names=AttachmentCallerActivity.names;
            assertNotNull("Target-owned photo fixtures must be returned as metadata",names);
            assertEquals(3,names.length);
            assertFalse("Before user selection caller must NOT be able to open target-owned files",
                AttachmentCallerActivity.hadAccessBeforeUserSelection);
            for(int index:TAP_ORDER) {
                UiObject2 photo=device.wait(Until.findObject(By.desc("imageorder.photo:"+names[index])),30000);
                assertNotNull("Photo must be visible to target gallery: "+names[index],photo);
                photo.click();
            }
            UiObject2 done=device.wait(Until.findObject(By.desc("imageorder.confirm")),15000);
            assertNotNull("Gallery Done button",done);
            done.click();
            assertTrue("Independent app must receive Activity RESULT_OK ("+AttachmentCallerActivity.error+")",
                AttachmentCallerActivity.done.await(30,TimeUnit.SECONDS));
            assertNull("Result path must not fail",AttachmentCallerActivity.error);
            assertEquals(Activity.RESULT_OK,AttachmentCallerActivity.resultCode);
            Intent result=AttachmentCallerActivity.resultData;
            assertNotNull(result);
            assertTrue("Result must include URI grant",(result.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            assertEquals(0,result.getFlags()&Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            ClipData clip=result.getClipData();assertNotNull(clip);
            assertEquals(3,clip.getItemCount());
            ContentResolver cr=context.getContentResolver();
            for(int i=0;i<3;i++) {
                int source=TAP_ORDER[i];
                Uri uri=clip.getItemAt(i).getUri();
                assertNotNull(uri);
                assertEquals("No image substitution or reordering",
                    android.content.ContentUris.parseId(Uri.parse(AttachmentCallerActivity.uriStrings[source])),
                    android.content.ContentUris.parseId(uri));
                assertEquals("image/png",cr.getType(uri));
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
            String[] saved=AttachmentCallerActivity.uriStrings;
            if(saved!=null) {
                Intent cleanup=new Intent();cleanup.setComponent(new ComponentName(TARGET,FIXTURE));
                cleanup.putExtra("test_cleanup_uri_strings",saved);
                cleanup.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try{context.startActivity(cleanup);}catch(Exception ignored){}
            }
            device.pressHome();
        }
    }
    private static String hex(byte[] bytes){
        char[] h="0123456789abcdef".toCharArray();StringBuilder o=new StringBuilder(bytes.length*2);
        for(byte b:bytes){o.append(h.charAt((b>>>4)&15));o.append(h.charAt(b&15));}
        return o.toString();
    }
}
