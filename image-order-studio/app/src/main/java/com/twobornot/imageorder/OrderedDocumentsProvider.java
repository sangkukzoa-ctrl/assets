package com.twobornot.imageorder;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.content.res.AssetFileDescriptor;
import android.graphics.Point;
import android.net.Uri;
import android.os.Build;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import android.provider.MediaStore;
import java.io.FileNotFoundException;
import java.util.HashSet;
import java.util.Locale;

/** Read-only SAF source for the REAL MediaStore images, not numbered/exported copies.
 *
 * The Android Files UI controls multi-selection; the full tap-ordered result is available
 * from Image Order's normal native gallery for GET_CONTENT/PICK integrations.
 * This provider supplies original bytes, names, MIME and thumbnails for OPEN_DOCUMENT.
 */
public final class OrderedDocumentsProvider extends DocumentsProvider {
    private static final String[] ROOT_COLUMNS={
        DocumentsContract.Root.COLUMN_ROOT_ID,DocumentsContract.Root.COLUMN_DOCUMENT_ID,
        DocumentsContract.Root.COLUMN_TITLE,DocumentsContract.Root.COLUMN_SUMMARY,
        DocumentsContract.Root.COLUMN_FLAGS,DocumentsContract.Root.COLUMN_MIME_TYPES,
        DocumentsContract.Root.COLUMN_ICON};
    private static final String[] DOC_COLUMNS={
        DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,
        DocumentsContract.Document.COLUMN_MIME_TYPE,DocumentsContract.Document.COLUMN_SIZE,
        DocumentsContract.Document.COLUMN_LAST_MODIFIED,DocumentsContract.Document.COLUMN_FLAGS};
    private static final String[] PHOTO_COLUMNS={
        MediaStore.Images.Media._ID,MediaStore.Images.Media.DISPLAY_NAME,
        MediaStore.Images.Media.MIME_TYPE,MediaStore.Images.Media.SIZE,
        MediaStore.Images.Media.DATE_MODIFIED,MediaStore.Images.Media.BUCKET_ID};
    private static final int MAX_PHOTOS=10000,MAX_ALBUM_SCAN=30000,RECENT_LIMIT=200;
    @Override public boolean onCreate(){return true;}
    private ContentResolver resolver(){return getContext().getContentResolver();}
    private Uri mediaUri(){
        return Build.VERSION.SDK_INT>=29
            ?MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)
            :MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
    }
    private Uri photoUri(long id){return ContentUris.withAppendedId(mediaUri(),id);}
    private String authority(){return getContext().getPackageName()+".documents";}
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor out=new MatrixCursor(projection==null?ROOT_COLUMNS:projection);
        String[] keys=ROOT_COLUMNS;
        Object[] vals={"images",SafDocumentIds.ROOT,"Image Order",
            "Original photos · use app to grant photo access",
            DocumentsContract.Root.FLAG_LOCAL_ONLY|DocumentsContract.Root.FLAG_SUPPORTS_RECENTS|DocumentsContract.Root.FLAG_SUPPORTS_SEARCH,
            "image/*",R.drawable.ic_launcher};
        addRow(out,keys,vals);
        return out;
    }
    @Override public Cursor queryDocument(String documentId,String[] projection) throws FileNotFoundException {
        MatrixCursor out=new MatrixCursor(projection==null?DOC_COLUMNS:projection);
        if(SafDocumentIds.ROOT.equals(documentId))folder(out,documentId,"Image Order");
        else if(SafDocumentIds.ALL.equals(documentId))folder(out,documentId,"All photos · 전체 사진");
        else if(SafDocumentIds.isAlbum(documentId)){
            final String bucket;
            try{bucket=SafDocumentIds.albumId(documentId);}catch(IllegalArgumentException e){throw missing(e);}
            folder(out,documentId,albumName(bucket));
        }else photo(out,documentId,readPhoto(documentId));
        return out;
    }
    @Override public Cursor queryChildDocuments(String parentDocumentId,String[] projection,String sortOrder) throws FileNotFoundException {
        MatrixCursor out=new MatrixCursor(projection==null?DOC_COLUMNS:projection);
        if(SafDocumentIds.ROOT.equals(parentDocumentId)){
            folder(out,SafDocumentIds.ALL,"All photos · 전체 사진");
            HashSet<String> seen=new HashSet<>();
            try(Cursor c=resolver().query(mediaUri(),
                new String[]{MediaStore.Images.Media.BUCKET_ID,MediaStore.Images.Media.BUCKET_DISPLAY_NAME},
                MediaStore.Images.Media.MIME_TYPE+" LIKE ?",new String[]{"image/%"},
                MediaStore.Images.Media.DATE_ADDED+" DESC")) {
                if(c!=null){int count=0;while(c.moveToNext()&&count++<MAX_ALBUM_SCAN){
                    String bucket=c.getString(0),title=c.getString(1);
                    if(bucket==null||bucket.isEmpty()||!seen.add(bucket))continue;
                    folder(out,SafDocumentIds.album(bucket),title==null||title.isEmpty()?"Other":title);
                }}
            }catch(SecurityException ignored){/* App gallery requests media permission. */}
        }else if(SafDocumentIds.ALL.equals(parentDocumentId))addPhotos(out,null,null,MAX_PHOTOS,null);
        else if(SafDocumentIds.isAlbum(parentDocumentId)){
            final String bucket;
            try{bucket=SafDocumentIds.albumId(parentDocumentId);}catch(IllegalArgumentException e){throw missing(e);}
            addPhotos(out,MediaStore.Images.Media.BUCKET_ID+" = ?",new String[]{bucket},MAX_PHOTOS,null);
        }else throw new FileNotFoundException("Not a folder: "+parentDocumentId);
        out.setNotificationUri(resolver(),mediaUri());
        return out;
    }
    @Override public Cursor queryRecentDocuments(String rootId,String[] projection) throws FileNotFoundException {
        if(!"images".equals(rootId))throw new FileNotFoundException("Unknown root");
        MatrixCursor out=new MatrixCursor(projection==null?DOC_COLUMNS:projection);
        addPhotos(out,null,null,RECENT_LIMIT,null);
        out.setNotificationUri(resolver(),mediaUri());return out;
    }
    @Override public Cursor querySearchDocuments(String rootId,String query,String[] projection) throws FileNotFoundException {
        if(!"images".equals(rootId))throw new FileNotFoundException("Unknown root");
        MatrixCursor out=new MatrixCursor(projection==null?DOC_COLUMNS:projection);
        addPhotos(out,null,null,MAX_PHOTOS,query==null?"":query.toLowerCase(Locale.ROOT));
        out.setNotificationUri(resolver(),mediaUri());return out;
    }
    @Override public ParcelFileDescriptor openDocument(String documentId,String mode,CancellationSignal signal) throws FileNotFoundException {
        if(!"r".equals(mode))throw new FileNotFoundException("Original images are read-only");
        readPhoto(documentId); // An image row must exist; never open a guessed/raw path.
        try {
            ParcelFileDescriptor fd=resolver().openFileDescriptor(photoUri(SafDocumentIds.photoId(documentId)),"r",signal);
            if(fd==null)throw new FileNotFoundException(documentId);
            return fd;
        }catch(SecurityException | IllegalArgumentException e){throw missing(e);}
    }
    @Override public AssetFileDescriptor openDocumentThumbnail(String documentId,Point sizeHint,CancellationSignal signal) throws FileNotFoundException {
        // DocsUI decodes the source at preview size. No modified image is ever stored.
        return new AssetFileDescriptor(openDocument(documentId,"r",signal),0,AssetFileDescriptor.UNKNOWN_LENGTH);
    }
    @Override public String getDocumentType(String documentId) throws FileNotFoundException {
        if(SafDocumentIds.ROOT.equals(documentId)||SafDocumentIds.ALL.equals(documentId))
            return DocumentsContract.Document.MIME_TYPE_DIR;
        if(SafDocumentIds.isAlbum(documentId)){
            try{SafDocumentIds.albumId(documentId);return DocumentsContract.Document.MIME_TYPE_DIR;}
            catch(IllegalArgumentException e){throw missing(e);}
        }
        Photo p=readPhoto(documentId);return p.mime;
    }
    private static final class Photo {
        final String name,mime,bucket;
        final long size,modified;
        Photo(String name,String mime,String bucket,long size,long modified){
            this.name=name;this.mime=mime;this.bucket=bucket;this.size=size;this.modified=modified;
        }
    }
    private Photo readPhoto(String documentId) throws FileNotFoundException {
        final long id;
        try{id=SafDocumentIds.photoId(documentId);}catch(IllegalArgumentException e){throw missing(e);}
        try(Cursor c=resolver().query(photoUri(id),PHOTO_COLUMNS,null,null,null)) {
            if(c==null || !c.moveToFirst())throw new FileNotFoundException("Image not available");
            String mime=c.getString(2);
            if(mime==null||!mime.startsWith("image/"))throw new FileNotFoundException("Not an image");
            return new Photo(c.getString(1),mime,c.getString(5),c.getLong(3),c.getLong(4)*1000L);
        }catch(SecurityException e){throw missing(e);}
    }
    private String albumName(String bucket) {
        try(Cursor c=resolver().query(mediaUri(),new String[]{MediaStore.Images.Media.BUCKET_DISPLAY_NAME},
            MediaStore.Images.Media.BUCKET_ID+" = ?",new String[]{bucket},null)){
            if(c!=null && c.moveToFirst()){
                String name=c.getString(0);if(name!=null && !name.isEmpty())return name;
            }
        }catch(SecurityException ignored){}
        return "Album";
    }
    private void addPhotos(MatrixCursor out,String constraint,String[] args,int limit,String search) {
        String where=MediaStore.Images.Media.MIME_TYPE+" LIKE ?"+(constraint==null?"":" AND "+constraint);
        String[] selectionArgs=new String[(args==null?0:args.length)+1];selectionArgs[0]="image/%";
        if(args!=null)System.arraycopy(args,0,selectionArgs,1,args.length);
        try(Cursor c=resolver().query(mediaUri(),PHOTO_COLUMNS,where,selectionArgs,
            MediaStore.Images.Media.DATE_ADDED+" DESC, "+MediaStore.Images.Media._ID+" DESC")){
            if(c==null)return;
            int visited=0,added=0;
            while(c.moveToNext() && visited++<MAX_ALBUM_SCAN && added<limit){
                long id=c.getLong(0);String name=c.getString(1),mime=c.getString(2);
                if(id<=0||mime==null||!mime.startsWith("image/"))continue;
                if(search!=null && (name==null || !name.toLowerCase(Locale.ROOT).contains(search)))continue;
                photo(out,SafDocumentIds.photo(id),new Photo(name,mime,c.getString(5),c.getLong(3),c.getLong(4)*1000L));
                added++;
            }
        }catch(SecurityException ignored){/* The user can grant access in the main gallery. */}
    }
    private static void folder(MatrixCursor out,String id,String title){
        addRow(out,DOC_COLUMNS,new Object[]{id,title,DocumentsContract.Document.MIME_TYPE_DIR,null,null,0});
    }
    private static void photo(MatrixCursor out,String id,Photo p){
        addRow(out,DOC_COLUMNS,new Object[]{id,p.name,p.mime,p.size,p.modified,DocumentsContract.Document.FLAG_SUPPORTS_THUMBNAIL});
    }
    private static FileNotFoundException missing(Exception e){return new FileNotFoundException("Invalid image document: "+e.getMessage());}
    private static void addRow(MatrixCursor cursor,String[] keys,Object[] values){
        MatrixCursor.RowBuilder builder=cursor.newRow();
        for(String column:cursor.getColumnNames()){
            Object v=null;
            for(int i=0;i<keys.length;i++)if(keys[i].equals(column)){v=values[i];break;}
            builder.add(column,v);
        }
    }
}
