package com.twobornot.imageorder.caller;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;

/**
 * App-host-side WebView compatibility. Android WebChromeClient.FileChooserParams.parseResult
 * can read only getData(), silently ignoring multi-item ClipData on common WebView builds.
 *
 * This adapter belongs in the independent TEST caller, not the Image Order picker.
 * A third-party browser/app must itself support multi-item ClipData to display all files.
 */
final class OrderedWebFileChooserResult {
    private OrderedWebFileChooserResult(){}
    static Uri[] parse(int code,Intent result){
        if(code!=Activity.RESULT_OK || result==null)return null;
        ClipData clip=result.getClipData();
        if(clip!=null && clip.getItemCount()>0){
            int length=clip.getItemCount();
            Uri[] ordered=new Uri[length];
            for(int i=0;i<length;i++){
                Uri item=clip.getItemAt(i).getUri();
                if(item==null)return null;
                ordered[i]=item;
            }
            return ordered;
        }
        Uri one=result.getData();
        return one==null?null:new Uri[]{one};
    }
}
