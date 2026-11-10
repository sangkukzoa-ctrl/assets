package com.twobornot.imageorder;

import android.content.Context;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;

/** Persistent, read-only source visible to Android Files / ACTION_OPEN_DOCUMENT. */
final class OrderedOutbox {
    static final String NAME="Upload-ready batches";
    private OrderedOutbox() {}
    static File root(Context c) {return new File(c.getFilesDir(),"ordered-outbox");}
    static synchronized File publish(Context ctx,List<File> files) throws IOException {
        if(files.isEmpty())throw new IOException("No images");
        File root=root(ctx);
        if(!root.isDirectory() && !root.mkdirs())throw new IOException("Cannot create outbox");
        String stamp=new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.ROOT).format(new Date());
        File batch=new File(root,"batch-"+stamp+"-"+UUID.randomUUID());
        if(!batch.mkdirs())throw new IOException("Cannot create batch");
        try {
            for(int i=0;i<files.size();i++) {
                File source=files.get(i);
                String ext=source.getName().toLowerCase(Locale.ROOT).endsWith(".png")?".png":".jpg";
                File dst=new File(batch,String.format(Locale.ROOT,"%04d_of_%04d%s",i+1,files.size(),ext));
                try(InputStream in=new FileInputStream(source);OutputStream out=new FileOutputStream(dst)) {
                    byte[] buf=new byte[65536];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);
                }
            }
        } catch(IOException ex) {remove(batch);throw ex;}
        cleanOld(root,12);
        ctx.getContentResolver().notifyChange(android.provider.DocumentsContract.buildRootsUri(ctx.getPackageName()+".documents"),null);
        return batch;
    }
    static File[] batches(Context ctx) {
        File[] r=root(ctx).listFiles(f->f.isDirectory()&&f.getName().matches("batch-[0-9]{8}_[0-9]{6}-[0-9a-f-]{36}"));
        if(r==null)return new File[0];
        Arrays.sort(r,(a,b)->b.getName().compareTo(a.getName()));return r;
    }
    static File[] images(File batch) {
        File[] r=batch.listFiles(f->f.isFile()&&f.getName().matches("[0-9]{4}_of_[0-9]{4}\\.(png|jpg)"));
        if(r==null)return new File[0];
        Arrays.sort(r,Comparator.comparing(File::getName));return r;
    }
    static File resolve(Context ctx,String id) throws FileNotFoundException {
        if("root".equals(id))return root(ctx);
        if(!id.startsWith("batch-")||id.contains("/")||id.contains("\\")||id.contains(".."))throw new FileNotFoundException("Invalid document ID");
        int separator=id.indexOf(':');
        String batchName=separator<0?id:id.substring(0,separator);
        if(!batchName.matches("batch-[0-9]{8}_[0-9]{6}-[0-9a-f-]{36}"))throw new FileNotFoundException("Invalid batch");
        File batch=new File(root(ctx),batchName);
        if(!batch.isDirectory())throw new FileNotFoundException(batchName);
        if(separator<0)return batch;
        String file=id.substring(separator+1);
        if(!file.matches("[0-9]{4}_of_[0-9]{4}\\.(png|jpg)"))throw new FileNotFoundException("Invalid filename");
        File entry=new File(batch,file);
        if(!entry.isFile())throw new FileNotFoundException(file);
        return entry;
    }
    private static void cleanOld(File root,int keep) {
        File[] arr=root.listFiles(f->f.isDirectory()&&f.getName().startsWith("batch-"));
        if(arr==null||arr.length<=keep)return;
        Arrays.sort(arr,(a,b)->b.getName().compareTo(a.getName()));
        for(int i=keep;i<arr.length;i++)remove(arr[i]);
    }
    private static void remove(File f) {
        if(f.isDirectory()){File[] children=f.listFiles();if(children!=null)for(File c:children)remove(c);}
        f.delete();
    }
}
