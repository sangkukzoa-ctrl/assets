package com.twobornot.imageorder;

import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;
import android.service.quicksettings.TileService;

/** Optional Quick Settings shortcut; no screen-overlay or accessibility permission. */
public final class OrderTileService extends TileService {
    @Override public void onClick() {
        super.onClick();
        Intent launch=new Intent(this,MainActivity.class);
        launch.setAction(Intent.ACTION_MAIN);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        if(Build.VERSION.SDK_INT>=34){
            PendingIntent intent=PendingIntent.getActivity(this,0,launch,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            startActivityAndCollapse(intent);
        }else startActivityAndCollapse(launch);
    }
}
