package com.twobornot.imageorder.caller;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.*;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Point;
import android.net.Uri;
import android.provider.MediaStore;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.Assume;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.TimeUnit;
import static org.junit.Assert.*;

/** Positive/negative control of the real platform picker, not a replacement app. */
@RunWith(AndroidJUnit4.class)
public final class SystemOrderContractTest {
    private static final String TARGET="com.twobornot.imageorder";
    private static final int[] COLORS={0xffe02020,0xff20c040,0xff3030e0,0xffe0a020,0xffd020d0};
    private static final int[] ORDER={3,4,0,1,2};
    private static final int[] TAPS={3,0,4,0,0,1,2};
    private static final int[] COUNTS={1,2,3,2,3,4,5};
    @Test public void platformPickerOrderControl() throws Exception {
        Assume.assumeTrue("Dedicated platform picker order experiment",
            "true".equals(InstrumentationRegistry.getArguments().getString("systemOrderQa")));
        boolean ordered="true".equals(InstrumentationRegistry.getArguments().getString("orderedProbe"));
        Instrumentation inst=InstrumentationRegistry.getInstrumentation();
        Context ctx=inst.getTargetContext();
        assertNotEquals(ctx.getPackageManager().getApplicationInfo(TARGET,0).uid,
            ctx.getPackageManager().getApplicationInfo(ctx.getPackageName(),0).uid);
        assertEquals(android.content.pm.PackageManager.PERMISSION_DENIED,ctx.checkSelfPermission(
            android.Manifest.permission.READ_MEDIA_IMAGES));
        TestMediaPermissions.grant(inst);
        AttachmentCallerActivity.reset();
        UiDevice device=UiDevice.getInstance(inst);
        Intent start=new Intent(ctx,AttachmentCallerActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK)
            .putExtra("pickerAction",MediaStore.ACTION_PICK_IMAGES)
            .putExtra("requestedMime","image/*").putExtra("testCount",5)
            .putExtra("testMixed",true).putExtra("allowMultiple",true)
            .putExtra("colorProbe",true).putExtra("orderedProbe",ordered);
        ctx.startActivity(start);
        try {
            assertTrue("First picker dispatch timeout",AttachmentCallerActivity.directDispatched.await(60,TimeUnit.SECONDS));
            assertNull(AttachmentCallerActivity.error);
            assertFalse(AttachmentCallerActivity.hadAccessBeforeUserSelection);
            String foreground=null;
            long deadline=android.os.SystemClock.uptimeMillis()+30000;
            while(android.os.SystemClock.uptimeMillis()<deadline){
                foreground=device.getCurrentPackageName();
                if(foreground!=null&&foreground.contains("providers.media"))break;
                Thread.sleep(400);
            }
            assertNotNull(foreground);
            assertTrue("First UI must be actual platform photo picker: "+foreground,foreground.contains("providers.media"));
            assertFalse(device.hasObject(By.desc("imageorder.photos")));
            // Locate original synthetic color tiles on a clean emulator by actual rendered pixels,
            // not by assuming MediaStore/grid order. No screenshots of a user's device.
            // Record the actual on-screen centers before taps (all five visible).
            // Selected tiles can be dimmed; keep the coordinates only within this
            // fixed grid session and assert the selection count after every touch.
            Point[] points=new Point[COLORS.length];
            for(int i=0;i<points.length;i++)points[i]=awaitTile(inst,COLORS[i]);
            for(int i=0;i<TAPS.length;i++){
                int index=TAPS[i];
                Point point=points[index];
                assertTrue("Tap rendered fixture "+index,device.click(point.x,point.y));
                UiObject2 count=waitForAddCount(device,foreground,COUNTS[i],12000);
                assertNotNull("Selection counter after tap "+index,count);
                android.util.Log.i("ImageOrderSystem","Tapped fixture "+index+" count="+COUNTS[i]);
            }
            UiObject2 confirm=waitForAddCount(device,foreground,ORDER.length,10000);
            assertNotNull(confirm);confirm.click();
            assertTrue("Platform result timeout",AttachmentCallerActivity.done.await(30,TimeUnit.SECONDS));
            assertEquals(Activity.RESULT_OK,AttachmentCallerActivity.resultCode);
            Intent result=AttachmentCallerActivity.resultData;
            assertNotNull(result);assertNotNull(result.getClipData());
            assertEquals(ORDER.length,result.getClipData().getItemCount());
            int[] actual=new int[ORDER.length];
            List<Uri> returnedUris=new ArrayList<>();
            for(int pos=0;pos<actual.length;pos++){
                Uri uri=result.getClipData().getItemAt(pos).getUri();
                assertNotNull(uri);
                returnedUris.add(uri);
                MessageDigest digest=MessageDigest.getInstance("SHA-256");
                try(InputStream in=ctx.getContentResolver().openInputStream(uri)){
                    assertNotNull(in);byte[] buf=new byte[8192];int n;
                    while((n=in.read(buf))!=-1)digest.update(buf,0,n);
                }
                StringBuilder hex=new StringBuilder();
                for(byte b:digest.digest())hex.append(String.format(Locale.ROOT,"%02x",b&255));
                int idx=Arrays.asList(AttachmentCallerActivity.hashes).indexOf(hex.toString());
                assertTrue("Returned bytes must match selected original",idx>=0);
                assertEquals(AttachmentCallerActivity.mimes[idx],ctx.getContentResolver().getType(uri));
                actual[pos]=idx;
            }
            int[] sorted=actual.clone(),expected=ORDER.clone();Arrays.sort(sorted);Arrays.sort(expected);
            assertArrayEquals("Same selected originals",expected,sorted);
            boolean same=Arrays.equals(ORDER,actual);
            android.util.Log.i("ImageOrderSystem","SYSTEM_ORDER_RESULT orderedExtra="+ordered+
                " tap="+Arrays.toString(ORDER)+" returned="+Arrays.toString(actual)+" matches="+same);
            if(ordered)assertArrayEquals("Ordered system API must preserve explicit tap order",ORDER,actual);
            // Independent caller uploads the real returned URIs, not fixture paths.
            // Never sort by name, MIME, or worker completion order.
            try(LoopbackUploadServer server=new LoopbackUploadServer("")){
                NativeUploadOrderProbe.upload(ctx.getContentResolver(),returnedUris,server.url()+"upload");
                assertTrue("HTTP receiver timeout",server.received.await(15,TimeUnit.SECONDS));
                assertNull(server.error);assertNotNull(server.parts);
                assertEquals(actual.length,server.parts.size());
                for(int i=0;i<actual.length;i++){
                    LoopbackUploadServer.Part part=server.parts.get(i);
                    assertEquals("photos",part.field);
                    assertEquals(AttachmentCallerActivity.names[actual[i]],part.filename);
                    assertEquals(AttachmentCallerActivity.mimes[actual[i]],part.mime);
                    assertEquals(AttachmentCallerActivity.hashes[actual[i]],NativeUploadOrderProbe.sha256(part.bytes));
                }
                android.util.Log.i("ImageOrderSystem","SYSTEM_HTTP_RESULT orderedExtra="+ordered+
                    " picker="+Arrays.toString(actual)+" server="+Arrays.toString(actual)+" originals=true");
            }
        } finally {
            try{
                java.io.ByteArrayOutputStream xml=new java.io.ByteArrayOutputStream();
                device.dumpWindowHierarchy(xml);
                android.util.Log.i("ImageOrderSystem","End hierarchy="+xml.toString("UTF-8"));
            }catch(Exception ignored){}
            if(AttachmentCallerActivity.uriStrings!=null){
                Intent cleanup=new Intent().setComponent(new ComponentName(TARGET,TARGET+".CrossAppMediaFixtureActivity"))
                    .putExtra("test_cleanup_uri_strings",AttachmentCallerActivity.uriStrings)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try{ctx.startActivity(cleanup);}catch(Exception ignored){}
            }
        }
    }
    private static Point awaitTile(Instrumentation inst,int target) throws Exception {
        long deadline=android.os.SystemClock.uptimeMillis()+30000;
        while(android.os.SystemClock.uptimeMillis()<deadline){
            Bitmap b=inst.getUiAutomation().takeScreenshot();
            if(b!=null){
                try {
                    // Count only pixels close to the distinctive synthetic color.
                    // Check the center is itself a matching pixel; no arbitrary fixed tap.
                    int left=b.getWidth(),right=0,top=b.getHeight(),bottom=0,n=0;
                    for(int y=0;y<b.getHeight();y+=4)for(int x=0;x<b.getWidth();x+=4){
                        if(close(b.getPixel(x,y),target)){
                            left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);n++;
                        }
                    }
                    int x=(left+right)/2,y=(top+bottom)/2;
                    if(n>=100&&right-left>=40&&bottom-top>=40&&close(b.getPixel(x,y),target))
                        return new Point(x,y);
                }finally{b.recycle();}
            }
            Thread.sleep(500);
        }
        throw new AssertionError("Distinct synthetic photo tile not visible: "+Integer.toHexString(target));
    }
    private static boolean close(int a,int b){
        return Math.abs(Color.red(a)-Color.red(b))<=22&&Math.abs(Color.green(a)-Color.green(b))<=22&&Math.abs(Color.blue(a)-Color.blue(b))<=22;
    }
    private static UiObject2 waitForAddCount(UiDevice device,String pkg,int count,long ms) throws Exception {
        long deadline=android.os.SystemClock.uptimeMillis()+ms;
        java.util.regex.Pattern label=java.util.regex.Pattern.compile("(?i)^(?:add|select|done|confirm|attach)(?:\\s+)?\\(?" + count + "\\)?$");
        while(android.os.SystemClock.uptimeMillis()<deadline){
            try {
                UiObject2 node=device.findObject(By.pkg(pkg).text(label));
                if(node==null)node=device.findObject(By.pkg(pkg).desc(label));
                if(node!=null)return node;
            }catch(StaleObjectException ignored){}
            Thread.sleep(250);
        }
        return null;
    }
}
