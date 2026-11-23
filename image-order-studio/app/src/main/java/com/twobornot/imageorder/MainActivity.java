package com.twobornot.imageorder;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.MediaStore;
import android.os.ext.SdkExtensions;
import android.view.*;
import android.widget.*;
import android.util.LruCache;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.*;

/**
 * Sequence is set by taps IN THIS APP, never by a provider's returned ClipData ordering.
 * All exported image bytes are preserved. Only the ordered URI list is constructed here.
 */
public class MainActivity extends Activity {
    private static final int IMPORT_IMAGES=100, CHOOSE_FOLDER=200;
    private static final String SAMSUNG_GALLERY="com.sec.android.gallery3d";
    private static final String PHOTO_PREF="preferred_photo_source";
    private static final int NAVY=0xff182C46, BLUE=0xff2563EB, MUTED=0xff60748C;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final ExecutorService thumbWorker=Executors.newFixedThreadPool(2);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private GalleryStore store;
    private GridView grid;
    private BaseAdapter adapter;
    private TextView status, subtitle;
    private final LruCache<String,Bitmap> thumbs=new LruCache<String,Bitmap>(12*1024*1024) {
        @Override protected int sizeOf(String id,Bitmap b){ return b.getByteCount(); }
    };
    private final Set<String> loading=Collections.synchronizedSet(new HashSet<>());
    private final Set<String> failedThumbs=Collections.synchronizedSet(new HashSet<>());
    /** External IMAGE GET_CONTENT/PICK requests are isolated from the user's persistent library. */
    private boolean externalMode=false;
    private boolean externalAllowsMultiple=false;
    private String requestedMime="image/*";
    private boolean nativePickerOrdered=false;
    private boolean working=false;
    private boolean selectedOnly=false;
    private boolean selectedFirst=false;

    private final ArrayList<GalleryStore.Item> visibleItems = new ArrayList<>();

    private boolean ko() {return Locale.getDefault().getLanguage().equals("ko");}
    private String t(String ko,String en) {return ko()?ko:en;}
    private int dp(float n) {return (int)(getResources().getDisplayMetrics().density*n+0.5f);}

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(NAVY);getWindow().setNavigationBarColor(0xffeef2f8);
        Intent launch=getIntent();
        externalMode=isExternalImageRequest(launch);
        externalAllowsMultiple=externalMode && launch.getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false);
        if(externalMode && Intent.ACTION_PICK.equals(launch.getAction())) externalAllowsMultiple=false;
        if(externalMode && launch.getType()!=null)requestedMime=launch.getType();
        store=new GalleryStore(this,externalMode);
        setup();rebuildVisible();updateCounters();
        if(externalMode) ui.post(this::openPicker);
        else handleIncoming(launch);
    }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);setIntent(intent);
        if(!externalMode)handleIncoming(intent);
    }
    private static boolean isExternalImageRequest(Intent intent) {
        if(intent==null)return false;
        String a=intent.getAction(), type=intent.getType();
        if(Intent.ACTION_GET_CONTENT.equals(a))return type!=null && (type.startsWith("image/") || "*/*".equals(type));
        if(!Intent.ACTION_PICK.equals(a))return false;
        if(type!=null && (type.startsWith("image/") || type.contains("cursor.dir/image")))return true;
        Uri data=intent.getData();
        if(data==null || !"content".equals(data.getScheme()))return false;
        String authority=data.getAuthority(), path=data.getPath();
        return authority!=null && authority.startsWith("media") && path!=null
            && path.contains("images");
    }
    private void setup() {
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xfff3f6fa);setContentView(root);
        LinearLayout header=new LinearLayout(this);header.setPadding(dp(18),dp(18),dp(18),dp(13));
        header.setOrientation(LinearLayout.VERTICAL);header.setBackgroundColor(NAVY);root.addView(header);
        TextView title=text(externalMode?t("사진 첨부 · 순서 지정","Attach images · set order"):"Image Order Studio",23,0xffffffff,true);header.addView(title);
        subtitle=text(externalMode?t("원본 사진 선택 → 그대로 첨부", "Select original images → attach unchanged"):
            t("원본 그대로 · 선택 순서대로", "Original files · selected order"),12,0xffcbd8ee,false);
        header.addView(subtitle);
        LinearLayout toolbar=row(); toolbar.setPadding(dp(8),dp(10),dp(8),dp(5));root.addView(toolbar);
        addButton(toolbar,t("＋ 갤러리","＋ Gallery"),()->openPicker(),BLUE);

        LinearLayout toolbarOrder=row();toolbarOrder.setPadding(dp(8),0,dp(8),dp(5));root.addView(toolbarOrder);
        addButton(toolbarOrder,t("순서 편집","Edit order"),()->editSequence(),NAVY);
        if(!externalMode)addButton(toolbarOrder,t("다른 기능 · 설정","More tools / settings"),()->showOtherTools(),0xff6f8095);
        status=text("",13,NAVY,true);status.setPadding(dp(14),dp(8),dp(14),dp(5));root.addView(status);
        TextView instructions=text(externalMode?
            t("파란 숫자는 업로드 순서입니다. 사진 내용은 변경하지 않습니다.",
              "Blue numbers show the upload order. Image contents are never changed."):
            t("갤러리에서 사진을 순서대로 선택하세요. 원본 이미지 그대로 전달됩니다.",
              "Select images in order. Original image bytes will be sent unchanged."),12,MUTED,false);
        instructions.setPadding(dp(14),0,dp(14),dp(12));root.addView(instructions);
        grid=new GridView(this);grid.setNumColumns(GridView.AUTO_FIT);grid.setColumnWidth(dp(109));
        grid.setHorizontalSpacing(dp(6));grid.setVerticalSpacing(dp(6));grid.setPadding(dp(9),dp(8),dp(9),dp(10));
        grid.setClipToPadding(false);grid.setStretchMode(GridView.STRETCH_COLUMN_WIDTH);
        grid.setBackgroundColor(0xfff3f6fa);root.addView(grid,new LinearLayout.LayoutParams(-1,0,1));
        adapter=new BaseAdapter() {
            @Override public int getCount(){return visibleItems.size();}
            @Override public Object getItem(int p){return visibleItems.get(p);}
            @Override public long getItemId(int p){return p;}
            @Override public View getView(int p,View convert,android.view.ViewGroup parent){return tile(visibleItems.get(p));}
        };
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent,view,position,id)->{
            if(working) return;
            GalleryStore.Item item=visibleItems.get(position);
            if(store.sequence.rank(item.id)>0) store.sequence.deselect(item.id);
            else store.sequence.select(item.id);
            store.save();rebuildVisible();updateCounters();
        });
        grid.setOnItemLongClickListener((parent,view,position,id)->{
            if(working)return true;
            GalleryStore.Item item=visibleItems.get(position);
            new AlertDialog.Builder(this).setTitle(t("이미지 삭제","Remove image"))
                .setMessage(item.name+"\n"+t("앱 보관함에서만 삭제합니다. 원본은 그대로 둡니다.",
                    "Remove the private copy only. The original stays on your device."))
                .setPositiveButton(t("삭제","Remove"),(d,w)->{
                    store.remove(item);thumbs.remove(item.id);rebuildVisible();updateCounters();
                }).setNegativeButton(t("취소","Cancel"),null).show();
            return true;
        });
        if(externalMode) {
            selectedFirst=true;
            LinearLayout primary=row();primary.setPadding(dp(8),dp(6),dp(8),dp(4));root.addView(primary);
            addButton(primary,t("✓ 원본 그대로 첨부","✓ Attach originals"),()->returnToCaller(),BLUE);
            LinearLayout secondary=row();secondary.setPadding(dp(8),0,dp(8),dp(10));root.addView(secondary);
            addButton(secondary,t("처음부터 선택","Restart order"),()->confirmClearSequence(),NAVY);
            addButton(secondary,t("취소하고 돌아가기","Cancel and return"),()->cancelExternal(),0xff6f8095);
        } else {
            LinearLayout primary=row();primary.setPadding(dp(8),dp(6),dp(8),dp(6));root.addView(primary);
            addButton(primary,t("✓ 원본 순서대로 공유","✓ Share originals in order"),this::shareOriginals,BLUE);
        }
    }
    private LinearLayout row() {
        LinearLayout r=new LinearLayout(this);r.setOrientation(LinearLayout.HORIZONTAL);return r;
    }
    private void addButton(LinearLayout parent,String label,Runnable f,int color) {
        TextView b=text(label,13,0xffffffff,true);b.setGravity(Gravity.CENTER);
        GradientDrawable bg=new GradientDrawable();bg.setColor(color);bg.setCornerRadius(dp(10));b.setBackground(bg);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(44),1);lp.setMargins(dp(3),dp(2),dp(3),dp(2));parent.addView(b,lp);
        b.setOnClickListener(v->f.run());
    }
    private TextView text(String s,int sp,int color,boolean bold) {
        TextView tv=new TextView(this);tv.setText(s);tv.setTextSize(sp);tv.setTextColor(color);
        if(bold)tv.setTypeface(null,1);return tv;
    }
    private View tile(GalleryStore.Item item) {
        FrameLayout card=new FrameLayout(this);card.setBackgroundColor(0xffffffff);
        int rank=store.sequence.rank(item.id);
        GradientDrawable shape=new GradientDrawable();shape.setColor(0xffffffff);shape.setCornerRadius(dp(6));
        shape.setStroke(dp(rank>0?3:1),rank>0?BLUE:0xffd5dce5);card.setBackground(shape);
        ImageView image=new ImageView(this);image.setScaleType(ImageView.ScaleType.CENTER_CROP);
        image.setBackgroundColor(0xffe4ebf3);card.addView(image,new FrameLayout.LayoutParams(-1,-1));
        Bitmap cached=thumbs.get(item.id);
        if(cached!=null && !cached.isRecycled()) image.setImageBitmap(cached);
        else loadThumbnail(item);
        if(rank>0) {
            GradientDrawable outline=new GradientDrawable();outline.setColor(0x00000000);
            outline.setStroke(dp(3),BLUE);outline.setCornerRadius(dp(6));
            View highlight=new View(this);highlight.setBackground(outline);
            card.addView(highlight,new FrameLayout.LayoutParams(-1,-1));
        }
        TextView name=text(item.name,10,0xffffffff,false);name.setSingleLine(true);name.setEllipsize(android.text.TextUtils.TruncateAt.END);
        name.setPadding(dp(5),dp(4),dp(5),dp(4));name.setBackgroundColor(0xb6000000);
        FrameLayout.LayoutParams labelLp=new FrameLayout.LayoutParams(-1,dp(29),Gravity.BOTTOM);card.addView(name,labelLp);
        if(rank>0) {
            TextView rankView=text(String.valueOf(rank),17,0xffffffff,true);rankView.setGravity(Gravity.CENTER);
            GradientDrawable badge=new GradientDrawable();badge.setColor(BLUE);badge.setCornerRadius(dp(24));rankView.setBackground(badge);
            FrameLayout.LayoutParams rlp=new FrameLayout.LayoutParams(dp(39),dp(39),Gravity.TOP|Gravity.END);
            rlp.setMargins(0,dp(4),dp(4),0);card.addView(rankView,rlp);
        }
        card.setLayoutParams(new AbsListView.LayoutParams(-1,dp(113)));
        return card;
    }
    private void loadThumbnail(GalleryStore.Item item) {
        if(failedThumbs.contains(item.id) || !loading.add(item.id)) return;
        thumbWorker.execute(()->{
            Bitmap bmp=null;
            try {
                bmp=ThumbnailDecoder.decode(store.source(item),256,160000);
            } catch(Exception ignored) {}
            final Bitmap result=bmp;
            ui.post(()->{
                loading.remove(item.id);
                if(result!=null) thumbs.put(item.id,result);
                else failedThumbs.add(item.id);
                if(adapter!=null) adapter.notifyDataSetChanged();
            });
        });
    }
    private void rebuildVisible() {
        visibleItems.clear();
        for(GalleryStore.Item item:store.items) {
            if(!selectedOnly || store.sequence.rank(item.id)>0) visibleItems.add(item);
        }
        if(selectedFirst) {
            final Map<String,Integer> originalPositions = new HashMap<>();
            for(int i=0;i<store.items.size();i++) originalPositions.put(store.items.get(i).id,i);
            Collections.sort(visibleItems,(a,b)->{
                int ra=store.sequence.rank(a.id),rb=store.sequence.rank(b.id);
                if(ra==0 && rb!=0)return 1;
                if(rb==0 && ra!=0)return -1;
                if(ra!=0 && rb!=0)return Integer.compare(ra,rb);
                return Integer.compare(originalPositions.get(a.id),originalPositions.get(b.id));
            });
        }
        if(adapter!=null)adapter.notifyDataSetChanged();
    }
    private void updateCounters(){
        if(status!=null) status.setText(t("보관함 ","Library ")+store.items.size()+
            t("장  •  선택 "," images  •  Selected ")+store.sequence.size()
            +t("장"," images") + (selectedOnly?t("  •  선택만 표시","  •  Filtered"):"")
            + (selectedFirst?t("  •  선택순 정렬","  •  Ordered first"):""));
    }
    /** One gallery experience for both launcher use and third-party GET_CONTENT/PICK calls. */
    private void openPicker() {
        if(working)return;
        Intent gallery=new Intent(this,NativeGalleryActivity.class);
        gallery.putExtra(NativeGalleryActivity.EXTRA_MAX_SELECTION,externalMode&&!externalAllowsMultiple?1:100);
        gallery.putExtra(NativeGalleryActivity.EXTRA_ACCEPTED_MIME,externalMode?requestedMime:"image/*");
        if(externalMode) {
            String[] accepted=getIntent().getStringArrayExtra(Intent.EXTRA_MIME_TYPES);
            if(accepted!=null)gallery.putExtra(NativeGalleryActivity.EXTRA_MIME_TYPES,accepted);
        }
        startActivityForResult(gallery,IMPORT_IMAGES);
    }
    private boolean trySamsungPicker() {
        // Package-targeted ACTION_GET_CONTENT bypasses the unrequested AOSP Photo Picker UI.
        // Samsung Gallery returns the user's chosen images via ordinary content:// URIs.
        Intent gallery=new Intent(Intent.ACTION_GET_CONTENT);
        gallery.setType("image/*");gallery.setPackage(SAMSUNG_GALLERY);
        gallery.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
        if(tryPhotoIntent(gallery))return true;
        Intent pick=new Intent(Intent.ACTION_PICK,MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        pick.setType("image/*");pick.setPackage(SAMSUNG_GALLERY);
        pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
        return tryPhotoIntent(pick);
    }
    private boolean tryPhotoIntent(Intent intent) {
        try {
            if(intent.resolveActivity(getPackageManager())==null)return false;
            nativePickerOrdered=false;
            startActivityForResult(intent,IMPORT_IMAGES);
            return true;
        }catch(Exception ignored){return false;}
    }
    private boolean trySystemPhotoPicker() {
        try {
            int extension=Build.VERSION.SDK_INT>=30?SdkExtensions.getExtensionVersion(Build.VERSION_CODES.R):0;
            boolean ordered=PickerDecision.supportsOrderedPicker(Build.VERSION.SDK_INT,extension);
            if(!PickerDecision.supportsPhotoPicker(Build.VERSION.SDK_INT,extension))return false;
            Intent photo=new Intent(MediaStore.ACTION_PICK_IMAGES);
            photo.setType("image/*");
            int limit=MediaStore.getPickImagesMaxLimit();
            if(limit>1)photo.putExtra(MediaStore.EXTRA_PICK_IMAGES_MAX,Math.min(limit,100));
            if(ordered)photo.putExtra(MediaStore.EXTRA_PICK_IMAGES_IN_ORDER,true);
            if(photo.resolveActivity(getPackageManager())==null)return false;
            nativePickerOrdered=ordered;
            startActivityForResult(photo,IMPORT_IMAGES);
            return true;
        }catch(Exception ignored){nativePickerOrdered=false;return false;}
    }
    private boolean tryOtherGalleryPicker() {
        try {
            Intent images=new Intent(Intent.ACTION_GET_CONTENT);
            images.setType("image/*");images.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
            images.addCategory(Intent.CATEGORY_OPENABLE);
            Intent chooser=Intent.createChooser(images,t("앨범/갤러리에서 선택","Select from Gallery / albums"));
            chooser.putExtra(Intent.EXTRA_EXCLUDE_COMPONENTS,new android.content.ComponentName[]{
                new android.content.ComponentName(this,MainActivity.class)});
            nativePickerOrdered=false;
            startActivityForResult(chooser,IMPORT_IMAGES);
            return true;
        }catch(Exception ignored){return false;}
    }
    private void choosePhotoSource() {
        final String[] methods={t("삼성 갤러리 우선 (권장)","Samsung Gallery first (recommended)"),
            t("안드로이드 시스템 사진 선택기","Android system photo picker"),
            t("다른 갤러리 / 이미지 선택 앱","Other gallery / image picker")};
        final String[] ids={"samsung","system","generic"};
        String saved=getPreferences(MODE_PRIVATE).getString(PHOTO_PREF,"samsung");
        int current=0;for(int i=0;i<ids.length;i++)if(ids[i].equals(saved))current=i;
        new AlertDialog.Builder(this).setTitle(t("사진을 어디에서 선택할까요?","Choose image source"))
            .setSingleChoiceItems(methods,current,(d,which)->{
                getPreferences(MODE_PRIVATE).edit().putString(PHOTO_PREF,ids[which]).apply();
                d.dismiss();openPicker();
            }).setNegativeButton(t("닫기","Close"),null).show();
    }
    private void openFullSamsungGallery() {
        try {
            Intent gallery=getPackageManager().getLaunchIntentForPackage(SAMSUNG_GALLERY);
            if(gallery==null)throw new android.content.ActivityNotFoundException("Samsung Gallery not installed");
            toastDialog(t("삼성 갤러리에서 사진을 선택한 뒤 '공유' → Image Order Studio를 선택하세요.",
                "Select images in Samsung Gallery, then Share → Image Order Studio."));
            startActivity(gallery);
        }catch(Exception e){toastDialog(t("삼성 갤러리를 찾지 못했습니다. '갤러리에서 선택'을 이용하세요.",
            "Samsung Gallery unavailable. Use Gallery / albums instead."));}
    }
    private void handleIncoming(Intent i) {
        if(i==null) return;
        String action=i.getAction();if(!Intent.ACTION_SEND.equals(action)&&!Intent.ACTION_SEND_MULTIPLE.equals(action))return;
        ArrayList<Uri> uris=new ArrayList<>();
        if(Intent.ACTION_SEND.equals(action)) {
            Uri u=i.getParcelableExtra(Intent.EXTRA_STREAM);if(u!=null)uris.add(u);
        } else {
            ArrayList<Uri> list=i.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
            if(list!=null)uris.addAll(list);
        }
        // Do not trust order in an incoming share intent; import as unranked gallery entries.
        importAll(uris,false); i.setAction(Intent.ACTION_MAIN);
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK||data==null){
            if(request==IMPORT_IMAGES) {
                nativePickerOrdered=false;
                if(externalMode)cancelExternal();
            }
            return;
        }
        if(request==IMPORT_IMAGES) {
            ArrayList<Uri> uris=new ArrayList<>();
            if(data.getClipData()!=null) {
                for(int j=0;j<data.getClipData().getItemCount();j++) uris.add(data.getClipData().getItemAt(j).getUri());
            } else if(data.getData()!=null) uris.add(data.getData());
            boolean trustOrder=data.getBooleanExtra(NativeGalleryActivity.EXTRA_ORDER_VERIFIED,false)
                || PickerDecision.trustNativeOrder(nativePickerOrdered,uris.size());
            nativePickerOrdered=false;
            if(trustOrder && !uris.isEmpty()) {
                // NativeGalleryActivity has already established the user's exact tap order.
                // Forward the ORIGINAL content URIs immediately. Do not re-import or re-encode.
                if(externalMode)deliverDirectToCaller(uris);
                else shareDirectOriginals(uris);
            } else importAll(uris,false);
        } else if(request==CHOOSE_FOLDER) {
            Uri tree=data.getData();if(tree!=null) saveToFolder(tree);
        }
    }
    private void deliverDirectToCaller(ArrayList<Uri> uris) {
        if(!externalMode || uris.isEmpty())return;
        if(!externalAllowsMultiple && uris.size()!=1) {
            toastDialog(t("이미지 한 장을 선택하세요.","Select exactly one image."));
            return;
        }
        try {
            Intent result=MediaIntentResult.forSelection(getContentResolver(),uris);
            setResult(RESULT_OK,result);
            finish();
        }catch(Exception ex){toastDialog(t("원본 전달 실패: ","Cannot return originals: ")+ex);}
    }
    private void shareDirectOriginals(ArrayList<Uri> uris) {
        if(uris.isEmpty())return;
        try {
            Intent share=MediaIntentResult.forShare(getContentResolver(),uris);
            startActivity(Intent.createChooser(share,t("원본 이미지 첨부","Attach original images")));
        }catch(Exception ex){toastDialog(t("원본 공유 실패: ","Cannot share originals: ")+ex);}
    }
    private void importAll(List<Uri> uris,boolean sourceHasVerifiedOrder) {
        if(uris.isEmpty()||working)return;
        run(t("이미지 가져오는 중…","Importing images…"),()->{
            // A fresh gallery confirmation is a new upload batch, not an append of old ranks.
            if(sourceHasVerifiedOrder){store.sequence.clear();store.save();}
            int ok=0;ArrayList<String> errors=new ArrayList<>();
            for(Uri uri:uris) {
                try{
                    if(uri==null)throw new IOException("Picker returned an empty image URI");
                    GalleryStore.Item imported=store.add(uri);
                    // Only use a provider's return order when Android guarantees it.
                    if(sourceHasVerifiedOrder)store.sequence.select(imported.id);
                    ok++;
                }catch(Exception e){errors.add(e.getMessage()==null?e.toString():e.getMessage());}
            }
            if(sourceHasVerifiedOrder)store.save();
            final int count=ok;
            ui.post(()->{
                rebuildVisible();updateCounters();
                if(sourceHasVerifiedOrder && count>0) {
                    // Let run() clear working before launching the export/return job.
                    ui.postDelayed(()->{
                        if(isFinishing()||working)return;
                        if(externalMode) returnToCaller();
                        else shareOriginals();
                    },250);
                }
                // Avoid an extra OK dialog after a successful native photo selection.
                if(!errors.isEmpty())toastDialog(t("가져오기 실패 ","Import errors ")+errors.size()+"\n"+errors.get(0));
                else if(!sourceHasVerifiedOrder && count>0)Toast.makeText(this,
                    t("사진을 가져왔습니다. 원하는 순서대로 탭하세요.",
                      "Photos imported. Tap in your chosen order."),Toast.LENGTH_LONG).show();
            });
        });
    }
    private void cancelExternal(){
        setResult(RESULT_CANCELED);finish();
    }
    /** Only the order of URI references is changed; no image bytes are encoded or rendered. */
    private void returnToCaller() {
        if(!externalMode||!hasSelection()||working)return;
        List<String> ids=store.sequence.snapshot();
        if(!externalAllowsMultiple && ids.size()!=1) {
            toastDialog(t("이 화면에는 원본 사진 한 장만 첨부할 수 있습니다.",
                "This upload accepts one original image. Please select one photo."));
            return;
        }
        deliverToCaller(ids);
    }
    private void deliverToCaller(List<String> ids) {
        run(t("원본 사진 전달 중…","Returning original images…"),()->{
            ArrayList<Uri> uris=originalUris(ids);
            ArrayList<String> mimes=originalMimes(ids);
            if(uris.isEmpty())throw new IOException("No originals to deliver");
            Intent result=MediaIntentResult.forSelection(uris,mimes);
            ui.post(()->{setResult(RESULT_OK,result);finish();});
        });
    }
    private ArrayList<Uri> originalUris(List<String> ids) throws IOException {
        ArrayList<Uri> uris=new ArrayList<>();
        for(String id:ids){
            GalleryStore.Item item=store.find(id);
            if(item==null||!store.source(item).isFile())throw new IOException("Original image missing: "+id);
            uris.add(OriginalImageProvider.uriFor(this,store,item));
        }
        return uris;
    }
    private ArrayList<String> originalMimes(List<String> ids) throws IOException {
        ArrayList<String> mimes=new ArrayList<>();
        for(String id:ids){
            GalleryStore.Item item=store.find(id);
            if(item==null)throw new IOException("Missing image: "+id);
            mimes.add(item.mime);
        }
        return mimes;
    }
    @Override public void onBackPressed() {
        if(externalMode){if(!working)cancelExternal();}
        else super.onBackPressed();
    }
    private void editSequence() {
        List<String> ids=store.sequence.snapshot();
        if(ids.isEmpty()){toastDialog(t("이미지를 먼저 선택하세요.","Select images first."));return;}
        String[] labels=new String[ids.size()];
        for(int i=0;i<ids.size();i++){
            GalleryStore.Item item=store.find(ids.get(i));
            labels[i]=String.format(Locale.ROOT,"%04d  %s",i+1,item==null?"?":item.name);
        }
        new AlertDialog.Builder(this).setTitle(t("선택 순서 편집","Edit sequence"))
            .setItems(labels,(d,position)->{
                new AlertDialog.Builder(this).setTitle(labels[position]).setItems(new String[]{
                    t("한 칸 앞으로","Move earlier"),t("한 칸 뒤로","Move later"),t("선택 해제","Remove")},(d2,choice)->{
                    if(choice==0)store.sequence.swap(position,position-1);
                    if(choice==1)store.sequence.swap(position,position+1);
                    if(choice==2)store.sequence.deselect(ids.get(position));
                    store.save();rebuildVisible();updateCounters();editSequence();
                }).show();
            }).setNegativeButton(t("닫기","Close"),null).show();
    }
    private void confirmClearSequence() {
        new AlertDialog.Builder(this).setTitle(t("선택 순서 초기화","Clear selection?"))
          .setMessage(t("이미지는 보관함에 남습니다.","Imported images stay in your library."))
          .setPositiveButton(t("초기화","Clear"),(d,w)->{
              store.sequence.clear();store.save();rebuildVisible();updateCounters();
          }).setNegativeButton(t("취소","Cancel"),null).show();
    }
    private void confirmClearLibrary() {
        new AlertDialog.Builder(this).setTitle(t("보관함 비우기","Clear library?"))
          .setMessage(t("앱 내부 복사본과 선택 순서를 삭제합니다. 휴대전화의 원본은 삭제하지 않습니다.",
            "Delete app copies and order. Originals on your device are untouched."))
          .setPositiveButton(t("모두 삭제","Delete all"),(d,w)->{
              if(working)return;store.clear();thumbs.evictAll();failedThumbs.clear();rebuildVisible();updateCounters();
          }).setNegativeButton(t("취소","Cancel"),null).show();
    }
    private void pickFolder() {
        if(!hasSelection())return;
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        startActivityForResult(intent,CHOOSE_FOLDER);
    }
    private void saveToFolder(Uri tree) {
        if(!hasSelection())return;
        List<String> ids=store.sequence.snapshot();
        run(t("원본 사진 저장 중…","Saving original images…"),()->{
            android.content.ContentResolver cr=getContentResolver();
            Uri parent=DocumentsContract.buildDocumentUriUsingTree(tree,DocumentsContract.getTreeDocumentId(tree));
            int saved=0;
            for(String id:ids){
                GalleryStore.Item item=store.find(id);
                if(item==null)throw new IOException("Missing image: "+id);
                Uri dest=DocumentsContract.createDocument(cr,parent,item.mime,item.name);
                if(dest==null)throw new IOException("Cannot create original "+item.name);
                try(java.io.InputStream in=new java.io.FileInputStream(store.source(item));
                    java.io.OutputStream out=cr.openOutputStream(dest,"w")){
                    if(out==null)throw new IOException("Cannot write original "+item.name);
                    byte[] b=new byte[65536];int n;
                    while((n=in.read(b))!=-1)out.write(b,0,n);
                }
                saved++;
            }
            int done=saved;
            ui.post(()->toastDialog(t("원본 이미지 ","Saved ")+done
                +t("장을 내용 변경 없이 저장했습니다."," original files without alteration.")));
        });
    }
    private void showOtherTools() {
        String[] items={
            t("원본 이미지 순서대로 공유","Share originals in order"),
            t("원본 파일 폴더에 저장","Save original files to folder"),
            t("선택 순서 목록 복사","Copy sequence list"),
            t("선택한 이미지만 보기","Show selected only"),
            t("선택순 먼저 보기","Show selected first"),
            t("선택 순서 초기화","Clear selection"),
            t("보관함 비우기","Clear library")
        };
        new AlertDialog.Builder(this).setTitle(t("설정","Options"))
            .setItems(items,(d,i)->{
                switch(i){
                    case 0:shareOriginals();break;
                    case 1:pickFolder();break;
                    case 2:copyManifest();break;
                    case 3:selectedOnly=!selectedOnly;rebuildVisible();updateCounters();break;
                    case 4:selectedFirst=!selectedFirst;rebuildVisible();updateCounters();break;
                    case 5:confirmClearSequence();break;
                    case 6:confirmClearLibrary();break;
                }
            }).setNegativeButton(t("닫기","Close"),null).show();
    }
    private void copyManifest() {
        if(!hasSelection())return;
        StringBuilder text=new StringBuilder(t("이미지 순서 (순서 고정)","Image order (authoritative)")+"\n");
        List<String> ids=store.sequence.snapshot();
        for(int n=0;n<ids.size();n++) {
            GalleryStore.Item item=store.find(ids.get(n));
            if(item!=null)text.append(String.format(Locale.ROOT,"%04d / %04d  %s\n",n+1,ids.size(),item.name));
        }
        ((android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE))
            .setPrimaryClip(ClipData.newPlainText("Image Order Studio",text.toString()));
        toastDialog(t("선택한 이미지 순서를 복사했습니다.","Image sequence copied to clipboard."));
    }
    /** Shares the original bitstreams with their original names and MIME types. */
    private void shareOriginals() {
        if(!hasSelection()||working)return;
        List<String> ids=store.sequence.snapshot();
        try {
            ArrayList<Uri> uris=originalUris(ids);
            ArrayList<String> mimes=originalMimes(ids);
            Intent intent=MediaIntentResult.forShare(uris,mimes);
            startActivity(Intent.createChooser(intent,t("원본 이미지 전송","Send original images")));
        }catch(Exception ex){toastDialog(t("원본 공유 실패: ","Cannot share originals: ")+ex.toString());}
    }
    private boolean hasSelection() {
        if(store.sequence.size()>0)return true;
        toastDialog(t("이미지를 순서대로 선택하세요.","Select images in order first."));return false;
    }
    private interface Job { void execute() throws Exception; }
    private void run(String title,Job job) {
        if(working)return;working=true;
        ProgressDialog dialog=new ProgressDialog(this);dialog.setMessage(title);dialog.setCancelable(false);dialog.show();
        worker.execute(()->{
            String error=null;try{job.execute();}catch(Exception e){error=e.getMessage();if(error==null)error=e.toString();}
            final String failure=error;
            ui.post(()->{
                working=false;if(dialog.isShowing())dialog.dismiss();
                if(failure!=null)toastDialog(t("작업 실패: ","Operation failed: ")+failure);
            });
        });
    }
    private void toastDialog(String message) {
        if(!isFinishing())new AlertDialog.Builder(this).setMessage(message).setPositiveButton("OK",null).show();
    }
    @Override protected void onDestroy(){super.onDestroy();worker.shutdown();thumbWorker.shutdown();}
}
