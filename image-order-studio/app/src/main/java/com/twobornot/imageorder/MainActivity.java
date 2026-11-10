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
 * Rendered numbered images are the cross-site fallback when receivers re-sort attachments.
 */
public class MainActivity extends Activity {
    private static final int IMPORT_IMAGES=100, CHOOSE_FOLDER=200, WRITE_OLD_GALLERY=300;
    private static final String SAMSUNG_GALLERY="com.sec.android.gallery3d";
    private static final String PHOTO_PREF="preferred_photo_source";
    private static final int NAVY=0xff182C46, BLUE=0xff2563EB, MUTED=0xff60748C;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final ExecutorService thumbWorker=Executors.newFixedThreadPool(2);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private GalleryStore store;
    private ImageExporter exporter;
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
    private boolean pendingGalleryCombine=false;
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
        store=new GalleryStore(this,externalMode);exporter=new ImageExporter(this);
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
        return (Intent.ACTION_GET_CONTENT.equals(a)||Intent.ACTION_PICK.equals(a))
            && type!=null && type.startsWith("image/");
    }
    private void setup() {
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xfff3f6fa);setContentView(root);
        LinearLayout header=new LinearLayout(this);header.setPadding(dp(18),dp(18),dp(18),dp(13));
        header.setOrientation(LinearLayout.VERTICAL);header.setBackgroundColor(NAVY);root.addView(header);
        TextView title=text(externalMode?t("사진 첨부 · 순서 지정","Attach images · set order"):"Image Order Studio",23,0xffffffff,true);header.addView(title);
        subtitle=text(externalMode?t("갤러리 선택 → 순서 확인 → 사이트에 첨부", "Pick photos → confirm order → return to website"):
            t("선택한 순서가 곧 정답입니다", "Your selection order is authoritative"),12,0xffcbd8ee,false);
        header.addView(subtitle);
        LinearLayout toolbar=row(); toolbar.setPadding(dp(8),dp(10),dp(8),dp(5));root.addView(toolbar);
        addButton(toolbar,t("＋ 삼성/기본 갤러리","＋ Gallery / albums"),()->openPicker(),BLUE);
        addButton(toolbar,t("사진 선택 설정","Photo source"),()->choosePhotoSource(),NAVY);
        LinearLayout toolbarOrder=row();toolbarOrder.setPadding(dp(8),0,dp(8),dp(5));root.addView(toolbarOrder);
        addButton(toolbarOrder,t("순서 편집","Edit order"),()->editSequence(),NAVY);
        if(!externalMode)addButton(toolbarOrder,t("다른 기능 · 설정","More tools / settings"),()->showOtherTools(),0xff6f8095);
        status=text("",13,NAVY,true);status.setPadding(dp(14),dp(8),dp(14),dp(5));root.addView(status);
        TextView instructions=text(externalMode?
            t("사진의 파란 숫자가 업로드 순서입니다. 원하는 순서대로 누르고 '사이트에 첨부'를 누르세요.",
              "Blue numbers indicate upload order. Tap photos in order, then press Return to website."):
            t("갤러리에서 사진을 선택한 뒤 순서를 확인하세요. 파란 숫자가 실제 첨부 순서입니다.",
              "Choose photos from the gallery; confirm the numbered sequence before exporting."),12,MUTED,false);
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
            addButton(primary,t("✓ 사이트에 첨부","✓ Return images to website"),()->returnToCaller(),BLUE);
            LinearLayout secondary=row();secondary.setPadding(dp(8),0,dp(8),dp(10));root.addView(secondary);
            addButton(secondary,t("처음부터 선택","Restart order"),()->confirmClearSequence(),NAVY);
            addButton(secondary,t("취소하고 돌아가기","Cancel and return"),()->cancelExternal(),0xff6f8095);
        } else {
            TextView actions=text(t("모든 사이트에서 사용하기 · 갤러리에 저장","USE FROM ANY WEBSITE · SAVE TO GALLERY"),11,MUTED,true);
            actions.setPadding(dp(13),dp(9),0,dp(4));root.addView(actions);
            LinearLayout albumActions=row();albumActions.setPadding(dp(8),0,dp(8),dp(5));root.addView(albumActions);
            addButton(albumActions,t("① 갤러리 앨범에 저장","① Save to Gallery album"),()->publishGallery(false),BLUE);
            addButton(albumActions,t("② 한 장으로 갤러리 저장","② Single image to Gallery"),()->publishGallery(true),NAVY);
            LinearLayout bottomActions=row();bottomActions.setPadding(dp(8),0,dp(8),dp(5));root.addView(bottomActions);
            addButton(bottomActions,t("공유하기","Share images"),()->shareNumbered(true),NAVY);
            addButton(bottomActions,t("다른 기능 · 설정","More options"),()->showOtherTools(),0xff6f8095);
            TextView hint=text(t("어느 사이트에서든: 이 앱에서 순서 지정 → 갤러리 앨범에 저장 → 원래 앱의 기본 첨부창에서 'Image Order Studio' 앨범 선택",
                "For any website: set order here → Save to Gallery → select from the Image Order Studio album in that site's normal picker"),11,MUTED,false);
            hint.setPadding(dp(13),0,dp(13),dp(8));root.addView(hint);
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
                bmp=ImageExporter.decode(store.source(item),256,160000);
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
    /** Prefers the actual Samsung Gallery component (Galaxy devices), not Android's Photo Picker album sheet. */
    private void openPicker() {
        if(working)return;
        String source=getPreferences(MODE_PRIVATE).getString(PHOTO_PREF,"samsung");
        if("samsung".equals(source)&&trySamsungPicker())return;
        if("system".equals(source)&&trySystemPhotoPicker())return;
        if("generic".equals(source)&&tryOtherGalleryPicker())return;
        if(!"system".equals(source)&&tryOtherGalleryPicker())return;
        if(trySystemPhotoPicker())return;
        toastDialog(t("사용 가능한 사진 선택기를 찾지 못했습니다.","No compatible gallery picker found."));
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
            if(request==IMPORT_IMAGES)nativePickerOrdered=false;
            return;
        }
        if(request==IMPORT_IMAGES) {
            ArrayList<Uri> uris=new ArrayList<>();
            if(data.getClipData()!=null) {
                for(int j=0;j<data.getClipData().getItemCount();j++) uris.add(data.getClipData().getItemAt(j).getUri());
            } else if(data.getData()!=null) uris.add(data.getData());
            boolean trustOrder=PickerDecision.trustNativeOrder(nativePickerOrdered,uris.size());
            nativePickerOrdered=false;
            importAll(uris,trustOrder);
        } else if(request==CHOOSE_FOLDER) {
            Uri tree=data.getData();if(tree!=null) saveToFolder(tree);
        }
    }
    private void importAll(List<Uri> uris,boolean sourceHasVerifiedOrder) {
        if(uris.isEmpty()||working)return;
        run(t("이미지 가져오는 중…","Importing images…"),()->{
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
    /** Return real content:// file grants directly to the image-upload requester. */
    private void returnToCaller() {
        if(!externalMode||!hasSelection()||working)return;
        List<String> ids=store.sequence.snapshot();
        if(PickerDecision.needsCombine(ids.size(),externalAllowsMultiple)) {
            new AlertDialog.Builder(this)
                .setTitle(t("사이트에서는 한 장만 받을 수 있습니다.","This website requests one image."))
                .setMessage(t("선택한 이미지를 순서대로 한 장으로 합쳐서 첨부할까요? (최대 12장)",
                    "Combine selected photos in order into one upload? (up to 12)"))
                .setPositiveButton(t("한 장으로 결합","Combine"),(d,w)->deliverToCaller(ids,true))
                .setNegativeButton(t("선택 수정","Change selection"),null).show();
            return;
        }
        deliverToCaller(ids,false);
    }
    private void deliverToCaller(List<String> ids,boolean combine) {
        boolean png="image/png".equals(requestedMime);
        run(t("사이트에 첨부할 파일 준비 중…","Preparing upload for website…"),()->{
            List<File> files;
            if(combine)files=Collections.singletonList(exporter.renderCombined(store,ids,!png));
            else files=exporter.renderNumbered(store,ids,!png);
            if(!externalAllowsMultiple && files.size()!=1)throw new IOException("Single-image caller cannot receive multiple images");
            ArrayList<Uri> uris=new ArrayList<>();
            for(File f:files)uris.add(FileProvider.getUriForFile(this,getPackageName()+".provider",f));
            Intent result=new Intent();
            result.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            ClipData clip=ClipData.newRawUri("Image Order Studio",uris.get(0));
            for(int j=1;j<uris.size();j++)clip.addItem(new ClipData.Item(uris.get(j)));
            result.setClipData(clip);
            if(uris.size()==1)result.setDataAndType(uris.get(0),png?"image/png":"image/jpeg");
            else result.setType(png?"image/png":"image/jpeg");
            ui.post(()->{setResult(RESULT_OK,result);finish();});
        });
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
        List<String> ids=store.sequence.snapshot();
        run(t("번호 이미지 저장 중…","Saving numbered images…"),()->{
            List<File> files=exporter.renderNumbered(store,ids,true);
            exporter.saveToTree(tree,files);
            ui.post(()->toastDialog(t("순서가 기록된 ","Saved ")+files.size()+t("개 이미지를 저장했습니다."," numbered images.")));
        });
    }
    private void shareNumbered(boolean compact) {
        if(!hasSelection())return;
        List<String> ids=store.sequence.snapshot();
        run(t("순번 이미지 생성 중…","Rendering numbered images…"),()->{
            List<File> files=exporter.renderNumbered(store,ids,compact);
            ui.post(()->shareFiles(files,compact?"image/jpeg":"image/png"));
        });
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants) {
        super.onRequestPermissionsResult(request,permissions,grants);
        if(request==WRITE_OLD_GALLERY) {
            if(grants.length>0 && grants[0]==android.content.pm.PackageManager.PERMISSION_GRANTED)
                publishGallery(pendingGalleryCombine);
            else toastDialog(t("이 Android 버전에서는 갤러리 저장 권한이 필요합니다. 앱 내부 공유 기능은 계속 이용할 수 있습니다.",
                "This Android version requires Gallery write permission. You can still share images from inside the app."));
        }
    }
    private void publishGallery(boolean combined) {
        if(!hasSelection()||working)return;
        if(Build.VERSION.SDK_INT<29 && checkSelfPermission(android.Manifest.permission.WRITE_EXTERNAL_STORAGE)
                !=android.content.pm.PackageManager.PERMISSION_GRANTED) {
            pendingGalleryCombine=combined;
            requestPermissions(new String[]{android.Manifest.permission.WRITE_EXTERNAL_STORAGE},WRITE_OLD_GALLERY);
            return;
        }
        List<String> ids=store.sequence.snapshot();
        if(combined&&ids.size()>12){toastDialog(t("한 장 결합은 최대 12장입니다. '갤러리 앨범에 저장'을 이용하세요.",
            "Single-image combining supports 12 images. Use Save to Gallery album."));return;}
        run(t("갤러리 앨범에 순서대로 저장 중…","Publishing numbered images into Gallery…"),()->{
            List<File> results=combined?Collections.singletonList(exporter.renderCombined(store,ids,true)):
                exporter.renderNumbered(store,ids,true);
            // Keep independent copies in the SAF source for system Files pickers.
            OrderedOutbox.publish(this,results);
            List<Uri> added=GalleryMediaExporter.publish(this,results);
            ui.post(()->new AlertDialog.Builder(this)
                .setTitle(t("갤러리에서 바로 선택할 수 있습니다","Ready in your Gallery"))
                .setMessage(t("사진 "+added.size()+"장을 'Image Order Studio' 앨범에 저장했습니다.\n\n원래 사이트의 이미지 첨부 화면으로 돌아가 일반 갤러리에서 이 앨범을 선택하세요. 이미지에는 순서가 직접 표시되어 있습니다.",
                    "Saved "+added.size()+" images in the Image Order Studio album.\n\nReturn to the website and select this album from its regular image picker. Visible image labels preserve your order."))
                .setPositiveButton(t("확인","OK"),(d,w)->{})
                .show());
        });
    }
    private void showOtherTools() {
        String[] items={
            t("JPG 번호 이미지 공유","Share numbered JPG"),
            t("PNG 번호 이미지 공유","Share numbered PNG"),
            t("저장 폴더 선택","Save into selected folder"),
            t("이미지 순서 목록 복사","Copy selection sequence"),
            t("원본 이미지 공유","Share original bytes"),
            t("삼성 갤러리 앱 직접 열기 (공유로 가져오기)","Open Samsung Gallery (import via Share)"),
            t("선택한 이미지만 보기","Show selected only"),
            t("선택순 먼저 보기","Sort selected first"),
            t("선택 순서 초기화","Clear selection order"),
            t("보관함 비우기","Clear private library"),
            t("어디서든 빠른 실행 설정","Quick Settings shortcut instructions")
        };
        new AlertDialog.Builder(this).setTitle(t("다른 기능 · 설정","More tools and settings"))
            .setItems(items,(d,i)->{
                switch(i){
                    case 0:shareNumbered(true);break;
                    case 1:shareNumbered(false);break;
                    case 2:pickFolder();break;
                    case 3:copyManifest();break;
                    case 4:shareOriginals();break;
                    case 5:openFullSamsungGallery();break;
                    case 6:selectedOnly=!selectedOnly;rebuildVisible();updateCounters();break;
                    case 7:selectedFirst=!selectedFirst;rebuildVisible();updateCounters();break;
                    case 8:confirmClearSequence();break;
                    case 9:confirmClearLibrary();break;
                    case 10:toastDialog(t("상단 빠른 설정 패널을 두 번 내리고 편집(＋)에서 'Image Order Studio' 타일을 추가하세요. 어떤 앱에서도 빠르게 실행할 수 있습니다.",
                        "Expand Quick Settings, tap Edit (+), add the Image Order Studio tile. Open it from any app."));break;
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
    private void shareCombined() {
        if(!hasSelection())return;
        List<String> ids=store.sequence.snapshot();
        run(t("단일 이미지 생성 중…","Building a single image…"),()->{
            File f=exporter.renderCombined(store,ids);
            ui.post(()->shareFiles(Collections.singletonList(f),"image/png"));
        });
    }
    private void shareOriginals() {
        if(!hasSelection())return;
        ArrayList<File> files=new ArrayList<>();
        for(String id:store.sequence.snapshot()) {
            GalleryStore.Item item=store.find(id);if(item!=null)files.add(store.source(item));
        }
        shareFiles(files,"image/*");
    }
    private void shareFiles(List<File> files,String mime) {
        if(files.isEmpty())return;
        ArrayList<Uri> uris=new ArrayList<>();
        for(File f:files)uris.add(FileProvider.getUriForFile(this,getPackageName()+".provider",f));
        Intent i=new Intent(uris.size()==1?Intent.ACTION_SEND:Intent.ACTION_SEND_MULTIPLE);
        i.setType(mime);
        if(uris.size()==1)i.putExtra(Intent.EXTRA_STREAM,uris.get(0));
        else i.putParcelableArrayListExtra(Intent.EXTRA_STREAM,uris);
        android.content.ClipData cd=android.content.ClipData.newRawUri("ordered-image",uris.get(0));
        for(int j=1;j<uris.size();j++)cd.addItem(new android.content.ClipData.Item(uris.get(j)));
        i.setClipData(cd);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try{startActivity(Intent.createChooser(i,t("이미지 업로드 / 공유","Upload / share images")));}
        catch(Exception ex){toastDialog(ex.toString());}
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
