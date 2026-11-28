package com.twobornot.imageorder.integration;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.net.Uri;
import android.os.Build;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Optional host-side integration. The HOST must explicitly adopt this helper and
 * let its user opt in. It does not intercept other apps or change Android settings.
 * No storage, network, accessibility or device-admin permission is needed here.
 */
public final class OrderedAttachment {
    public static final String PACKAGE="com.twobornot.imageorder";
    private static final String RELEASE_CERT="9e7a1a9bf4d2e8e7bac63c3315e0a84aae66e82ab392198f0e854cf4720370c0";
    private OrderedAttachment(){}
    public static Intent request(Context context, boolean userOptedIn, String imageMime,
            int maxSelection, Intent normalRequest) {
        return requestForTrustedSigner(context,userOptedIn,imageMime,maxSelection,normalRequest,RELEASE_CERT);
    }
    /** Test harness may provide its own debug signer. Production hosts use request(). */
    public static Intent requestForTrustedSigner(Context context, boolean userOptedIn, String imageMime,
            int maxSelection, Intent normalRequest,String trustedSha256) {
        if(normalRequest==null)throw new IllegalArgumentException("Missing normal picker");
        Intent unchanged=new Intent(normalRequest);
        if(!userOptedIn || imageMime==null || !imageMime.startsWith("image/") ||
                maxSelection<1 || maxSelection>200 || !trusted(context, trustedSha256))return unchanged;
        Intent direct=new Intent(Intent.ACTION_GET_CONTENT)
            .addCategory(Intent.CATEGORY_OPENABLE).setType(imageMime).setPackage(PACKAGE)
            .putExtra(Intent.EXTRA_ALLOW_MULTIPLE,maxSelection>1)
            .putExtra(PACKAGE+".MAX_SELECTION",maxSelection);
        return direct.resolveActivity(context.getPackageManager())!=null?direct:unchanged;
    }
    private static boolean trusted(Context context,String fingerprint) {
        try {
            if(fingerprint==null||!fingerprint.matches("[0-9a-fA-F]{64}"))return false;
            byte[] wanted=new byte[32];
            for(int i=0;i<wanted.length;i++)wanted[i]=(byte)Integer.parseInt(fingerprint.substring(2*i,2*i+2),16);
            PackageManager pm=context.getPackageManager();
            if(Build.VERSION.SDK_INT>=28){
                PackageInfo info=pm.getPackageInfo(PACKAGE,PackageManager.GET_SIGNING_CERTIFICATES);
                if(info.getLongVersionCode()<11||info.signingInfo==null)return false;
                Signature[] signers=info.signingInfo.getApkContentsSigners();
                return signers!=null&&signers.length==1&&MessageDigest.isEqual(wanted,
                    MessageDigest.getInstance("SHA-256").digest(signers[0].toByteArray()));
            }
            PackageInfo info=pm.getPackageInfo(PACKAGE,PackageManager.GET_SIGNATURES);
            return info.versionCode>=11&&info.signatures!=null&&info.signatures.length==1&&
                MessageDigest.isEqual(wanted,MessageDigest.getInstance("SHA-256").digest(info.signatures[0].toByteArray()));
        } catch(Exception unavailable){return false;}
    }
    /** Preserve ClipData order. Never reorder, rename, copy or infer missing items. */
    public static List<Uri> readResult(int resultCode,Intent data,int maxSelection){
        if(resultCode!=android.app.Activity.RESULT_OK||data==null)return Collections.emptyList();
        if(maxSelection<1)throw new IllegalArgumentException("Invalid limit");
        ArrayList<Uri> result=new ArrayList<>();
        if(data.getClipData()!=null){
            for(int i=0;i<data.getClipData().getItemCount();i++)result.add(data.getClipData().getItemAt(i).getUri());
        }else if(data.getData()!=null)result.add(data.getData());
        if(result.size()>maxSelection)throw new IllegalArgumentException("Picker exceeded limit");
        for(Uri uri:result)if(uri==null||!"content".equals(uri.getScheme()))
            throw new IllegalArgumentException("Invalid content URI");
        return Collections.unmodifiableList(result);
    }
}
