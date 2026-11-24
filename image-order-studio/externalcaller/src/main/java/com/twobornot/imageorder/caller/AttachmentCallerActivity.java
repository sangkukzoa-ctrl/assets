package com.twobornot.imageorder.caller;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.net.Uri;
import android.provider.MediaStore;
import android.os.Bundle;
import java.io.InputStream;
import java.util.concurrent.CountDownLatch;

/** Truly separate UID and APK: asks Image Order to pick original photos. */
public final class AttachmentCallerActivity extends Activity {
    public static volatile String[] names,uriStrings,hashes,mimes;
    public static volatile boolean hadAccessBeforeUserSelection;
    public static volatile int resultCode;
    public static volatile Intent resultData;
    public static volatile String error;
    public static volatile CountDownLatch done=new CountDownLatch(1);
    private static final int SEED=320, PICK=321;
    private static final String TARGET="com.twobornot.imageorder";
    private static final String FIXTURE="com.twobornot.imageorder.CrossAppMediaFixtureActivity";
    private String requestedType;
    private boolean allowMultiple;
    private String pickerAction;
    private boolean uriOnlyPick;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        requestedType=getIntent().getStringExtra("requestedMime");
        allowMultiple=getIntent().getBooleanExtra("allowMultiple",true);
        pickerAction=getIntent().getStringExtra("pickerAction");
        if(pickerAction==null)pickerAction=Intent.ACTION_GET_CONTENT;
        uriOnlyPick=getIntent().getBooleanExtra("uriOnlyPick",false);
        if(requestedType==null)requestedType="image/png";
        Intent seed=new Intent();seed.setComponent(new ComponentName(TARGET,FIXTURE));
        seed.putExtra("test_count",getIntent().getIntExtra("testCount",3));
        seed.putExtra("test_mixed",getIntent().getBooleanExtra("testMixed",false));
        try{startActivityForResult(seed,SEED);}
        catch(Exception ex){error="Fixture start: "+ex;done.countDown();}
    }
    @Override protected void onActivityResult(int request,int code,Intent returned){
        super.onActivityResult(request,code,returned);
        android.util.Log.i("ImageOrderFlow","ThirdParty onActivityResult request="+request+" code="+code+" data="+(returned!=null));
        if(request==SEED){
            if(code!=RESULT_OK||returned==null){error="Fixture failed: "+(returned==null?"missing result":returned.getStringExtra("error"));done.countDown();return;}
            names=returned.getStringArrayExtra("test_names");
            uriStrings=returned.getStringArrayExtra("test_uri_strings");
            hashes=returned.getStringArrayExtra("test_sha256");
            mimes=returned.getStringArrayExtra("test_mimes");
            try {
                // The first access MUST fail: this APK has no media permission and the
                // seeder only returned strings, without any content URI read grant.
                try(InputStream in=getContentResolver().openInputStream(Uri.parse(uriStrings[0]))){
                    hadAccessBeforeUserSelection=(in!=null);
                }catch(SecurityException|java.io.FileNotFoundException denied){hadAccessBeforeUserSelection=false;}
                Intent picker=new Intent(pickerAction);
                if(Intent.ACTION_OPEN_DOCUMENT.equals(pickerAction)){
                    // Real system DocumentsUI, NOT an Image Order activity or direct URI grant.
                    picker.addCategory(Intent.CATEGORY_OPENABLE);
                    picker.setType(requestedType);
                    picker.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,allowMultiple);
                    picker.putExtra(android.provider.DocumentsContract.EXTRA_INITIAL_URI,
                        android.provider.DocumentsContract.buildRootUri(TARGET+".documents","images"));
                }else if(Intent.ACTION_PICK.equals(pickerAction)){
                    picker.setPackage(TARGET);
                    // Real-world ACTION_PICK callers often supply the MediaStore collection URI
                    // instead of a MIME type, or provide both with setDataAndType().
                    if(uriOnlyPick)picker.setData(MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
                    else picker.setDataAndType(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,requestedType);
                }else{
                    picker.setPackage(TARGET);
                    picker.addCategory(Intent.CATEGORY_OPENABLE);
                    picker.setType(requestedType);
                    picker.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,allowMultiple);
                }
                android.util.Log.i("ImageOrderFlow","ThirdParty launching action="+pickerAction
                    +" mime="+picker.getType()+" uri="+picker.getData());
                startActivityForResult(picker,PICK);
            }catch(Exception ex){error="Picker launch: "+ex;done.countDown();}
        }else if(request==PICK){
            resultCode=code;resultData=returned;done.countDown();
        }
    }
    public static void reset(){
        names=null;uriStrings=null;hashes=null;mimes=null;error=null;resultData=null;
        resultCode=RESULT_CANCELED;hadAccessBeforeUserSelection=false;
        done=new CountDownLatch(1);
    }
}
