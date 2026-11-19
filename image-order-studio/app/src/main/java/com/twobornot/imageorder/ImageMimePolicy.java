package com.twobornot.imageorder;

import java.util.Locale;
/** Applies the requesting app's MIME constraint without touching any image bytes. */
final class ImageMimePolicy {
    private ImageMimePolicy() {}
    static boolean matches(String accept, String actual) {
        if(accept==null || actual==null)return false;
        String a=accept.trim().toLowerCase(Locale.ROOT);
        String m=actual.trim().toLowerCase(Locale.ROOT);
        if(!m.startsWith("image/"))return false;
        return ("image/*".equals(a) || a.equals(m));
    }
    static boolean accepts(String requested,String[] acceptedTypes,String actual) {
        if(actual==null||!actual.toLowerCase(Locale.ROOT).startsWith("image/"))return false;
        if(acceptedTypes!=null && acceptedTypes.length>0){
            for(String t:acceptedTypes)if(matches(t,actual))return true;
            return false;
        }
        return matches(requested==null?"image/*":requested,actual);
    }
}
