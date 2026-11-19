package com.twobornot.imageorder;

import java.util.List;

/** Original byte streams stay untouched; MIME only describes the selected collection. */
final class OriginalDelivery {
    private OriginalDelivery() {}
    static String commonMime(List<String> mimes) {
        if(mimes==null || mimes.isEmpty())throw new IllegalArgumentException("Empty selection");
        String first=mimes.get(0);
        if(first==null || !first.startsWith("image/"))throw new IllegalArgumentException("Not an image");
        for(String mime:mimes) {
            if(mime==null || !mime.startsWith("image/"))throw new IllegalArgumentException("Not an image");
            if(!first.equals(mime))return "image/*";
        }
        return first;
    }
}
