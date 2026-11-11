package com.twobornot.imageorder;

import android.Manifest;
import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.*;
import android.net.Uri;
import android.os.*;
import android.provider.MediaStore;
import android.util.LruCache;
import android.util.Size;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/**
 * Single direct media gallery for both launcher and external upload picker requests.
 * The ONLY sequence source is a user's taps in this Activity, not MediaStore sorting.
 */
public final class NativeGalleryActivity extends Activity {
    static final String EXTRA_MAX_SELECTION="com.twobornot.imageorder.MAX_SELECTION";
    static final String EXTRA_ORDER_VERIFIED="com.twobornot.imageorder.ORDER_VERIFIED";
    private static final int PERMISSION=27, FALLBACK=28;
    private static final int NAVY=0xff0e1218, BLUE=0xff73c2f7, CARD=0xff20262e;
    private final ArrayList<Photo> photos=new ArrayList<>();
    private final ArrayList<Photo> displayed=new ArrayList<>();
    private final LinkedHashMap<String,Uri> ordered=new LinkedHashMap<>();
    private final LinkedHashMap<String,ArrayList<Photo>> albums=new LinkedHashMap<>();
    private String activeAlbum=null;
    private boolean albumsTab=true;
    private int maxSelection=100;
    private GridView grid;
    private BaseAdapter adapter;
    private TextView heading, confirm, photosTab, albumsTabView, hint;
    private final Handler ui=new Handler(Looper.getMainLooper());
    private final ExecutorService thumbs=Executors.newFixedThreadPool(3);
    private final ExecutorService images=Executors.newSingleThreadExecutor();
    private final LruCache<String,Bitmap> cache=new LruCache<String,Bitmap>(16*1024*1024) {
        @Override protected int sizeOf(String key,Bitmap bitmap){return bitmap.getByteCount();}
    };
    private final Set<String> pending=Collections.synchronizedSet(new HashSet<>());

    private static final class Photo {
        final String key, album, name;
        final Uri uri;
        Photo(String key,String album,String name,Uri uri){this.key=key;this.album=album;this.name=name;this.uri=uri;}
    }
    private boolean ko(){return Locale.getDefault().getLanguage().equals("ko");}
    private String t(String kr,String en){return ko()?kr:en;}
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+0.5f);}
    private TextView text(String s,int size,int color,boolean weight){
        TextView v=new TextView(this);v.setText(s);v.setTextSize(size);v.setTextColor(color);
        if(weight)v.setTypeface(null,1);return v;
    }
    @Override public void onCreate(Bundle b){
        super.onCreate(b);
        maxSelection=Math.max(1,Math.min(200,getIntent().getIntExtra(EXTRA_MAX_SELECTION,100)));
        getWindow().setStatusBarColor(NAVY);getWindow().setNavigationBarColor(NAVY);
        makeUi();
        if(hasPermission())reload();else askPermission();
    }
    private void makeUi(){
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(NAVY);setContentView(root);
        LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);
        top.setPadding(dp(15),dp(14),dp(15),dp(13));root.addView(top);
        TextView back=text("‹",32,0xffffffff,false);back.setGravity(Gravity.CENTER);
        top.addView(back,new LinearLayout.LayoutParams(dp(42),dp(48)));back.setOnClickListener(v->onBackPressed());
        heading=text(t("앨범","Albums"),23,0xffffffff,true);top.addView(heading,new LinearLayout.LayoutParams(0,dp(48),1));
        confirm=text(t("확인","Done"),16,BLUE,true);confirm.setGravity(Gravity.CENTER);
        top.addView(confirm,new LinearLayout.LayoutParams(dp(115),dp(48)));
        confirm.setOnClickListener(v->finishSelection());
        hint=text(t("사진을 누른 순서대로 1, 2, 3… 번호가 매겨집니다", "Tap photos in order: 1, 2, 3…"),12,0xffbfc6cf,false);
        hint.setPadding(dp(19),0,dp(10),dp(9));root.addView(hint);
        grid=new GridView(this);grid.setNumColumns(3);grid.setVerticalSpacing(dp(7));grid.setHorizontalSpacing(dp(7));
        grid.setPadding(dp(7),dp(7),dp(7),dp(7));grid.setClipToPadding(false);
        root.addView(grid,new LinearLayout.LayoutParams(-1,0,1));
        adapter=new BaseAdapter(){
            @Override public int getCount(){return albumsTab?albums.size():displayed.size();}
            @Override public Object getItem(int p){return albumsTab?new ArrayList<>(albums.keySet()).get(p):displayed.get(p);}
            @Override public long getItemId(int p){return p;}
            @Override public View getView(int p,View reuse,android.view.ViewGroup parent){return tile(p);}
        };grid.setAdapter(adapter);
        grid.setOnItemClickListener((p,v,index,id)->{
            if(albumsTab){
                activeAlbum=new ArrayList<>(albums.keySet()).get(index);albumsTab=false;renderList();
            }else{
                Photo photo=displayed.get(index);
                if(ordered.containsKey(photo.key))ordered.remove(photo.key);
                else if(ordered.size()<maxSelection)ordered.put(photo.key,photo.uri);
                else Toast.makeText(this,t("최대 ","Maximum ")+maxSelection+t("장"," images"),Toast.LENGTH_SHORT).show();
                updateSelection();adapter.notifyDataSetChanged();
            }
        });
        LinearLayout bottom=new LinearLayout(this);bottom.setGravity(Gravity.CENTER);
        bottom.setPadding(dp(14),dp(8),dp(14),dp(16));bottom.setBackgroundColor(0xff161b22);
        root.addView(bottom);
        photosTab=text(t("사진","Photos"),17,0xffdddddd,true);
        albumsTabView=text(t("앨범","Albums"),17,0xffdddddd,true);
        for(TextView v:new TextView[]{photosTab,albumsTabView}){
            v.setGravity(Gravity.CENTER);bottom.addView(v,new LinearLayout.LayoutParams(0,dp(54),1));
        }
        photosTab.setOnClickListener(v->{albumsTab=false;activeAlbum=null;renderList();});
        albumsTabView.setOnClickListener(v->{albumsTab=true;activeAlbum=null;renderList();});
        updateSelection();
    }
    private View tile(int index){
        FrameLayout frame=new FrameLayout(this);frame.setBackgroundColor(CARD);
        frame.setLayoutParams(new AbsListView.LayoutParams(-1,dp(albumsTab?175:122)));
        Photo p;
        String folder="";int count=0;
        if(albumsTab){
            folder=new ArrayList<>(albums.keySet()).get(index);
            ArrayList<Photo> group=albums.get(folder);p=group.get(0);count=group.size();
        }else p=displayed.get(index);
        ImageView image=new ImageView(this);image.setScaleType(ImageView.ScaleType.CENTER_CROP);
        image.setBackgroundColor(0xff2b333c);frame.addView(image,new FrameLayout.LayoutParams(-1,-1));
        Bitmap b=cache.get(p.key);
        if(b!=null&&!b.isRecycled())image.setImageBitmap(b);
        else requestThumbnail(p);
        if(albumsTab){
            TextView caption=text(folder+"\n"+count,12,0xffffffff,true);
            caption.setBackgroundColor(0xba10151b);caption.setPadding(dp(7),dp(5),dp(4),dp(6));
            FrameLayout.LayoutParams cp=new FrameLayout.LayoutParams(-1,dp(47),Gravity.BOTTOM);
            frame.addView(caption,cp);
        }else{
            int rank=rankOf(p.key);
            if(rank>0){
                TextView badge=text(String.valueOf(rank),17,0xff101621,true);badge.setGravity(Gravity.CENTER);
                android.graphics.drawable.GradientDrawable bg=new android.graphics.drawable.GradientDrawable();
                bg.setColor(BLUE);bg.setCornerRadius(dp(40));badge.setBackground(bg);
                FrameLayout.LayoutParams badgeLp=new FrameLayout.LayoutParams(dp(35),dp(35),Gravity.RIGHT|Gravity.TOP);
                badgeLp.setMargins(dp(4),dp(5),dp(5),dp(4));frame.addView(badge,badgeLp);
            }
        }
        return frame;
    }
    private int rankOf(String key){int rank=0;for(String k:ordered.keySet()){rank++;if(k.equals(key))return rank;}return 0;}
    private void requestThumbnail(Photo photo){
        if(!pending.add(photo.key))return;
        thumbs.execute(()->{
            Bitmap b=null;
            try{
                if(Build.VERSION.SDK_INT>=29) b=getContentResolver().loadThumbnail(photo.uri,new Size(280,280),null);
                else{
                    BitmapFactory.Options opts=new BitmapFactory.Options();opts.inSampleSize=4;
                    try(InputStream in=getContentResolver().openInputStream(photo.uri)){
                        if(in!=null)b=BitmapFactory.decodeStream(in,null,opts);
                    }
                }
            }catch(Exception ignored){}
            Bitmap result=b;
            ui.post(()->{
                pending.remove(photo.key);
                if(result!=null)cache.put(photo.key,result);
                if(!isFinishing()&&adapter!=null)adapter.notifyDataSetChanged();
            });
        });
    }
    private void updateSelection(){
        if(confirm!=null)confirm.setText(t("확인 ","Done ")+ordered.size());
        if(photosTab!=null)photosTab.setTextColor(albumsTab?0xffb3b3b3:BLUE);
        if(albumsTabView!=null)albumsTabView.setTextColor(albumsTab?BLUE:0xffb3b3b3);
    }
    private void renderList(){
        displayed.clear();
        if(!albumsTab){
            if(activeAlbum!=null)displayed.addAll(albums.getOrDefault(activeAlbum,new ArrayList<>()));
            else displayed.addAll(photos);
        }
        heading.setText(albumsTab?t("앨범","Albums"):(activeAlbum==null?t("사진","Photos"):activeAlbum));
        updateSelection();adapter.notifyDataSetChanged();grid.setSelection(0);
    }
    private boolean hasPermission(){
        if(Build.VERSION.SDK_INT>=34){return checkSelfPermission(Manifest.permission.READ_MEDIA_IMAGES)==PackageManager.PERMISSION_GRANTED
               ||checkSelfPermission(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)==PackageManager.PERMISSION_GRANTED;}
        if(Build.VERSION.SDK_INT>=33)return checkSelfPermission(Manifest.permission.READ_MEDIA_IMAGES)==PackageManager.PERMISSION_GRANTED;
        return checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE)==PackageManager.PERMISSION_GRANTED;
    }
    private void askPermission(){
        String[] permissions;
        if(Build.VERSION.SDK_INT>=34)permissions=new String[]{Manifest.permission.READ_MEDIA_IMAGES,Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED};
        else if(Build.VERSION.SDK_INT>=33)permissions=new String[]{Manifest.permission.READ_MEDIA_IMAGES};
        else permissions=new String[]{Manifest.permission.READ_EXTERNAL_STORAGE};
        requestPermissions(permissions,PERMISSION);
    }
    @Override public void onRequestPermissionsResult(int req,String[] per,int[] grants){
        super.onRequestPermissionsResult(req,per,grants);
        if(req==PERMISSION){if(hasPermission())reload();else fallbackPicker();}
    }
    private void reload(){
        hint.setText(t("갤러리 불러오는 중…","Loading gallery…"));
        images.execute(()->{
            ArrayList<Photo> list=new ArrayList<>();
            Uri uri=Build.VERSION.SDK_INT>=29?MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL):MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
            String[] cols={MediaStore.Images.Media._ID,MediaStore.Images.Media.DISPLAY_NAME,
                MediaStore.Images.Media.BUCKET_DISPLAY_NAME};
            try(Cursor c=getContentResolver().query(uri,cols,null,null,
                MediaStore.Images.Media.DATE_ADDED+" DESC, "+MediaStore.Images.Media._ID+" DESC")){
                if(c!=null){
                    int idIndex=c.getColumnIndexOrThrow(MediaStore.Images.Media._ID);
                    int nm=c.getColumnIndexOrThrow(MediaStore.Images.Media.DISPLAY_NAME);
                    int bucket=c.getColumnIndexOrThrow(MediaStore.Images.Media.BUCKET_DISPLAY_NAME);
                    while(c.moveToNext() && list.size()<10000){
                        long id=c.getLong(idIndex);String name=c.getString(nm),folder=c.getString(bucket);
                        if(folder==null||folder.isEmpty())folder=t("기타","Other");
                        list.add(new Photo(String.valueOf(id),folder,name,
                            ContentUris.withAppendedId(uri,id)));
                    }
                }
            }catch(Exception e){android.util.Log.w("ImageOrderStudio","MediaStore read error",e);}
            ui.post(()->{
                photos.clear();photos.addAll(list);albums.clear();
                for(Photo p:photos)albums.computeIfAbsent(p.album,k->new ArrayList<>()).add(p);
                hint.setText(photos.isEmpty()?t("사진이 없습니다. 갤러리 접근 권한을 확인하세요.","No photos. Check gallery permission."):
                    t("선택한 순서대로 번호가 매겨집니다", "Your taps determine the image order"));
                renderList();
            });
        });
    }
    /** Denied gallery permission still permits intentional system-photo selection. */
    private void fallbackPicker(){
        try{
            Intent i;
            if(Build.VERSION.SDK_INT>=33) {
                i=new Intent(MediaStore.ACTION_PICK_IMAGES);i.setType("image/*");
                int max=MediaStore.getPickImagesMaxLimit();
                if(max>1)i.putExtra(MediaStore.EXTRA_PICK_IMAGES_MAX,Math.min(max,maxSelection));
            }else{
                i=new Intent(Intent.ACTION_GET_CONTENT);i.setType("image/*");
                i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
                i=Intent.createChooser(i,t("사진 선택","Select photos"));
                i.putExtra(Intent.EXTRA_EXCLUDE_COMPONENTS,new ComponentName[]{new ComponentName(this,MainActivity.class)});
            }
            startActivityForResult(i,FALLBACK);
        }catch(Exception ex){Toast.makeText(this,t("사진 접근 권한이 필요합니다.","Photo access is required."),Toast.LENGTH_LONG).show();finish();}
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=FALLBACK)return;
        if(result!=RESULT_OK||data==null){finish();return;}
        ArrayList<Uri> uris=new ArrayList<>();
        if(data.getClipData()!=null){
            for(int i=0;i<data.getClipData().getItemCount();i++)uris.add(data.getClipData().getItemAt(i).getUri());
        }else if(data.getData()!=null)uris.add(data.getData());
        // Imported order from an external picker is not verified. Require explicit taps.
        ordered.clear();photos.clear();albums.clear();
        for(int i=0;i<uris.size();i++){
            Uri uri=uris.get(i);
            Photo p=new Photo("fallback:"+i,t("선택한 사진","Imported Photos"),"Photo "+(i+1),uri);
            photos.add(p);albums.computeIfAbsent(p.album,k->new ArrayList<>()).add(p);
        }
        albumsTab=false;activeAlbum=null;renderList();
        hint.setText(t("사진을 원하는 순서대로 다시 눌러주세요", "Tap imported photos in the intended order"));
    }
    private void finishSelection(){
        if(ordered.isEmpty()){
            Toast.makeText(this,t("사진을 순서대로 선택하세요","Select photos in order"),Toast.LENGTH_SHORT).show();return;
        }
        Intent data=new Intent();data.setType("image/*");
        data.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        ClipData clips=null;
        for(Uri uri:ordered.values()){
            if(clips==null)clips=ClipData.newRawUri("Image Order Studio",uri);
            else clips.addItem(new ClipData.Item(uri));
        }
        data.setClipData(clips);
        data.setData(ordered.values().iterator().next());
        data.putExtra(EXTRA_ORDER_VERIFIED,true);
        setResult(RESULT_OK,data);finish();
    }
    @Override public void onBackPressed(){
        if(!albumsTab && activeAlbum!=null){activeAlbum=null;albumsTab=true;renderList();return;}
        super.onBackPressed();
    }
    @Override protected void onDestroy(){super.onDestroy();thumbs.shutdownNow();images.shutdownNow();}
}
