package com.twobornot.imageorder.caller;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import java.util.concurrent.CountDownLatch;

/** Test-only: seed originals and launch the installed, unmodified Chrome browser. */
public final class ChromeUploadFixtureActivity extends Activity {
    private static final String TARGET="com.twobornot.imageorder";
    public static volatile String[] names,hashes,mimes,uris;
    public static volatile LoopbackUploadServer server;
    public static volatile String error;
    public static volatile CountDownLatch ready=new CountDownLatch(1);
    public static void reset(){
        names=null;hashes=null;mimes=null;uris=null;server=null;error=null;
        ready=new CountDownLatch(1);
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        Intent seed=new Intent().setComponent(new ComponentName(TARGET,TARGET+".CrossAppMediaFixtureActivity"));
        seed.putExtra("test_count",5);seed.putExtra("test_mixed",true);
        startActivityForResult(seed,701);
    }
    @Override protected void onActivityResult(int req,int result,Intent data){
        super.onActivityResult(req,result,data);
        if(req!=701)return;
        try{
            if(result!=RESULT_OK||data==null)throw new IllegalStateException("Fixture failed");
            names=data.getStringArrayExtra("test_names");hashes=data.getStringArrayExtra("test_sha256");
            mimes=data.getStringArrayExtra("test_mimes");uris=data.getStringArrayExtra("test_uri_strings");
            String accept=getIntent().getBooleanExtra("generic",false)?"":" accept='image/*'";
            String html="<!doctype html><meta name='viewport' content='width=device-width, initial-scale=1'>"+
                "<title>Image Order Chrome QA</title><form id='upload' action='/upload' method='post' enctype='multipart/form-data'>"+
                "<label for='images' style='display:block;padding:32px;font-size:24px'>Choose originals for Chrome test</label>"+
                "<input id='images' name='photos' type='file' multiple"+accept+" style='position:absolute;left:0;top:0;opacity:0;width:100%;height:120px'>"+
                "<button type='submit' style='padding:24px'>Upload originals</button></form>"+
                "<p id='count'>No files selected</p><script>document.getElementById('images').onchange=function(){"+
                "document.getElementById('count').textContent=this.files.length+' originals selected';};</script>";
            server=new LoopbackUploadServer(html);
            // Package specifies ONLY the browser, not the image picker. Chrome controls its own upload intent.
            Intent browser=new Intent(Intent.ACTION_VIEW,Uri.parse(server.url())).setPackage("com.android.chrome");
            startActivity(browser);
        }catch(Exception ex){error=ex.toString();}
        finally{ready.countDown();}
    }
    @Override protected void onDestroy(){
        if(server!=null)server.close();
        super.onDestroy();
    }
}
