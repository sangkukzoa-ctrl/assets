package com.twobornot.imageorder;

public final class SafDocumentIdsTest {
    private static void same(Object a,Object b){if(!a.equals(b))throw new AssertionError(a+" != "+b);}
    private static void reject(Runnable r){try{r.run();throw new AssertionError("Accepted invalid ID");}catch(IllegalArgumentException expected){}}
    public static void main(String[] args){
        same("photo:42",SafDocumentIds.photo(42));
        same(9223372036854775807L,SafDocumentIds.photoId("photo:9223372036854775807"));
        reject(()->SafDocumentIds.photo(0));
        for(String bad:new String[]{"photo:0","photo:01","photo:../42","photo:1/../../etc","photo:-1","photo:9223372036854775808","album:x","root","album:%%%%"}) {
            if(bad.startsWith("photo:")||bad.equals("root"))reject(()->SafDocumentIds.photoId(bad));
            else reject(()->SafDocumentIds.albumId(bad));
        }
        for(String bucket:new String[]{"-19829822","My camera album","카메라 / 🎞️","123","a-b-c"}){
            String id=SafDocumentIds.album(bucket);
            same(bucket,SafDocumentIds.albumId(id));
            if(id.contains("/")||id.contains("+"))throw new AssertionError("Unsafe ID: "+id);
        }
        reject(()->SafDocumentIds.album(""));
        reject(()->SafDocumentIds.albumId("album:AA"));
        System.out.println("SAF document IDs: PASS");
    }
}
