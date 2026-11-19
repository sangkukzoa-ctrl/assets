package com.twobornot.imageorder;

public final class ImageMimePolicyTest {
    private static int cases=0;
    private static void check(boolean v,String name){cases++;if(!v)throw new AssertionError(name);}
    public static void main(String[] args){
        check(ImageMimePolicy.accepts("image/*",null,"image/jpeg"),"wildcard JPEG");
        check(ImageMimePolicy.accepts("image/*",null,"image/heic"),"HEIC");
        check(ImageMimePolicy.accepts("image/png",null,"image/png"),"PNG");
        check(!ImageMimePolicy.accepts("image/png",null,"image/jpeg"),"PNG only");
        check(ImageMimePolicy.accepts("image/*",new String[]{"image/png","image/heic"},"image/heic"),"MIME extras");
        check(!ImageMimePolicy.accepts("image/*",new String[]{"image/png","image/heic"},"image/jpeg"),"MIME extras exclude JPEG");
        check(!ImageMimePolicy.accepts("image/*",null,"video/mp4"),"Reject video");
        check(!ImageMimePolicy.accepts("image/*",null,null),"Reject null");
        check(ImageMimePolicy.accepts("IMAGE/PNG",null,"image/png"),"Case insensitive");
        check(!ImageMimePolicy.accepts("image/*",new String[]{"video/mp4"},"image/png"),"Reject non-image MIME extras");
        System.out.println("ImageMimePolicyTest PASS "+cases+" cases");
    }
}
