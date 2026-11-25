package com.twobornot.imageorder.caller;

import android.app.Instrumentation;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.ParcelFileDescriptor;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import org.junit.Assume;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Real Chrome, actual multipart HTTP, never WebView or a patched browser file chooser. */
@RunWith(AndroidJUnit4.class)
public final class ChromeUploadTest {
    private static final String CHROME="com.android.chrome",TARGET="com.twobornot.imageorder";
    private static final int[] ORDER={4,1,3,0,2};
    @Test public void chromeImageInputUploadsOriginalsInTapOrder() throws Exception {verify(false);}
    @Test public void chromeGenericInputUploadsOriginalsInTapOrder() throws Exception {verify(true);}
    private void verify(boolean generic) throws Exception {
        Assume.assumeTrue("Dedicated real-browser CI only",
            "true".equals(InstrumentationRegistry.getArguments().getString("chromeQa")));
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        PackageManager pm=ctx.getPackageManager();
        assertNotEquals(pm.getApplicationInfo(CHROME,0).uid,pm.getApplicationInfo(TARGET,0).uid);
        assertNotEquals(pm.getApplicationInfo(CHROME,0).uid,pm.getApplicationInfo(ctx.getPackageName(),0).uid);
        android.util.Log.i("ImageOrderChrome","Chrome version="+pm.getPackageInfo(CHROME,0).versionName+" generic="+generic);
        TestMediaPermissions.grant(inst);
        UiDevice device=UiDevice.getInstance(inst);
        ChromeUploadFixtureActivity.reset();
        Intent start=new Intent(ctx,ChromeUploadFixtureActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK)
            .putExtra("generic",generic);
        ctx.startActivity(start);
        try{
            assertTrue("Chrome launch timed out",ChromeUploadFixtureActivity.ready.await(30,TimeUnit.SECONDS));
            assertNull("Chrome launch failed",ChromeUploadFixtureActivity.error);
            LoopbackUploadServer server=ChromeUploadFixtureActivity.server;
            assertNotNull(server);
            assertTrue("Chrome did not load the real test page",server.pageServed.await(45,TimeUnit.SECONDS));
            UiObject2 input=device.wait(Until.findObject(By.text("Choose originals for Chrome test")),20000);
            if(input==null)input=device.findObject(By.desc("Choose originals for Chrome test"));
            assertNotNull("Real Chrome file input must be visible",input);
            assertEquals("Actual installed Chrome UI",CHROME,device.getCurrentPackageName());
            input.click();
            WebUploadCallerTest.selectRealSystemGallery(device);
            UiObject2 photos=device.wait(Until.findObject(By.desc("imageorder.photos")),15000);
            assertNotNull("Image Order native gallery must open from Chrome",photos);
            photos.click();
            int count=0;
            for(int source:ORDER)WebUploadCallerTest.clickPhotoAndWaitForCount(device,
                "imageorder.photo:"+ChromeUploadFixtureActivity.names[source],++count);
            UiObject2 done=device.wait(Until.findObject(By.desc("imageorder.confirm")),15000);
            assertNotNull(done);done.click();
            UiObject2 submit=device.wait(Until.findObject(By.text("Upload originals")),30000);
            assertNotNull("Chrome must return to the upload page",submit);
            assertEquals(CHROME,device.getCurrentPackageName());
            submit.click();
            assertTrue("Chrome did not POST selected files: "+server.error,server.received.await(30,TimeUnit.SECONDS));
            assertNull(server.error);
            assertNotNull("Browser User-Agent",server.uploadUserAgent);
            assertTrue("Real Chrome HTTP user agent: "+server.uploadUserAgent,server.uploadUserAgent.contains("Chrome/"));
            assertNotNull(server.parts);assertEquals(ORDER.length,server.parts.size());
            for(int pos=0;pos<ORDER.length;pos++){
                int source=ORDER[pos];LoopbackUploadServer.Part part=server.parts.get(pos);
                assertEquals("photos",part.field);
                assertEquals("Chrome server filename and order",ChromeUploadFixtureActivity.names[source],part.filename);
                assertEquals("Chrome server MIME",ChromeUploadFixtureActivity.mimes[source],part.mime);
                StringBuilder hex=new StringBuilder();
                for(byte b:MessageDigest.getInstance("SHA-256").digest(part.bytes))
                    hex.append(String.format(Locale.ROOT,"%02x",b&255));
                assertEquals("Chrome server original SHA-256",ChromeUploadFixtureActivity.hashes[source],hex.toString());
            }
            android.util.Log.i("ImageOrderChrome","PASS real Chrome multipart, five originals in tap order");
        }catch(Throwable failure){
            try{
                java.io.ByteArrayOutputStream xml=new java.io.ByteArrayOutputStream();
                device.dumpWindowHierarchy(xml);
                android.util.Log.e("ImageOrderChrome",xml.toString("UTF-8"));
            }catch(Exception ignored){}
            try(InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(inst.getUiAutomation().executeShellCommand(
                "screencap -p /sdcard/Download/imageorder-chrome-"+(generic?"generic":"image")+".png"))){
                byte[] buf=new byte[256];while(in.read(buf)!=-1){}
            }catch(Exception ignored){}
            throw failure;
        }finally{
            if(ChromeUploadFixtureActivity.server!=null)ChromeUploadFixtureActivity.server.close();
            if(ChromeUploadFixtureActivity.uris!=null){
                Intent cleanup=new Intent().setComponent(new ComponentName(TARGET,TARGET+".CrossAppMediaFixtureActivity"))
                    .putExtra("test_cleanup_uri_strings",ChromeUploadFixtureActivity.uris)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try{ctx.startActivity(cleanup);}catch(Exception ignored){}
            }
            device.pressHome();
        }
    }
}
