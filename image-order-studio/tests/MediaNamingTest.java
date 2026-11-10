package com.twobornot.imageorder;
import java.util.*;
public final class MediaNamingTest {
    public static void main(String[] args) {
        int count=166;Set<String> found=new HashSet<>();
        for(int i=0;i<count;i++){
            String name=MediaNaming.galleryFileName("20261110_204000",i,count,false);
            if(!found.add(name))throw new AssertionError("duplicated filename");
            if(!name.contains(String.format(Locale.ROOT,"%04d_of_0166",i+1)))throw new AssertionError(name);
        }
        if(!"ISO_20261110_204000_0001_of_0001.png".equals(
            MediaNaming.galleryFileName("20261110_204000",0,1,true)))throw new AssertionError();
        try{MediaNaming.galleryFileName("../",0,1,false);throw new AssertionError();}
        catch(IllegalArgumentException expected){}
        System.out.println("MediaNaming 166-image source-agnostic order tests PASS");
    }
}
