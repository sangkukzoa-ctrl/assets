package com.twobornot.imageorder;

import android.content.ClipData;
import android.content.Intent;
import android.content.ContentResolver;
import android.net.Uri;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Builds one ordered, grantable set of original URIs for both picker and share callers. */
final class MediaIntentResult {
    private MediaIntentResult() {}
    static Intent forSelection(ContentResolver resolver, ArrayList<Uri> uris) {
        return forSelection(uris,resolveTypes(resolver,uris));
    }
    static Intent forSelection(ArrayList<Uri> uris,List<String> mimes) {
        if(uris==null || uris.isEmpty() || mimes==null || uris.size()!=mimes.size())
            throw new IllegalArgumentException("Invalid original URI selection");
        String mime=OriginalDelivery.commonMime(mimes);
        Intent out=new Intent();
        if(uris.size()==1)out.setDataAndType(Objects.requireNonNull(uris.get(0)),mime);
        else out.setType(mime);
        ClipData clip=new ClipData("Image Order",new String[]{mime,"image/*"},
            new ClipData.Item(Objects.requireNonNull(uris.get(0))));
        for(int i=1;i<uris.size();i++)clip.addItem(new ClipData.Item(Objects.requireNonNull(uris.get(i))));
        out.setClipData(clip);
        out.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        return out;
    }
    static Intent forShare(ContentResolver resolver,ArrayList<Uri> uris){
        return forShare(uris,resolveTypes(resolver,uris));
    }
    static Intent forShare(ArrayList<Uri> uris,List<String> mimes){
        Intent intent=forSelection(uris,mimes);
        intent.setAction(uris.size()==1?Intent.ACTION_SEND:Intent.ACTION_SEND_MULTIPLE);
        if(uris.size()==1)intent.putExtra(Intent.EXTRA_STREAM,uris.get(0));
        else intent.putParcelableArrayListExtra(Intent.EXTRA_STREAM,new ArrayList<>(uris));
        return intent;
    }
    private static ArrayList<String> resolveTypes(ContentResolver resolver,List<Uri> uris){
        if(resolver==null || uris==null)throw new IllegalArgumentException("Missing media resolver");
        ArrayList<String> mimes=new ArrayList<>();
        for(Uri uri:uris){
            if(uri==null)throw new IllegalArgumentException("Null image URI");
            String mime=resolver.getType(uri);
            if(mime==null || !mime.startsWith("image/"))
                throw new IllegalArgumentException("Not a compatible image: "+uri);
            mimes.add(mime);
        }
        return mimes;
    }
}
