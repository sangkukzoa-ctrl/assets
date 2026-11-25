package com.twobornot.imageorder;
import android.Manifest;
import android.app.Instrumentation;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.ParcelFileDescriptor;
import java.io.InputStream;
import java.io.IOException;

/** Test-only: grant the picker, never the independent caller. */
final class TestMediaPermissions {
    private static final String TARGET="com.twobornot.imageorder";
    private TestMediaPermissions(){}
    static void grant(Instrumentation inst) throws IOException {
        grantOne(inst,Build.VERSION.SDK_INT>=33?Manifest.permission.READ_MEDIA_IMAGES:Manifest.permission.READ_EXTERNAL_STORAGE);
        if(Build.VERSION.SDK_INT<=28)grantOne(inst,Manifest.permission.WRITE_EXTERNAL_STORAGE);
    }
    private static void grantOne(Instrumentation inst,String permission) throws IOException {
        PackageManager pm=inst.getTargetContext().getPackageManager();
        if(pm.checkPermission(permission,TARGET)==PackageManager.PERMISSION_GRANTED)return;
        if(Build.VERSION.SDK_INT>=28)inst.getUiAutomation().grantRuntimePermission(TARGET,permission);
        else{
            try(InputStream out=new ParcelFileDescriptor.AutoCloseInputStream(
                    inst.getUiAutomation().executeShellCommand("pm grant "+TARGET+" "+permission))){
                byte[] buffer=new byte[256];while(out.read(buffer)!=-1){}
            }
        }
        if(pm.checkPermission(permission,TARGET)!=PackageManager.PERMISSION_GRANTED)
            throw new IOException("Test fixture permission not granted: "+permission);
    }
}
