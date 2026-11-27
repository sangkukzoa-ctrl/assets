package com.twobornot.imageorder.caller;

import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;

/** Test-only native client: retain selection index across concurrent file preparation. */
final class NativeUploadOrderProbe {
    private NativeUploadOrderProbe(){}
    private static final class Part {
        final String name,mime;final byte[] data;
        Part(String n,String m,byte[] d){name=n;mime=m;data=d;}
    }
    static void upload(ContentResolver resolver,List<Uri> uris,String endpoint) throws Exception {
        ExecutorService pool=Executors.newFixedThreadPool(uris.size());
        List<Future<Part>> futures=new ArrayList<>();
        try{
            // Reverse completion is made likely by staggered preparation. Futures are
            // collected by input index, never by completion time.
            for(int i=0;i<uris.size();i++){
                final Uri uri=uris.get(i);final int index=i;
                futures.add(pool.submit(()->{
                    Thread.sleep(120L*(uris.size()-1-index));
                    String name;
                    try(Cursor c=resolver.query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){
                        if(c==null||!c.moveToFirst())throw new IOException("Missing display name");
                        name=c.getString(0);
                    }
                    String mime=resolver.getType(uri);
                    if(name==null||!name.matches("[A-Za-z0-9_.-]+")||mime==null||!mime.startsWith("image/"))
                        throw new IOException("Unexpected synthetic fixture metadata");
                    try(InputStream in=resolver.openInputStream(uri)){
                        if(in==null)throw new IOException("Missing original");
                        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                        byte[] buf=new byte[8192];int n;
                        while((n=in.read(buf))!=-1)bytes.write(buf,0,n);
                        return new Part(name,mime,bytes.toByteArray());
                    }
                }));
            }
            String boundary="imageorder-"+UUID.randomUUID();
            ByteArrayOutputStream body=new ByteArrayOutputStream();
            for(Future<Part> future:futures){
                Part p=future.get(15,TimeUnit.SECONDS);
                body.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\"photos\"; filename=\""+p.name+"\"\r\n"+
                    "Content-Type: "+p.mime+"\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
                body.write(p.data);body.write("\r\n".getBytes(StandardCharsets.US_ASCII));
            }
            body.write(("--"+boundary+"--\r\n").getBytes(StandardCharsets.US_ASCII));
            URL url=new URL(endpoint);
            if(!"127.0.0.1".equals(url.getHost()))throw new IOException("Loopback only");
            HttpURLConnection c=(HttpURLConnection)url.openConnection();
            try{
                c.setRequestMethod("POST");c.setDoOutput(true);c.setConnectTimeout(10000);c.setReadTimeout(15000);
                c.setRequestProperty("Content-Type","multipart/form-data; boundary="+boundary);
                c.setFixedLengthStreamingMode(body.size());
                try(OutputStream out=c.getOutputStream()){body.writeTo(out);}
                if(c.getResponseCode()!=200)throw new IOException("HTTP "+c.getResponseCode());
                try(InputStream in=c.getInputStream()){while(in.read()!=-1){}}
            }finally{c.disconnect();}
        }finally{pool.shutdownNow();}
    }
    static String sha256(byte[] bytes) throws Exception {
        StringBuilder out=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))out.append(String.format(Locale.ROOT,"%02x",b&255));
        return out.toString();
    }
}
