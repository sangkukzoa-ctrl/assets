package com.twobornot.imageorder.caller;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.provider.MediaStore;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.concurrent.TimeUnit;
import org.junit.Assume;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public final class DirectPhotoPickerTrialTest {
    private static final String TARGET="com.twobornot.imageorder";
    @Test public void firstPhotoPickerWithoutPackageOrChooser() throws Exception {
        Assume.assumeTrue("Dedicated direct picker trial only",
            "true".equals(InstrumentationRegistry.getArguments().getString("directQa")));
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        PackageManager pm=ctx.getPackageManager();
        assertNotEquals(pm.getApplicationInfo(TARGET,0).uid,pm.getApplicationInfo(ctx.getPackageName(),0).uid);
        assertEquals(PackageManager.PERMISSION_DENIED,pm.checkPermission(
            android.Manifest.permission.READ_MEDIA_IMAGES,ctx.getPackageName()));
        TestMediaPermissions.grant(inst);
        AttachmentCallerActivity.reset();
        UiDevice device=UiDevice.getInstance(inst);
        Intent start=new Intent(ctx,AttachmentCallerActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK)
            .putExtra("pickerAction",MediaStore.ACTION_PICK_IMAGES)
            .putExtra("requestedMime","image/*").putExtra("testCount",5)
            .putExtra("testMixed",true).putExtra("allowMultiple",true);
        ctx.startActivity(start);
        try{
            assertTrue("Direct caller did not launch",AttachmentCallerActivity.directDispatched.await(60,TimeUnit.SECONDS));
            assertNull(AttachmentCallerActivity.error);
            assertFalse("Caller had original before selection",AttachmentCallerActivity.hadAccessBeforeUserSelection);
            assertNotNull("Resolver missing",AttachmentCallerActivity.directResolved);
            long until=android.os.SystemClock.uptimeMillis()+25000;
            String foreground=null;
            while(android.os.SystemClock.uptimeMillis()<until){
                foreground=device.getCurrentPackageName();
                if(TARGET.equals(foreground)&&device.hasObject(By.desc("imageorder.photos")))break;
                if(foreground!=null&&(foreground.contains("providers.media")||foreground.contains("photopicker"))){
                    // Observe the actual first system picker. Do not force a different activity.
                    android.util.Log.i("ImageOrderDirect","P0_BLOCKED first picker="+foreground+
                        " targetCandidate="+AttachmentCallerActivity.directCandidate+
                        " default="+AttachmentCallerActivity.directResolved);
                    // Save evidence before leaving the first picker, not merely the caller afterward.
                    java.io.ByteArrayOutputStream firstXml=new java.io.ByteArrayOutputStream();
                    device.dumpWindowHierarchy(firstXml);
                    android.util.Log.i("ImageOrderDirect","First picker hierarchy="+firstXml.toString("UTF-8"));
                    device.pressBack();
                    assertTrue("Canceled picker must return",AttachmentCallerActivity.done.await(15,TimeUnit.SECONDS));
                    assertEquals(Activity.RESULT_CANCELED,AttachmentCallerActivity.resultCode);
                    return;
                }
                Thread.sleep(350);
            }
            assertEquals("First picker foreground (unexpected or chooser)",TARGET,foreground);
            UiObject2 photos=device.wait(Until.findObject(By.desc("imageorder.photos")),15000);
            assertNotNull("Native gallery not visible",photos);photos.click();
            assertNotNull(AttachmentCallerActivity.names);
            assertEquals(5,AttachmentCallerActivity.names.length);
            int[] order={4,1,3,0,2};int n=0;
            for(int index:order)WebUploadCallerTest.clickPhotoAndWaitForCount(device,
                "imageorder.photo:"+AttachmentCallerActivity.names[index],++n);
            UiObject2 done=device.wait(Until.findObject(By.desc("imageorder.confirm")),15000);
            assertNotNull(done);done.click();
            assertTrue("Result not delivered",AttachmentCallerActivity.done.await(30,TimeUnit.SECONDS));
            assertEquals(Activity.RESULT_OK,AttachmentCallerActivity.resultCode);
            Intent result=AttachmentCallerActivity.resultData;assertNotNull(result);assertNotNull(result.getClipData());
            assertEquals(5,result.getClipData().getItemCount());
            for(int i=0;i<order.length;i++){
                Uri uri=result.getClipData().getItemAt(i).getUri();assertNotNull(uri);
                assertEquals(AttachmentCallerActivity.mimes[order[i]],ctx.getContentResolver().getType(uri));
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                try(InputStream in=ctx.getContentResolver().openInputStream(uri)){
                    assertNotNull(in);byte[] buf=new byte[8192];int count;
                    while((count=in.read(buf))!=-1)digest.update(buf,0,count);
                }
                StringBuilder hex=new StringBuilder();
                for(byte b:digest.digest())hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
                assertEquals(AttachmentCallerActivity.hashes[order[i]],hex.toString());
            }
            android.util.Log.i("ImageOrderDirect","P0_NATIVE_SUCCESS five originals in tap order");
        }finally{
            try{
                java.io.ByteArrayOutputStream xml=new java.io.ByteArrayOutputStream();
                device.dumpWindowHierarchy(xml);
                android.util.Log.i("ImageOrderDirect","End hierarchy="+xml.toString("UTF-8"));
            }catch(Exception ignored){}
            if(AttachmentCallerActivity.uriStrings!=null){
                Intent cleanup=new Intent().setComponent(new android.content.ComponentName(TARGET,TARGET+".CrossAppMediaFixtureActivity"))
                    .putExtra("test_cleanup_uri_strings",AttachmentCallerActivity.uriStrings)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try{ctx.startActivity(cleanup);}catch(Exception ignored){}
            }
        }
    }
}
