package com.twobornot.imageorder;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.content.*;
import android.graphics.PixelFormat;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.util.*;

/**
 * User-enabled, on-device, narrowly scoped upload picker shortcut.
 * Never modifies target windows, presses upload/submit, or reads user images.
 * DOES NOT replace an external app's ActivityResult contract.
 */
public final class UploadAssistService extends AccessibilityService {
    private static final Set<String> PICKERS=new HashSet<>(Arrays.asList(
        "com.google.android.providers.media.module", "com.android.documentsui",
        "com.google.android.documentsui", "com.sec.android.gallery3d",
        "com.android.providers.media", "com.google.android.apps.photos"));
    private static final String[] LABELS={"사진 첨부","사진 선택","갤러리","파일 선택","이미지 업로드",
        "select photo","choose image","select image","upload image"};
    private WindowManager windows;
    private View bubble;
    private String previous="";
    private long lastShown=0;
    @Override public void onServiceConnected(){super.onServiceConnected();windows=(WindowManager)getSystemService(WINDOW_SERVICE);}
    @Override public void onAccessibilityEvent(AccessibilityEvent e){
        if(e==null||e.getPackageName()==null)return;
        String pkg=e.getPackageName().toString();
        if(pkg.equals(getPackageName())){hide();return;}
        int type=e.getEventType();
        if(type!=AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED && type!=AccessibilityEvent.TYPE_WINDOWS_CHANGED)return;
        boolean recognized=PICKERS.contains(pkg);
        if(!recognized) {
            // Limit scanning to visible clickable labels; never inspect editable text or passwords.
            AccessibilityNodeInfo node=getRootInActiveWindow();
            recognized=hasUploadLabel(node,0,new int[]{0});
        }
        if(!recognized){hide();return;}
        long now=SystemClock.elapsedRealtime();
        if(bubble!=null&&pkg.equals(previous))return;
        if((pkg.equals(previous) && now-lastShown<30000) || now-lastShown<1500)return;
        previous=pkg;lastShown=now;show();
    }
    private boolean hasUploadLabel(AccessibilityNodeInfo node,int depth,int[] seen){
        if(node==null||depth>5||seen[0]++>80)return false;
        try{
            if(node.isClickable()&&!node.isEditable()&&!node.isPassword()){
                String label=String.valueOf(node.getText())+" "+String.valueOf(node.getContentDescription());
                label=label.toLowerCase(Locale.ROOT);
                for(String s:LABELS)if(label.contains(s))return true;
            }
            for(int i=0;i<node.getChildCount();i++)if(hasUploadLabel(node.getChild(i),depth+1,seen))return true;
        }catch(Exception ignored){}
        return false;
    }
    private void show(){
        if(windows==null||bubble!=null)return;
        TextView button=new TextView(this);
        button.setText("▣ " +(Locale.getDefault().getLanguage().equals("ko")?"순서대로 첨부":"Ordered upload"));
        button.setTextSize(14);button.setTextColor(0xffffffff);button.setGravity(Gravity.CENTER);
        button.setPadding(25,14,25,14);
        android.graphics.drawable.GradientDrawable bg=new android.graphics.drawable.GradientDrawable();
        bg.setColor(0xff235cc6);bg.setCornerRadius(55);button.setBackground(bg);
        WindowManager.LayoutParams params=new WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT);
        params.gravity=Gravity.TOP|Gravity.RIGHT;params.x=16;params.y=140;
        button.setOnClickListener(v->{
            hide();
            Intent launch=new Intent(this,MainActivity.class);
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            launch.putExtra("from_upload_assist",true);
            startActivity(launch);
        });
        try{windows.addView(button,params);bubble=button;}catch(Exception ex){android.util.Log.w("ImageOrderStudio","Overlay unavailable",ex);}
    }
    private void hide(){
        if(windows!=null&&bubble!=null){try{windows.removeView(bubble);}catch(Exception ignored){}bubble=null;}
    }
    @Override public void onInterrupt(){hide();}
    @Override public void onDestroy(){hide();super.onDestroy();}
}
