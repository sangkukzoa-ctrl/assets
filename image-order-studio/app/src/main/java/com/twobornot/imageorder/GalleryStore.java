package com.twobornot.imageorder;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.util.AtomicFile;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.util.*;

/** Original byte copies live in app-private storage. Metadata and ordering are persisted atomically. */
final class GalleryStore {
    static final class Item {
        final String id, name, mime, path;
        Item(String id, String name, String mime, String path) {
            this.id=id; this.name=name; this.mime=mime; this.path=path;
        }
        JSONObject json() throws Exception {
            JSONObject j = new JSONObject();
            j.put("id",id); j.put("name",name); j.put("mime",mime); j.put("path",path); return j;
        }
    }
    private final Context ctx;
    final ArrayList<Item> items = new ArrayList<>();
    final SequenceLedger sequence = new SequenceLedger();
    private final File library, metadata;
    GalleryStore(Context ctx) { this(ctx,false); }
    GalleryStore(Context ctx,boolean externalSession) {
        this.ctx=ctx;
        File home;
        if(externalSession) {
            File sessions=new File(ctx.getFilesDir(),"picker-sessions");
            if(!sessions.exists() && !sessions.mkdirs())throw new IllegalStateException("Picker storage unavailable");
            cleanExpiredSessions(sessions);
            home=new File(sessions,"session-"+UUID.randomUUID().toString());
            if(!home.mkdirs())throw new IllegalStateException("Picker session unavailable");
        } else home=ctx.getFilesDir();
        library=new File(home,"library");
        metadata=new File(home,"gallery.json");
        if (!library.exists() && !library.mkdirs()) throw new IllegalStateException("Cannot initialize library");
        load();
    }
    synchronized Item find(String id) {
        for (Item i:items) if(i.id.equals(id)) return i;
        return null;
    }
    File source(Item item) { return new File(library,item.path); }
    synchronized Item add(Uri uri) throws Exception {
        ContentResolver cr=ctx.getContentResolver();
        String mime=cr.getType(uri);
        if(mime==null) mime="image/*";
        if(!mime.startsWith("image/")) throw new IOException("Not an image: "+uri);
        String name=readName(cr,uri);
        String ext=extension(mime,name);
        String id=UUID.randomUUID().toString();
        String path=id+ext;
        File target=new File(library,path);
        try(InputStream in=cr.openInputStream(uri);OutputStream out=new FileOutputStream(target)) {
            if(in==null) throw new IOException("Cannot read image: "+uri);
            byte[] buf=new byte[65536]; int n; long total=0;
            while((n=in.read(buf))!=-1) { out.write(buf,0,n); total+=n; }
            if(total==0) throw new IOException("Empty image: "+name);
        } catch(Exception ex) { target.delete(); throw ex; }
        Item item=new Item(id,name,mime,path);
        items.add(item);
        save();
        return item;
    }
    private static void cleanExpiredSessions(File sessions) {
        File[] list=sessions.listFiles();if(list==null)return;
        long cutoff=System.currentTimeMillis()-7L*24*60*60*1000;
        for(File session:list)if(session.isDirectory() && session.getName().startsWith("session-")
            && session.lastModified()<cutoff)deleteTree(session);
    }
    private static void deleteTree(File f) {
        if(f.isDirectory()) {
            File[] files=f.listFiles();if(files!=null)for(File c:files)deleteTree(c);
        }
        f.delete();
    }
    static String readName(ContentResolver cr,Uri uri) {
        try(Cursor c=cr.query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)) {
            if(c!=null && c.moveToFirst()) {
                String n=c.getString(0);
                if(n!=null && !n.isEmpty()) return n;
            }
        } catch(Exception ignored) {}
        return "image_"+System.currentTimeMillis();
    }
    private static String extension(String mime,String name) {
        if(name!=null) {
            int dot=name.lastIndexOf('.');
            if(dot>=0) {
                String ext=name.substring(dot).toLowerCase(Locale.ROOT);
                if(ext.matches("\\.[a-z0-9]{1,8}")) return ext;
            }
        }
        switch(mime) {
            case "image/png":return ".png";
            case "image/jpeg":return ".jpg";
            case "image/webp":return ".webp";
            case "image/gif":return ".gif";
            case "image/heic":case "image/heif":return ".heic";
            default:return ".img";
        }
    }
    synchronized void remove(Item item) {
        if(item==null)return;
        sequence.deselect(item.id);
        if(items.remove(item)) {
            source(item).delete();
            save();
        }
    }
    synchronized void clear() {
        for(Item i:items) source(i).delete();
        items.clear(); sequence.clear(); save();
    }
    synchronized void save() {
        AtomicFile atomic = new AtomicFile(metadata);
        FileOutputStream out = null;
        try {
            JSONObject root=new JSONObject(); JSONArray gallery=new JSONArray(); JSONArray selected=new JSONArray();
            for(Item i:items) gallery.put(i.json());
            for(String id:sequence.snapshot()) selected.put(id);
            root.put("images",gallery); root.put("sequence",selected); root.put("version",1);
            out=atomic.startWrite(); out.write(root.toString().getBytes("UTF-8"));
            atomic.finishWrite(out);
        } catch(Exception ex) { if(out!=null) atomic.failWrite(out); throw new IllegalStateException("Save failed",ex); }
    }
    private void load() {
        if(!metadata.exists()) return;
        try(InputStream in=new AtomicFile(metadata).openRead()) {
            ByteArrayOutputStream bytes=new ByteArrayOutputStream(); byte[] buffer=new byte[8192]; int n;
            while((n=in.read(buffer))!=-1) bytes.write(buffer,0,n);
            JSONObject root=new JSONObject(bytes.toString("UTF-8")); JSONArray gallery=root.getJSONArray("images");
            for(int i=0;i<gallery.length();i++) {
                JSONObject j=gallery.getJSONObject(i);
                Item item=new Item(j.getString("id"),j.getString("name"),j.getString("mime"),j.getString("path"));
                if(item.path.matches("[a-f0-9-]{36}\\.[a-zA-Z0-9]{1,8}") && source(item).isFile()) items.add(item);
            }
            HashSet<String> valid=new HashSet<>(); for(Item i:items) valid.add(i.id);
            ArrayList<String> selected=new ArrayList<>(); JSONArray a=root.getJSONArray("sequence");
            for(int i=0;i<a.length();i++) selected.add(a.getString(i));
            sequence.restore(selected,valid);
        } catch(Exception ex) { android.util.Log.e("ImageOrderStudio","Could not restore gallery",ex); }
    }
}
