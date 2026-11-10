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
    private static final int IMPORT_IMAGES=100, CHOOSE_FOLDER=200;
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
        addButton(toolbar,t("＋ 갤러리에서 사진 선택","＋ Choose photos in gallery"),()->openPicker(),BLUE);
        addButton(toolbar,t("순서 편집","Edit order"),()->editSequence(),NAVY);
        if(!externalMode) {
            LinearLayout toolbar2=row();toolbar2.setPadding(dp(8),0,dp(8),dp(8));root.addView(toolbar2);
            addButton(toolbar2,t("선택한 것만","Selected only"),()->{
                selectedOnly=!selectedOnly;rebuildVisible();updateCounters();
            },NAVY);
            addButton(toolbar2,t("선택 먼저","Selected first"),()->{
                selectedFirst=!selectedFirst;rebuildVisible();updateCounters();
            },NAVY);
            LinearLayout toolbar3=row(); toolbar3.setPadding(dp(8),0,dp(8),dp(6));root.addView(toolbar3);
            addButton(toolbar3,t("선택 초기화","Clear selection"),()->confirmClearSequence(),0xff6f8095);
            addButton(toolbar3,t("보관함 비우기","Clear library"),()->confirmClearLibrary(),0xff6f8095);
        }
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
            TextView actions=text(t("외부 업로드용 내보내기","EXPORT FOR OTHER APPS / WEBSITES"),11,MUTED,true);
            actions.setPadding(dp(13),dp(9),0,dp(4));root.addView(actions);
            LinearLayout bottom1=row();bottom1.setPadding(dp(8),0,dp(8),dp(5));root.addView(bottom1);
            addButton(bottom1,t("JPG 최적화 공유","Share compact JPG"),()->shareNumbered(true),BLUE);
            addButton(bottom1,t("PNG 원본화질 공유","Share numbered PNG"),()->shareNumbered(false),NAVY);
            LinearLayout bottomSave=row();bottomSave.setPadding(dp(8),0,dp(8),dp(4));root.addView(bottomSave);
            addButton(bottomSave,t("폴더에 저장","Save to folder"),()->pickFolder(),NAVY);
            addButton(bottomSave,t("순서 목록 복사","Copy sequence"),()->copyManifest(),0xff6f8095);
            LinearLayout bottom2=row();bottom2.setPadding(dp(8),0,dp(8),dp(11));root.addView(bottom2);
            addButton(bottom2,t("한 장으로 결합","Combine to one"),()->shareCombined(),NAVY);
            addButton(bottom2,t("원본 공유","Share originals"),()->shareOriginals(),0xff6f8095);
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
    private void openPicker() {
        if(working)return;
        // Android 15 / R Extensions 12: the OS itself displays and preserves tap order.
        int extension=Build.VERSION.SDK_INT>=30?
            SdkExtensions.getExtensionVersion(Build.VERSION_CODES.R):0;
        boolean ordered=PickerDecision.supportsOrderedPicker(Build.VERSION.SDK_INT,extension);
        boolean supported=PickerDecision.supportsPhotoPicker(Build.VERSION.SDK_INT,extension);
        if(supported) {
            try {
                Intent photo=new Intent(MediaStore.ACTION_PICK_IMAGES);
                photo.setType("image/*");
                int limit=MediaStore.getPickImagesMaxLimit();
                if(limit>1)photo.putExtra(MediaStore.EXTRA_PICK_IMAGES_MAX,Math.min(limit,100));
                if(ordered)photo.putExtra(MediaStore.EXTRA_PICK_IMAGES_IN_ORDER,true);
                nativePickerOrdered=ordered;
                startActivityForResult(photo,IMPORT_IMAGES);
                return;
            } catch(Exception notAvailable) { nativePickerOrdered=false; }
        }
        // Older devices: the gallery app can be chosen in this multi-select chooser.
        // Exclude this app so we do not recursively open ourselves as an image provider.
        try {
            Intent photos=new Intent(Intent.ACTION_GET_CONTENT);
            photos.setType("image/*");photos.addCategory(Intent.CATEGORY_OPENABLE);
            photos.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
            Intent chooser=Intent.createChooser(photos,t("갤러리 / 사진 선택","Gallery / choose photos"));
            chooser.putExtra(Intent.EXTRA_EXCLUDE_COMPONENTS,new android.content.ComponentName[]{
                new android.content.ComponentName(this,MainActivity.class)
            });
            nativePickerOrdered=false;
            startActivityForResult(chooser,IMPORT_IMAGES);
        } catch(Exception e){toastDialog(t("사진 선택기를 열 수 없습니다: ","Cannot open photo picker: ")+e.getMessage());}
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
