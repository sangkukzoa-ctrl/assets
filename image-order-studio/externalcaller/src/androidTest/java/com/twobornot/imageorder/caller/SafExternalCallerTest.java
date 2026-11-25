package com.twobornot.imageorder.caller;

import android.Manifest;
import android.app.Activity;
import android.app.Instrumentation;
import android.content.ComponentName;
import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
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
import java.util.concurrent.TimeUnit;
import static org.junit.Assert.*;

/** Real ACTION_OPEN_DOCUMENT UI and grant propagation across independent application UIDs. */
@RunWith(AndroidJUnit4.class)
public final class SafExternalCallerTest {
    private static final String TARGET="com.twobornot.imageorder";
    private static final String AUTHORITY=TARGET+".documents";
    @Test public void systemDocumentsUiReturnsReadableOriginalWithoutMediaPermission() throws Exception {
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context context=inst.getTargetContext();
        ContentResolver cr=context.getContentResolver();
        PackageManager pm=context.getPackageManager();
        assertNotEquals(pm.getApplicationInfo(TARGET,0).uid,
            pm.getApplicationInfo(context.getPackageName(),0).uid);
        assertEquals(PackageManager.PERMISSION_DENIED,pm.checkPermission(
            (android.os.Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE),context.getPackageName()));
        TestMediaPermissions.grant(inst);
        UiDevice device=UiDevice.getInstance(inst);
        AttachmentCallerActivity.reset();
        Intent launch=new Intent(context,AttachmentCallerActivity.class);
        launch.putExtra("requestedMime","image/*");
        launch.putExtra("pickerAction",Intent.ACTION_OPEN_DOCUMENT);
        launch.putExtra("allowMultiple",false);
        launch.putExtra("testCount",3);
        launch.putExtra("testMixed",true);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
        Uri persisted=null;
        context.startActivity(launch);
        try {
            for(int i=0;i<100 && AttachmentCallerActivity.names==null;i++)Thread.sleep(200);
            assertNotNull("Image Order must create media fixtures",AttachmentCallerActivity.names);
            assertNull(AttachmentCallerActivity.error);
            final int selected=2;
            String name=AttachmentCallerActivity.names[selected];
            Uri source=Uri.parse(AttachmentCallerActivity.uriStrings[selected]);
            Uri doc=DocumentsContract.buildDocumentUri(AUTHORITY,
                "photo:"+ContentUris.parseId(source));
            Uri other=DocumentsContract.buildDocumentUri(AUTHORITY,
                "photo:"+ContentUris.parseId(Uri.parse(AttachmentCallerActivity.uriStrings[0])));
            assertUnreadable(cr,doc);
            assertUnreadable(cr,other);
            assertFalse("Direct MediaStore URI remains inaccessible before user selection",
                AttachmentCallerActivity.hadAccessBeforeUserSelection);
            // INITIAL_URI can be ignored by a DocumentsUI implementation. Navigate
            // through the visible provider root if that happens, never forge a grant.
            // A matching filename in Recents/Images is NOT proof of our provider.
            // Oreo/Pie can ignore EXTRA_INITIAL_URI and show the same fixture there.
            UiObject2 photo=null;
            {
                UiObject2 all=device.findObject(By.textStartsWith("All photos"));
                if(all==null){
                    UiObject2 root=device.findObject(By.text("Image Order (Files)"));
                    if(root==null){
                        UiObject2 drawer=device.findObject(By.descContains("Show roots"));
                        if(drawer==null)drawer=device.findObject(By.descContains("Open navigation drawer"));
                        if(drawer==null)drawer=device.findObject(By.descContains("Show navigation"));
                        assertNotNull("System DocumentsUI navigation drawer must be available",drawer);
                        drawer.click();
                        root=device.wait(Until.findObject(By.text("Image Order (Files)")),15000);
                    }
                    assertNotNull("Image Order DocumentsProvider must appear in system roots",root);
                    root.click();
                    all=device.wait(Until.findObject(By.textStartsWith("All photos")),15000);
                }
                assertNotNull("Image Order provider root must expose All photos",all);
                all.click();
                device.waitForIdle(5000);
                photo=device.wait(Until.findObject(By.text(name)),3000);
                if(photo==null){
                    // DocumentsUI may present image-only grid tiles without visible
                    // text labels. Use its actual List view control, not guessed taps.
                    UiObject2 list=device.findObject(By.res(java.util.regex.Pattern.compile(
                        ".*:id/(option_menu_list|menu_list)")));
                    if(list==null)list=device.findObject(By.desc("List view"));
                    if(list==null)list=device.findObject(By.text("List view"));
                    if(list!=null){
                        list.click();
                        device.waitForIdle(5000);
                    }
                    photo=device.wait(Until.findObject(By.text(name)),8000);
                }
                if(photo==null){
                    // In list mode a fixture may be outside the visible viewport.
                    for(int scroll=0;scroll<5 && photo==null;scroll++){
                        device.swipe(device.getDisplayWidth()/2,device.getDisplayHeight()*3/4,
                            device.getDisplayWidth()/2,device.getDisplayHeight()/3,24);
                        device.waitForIdle(3000);
                        photo=device.findObject(By.text(name));
                    }
                }
            }
            assertNotNull("DocumentsUI must display the real fixture filename: "+name,photo);
            photo.click();
            assertTrue("Real system picker must return to requesting external UID",
                AttachmentCallerActivity.done.await(20,TimeUnit.SECONDS));
            assertNull(AttachmentCallerActivity.error);
            assertEquals(Activity.RESULT_OK,AttachmentCallerActivity.resultCode);
            Intent result=AttachmentCallerActivity.resultData;
            assertNotNull(result);
            Uri chosen=result.getData();
            assertNotNull("OPEN_DOCUMENT returns document URI",chosen);
            assertEquals(AUTHORITY,chosen.getAuthority());
            assertEquals(DocumentsContract.getDocumentId(doc),DocumentsContract.getDocumentId(chosen));
            assertTrue("Result must grant URI read access",
                (result.getFlags()&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);
            assertEquals("Original MIME",AttachmentCallerActivity.mimes[selected],cr.getType(chosen));
            try(Cursor c=cr.query(chosen,new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE},null,null,null)){
                assertNotNull(c);assertTrue(c.moveToFirst());
                assertEquals(name,c.getString(0));
                assertTrue("Original file size must be positive",c.getLong(1)>0);
            }
            try(InputStream in=cr.openInputStream(chosen)){
                assertNotNull(in);
                MessageDigest md=MessageDigest.getInstance("SHA-256");
                byte[] buf=new byte[8192];int len;
                while((len=in.read(buf))!=-1)md.update(buf,0,len);
                StringBuilder hex=new StringBuilder();
                for(byte value:md.digest())hex.append(String.format(java.util.Locale.ROOT,"%02x",value&255));
                assertEquals("Original byte SHA-256",AttachmentCallerActivity.hashes[selected],hex.toString());
            }
            assertUnreadable(cr,other);
            try(ParcelFileDescriptor ignored=cr.openFileDescriptor(chosen,"w")){
                fail("Original SAF document must be read-only");
            }catch(SecurityException|java.io.FileNotFoundException expected){}
            cr.takePersistableUriPermission(chosen,Intent.FLAG_GRANT_READ_URI_PERMISSION);
            persisted=chosen;
            boolean granted=false;
            for(android.content.UriPermission permission:cr.getPersistedUriPermissions()){
                if(chosen.equals(permission.getUri())&&permission.isReadPermission())granted=true;
            }
            assertTrue("OPEN_DOCUMENT must permit persistent read grants",granted);
        }catch(Throwable failure){
            // Capture into Download via shell so the existing CI diagnostic pull
            // retains evidence even when the test APK is automatically uninstalled.
            try {
                java.io.ByteArrayOutputStream hierarchy=new java.io.ByteArrayOutputStream();
                device.dumpWindowHierarchy(hierarchy);
                android.util.Log.e("ImageOrderSAF","DocumentsUI hierarchy: "+
                    hierarchy.toString("UTF-8"));
            }catch(Exception ignored){}
            try(ParcelFileDescriptor shell=inst.getUiAutomation().executeShellCommand(
                    "screencap -p /sdcard/Download/imageorder-saf-failure.png");
                InputStream out=new ParcelFileDescriptor.AutoCloseInputStream(shell)){
                byte[] buf=new byte[256];while(out.read(buf)!=-1){}
            }catch(Exception ignored){}
            try(ParcelFileDescriptor shell=inst.getUiAutomation().executeShellCommand(
                    "uiautomator dump /sdcard/Download/imageorder-saf-hierarchy.xml");
                InputStream out=new ParcelFileDescriptor.AutoCloseInputStream(shell)){
                byte[] buf=new byte[256];while(out.read(buf)!=-1){}
            }catch(Exception ignored){}
            throw failure;
        }finally{
            if(persisted!=null)cr.releasePersistableUriPermission(persisted,Intent.FLAG_GRANT_READ_URI_PERMISSION);
            String[] saved=AttachmentCallerActivity.uriStrings;
            if(saved!=null){
                Intent cleanup=new Intent();
                cleanup.setComponent(new ComponentName(TARGET,TARGET+".CrossAppMediaFixtureActivity"));
                cleanup.putExtra("test_cleanup_uri_strings",saved);
                cleanup.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(cleanup);
            }
            device.pressBack();device.pressHome();
        }
    }
    private static void assertUnreadable(ContentResolver cr,Uri uri) throws Exception {
        try(InputStream in=cr.openInputStream(uri)){
            fail("No user-granted access to "+uri);
        }catch(SecurityException|java.io.FileNotFoundException expected){}
    }
}
