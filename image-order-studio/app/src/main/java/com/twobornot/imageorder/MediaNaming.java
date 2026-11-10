package com.twobornot.imageorder;
import java.util.Locale;
/** Pure-Java stable naming rules. Never use input filename to determine sequence. */
final class MediaNaming {
    private MediaNaming() {}
    static String galleryFileName(String batch,int index,int count,boolean png) {
        if(!batch.matches("[0-9]{8}_[0-9]{6}")||index<0||index>=count||count<1||count>9999)
            throw new IllegalArgumentException("Invalid gallery batch or ordinal");
        return String.format(Locale.ROOT,"ISO_%s_%04d_of_%04d.%s",batch,index+1,count,png?"png":"jpg");
    }
}
