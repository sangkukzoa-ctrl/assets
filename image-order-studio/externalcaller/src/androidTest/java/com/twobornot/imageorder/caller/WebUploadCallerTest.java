package com.twobornot.imageorder.caller;

import android.Manifest;
import android.app.Activity;
import android.app.Instrumentation;
import android.content.ComponentName;
import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Real local HTML input -> WebChromeClient -> external Image Order -> HTML FileList. */
@RunWith(AndroidJUnit4.class)
public final class WebUploadCallerTest {
    private static final String TARGET="com.twobornot.imageorder";
    private static final int[] ORDER={4,1,3,0,2};
    @Test public void localHtmlMultiUploadPreservesOriginalFilesAndTapOrder() throws Exception {
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        PackageManager pm=ctx.getPackageManager();
        assertNotEquals(pm.getApplicationInfo(TARGET,0).uid,
            pm.getApplicationInfo(ctx.getPackageName(),0).uid);
        assertEquals(PackageManager.PERMISSION_DENIED,
            pm.checkPermission((android.os.Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE),ctx.getPackageName()));
        TestMediaPermissions.grant(inst);
        WebUploadCallerActivity.reset();
        Intent launch=new Intent(ctx,WebUploadCallerActivity.class);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
        ctx.startActivity(launch);
        UiDevice device=UiDevice.getInstance(inst);
        try{
            assertTrue("Local HTML page did not load: "+WebUploadCallerActivity.error,
                WebUploadCallerActivity.ready.await(30,TimeUnit.SECONDS));
            assertNull("HTML page initialization",WebUploadCallerActivity.error);
            UiObject2 label=device.wait(Until.findObject(By.text("Choose photos to upload")),5000);
            if(label!=null)label.click();
            else{
                assertTrue("HTML file input tap position missing",WebUploadCallerActivity.tapX>0
                    && WebUploadCallerActivity.tapY>0);
                assertTrue("Inject real touch onto HTML label",device.click(
                    WebUploadCallerActivity.tapX,WebUploadCallerActivity.tapY));
            }
            UiObject2 photos=device.wait(Until.findObject(By.desc("imageorder.photos")),30000);
            assertNotNull("The actual WebView HTML file input must launch Image Order",photos);
            photos.click();
            assertNotNull("Fixture metadata",WebUploadCallerActivity.names);
            assertEquals(5,WebUploadCallerActivity.names.length);
            int expected=0;
            for(int i:ORDER){
                String desc="imageorder.photo:"+WebUploadCallerActivity.names[i];
                clickPhotoAndWaitForCount(device,desc,++expected);
            }
            UiObject2 done=device.wait(Until.findObject(By.desc("imageorder.confirm")),15000);
            assertNotNull("Picker Done",done);
            assertTrue("Five selected originals must be shown",done.getText().trim().endsWith("5"));
            done.click();
            assertTrue("HTML onchange/FileList must receive images: "+WebUploadCallerActivity.error,
                WebUploadCallerActivity.finished.await(25,TimeUnit.SECONDS));
            assertNull("WebView file chooser must complete",WebUploadCallerActivity.error);
            assertEquals(Activity.RESULT_OK,WebUploadCallerActivity.rawCode);
            assertNotNull(WebUploadCallerActivity.rawResult);
            assertTrue((WebUploadCallerActivity.rawResult.getFlags()
                & Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            Uri[] actual=WebUploadCallerActivity.parsedUris;
            assertNotNull("Ordered ClipData compatibility parser must return all files",actual);
            assertEquals(5,actual.length);
            Uri[] framework=WebUploadCallerActivity.frameworkParsedUris;
            if(framework!=null){
                assertTrue("Framework may parse only one file; fallback must preserve all",
                    framework.length<=actual.length);
            }
            JSONArray html=new JSONArray(WebUploadCallerActivity.domFilesJson);
            assertEquals("Real DOM input.files length",5,html.length());
            ContentResolver cr=ctx.getContentResolver();
            for(int position=0;position<ORDER.length;position++){
                int originalIndex=ORDER[position];
                Uri uri=actual[position];
                assertEquals("WebView file order must follow taps",
                    android.content.ContentUris.parseId(Uri.parse(
                        WebUploadCallerActivity.uriStrings[originalIndex])),
                    android.content.ContentUris.parseId(uri));
                assertEquals(PackageManager.PERMISSION_GRANTED,ctx.checkUriPermission(
                    uri,android.os.Process.myPid(),android.os.Process.myUid(),
                    Intent.FLAG_GRANT_READ_URI_PERMISSION));
                String name;
                long size;
                try(Cursor c=cr.query(uri,new String[]{OpenableColumns.DISPLAY_NAME,
                        OpenableColumns.SIZE},null,null,null)){
                    assertNotNull(c);assertTrue(c.moveToFirst());
                    name=c.getString(0);size=c.getLong(1);
                }
                JSONObject f=html.getJSONObject(position);
                assertEquals("Real WebView DOM FileList must preserve name/order",name,f.getString("name"));
                assertEquals(WebUploadCallerActivity.names[originalIndex],name);
                assertEquals(WebUploadCallerActivity.mimes[originalIndex],f.getString("type"));
                assertEquals(size,f.getLong("size"));
                assertEquals(WebUploadCallerActivity.hashes[originalIndex],sha256(cr,uri));
            }
        }finally{
            if(WebUploadCallerActivity.uriStrings!=null){
                Intent cleanup=new Intent().setComponent(new ComponentName(
                    TARGET,TARGET+".CrossAppMediaFixtureActivity"));
                cleanup.putExtra("test_cleanup_uri_strings",WebUploadCallerActivity.uriStrings);
                cleanup.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try{ctx.startActivity(cleanup);}catch(Exception ignored){}
            }
            device.pressBack();device.pressHome();
        }
    }
    private static void clickPhotoAndWaitForCount(UiDevice device,String desc,int expected) throws Exception {
        for(int retry=0;retry<3;retry++){
            clickFresh(device,desc);
            long deadline=android.os.SystemClock.uptimeMillis()+3500;
            while(android.os.SystemClock.uptimeMillis()<deadline){
                UiObject2 done=device.wait(Until.findObject(By.desc("imageorder.confirm")),400);
                if(done!=null){
                    try{
                        String count=done.getText();
                        if(count!=null && count.trim().endsWith(" "+expected))return;
                    }catch(androidx.test.uiautomator.StaleObjectException ignored){}
                }
                Thread.sleep(100);
            }
        }
        fail("WebView target gallery did not commit photo tap #"+expected+" for "+desc);
    }
    private static void clickFresh(UiDevice d,String desc) throws Exception{
        for(int retry=0;retry<25;retry++){
            UiObject2 node=d.wait(Until.findObject(By.desc(desc)),1200);
            if(node==null)continue;
            try{node.click();return;}
            catch(androidx.test.uiautomator.StaleObjectException ignored){
                Thread.sleep(150);
            }
        }
        fail("Visible image tile not clickable: "+desc);
    }
    private static String sha256(ContentResolver cr,Uri uri) throws Exception{
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        try(InputStream in=cr.openInputStream(uri)){
            assertNotNull(in);byte[] buffer=new byte[4096];int n;
            while((n=in.read(buffer))!=-1)md.update(buffer,0,n);
        }
        StringBuilder out=new StringBuilder();
        for(byte b:md.digest())out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        return out.toString();
    }
}
