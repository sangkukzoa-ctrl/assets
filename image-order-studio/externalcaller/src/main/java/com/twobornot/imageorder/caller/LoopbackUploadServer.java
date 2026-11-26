package com.twobornot.imageorder.caller;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.regex.*;

/** Independent test HTTP receiver, bound ONLY to loopback. Never shipped in the product. */
final class LoopbackUploadServer implements AutoCloseable {
    private static final int MAX_BODY=4*1024*1024;
    private final ServerSocket listener;
    private final byte[] page;
    public final CountDownLatch received=new CountDownLatch(1);
    public volatile List<Part> parts;
    public volatile String error,uploadUserAgent;
    public final CountDownLatch pageServed=new CountDownLatch(1);
    private volatile boolean closed;
    static final class Part {
        final String field,filename,mime;
        final byte[] bytes;
        Part(String field,String filename,String mime,byte[] bytes){
            this.field=field;this.filename=filename;this.mime=mime;this.bytes=bytes;
        }
    }
    LoopbackUploadServer(String html) throws IOException {
        page=html.getBytes(StandardCharsets.UTF_8);
        listener=new ServerSocket(0,4,InetAddress.getByName("127.0.0.1"));
        Thread worker=new Thread(this::serve,"ImageOrder-http-fixture");
        worker.setDaemon(true);worker.start();
    }
    String url(){return "http://127.0.0.1:"+listener.getLocalPort()+"/";}
    private void serve(){
        while(!closed){
            try{
                Socket socket=listener.accept();
                Thread client=new Thread(()->{
                    try(Socket connection=socket){
                        connection.setSoTimeout(15000);
                        handle(connection);
                    }catch(IOException ex){
                        // Browser speculative connections can time out before an HTTP request.
                        // Only an actual multipart POST failure is a failed upload.
                        android.util.Log.w("ImageOrderHttp","Connection ended: "+ex);
                    }
                },"ImageOrder-http-client");
                client.setDaemon(true);client.start();
            }catch(IOException ex){
                if(!closed){error=ex.toString();received.countDown();}
            }
        }
    }
    private void handle(Socket socket) throws IOException {
        InputStream in=new BufferedInputStream(socket.getInputStream());
        OutputStream out=socket.getOutputStream();
        String request=line(in);
        if(request==null||request.isEmpty())return;
        Map<String,String> headers=new HashMap<>();
        for(String h;(h=line(in))!=null&&!h.isEmpty();){
            int k=h.indexOf(':');
            if(k>0)headers.put(h.substring(0,k).trim().toLowerCase(Locale.ROOT),h.substring(k+1).trim());
        }
        if(request.startsWith("GET / HTTP/")){
            respond(out,200,"text/html; charset=utf-8",page);pageServed.countDown();return;
        }
        if(!request.startsWith("POST /upload HTTP/")){
            respond(out,404,"text/plain",new byte[0]);return;
        }
        uploadUserAgent=headers.get("user-agent");
        try{
            if("100-continue".equalsIgnoreCase(headers.get("expect"))){
                out.write("HTTP/1.1 100 Continue\r\n\r\n".getBytes(StandardCharsets.US_ASCII));out.flush();
            }
            byte[] body;
            if("chunked".equalsIgnoreCase(headers.get("transfer-encoding"))){
                ByteArrayOutputStream all=new ByteArrayOutputStream();
                while(true){
                    String size=line(in);
                    if(size==null)throw new EOFException("Missing chunk length");
                    int n=Integer.parseInt(size.split(";",2)[0].trim(),16);
                    if(n==0)break;
                    if(n<0||n>MAX_BODY-all.size())throw new IOException("Multipart limit");
                    all.write(readExactly(in,n));
                    if(!"".equals(line(in)))throw new IOException("Bad chunk ending");
                }
                body=all.toByteArray();
            }else{
                String length=headers.get("content-length");
                if(length==null)throw new IOException("Missing Content-Length");
                body=readExactly(in,Integer.parseInt(length));
            }
            parts=parse(headers.get("content-type"),body);
            respond(out,200,"text/plain","ok".getBytes(StandardCharsets.US_ASCII));
        }catch(Exception ex){
            error=ex.toString();
            respond(out,400,"text/plain","invalid multipart".getBytes(StandardCharsets.US_ASCII));
        }finally{received.countDown();}
    }
    static List<Part> parse(String type,byte[] body) throws IOException {
        if(type==null||!type.toLowerCase(Locale.ROOT).startsWith("multipart/form-data"))
            throw new IOException("Expected multipart/form-data: "+type);
        Matcher bm=Pattern.compile("(?i)(?:^|;)\\s*boundary=(?:\"([^\"]+)\"|([^;\\s]+))").matcher(type);
        if(!bm.find())throw new IOException("Missing multipart boundary");
        String boundary="--"+(bm.group(1)!=null?bm.group(1):bm.group(2));
        String raw=new String(body,StandardCharsets.ISO_8859_1);
        List<Part> result=new ArrayList<>();
        int pos=0;
        while(true){
            if(!raw.startsWith(boundary,pos))throw new IOException("Invalid multipart delimiter");
            pos+=boundary.length();
            if(raw.startsWith("--",pos))return Collections.unmodifiableList(result);
            if(!raw.startsWith("\r\n",pos))throw new IOException("Missing part delimiter CRLF");
            pos+=2;
            int end=raw.indexOf("\r\n\r\n",pos);
            if(end<0)throw new IOException("Missing part headers");
            Map<String,String> hs=new HashMap<>();
            for(String h:raw.substring(pos,end).split("\r\n")){
                int k=h.indexOf(':');
                if(k>0)hs.put(h.substring(0,k).toLowerCase(Locale.ROOT),h.substring(k+1).trim());
            }
            String disposition=hs.get("content-disposition");
            if(disposition==null)throw new IOException("Missing disposition");
            String field=attribute(disposition,"name"),file=attribute(disposition,"filename");
            int start=end+4;
            int next=raw.indexOf("\r\n"+boundary,start);
            if(next<0)throw new IOException("Missing closing boundary");
            result.add(new Part(field,file,hs.get("content-type"),
                Arrays.copyOfRange(body,start,next)));
            pos=next+2;
        }
    }
    private static String attribute(String header,String name) throws IOException {
        Matcher m=Pattern.compile("(?:^|;)\\s*"+name+"=\"([^\"]*)\"").matcher(header);
        if(!m.find())throw new IOException("Missing disposition "+name);
        return m.group(1);
    }
    private static byte[] readExactly(InputStream in,int n) throws IOException {
        if(n<0||n>MAX_BODY)throw new IOException("Invalid request length "+n);
        byte[] data=new byte[n];
        int i=0;
        while(i<n){int count=in.read(data,i,n-i);if(count<0)throw new EOFException("Truncated HTTP body");i+=count;}
        return data;
    }
    private static String line(InputStream in) throws IOException {
        ByteArrayOutputStream b=new ByteArrayOutputStream();
        for(int c;(c=in.read())!=-1;){
            if(c=='\n'){
                byte[] bytes=b.toByteArray();int n=bytes.length;
                if(n>0&&bytes[n-1]=='\r')n--;
                return new String(bytes,0,n,StandardCharsets.US_ASCII);
            }
            if(b.size()>16384)throw new IOException("HTTP line too long");
            b.write(c);
        }
        return b.size()==0?null:new String(b.toByteArray(),StandardCharsets.US_ASCII);
    }
    private static void respond(OutputStream out,int status,String type,byte[] bytes) throws IOException {
        String header="HTTP/1.1 "+status+(status==200?" OK":status==404?" Not Found":" Bad Request")
            +"\r\nContent-Type: "+type+"\r\nContent-Length: "+bytes.length+"\r\nConnection: close\r\n\r\n";
        out.write(header.getBytes(StandardCharsets.US_ASCII));out.write(bytes);out.flush();
    }
    @Override public void close(){closed=true;try{listener.close();}catch(IOException ignored){}}
}
