package com.twobornot.imageorder;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/** Stable, opaque SAF identifiers. No filesystem paths or user-provided SQL fragments. */
final class SafDocumentIds {
    static final String ROOT="root", ALL="all";
    private static final String PHOTO="photo:", ALBUM="album:";
    private SafDocumentIds() {}
    static String photo(long id) {
        if(id<=0)throw new IllegalArgumentException("Invalid media ID");
        return PHOTO+id;
    }
    static long photoId(String documentId) {
        if(documentId==null || !documentId.matches("photo:[1-9][0-9]{0,18}"))
            throw new IllegalArgumentException("Invalid photo document ID");
        long value=Long.parseLong(documentId.substring(PHOTO.length()));
        if(value<=0)throw new IllegalArgumentException("Invalid media ID");
        return value;
    }
    static boolean isPhoto(String id){return id!=null && id.startsWith(PHOTO);}
    static String album(String bucketId) {
        if(bucketId==null || bucketId.isEmpty() || bucketId.length()>256 || bucketId.chars().anyMatch(ch->ch<32))
            throw new IllegalArgumentException("Invalid album");
        return ALBUM+Base64.getUrlEncoder().withoutPadding().encodeToString(bucketId.getBytes(StandardCharsets.UTF_8));
    }
    static String albumId(String documentId) {
        if(documentId==null || !documentId.matches("album:[A-Za-z0-9_-]{2,342}"))
            throw new IllegalArgumentException("Invalid album document ID");
        String encoded=documentId.substring(ALBUM.length());
        byte[] data=Base64.getUrlDecoder().decode(encoded);
        String result=new String(data,StandardCharsets.UTF_8);
        if(result.isEmpty() || result.length()>256 || !album(result).equals(documentId))
            throw new IllegalArgumentException("Noncanonical album document ID");
        return result;
    }
    static boolean isAlbum(String id){return id!=null && id.startsWith(ALBUM);}
}
