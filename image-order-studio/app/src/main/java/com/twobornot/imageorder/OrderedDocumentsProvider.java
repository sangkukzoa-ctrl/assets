package com.twobornot.imageorder;

import android.content.ContentResolver;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.graphics.Point;
import android.net.Uri;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import java.io.*;

/** Read-only Android SAF DocumentsProvider: visible as Image Order Studio in Files. */
public final class OrderedDocumentsProvider extends DocumentsProvider {
    private static final String[] ROOTS={DocumentsContract.Root.COLUMN_ROOT_ID,DocumentsContract.Root.COLUMN_DOCUMENT_ID,
        DocumentsContract.Root.COLUMN_TITLE,DocumentsContract.Root.COLUMN_FLAGS,DocumentsContract.Root.COLUMN_MIME_TYPES,
        DocumentsContract.Root.COLUMN_ICON};
    private static final String[] DOCS={DocumentsContract.Document.COLUMN_DOCUMENT_ID,
        DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,
        DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED,
        DocumentsContract.Document.COLUMN_FLAGS};
    @Override public boolean onCreate(){return true;}
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor result=new MatrixCursor(projection==null?ROOTS:projection);
        MatrixCursor.RowBuilder row=result.newRow();
        Object[] values={"ordered","root","Image Order Studio",0,"image/*",R.drawable.ic_launcher};
        fill(row,result.getColumnNames(),ROOTS,values);
        return result;
    }
    @Override public Cursor queryDocument(String documentId,String[] projection) throws FileNotFoundException {
        File f=OrderedOutbox.resolve(getContext(),documentId);
        MatrixCursor result=new MatrixCursor(projection==null?DOCS:projection);
        row(result,documentId,f);return result;
    }
    @Override public Cursor queryChildDocuments(String parentDocumentId,String[] projection,String sortOrder) throws FileNotFoundException {
        File folder=OrderedOutbox.resolve(getContext(),parentDocumentId);
        if(!folder.isDirectory())throw new FileNotFoundException("Not a folder");
        MatrixCursor result=new MatrixCursor(projection==null?DOCS:projection);
        if("root".equals(parentDocumentId)) {
            for(File batch:OrderedOutbox.batches(getContext()))row(result,batch.getName(),batch);
        } else {
            for(File f:OrderedOutbox.images(folder))row(result,parentDocumentId+":"+f.getName(),f);
        }
        return result;
    }
    @Override public ParcelFileDescriptor openDocument(String documentId,String mode,CancellationSignal signal) throws FileNotFoundException {
        if(!"r".equals(mode))throw new FileNotFoundException("Read-only image");
        File f=OrderedOutbox.resolve(getContext(),documentId);
        if(!f.isFile())throw new FileNotFoundException("Not an image");
        return ParcelFileDescriptor.open(f,ParcelFileDescriptor.MODE_READ_ONLY);
    }
    @Override public String getDocumentType(String documentId) throws FileNotFoundException {
        File f=OrderedOutbox.resolve(getContext(),documentId);
        return f.isDirectory()?DocumentsContract.Document.MIME_TYPE_DIR:f.getName().endsWith(".png")?"image/png":"image/jpeg";
    }
    private void row(MatrixCursor cursor,String id,File f) {
        String mime=f.isDirectory()?DocumentsContract.Document.MIME_TYPE_DIR:
            f.getName().endsWith(".png")?"image/png":"image/jpeg";
        MatrixCursor.RowBuilder row=cursor.newRow();
        fill(row,cursor.getColumnNames(),DOCS,new Object[]{id,"root".equals(id)?OrderedOutbox.NAME:f.getName(),mime,
            f.isDirectory()?0L:f.length(),f.lastModified(),0});
    }
    private static void fill(MatrixCursor.RowBuilder row,String[] columns,String[] known,Object[] values) {
        for(String col:columns){ Object value=null;
            for(int i=0;i<known.length;i++)if(known[i].equals(col)){value=values[i];break;}
            row.add(col,value);
        }
    }
}
