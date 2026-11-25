package com.twobornot.imageorder.caller;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import java.util.concurrent.CountDownLatch;

/**
 * Independent APK/UID with a REAL local HTML input[type=file] in Android WebView.
 * The HTML is bundled in code and makes no network requests.
 * WebChromeClient.createIntent()/parseResult() exercise the browser upload bridge.
 */
public final class WebUploadCallerActivity extends Activity {
    private static final String TARGET="com.twobornot.imageorder";
    private static final String FIXTURE=TARGET+".CrossAppMediaFixtureActivity";
    private static final int SEED=601, PICK=602;
    public static volatile String[] names,uriStrings,hashes,mimes;
    public static volatile Uri[] parsedUris,frameworkParsedUris;
    public static volatile Intent rawResult;
    public static volatile int rawCode;
    public static volatile String domFilesJson,error;
    public static volatile int tapX,tapY;
    public static volatile CountDownLatch ready=new CountDownLatch(1);
    public static volatile CountDownLatch finished=new CountDownLatch(1);
    private ValueCallback<Uri[]> chooser;
    private WebView web;

    public static void reset(){
        names=null;uriStrings=null;hashes=null;mimes=null;
        parsedUris=null;frameworkParsedUris=null;rawResult=null;rawCode=RESULT_CANCELED;
        domFilesJson=null;error=null;tapX=0;tapY=0;
        ready=new CountDownLatch(1);
        finished=new CountDownLatch(1);
    }
    @Override public void onCreate(Bundle savedState){
        super.onCreate(savedState);
        Intent seed=new Intent().setComponent(new ComponentName(TARGET,FIXTURE));
        seed.putExtra("test_count",5);
        seed.putExtra("test_mixed",true);
        try{startActivityForResult(seed,SEED);}
        catch(Exception ex){error="Fixture: "+ex;finished.countDown();ready.countDown();}
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request==SEED){
            if(result!=RESULT_OK || data==null){
                error="Fixture failed: "+(data==null?"null":data.getStringExtra("error"));
                finished.countDown();ready.countDown();return;
            }
            names=data.getStringArrayExtra("test_names");
            uriStrings=data.getStringArrayExtra("test_uri_strings");
            hashes=data.getStringArrayExtra("test_sha256");
            mimes=data.getStringArrayExtra("test_mimes");
            openLocalWebView();
        }else if(request==PICK){
            rawResult=data;rawCode=result;
            // Chromium's framework parser can ignore ClipData (multiple selection).
            // Preserve the exact ordered ClipData for our independent HTML host.
            frameworkParsedUris=WebChromeClient.FileChooserParams.parseResult(result,data);
            parsedUris=OrderedWebFileChooserResult.parse(result,data);
            Log.i("ImageOrderWeb","WebView framework parser count="
                +(frameworkParsedUris==null?0:frameworkParsedUris.length)
                +"; ordered result count="+(parsedUris==null?0:parsedUris.length)
                +"; clip="+(data!=null && data.getClipData()!=null
                    ?data.getClipData().getItemCount():0));
            if(chooser!=null){
                chooser.onReceiveValue(parsedUris);
                chooser=null;
            }
            if(result!=RESULT_OK || parsedUris==null){
                error="WebView file chooser result failed: "+result;
                finished.countDown();
            }
        }
    }
    private void openLocalWebView(){
        FrameLayout root=new FrameLayout(this);
        if(Build.VERSION.SDK_INT>=35){
            root.setOnApplyWindowInsetsListener((view,insets)->{
                Insets inset=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                view.setPadding(inset.left,inset.top,inset.right,inset.bottom);
                return insets;
            });
        }
        web=new WebView(this);
        web.setBackgroundColor(Color.WHITE);
        web.getSettings().setJavaScriptEnabled(true);
        web.addJavascriptInterface(new Bridge(this),"ImageOrderTestBridge");
        web.setWebChromeClient(new WebChromeClient(){
            @Override public boolean onShowFileChooser(WebView target,ValueCallback<Uri[]> callback,
                    WebChromeClient.FileChooserParams params){
                chooser=callback;
                try{
                    // Preserve WebView's generated action, MIME and categories.
                    // Older WebView versions omit EXTRA_ALLOW_MULTIPLE even for
                    // MODE_OPEN_MULTIPLE. The host must forward the HTML mode.
                    Intent request=params.createIntent();
                    boolean originalMultiple=request.getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false);
                    int mode=params.getMode();
                    if(mode==WebChromeClient.FileChooserParams.MODE_OPEN_MULTIPLE){
                        request.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
                    }else if(mode==WebChromeClient.FileChooserParams.MODE_OPEN){
                        request.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,false);
                    }
                    // The package restriction only isolates the test's target picker.
                    request.setPackage(TARGET);
                    Log.i("ImageOrderWeb","HTML chooser action="+request.getAction()
                        +" type="+request.getType()+" mode="+mode
                        +" generatedMultiple="+originalMultiple
                        +" forwardedMultiple="+request.getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false));
                    startActivityForResult(request,PICK);
                    return true;
                }catch(Exception ex){
                    error="HTML chooser launch: "+ex;
                    chooser.onReceiveValue(null);chooser=null;finished.countDown();
                    return true;
                }
            }
        });
        web.setWebViewClient(new WebViewClient(){
            @Override public void onPageFinished(WebView view,String url){
                view.evaluateJavascript("(function(){var r=document.getElementById('open').getBoundingClientRect();"+
                    "return Math.round(r.left+r.width/2)+','+Math.round(r.top+r.height/2);})()",json->{
                    try{
                        String[] p=new org.json.JSONTokener(json).nextValue().toString().split(",");
                        int[] location=new int[2];view.getLocationOnScreen(location);
                        tapX=location[0]+Math.round(Float.parseFloat(p[0])*view.getScale());
                        tapY=location[1]+Math.round(Float.parseFloat(p[1])*view.getScale());
                    }catch(Exception ex){error="Web click location: "+ex;}
                    ready.countDown();
                });
            }
        });
        root.addView(web,new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);
        final String html="<!doctype html><html><head><meta name='viewport' "+
            "content='width=device-width,initial-scale=1'></head><body style='margin:0;font:18px sans-serif'>"+
            "<label id='open' for='images' aria-label='imageorder.web-upload' "+
            "style='display:block;margin:24px;padding:24px;background:#cce4f8;width:240px;height:70px'>"+
            "Choose photos to upload</label>"+
            "<input id='images' type='file' accept='image/*' multiple style='display:none'>"+
            "<script>document.getElementById('images').addEventListener('change',function(){"+
            "var a=Array.from(this.files).map(function(f){return {name:f.name,type:f.type,size:f.size};});"+
            "ImageOrderTestBridge.report(JSON.stringify(a));});</script></body></html>";
        web.loadDataWithBaseURL("https://imageorder-local.invalid/",html,"text/html","UTF-8",null);
    }
    public static final class Bridge{
        private final WebUploadCallerActivity parent;
        Bridge(WebUploadCallerActivity parent){this.parent=parent;}
        @JavascriptInterface public void report(String files){
            domFilesJson=files;
            Log.i("ImageOrderWeb","HTML FileList after selection="+files);
            finished.countDown();
        }
    }
    @Override protected void onDestroy(){
        if(web!=null){
            if(chooser!=null){chooser.onReceiveValue(null);chooser=null;}
            web.destroy();
        }
        super.onDestroy();
    }
}
