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
        verifyUpload(false,false);
    }
    @Test public void actualHttpMultipartPreservesOriginalFilesAndTapOrder() throws Exception {
        verifyUpload(true,false);
    }
    @Test public void systemChooserCanSelectImageOrderAndUploadOriginals() throws Exception {
        verifyUpload(true,true);
    }
    private void verifyUpload(boolean http,boolean implicit) throws Exception {
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
        launch.putExtra("httpUpload",http);
        launch.putExtra("implicitChooser",implicit);
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
            if(implicit){
                // No package pinning, no forced component, no system-setting changes.
                selectRealSystemGallery(device);
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
            if(http){
                LoopbackUploadServer server=WebUploadCallerActivity.uploadServer;
                assertNotNull("Real HTTP receiver",server);
                assertTrue("Server did not receive multipart POST: "+server.error,
                    server.received.await(30,TimeUnit.SECONDS));
                assertNull("HTTP receiver error",server.error);
                assertNotNull(server.parts);
                assertEquals("Actual received multipart part count",ORDER.length,server.parts.size());
                for(int position=0;position<ORDER.length;position++){
                    int source=ORDER[position];
                    LoopbackUploadServer.Part part=server.parts.get(position);
                    assertEquals("Multipart field","photos",part.field);
                    assertEquals("Actual server filename/order",WebUploadCallerActivity.names[source],part.filename);
                    assertEquals("Actual server MIME",WebUploadCallerActivity.mimes[source],part.mime);
                    assertEquals("Actual server size",html.getJSONObject(position).getLong("size"),part.bytes.length);
                    assertEquals("Actual server SHA-256",WebUploadCallerActivity.hashes[source],sha256(part.bytes));
                }
            }
        }catch(Throwable failure){
            if(implicit){
                try{
                    java.io.ByteArrayOutputStream xml=new java.io.ByteArrayOutputStream();
                    device.dumpWindowHierarchy(xml);
                    android.util.Log.e("ImageOrderResolver","Final hierarchy: "+xml.toString("UTF-8"));
                }catch(Exception ignored){}
                android.util.Log.e("ImageOrderResolver","Resolver candidates: "+WebUploadCallerActivity.resolverDiagnostics);
                try(android.os.ParcelFileDescriptor shell=inst.getUiAutomation().executeShellCommand(
                        "screencap -p /sdcard/Download/imageorder-chooser-failure.png");
                    InputStream out=new android.os.ParcelFileDescriptor.AutoCloseInputStream(shell)){
                    byte[] b=new byte[256];while(out.read(b)!=-1){}
                }catch(Exception ignored){}
            }
            throw failure;
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
    static void selectRealSystemGallery(UiDevice device) throws Exception {
        selectRealSystemGallery(device,false);
    }
    static void selectRealSystemGallery(UiDevice device,boolean chromeCase) throws Exception {
        boolean nativeOnly=chromeCase && "true".equals(
            androidx.test.platform.app.InstrumentationRegistry.getArguments().getString("nativeOnlyQa"));
        boolean clickedNativeDocumentTile=false;
        long deadline=android.os.SystemClock.uptimeMillis()+(chromeCase?90000:60000);
        String previousPackage=null;
        long cameraApprovedAt=0;
        int permissionRetries=0;
        boolean awaitingPermissionReturn=false;
        int chooserActions=0;
        int clicks=0,drawerAttempts=0,menuAttempts=0,scrolls=0;
        while(android.os.SystemClock.uptimeMillis()<deadline){
            if(device.hasObject(By.desc("imageorder.photos"))){
                if(nativeOnly)assertTrue("Native-only trial must open via the ordinary DocumentsUI app tile",clickedNativeDocumentTile);
                return;
            }
            try{
                String foreground=device.getCurrentPackageName();
                if(!java.util.Objects.equals(previousPackage,foreground)){
                    android.util.Log.i("ImageOrderResolver","Picker foreground="+foreground);
                    previousPackage=foreground;
                    if(chromeCase)logVisiblePickerControls(device,foreground);
                }
                if(chromeCase && foreground!=null && foreground.contains("permissioncontroller")){
                    // Observed Chrome 113/124 camera permission prompt. Use the ordinary
                    // user-facing foreground-only grant on synthetic test devices.
                    UiObject2 message=device.findObject(By.textContains("Allow Chrome to take pictures and record video"));
                    if(message!=null){
                        UiObject2 allow=device.findObject(By.res(java.util.regex.Pattern.compile(
                            ".*:id/permission_allow_foreground_only_button")));
                        if(allow!=null){
                            android.util.Log.i("ImageOrderResolver","Accepting Chrome camera prompt via UI");
                            allow.click();
                            cameraApprovedAt=android.os.SystemClock.uptimeMillis();
                            awaitingPermissionReturn=true;
                            Thread.sleep(900);continue;
                        }
                    }
                    UiObject2 photosPermission=device.findObject(By.textContains("Allow Chrome to access photos and videos"));
                    if(photosPermission!=null){
                        // Only synthetic fixture images exist on this isolated QA device.
                        UiObject2 allowAll=device.findObject(By.res(java.util.regex.Pattern.compile(
                            ".*:id/permission_allow_all_button")));
                        if(allowAll==null)allowAll=device.findObject(By.text("Allow all"));
                        if(allowAll!=null){
                            android.util.Log.i("ImageOrderResolver","Accepting Chrome photo access on isolated QA device");
                            allowAll.click();
                            cameraApprovedAt=android.os.SystemClock.uptimeMillis();
                            awaitingPermissionReturn=true;
                            Thread.sleep(900);continue;
                        }
                    }
                }
                // The merged RootAndAppItem has a separate app-launch action.
                // Clicking its title opens SAF instead, which cannot guarantee tap order.
                UiObject2 open=device.findObject(By.desc("Open Image Order (Files)"));
                if(open==null)open=device.findObject(By.desc("Open Image Order"));
                if(open!=null && nativeOnly && foreground!=null && foreground.contains("documentsui")){
                    fail("Native-only trial still exposes merged provider/app action");
                }
                if(open!=null && !nativeOnly && clicks<5){
                    android.util.Log.i("ImageOrderResolver","Opening merged RootAndAppItem app action");
                    open.click();clicks++;Thread.sleep(900);continue;
                }
                UiObject2 once=device.findObject(By.text(java.util.regex.Pattern.compile("(?i)just once|only once")));
                if(once!=null){once.click();Thread.sleep(500);continue;}
                UiObject2 option=device.findObject(By.text("Image Order"));
                if(option==null)option=device.findObject(By.desc("Image Order"));
                boolean documentsEntry=foreground!=null&&foreground.contains("documentsui");
                if(option!=null && clicks<5 && (!nativeOnly||documentsEntry)){
                    if(nativeOnly){
                        assertFalse("Provider root must not be exposed in native-entry trial",
                            device.hasObject(By.text("Image Order (Files)")));
                        android.util.Log.i("ImageOrderResolver","Native-only trial: clicking ordinary Image Order tile in DocumentsUI");
                        clickedNativeDocumentTile=true;
                    }
                    android.util.Log.i("ImageOrderResolver","Opening standalone Image Order option");
                    option.click();clicks++;Thread.sleep(900);continue;
                }
                UiObject2 browse=device.findObject(By.text(java.util.regex.Pattern.compile("(?i)browse(?: files)?(?:\\.\\.\\.|…)?")));
                if(browse!=null){
                    android.util.Log.i("ImageOrderResolver","Selecting Photo Picker Browse");
                    browse.click();Thread.sleep(900);continue;
                }
                String current=device.getCurrentPackageName();
                boolean resolver=current!=null&&(current.contains("intentresolver")||
                    "android".equals(current));
                if(chromeCase && resolver){
                    // A real ACTION_CHOOSER can show camera/camcorder and Files as
                    // separate choices. Do not swipe a bottom sheet: it may dismiss.
                    UiObject2 files=null;
                    for(String label:new String[]{"Files","Browse files","Browse","Media picker","Photos & videos","Media"}){
                        files=device.findObject(By.pkg(current).text(label));
                        if(files==null)files=device.findObject(By.pkg(current).desc(label));
                        if(files!=null)break;
                    }
                    if(files!=null&&chooserActions<5){
                        android.util.Log.i("ImageOrderResolver","Opening actual system chooser file option "+files.getText());
                        files.click();chooserActions++;Thread.sleep(1000);continue;
                    }
                    Thread.sleep(500);continue;
                }
                boolean chrome="com.android.chrome".equals(current);
                if(chromeCase&&chrome){
                    // Chrome's own media chooser can offer a Files/Browse entry.
                    // Restrict this action to a picker UI, not the underlying web page.
                    boolean page=device.hasObject(By.text("Choose originals for Chrome test"));
                    if(page && cameraApprovedAt>0 && awaitingPermissionReturn && permissionRetries<2
                            && android.os.SystemClock.uptimeMillis()-cameraApprovedAt>=2500){
                        // Chrome 124 returned to the unchanged HTML form after the
                        // first camera grant. Re-open the same real file input once.
                        UiObject2 empty=device.findObject(By.textContains("No file chosen"));
                        if(empty==null)empty=device.findObject(By.descContains("No file chosen"));
                        if(empty!=null && device.hasObject(By.text("No files selected"))){
                            android.util.Log.i("ImageOrderResolver","Reopening empty Chrome file input after camera approval");
                            empty.click();permissionRetries++;awaitingPermissionReturn=false;
                            Thread.sleep(1000);continue;
                        }
                    }
                    if(page){
                        // Do not scroll the underlying web page or open browser menus.
                        Thread.sleep(400);continue;
                    }
                    if(!page){
                        UiObject2 files=device.findObject(By.text("Files"));
                        if(files==null)files=device.findObject(By.desc("Files"));
                        if(files!=null){
                            android.util.Log.i("ImageOrderResolver","Opening Chrome Files entry");
                            files.click();Thread.sleep(900);continue;
                        }
                    }
                }
                boolean systemPicker=current!=null &&
                    (current.contains("photopicker")||current.contains("providers.media"));
                if((systemPicker||chrome) && menuAttempts<4){
                    UiObject2 more=device.findObject(By.desc("More"));
                    if(more==null)more=device.findObject(By.desc("More options"));
                    if(more!=null){
                        more.click();menuAttempts++;
                        Thread.sleep(500);continue;
                    }
                }
                boolean documents=current!=null && current.contains("documentsui");
                boolean drawerVisible=device.hasObject(By.text("Open from"));
                if(documents && !drawerVisible && drawerAttempts<5){
                    UiObject2 drawer=device.findObject(By.descContains("Show roots"));
                    if(drawer==null)drawer=device.findObject(By.descContains("Open navigation drawer"));
                    if(drawer==null)drawer=device.findObject(By.descContains("Show navigation"));
                    if(drawer!=null){
                        drawer.click();drawerAttempts++;
                        Thread.sleep(650);continue;
                    }
                }
                // Scroll only actual scrollable chooser/drawer nodes. Never swipe the
                // navigation bar or dismiss an unknown window.
                if((drawerVisible||(!chromeCase&&!documents&&!systemPicker)) && scrolls<8){
                    UiObject2 list=device.findObject(By.scrollable(true));
                    if(list!=null){
                        android.graphics.Rect bounds=list.getVisibleBounds();
                        int x=bounds.centerX();
                        if(bounds.height()>100){
                            device.swipe(x,bounds.bottom-bounds.height()/5,
                                x,bounds.top+bounds.height()/5,25);
                            scrolls++;
                        }
                    }
                }
            }catch(androidx.test.uiautomator.StaleObjectException ignored){}
            Thread.sleep(400);
        }
        fail("System chooser did not open Image Order native gallery; foreground="+
            device.getCurrentPackageName()+"; candidates: "+WebUploadCallerActivity.resolverDiagnostics);
    }
    private static void logVisiblePickerControls(UiDevice device,String foreground){
        try{
            java.util.LinkedHashSet<String> labels=new java.util.LinkedHashSet<>();
            for(UiObject2 node:device.findObjects(By.text(java.util.regex.Pattern.compile(".+")))){
                String text=node.getText();
                if(text!=null&&!text.trim().isEmpty())labels.add("text="+text+" id="+node.getResourceName());
                if(labels.size()>=35)break;
            }
            for(UiObject2 node:device.findObjects(By.desc(java.util.regex.Pattern.compile(".+")))){
                String desc=node.getContentDescription();
                if(desc!=null&&!desc.trim().isEmpty())labels.add("desc="+desc+" id="+node.getResourceName());
                if(labels.size()>=55)break;
            }
            android.util.Log.i("ImageOrderResolver","Visible controls in "+foreground+": "+labels);
        }catch(Exception ignored){}
    }
    static void clickPhotoAndWaitForCount(UiDevice device,String desc,int expected) throws Exception {
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
    private static String sha256(byte[] bytes) throws Exception{
        StringBuilder out=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))
            out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        return out.toString();
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
