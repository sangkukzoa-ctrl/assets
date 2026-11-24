package com.twobornot.imageorder;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import java.util.concurrent.CountDownLatch;

/** Debug-only foreign-caller simulator for full ACTION_GET_CONTENT result testing.
 * It is NOT included in the signed release APK. */
public final class PickerHostActivity extends Activity {
    public static volatile int receivedCode=RESULT_CANCELED;
    public static volatile Intent receivedIntent;
    public static volatile CountDownLatch completed=new CountDownLatch(1);
    @Override public void onCreate(Bundle savedState){
        super.onCreate(savedState);
        // Existing MainActivity test remains unchanged unless direct native picker is
        // explicitly requested. Both paths are debug-only.
        boolean nativePicker=getIntent().getBooleanExtra("testNativeGallery",false);
        Intent pick=new Intent(this,nativePicker?NativeGalleryActivity.class:MainActivity.class);
        pick.setAction(Intent.ACTION_GET_CONTENT);
        String mime=getIntent().getStringExtra("testRequestedMime");
        pick.setType(mime==null?"image/png":mime);
        pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
        startActivityForResult(pick,567);
    }
    @Override protected void onActivityResult(int request,int code,Intent intent){
        super.onActivityResult(request,code,intent);
        if(request!=567)return;
        receivedCode=code;
        receivedIntent=intent;
        completed.countDown();
        finish();
    }
}
