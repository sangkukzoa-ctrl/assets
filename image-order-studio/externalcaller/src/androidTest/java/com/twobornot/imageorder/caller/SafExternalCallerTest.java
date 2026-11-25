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
            // Navigate via the actual provider root; a matching file in Recents
            // is not sufficient. Wait for asynchronous DocumentsUI initialization.
            selectProviderOriginal(device,name);
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
    private static final String ROOT_LABEL="Image Order (Files)";
    private static final String ALL_LABEL="All photos · 전체 사진";

    // Read actual DocumentsUI state on each iteration instead of assuming that a
    // click changed folders. Match navigation controls, not toolbar lookalikes.
    private static void selectProviderOriginal(UiDevice device,String name) throws Exception {
        long deadline=android.os.SystemClock.uptimeMillis()+65000;
        int scrolls=0;
        long lastAction=0;
        while(android.os.SystemClock.uptimeMillis()<deadline){
            try{
                String foreground=device.getCurrentPackageName();
                if(foreground==null||!foreground.contains("documentsui")){
                    Thread.sleep(400);continue;
                }
                long now=android.os.SystemClock.uptimeMillis();
                if(now-lastAction<850){Thread.sleep(250);continue;}
                boolean drawerVisible=device.hasObject(By.text("Open from"));
                if(drawerVisible){
                    // Select the provider's drawer row, never a matching breadcrumb
                    // or the separate Open app button in a merged RootAndAppItem.
                    UiObject2 root=null;
                    for(UiObject2 n:device.findObjects(By.text(ROOT_LABEL))){
                        if(n.getVisibleBounds().centerX()>device.getDisplayWidth()*4/5)continue;
                        if(isInNavigationDrawer(n)||isDrawerTitle(n)){root=n;break;}
                    }
                    if(root==null){
                        for(UiObject2 n:device.findObjects(By.desc(ROOT_LABEL))){
                            if(isInNavigationDrawer(n)){root=n;break;}
                        }
                    }
                    if(root!=null){
                        tapVisible(device,root,"provider drawer row");lastAction=now;continue;
                    }
                    UiObject2 scroll=device.findObject(By.scrollable(true));
                    if(scroll!=null && scrolls<8){
                        android.graphics.Rect r=scroll.getVisibleBounds();
                        if(r.height()>100){
                            device.swipe(r.centerX(),r.bottom-r.height()/5,r.centerX(),r.top+r.height()/5,25);
                            scrolls++;lastAction=now;continue;
                        }
                    }
                    Thread.sleep(300);continue;
                }

                // The root contains the All photos folder. It remains visible if
                // the prior click did not navigate, so retry the real folder row.
                // Use the filename/thumbnail listing only after the root breadcrumb
                // identifies this provider. The returned authority is checked again.
                boolean providerVisible=device.hasObject(By.text(ROOT_LABEL)) ||
                    device.hasObject(By.textContains("Images from "+ROOT_LABEL));
                UiObject2 folder=null;
                for(UiObject2 node:device.findObjects(By.text(ALL_LABEL))){
                    if(isFileListRow(node)){folder=node;break;}
                }
                if(providerVisible && folder!=null){
                    tapVisible(device,folder,"All photos folder");lastAction=now;continue;
                }

                boolean insideAll=providerVisible&&device.hasObject(By.text(ALL_LABEL));
                // Some versions display only the current folder in the toolbar,
                // but it is unique to our provider; authority remains mandatory.
                if(!insideAll&&device.hasObject(By.text(ALL_LABEL))&&folder==null)insideAll=true;
                if(insideAll){
                    UiObject2 photo=device.findObject(By.text(name));
                    if(photo==null)photo=device.findObject(By.descStartsWith(name+","));
                    if(photo!=null){
                        tapVisible(device,photo,"original "+name);return;
                    }
                    UiObject2 list=device.findObject(By.desc("List view"));
                    if(list==null)list=device.findObject(By.text("List view"));
                    if(list!=null){
                        tapVisible(device,list,"List view");lastAction=now;continue;
                    }
                    UiObject2 scroll=device.findObject(By.scrollable(true));
                    if(scroll!=null&&scrolls<12){
                        android.graphics.Rect r=scroll.getVisibleBounds();
                        if(r.height()>100){
                            device.swipe(r.centerX(),r.bottom-r.height()/5,r.centerX(),r.top+r.height()/5,25);
                            scrolls++;lastAction=now;continue;
                        }
                    }
                }
                if(!insideAll){
                    UiObject2 drawer=device.findObject(By.descContains("Show roots"));
                    if(drawer==null)drawer=device.findObject(By.descContains("Open navigation drawer"));
                    if(drawer==null)drawer=device.findObject(By.descContains("Show navigation"));
                    if(drawer!=null){
                        tapVisible(device,drawer,"Open from drawer");lastAction=now;continue;
                    }
                }
            }catch(androidx.test.uiautomator.StaleObjectException ignored){}
            Thread.sleep(350);
        }
        fail("DocumentsUI must expose provider original: "+name);
    }
    private static boolean isInNavigationDrawer(UiObject2 n){
        for(int depth=0;n!=null&&depth<12;depth++,n=n.getParent()){
            String id=n.getResourceName();
            if(id!=null&&(id.contains("roots_list")||id.contains("roots_fragment")||
                id.contains("drawer_roots")||id.endsWith(":id/roots")||id.contains("drawer_list")))return true;
            // A drawer row generally has a visible Open from ancestor/section.
            if(id!=null&&(id.contains("toolbar")||id.contains("breadcrumb")))return false;
        }
        return false;
    }
    private static boolean isDrawerTitle(UiObject2 n){
        String id=n.getResourceName();
        return id!=null&&(id.endsWith(":id/title")||id.endsWith(":id/root_title")) &&
            !n.getVisibleBounds().isEmpty();
    }
    private static boolean isFileListRow(UiObject2 n){
        for(int depth=0;n!=null&&depth<12;depth++,n=n.getParent()){
            String id=n.getResourceName();
            if(id!=null&&(id.contains("breadcrumb")||id.contains("toolbar")))return false;
            if(id!=null&&(id.contains("dir_list")||id.contains("directory_list")||
                id.contains("document_list")||id.contains("item_root")||
                id.endsWith(":id/dir_list")||id.contains("recycler_view")))return true;
            if(n.isScrollable())return true;
        }
        return false;
    }
    private static void tapVisible(UiDevice d,UiObject2 node,String label){
        android.graphics.Rect r=node.getVisibleBounds();
        android.util.Log.i("ImageOrderSAF","Tap "+label+" "+r+" id="+node.getResourceName());
        assertTrue("Visible touch target "+label,r.width()>0&&r.height()>0);
        assertTrue("Inject touch "+label,d.click(r.centerX(),r.centerY()));
    }
    private static void assertUnreadable(ContentResolver cr,Uri uri) throws Exception {
        try(InputStream in=cr.openInputStream(uri)){
            fail("No user-granted access to "+uri);
        }catch(SecurityException|java.io.FileNotFoundException expected){}
    }
}
