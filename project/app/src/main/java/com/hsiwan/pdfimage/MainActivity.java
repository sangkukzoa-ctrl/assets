package com.hsiwan.pdfimage;

import android.app.Activity;
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader;
import android.app.AlertDialog;
import android.os.Build;
import android.view.WindowInsets;
import android.content.ClipData;
import android.content.Intent;
import android.content.res.Configuration;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** Native Android activity; no internet permission, account, ads, or paid libraries. */
public final class MainActivity extends Activity {
    private static final int REQUEST_PDFS = 101;
    private static final int REQUEST_FOLDER = 102;
    private static final int ACCENT = Color.rgb(10, 128, 124);
    private static final int BACKGROUND = Color.rgb(244, 247, 251);
    private static final int DARK = Color.rgb(30, 43, 53);
    private static final int MUTED = Color.rgb(92, 106, 118);

    private final List<PdfConversionEngine.InputPdf> selected = new ArrayList<>();
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private AtomicBoolean cancelFlag = new AtomicBoolean();
    private Uri outputTree;
    private boolean converting = false;

    private TextView selectedText;
    private TextView folderText;
    private TextView qualityText;
    private TextView progressText;
    private TextView resultText;
    private Button selectButton;
    private Button clearButton;
    private Button folderButton;
    private Button convertButton;
    private Button cancelButton;
    private RadioGroup formatGroup;
    private RadioButton jpgButton;
    private RadioButton rawJpegButton;
    private View dpiLabel;
    private LinearLayout jpgOptions;
    private SeekBar qualitySlider;
    private Spinner dpiSpinner;
    private EditText pagesEdit;
    private ProgressBar progressBar;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        PDFBoxResourceLoader.init(getApplicationContext());
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        getWindow().setStatusBarColor(BACKGROUND);
        getWindow().setNavigationBarColor(BACKGROUND);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        buildUi();
        if (state != null) restoreState(state);
        refreshSelected();
        refreshFolder();
        refreshEnabled();
    }

    @Override public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BACKGROUND);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(20), dp(24), dp(20), dp(32));
        scroll.addView(body, new ScrollView.LayoutParams(-1, -2));
        setContentView(scroll);
        // On API 35+ the content extends beneath system bars; preserve safe insets.
        if (Build.VERSION.SDK_INT >= 35) {
            scroll.setOnApplyWindowInsetsListener((v, insets) -> {
                android.graphics.Insets safe = insets.getInsets(
                        WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                v.setPadding(safe.left, safe.top, safe.right, safe.bottom);
                return insets;
            });
            scroll.requestApplyInsets();
        }

        TextView emblem = label("▣  LOCAL PDF TOOL", 12, ACCENT, true);
        emblem.setText("2bornot");
        body.addView(emblem);
        TextView title = label(L10n.t("PDF → 이미지","PDF → Image"), 31, DARK, true);
        title.setText("Just PDF to Image");
        LinearLayout.LayoutParams titleLp = space(-1, -2, 8, 0);
        body.addView(title, titleLp);
        TextView subtitle = label(L10n.t("PDF를 PNG · JPG로 변환하세요.\n광고 없이, 인터넷 없이, 휴대폰 안에서만.","Convert PDF to PNG or JPG.\\nNo ads. No internet. On-device only."), 14, MUTED, false);
        subtitle.setLineSpacing(dp(3), 1f);
        body.addView(subtitle, space(-1, -2, 3, 20));

        LinearLayout filesCard = card();
        body.addView(filesCard, space(-1, -2, 0, 14));
        filesCard.addView(label(L10n.t("01   PDF 문서","01   PDF documents"), 17, DARK, true));
        filesCard.addView(label(L10n.t("여러 PDF를 한 번에 선택할 수 있습니다.","Select multiple PDFs at once."), 13, MUTED, false),
                space(-1, -2, 0, 10));
        LinearLayout fileButtons = row();
        selectButton = action(L10n.t("PDF 추가","Add PDFs"), true);
        clearButton = action(L10n.t("목록 비우기","Clear list"), false);
        fileButtons.addView(selectButton, new LinearLayout.LayoutParams(0, dp(47), 1.0f));
        fileButtons.addView(clearButton, space(dp(112), dp(47), 8, 0));
        filesCard.addView(fileButtons);
        selectedText = label(L10n.t("선택한 PDF 없음","No PDFs selected"), 13, MUTED, false);
        selectedText.setLineSpacing(dp(3), 1.0f);
        filesCard.addView(selectedText, space(-1, -2, 0, 12));
        selectButton.setOnClickListener(v -> pickPdfs());
        clearButton.setOnClickListener(v -> { selected.clear(); refreshSelected(); refreshEnabled(); });

        LinearLayout saveCard = card();
        body.addView(saveCard, space(-1, -2, 0, 14));
        saveCard.addView(label(L10n.t("02   저장 폴더","02   Output folder"), 17, DARK, true));
        saveCard.addView(label(L10n.t("변환된 이미지를 저장할 위치를 지정하세요.","Choose where to save converted images."), 13, MUTED, false),
                space(-1, -2, 0, 12));
        folderButton = action(L10n.t("저장 폴더 선택","Choose output folder"), false);
        saveCard.addView(folderButton, new LinearLayout.LayoutParams(-1, dp(47)));
        folderText = label(L10n.t("저장 폴더가 지정되지 않았습니다.","No output folder selected."), 13, MUTED, false);
        saveCard.addView(folderText, space(-1, -2, 0, 11));
        folderButton.setOnClickListener(v -> pickFolder());

        LinearLayout optionsCard = card();
        body.addView(optionsCard, space(-1, -2, 0, 14));
        optionsCard.addView(label(L10n.t("03   출력 설정","03   Output settings"), 17, DARK, true));
        optionsCard.addView(label(L10n.t("이미지 형식","Image format"), 14, DARK, true), space(-1, -2, 0, 13));
        formatGroup = new RadioGroup(this);
        formatGroup.setOrientation(RadioGroup.VERTICAL);
        RadioButton pngButton = new RadioButton(this);
        pngButton.setId(View.generateViewId());
        pngButton.setText(L10n.t("PNG · 무손실","PNG · Lossless"));
        pngButton.setTextSize(14);
        jpgButton = new RadioButton(this);
        jpgButton.setId(View.generateViewId());
        jpgButton.setText(L10n.t("JPG · 용량 절약","JPG · Smaller files"));
        jpgButton.setTextSize(14);
        rawJpegButton = new RadioButton(this);
        rawJpegButton.setId(View.generateViewId());
        rawJpegButton.setText(L10n.t("원본 JPEG 추출 · 재압축 없음","Extract embedded JPEG · No re-encoding"));
        rawJpegButton.setTextSize(14);
        formatGroup.addView(pngButton, new RadioGroup.LayoutParams(-1, -2));
        formatGroup.addView(jpgButton, new RadioGroup.LayoutParams(-1, -2));
        formatGroup.addView(rawJpegButton, new RadioGroup.LayoutParams(-1, -2));
        pngButton.setChecked(true);
        optionsCard.addView(formatGroup);

        jpgOptions = new LinearLayout(this);
        jpgOptions.setOrientation(LinearLayout.VERTICAL);
        qualityText = label(L10n.t("JPG 품질: 95%","JPG quality: 95%"), 13, MUTED, false);
        jpgOptions.addView(qualityText);
        qualitySlider = new SeekBar(this);
        qualitySlider.setMax(30);  // 70-100
        qualitySlider.setProgress(25);
        jpgOptions.addView(qualitySlider);
        jpgOptions.setVisibility(View.GONE);
        optionsCard.addView(jpgOptions, space(-1, -2, 0, 7));
        qualitySlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                qualityText.setText(L10n.t("JPG 품질: ","JPG quality: ") + (70 + progress) + "%");
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) { }
            @Override public void onStopTrackingTouch(SeekBar seekBar) { }
        });
        formatGroup.setOnCheckedChangeListener((group, id) -> {
            jpgOptions.setVisibility(id == jpgButton.getId() ? View.VISIBLE : View.GONE);
            boolean renderMode = id != rawJpegButton.getId();
            dpiLabel.setVisibility(renderMode ? View.VISIBLE : View.GONE);
            dpiSpinner.setVisibility(renderMode ? View.VISIBLE : View.GONE);
        });
        optionsCard.addView(label(L10n.t("원본 추출은 PDF에 내장된 JPEG만 대상으로 합니다. 글자·주석·도형을 이미지화하려면 PNG/JPG 변환을 선택하세요.","Extraction saves only JPEGs embedded in the PDF. For text, annotations and vector graphics, choose PNG/JPG rendering."),
                12, MUTED, false), space(-1, -2, 0, 10));
        dpiLabel = label(L10n.t("해상도","Resolution"), 14, DARK, true);
        optionsCard.addView(dpiLabel, space(-1, -2, 0, 16));
        dpiSpinner = new Spinner(this);
        String[] dpiItems = {L10n.t("150 DPI · 빠른 변환","150 DPI · Fast"), L10n.t("200 DPI · 기본 추천","200 DPI · Recommended"), L10n.t("300 DPI · 고화질","300 DPI · High quality")};
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_dropdown_item, dpiItems);
        dpiSpinner.setAdapter(adapter);
        dpiSpinner.setSelection(1);
        optionsCard.addView(dpiSpinner, new LinearLayout.LayoutParams(-1, dp(48)));
        optionsCard.addView(label(L10n.t("페이지 범위 (선택 사항)","Page range (optional)"), 14, DARK, true), space(-1, -2, 0, 13));
        pagesEdit = new EditText(this);
        pagesEdit.setSingleLine(true);
        pagesEdit.setTextSize(15);
        pagesEdit.setHint(L10n.t("비우면 전체 · 예: 1,3-5","Blank = all pages · e.g. 1,3-5"));
        pagesEdit.setPadding(dp(12), dp(5), dp(12), dp(5));
        pagesEdit.setBackground(round(Color.rgb(247, 249, 251), 10, Color.rgb(214, 223, 229)));
        optionsCard.addView(pagesEdit, new LinearLayout.LayoutParams(-1, dp(48)));
        optionsCard.addView(label(L10n.t("이미지가 여러 장이면 PDF별 하위 폴더에 저장합니다. 원본 추출은 DPI/JPG 품질과 무관합니다.","Multi-image results go into a folder per PDF. Original extraction ignores DPI and JPG quality."),
                12, MUTED, false), space(-1, -2, 0, 12));

        LinearLayout runCard = card();
        body.addView(runCard, space(-1, -2, 0, 14));
        runCard.addView(label(L10n.t("04   변환 실행","04   Convert"), 17, DARK, true));
        convertButton = action(L10n.t("이미지로 변환하기","Convert to images"), true);
        runCard.addView(convertButton, space(-1, dp(52), 0, 14));
        cancelButton = action(L10n.t("진행 중 취소","Cancel conversion"), false);
        cancelButton.setVisibility(View.GONE);
        runCard.addView(cancelButton, space(-1, dp(44), 0, 8));
        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(1000);
        progressBar.setProgress(0);
        runCard.addView(progressBar, space(-1, dp(8), 0, 14));
        progressText = label(L10n.t("대기 중","Ready"), 13, MUTED, false);
        runCard.addView(progressText, space(-1, -2, 0, 9));
        resultText = label("", 13, DARK, false);
        resultText.setLineSpacing(dp(3), 1.0f);
        runCard.addView(resultText);
        convertButton.setOnClickListener(v -> startConversion());
        cancelButton.setOnClickListener(v -> {
            cancelFlag.set(true);
            progressText.setText(L10n.t("취소 요청 중 · 현재 작업을 정리하고 있습니다…","Cancelling · Finishing the current operation…"));
            cancelButton.setEnabled(false);
        });

        TextView footer = label(L10n.t("100% 오프라인 · 저장소 전체 접근 권한 불필요 · 광고/추적 없음\n버전 1.3.1","100% offline · No broad storage access · No ads or tracking\nVersion 1.3.1"), 12, MUTED, false);
        footer.setGravity(Gravity.CENTER);
        footer.setLineSpacing(dp(4), 1f);
        body.addView(footer, space(-1, -2, 0, 8));
        TextView policy = label(L10n.t("개인정보 안내","Privacy notice"), 12, ACCENT, false);
        policy.setGravity(Gravity.CENTER);
        policy.setPadding(0, dp(12), 0, dp(12));
        policy.setOnClickListener(v -> new AlertDialog.Builder(this)
                .setTitle(L10n.t("개인정보 안내","Privacy notice"))
                .setMessage(L10n.t("이 앱은 광고, 분석 도구, 인터넷 연결을 사용하지 않습니다. ","This app uses no ads, analytics or internet connection. ")
                        + L10n.t("PDF 원본과 변환된 이미지는 사용자가 선택한 파일과 폴더에서 ","Your PDFs and images are processed only on the device in files and folders you choose. ")
                        + L10n.t("기기 내부에서만 처리되며 개발자 서버로 전송하지 않습니다. ","Files are never uploaded to developer servers. ")
                        + L10n.t("사용자 개인정보나 파일 내용을 수집하거나 공유하지 않습니다. ","We do not collect or share personal data or file contents. ")
                        + L10n.t("앱 사용에 필요한 파일 접근은 Android 문서 선택기를 통해 ","File access is limited to files and folders selected through the Android file picker. ")
                        + L10n.t("사용자가 선택한 항목에 한정됩니다.",""))
                .setPositiveButton(L10n.t("확인","OK"), null)
                .show());
        body.addView(policy);
    }

    private void pickPdfs() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/pdf");
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_PDFS);
    }

    private void pickFolder() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_FOLDER);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null) return;
        if (requestCode == REQUEST_PDFS) {
            Set<String> prior = new HashSet<>();
            for (PdfConversionEngine.InputPdf p : selected) prior.add(p.uri.toString());
            ClipData items = data.getClipData();
            int added = 0;
            if (items != null) {
                for (int i = 0; i < items.getItemCount(); i++) {
                    if (addPdf(items.getItemAt(i).getUri(), prior)) added++;
                }
            } else if (data.getData() != null) {
                if (addPdf(data.getData(), prior)) added++;
            }
            if (added == 0) toast(L10n.t("새로 추가한 PDF가 없습니다.","No new PDFs were added."));
            refreshSelected();
        } else if (requestCode == REQUEST_FOLDER && data.getData() != null) {
            Uri uri = data.getData();
            try {
                getContentResolver().takePersistableUriPermission(uri,
                        Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                outputTree = uri;
                refreshFolder();
            } catch (SecurityException ex) {
                outputTree = null;
                toast(L10n.t("폴더 쓰기 권한을 부여하지 못했습니다. 다시 선택하세요.","Could not grant folder write access. Please choose again."));
                refreshFolder();
            }
        }
        refreshEnabled();
    }

    private boolean addPdf(Uri uri, Set<String> existing) {
        if (uri == null || !existing.add(uri.toString())) return false;
        try {
            getContentResolver().takePersistableUriPermission(uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (SecurityException ignored) {
            // URI is still readable for the current session on many providers.
        }
        selected.add(new PdfConversionEngine.InputPdf(uri, displayName(uri)));
        return true;
    }

    private String displayName(Uri uri) {
        try (Cursor cursor = getContentResolver().query(uri,
                new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                String name = cursor.getString(0);
                if (name != null && !name.trim().isEmpty()) return name;
            }
        } catch (Exception ignored) { }
        String fallback = uri.getLastPathSegment();
        return fallback == null ? L10n.t("문서.pdf","document.pdf") : fallback;
    }

    private void refreshSelected() {
        if (selected.isEmpty()) { selectedText.setText(L10n.t("선택한 PDF가 없습니다.","No PDFs selected.")); return; }
        StringBuilder sb = new StringBuilder();
        sb.append(L10n.t("선택한 PDF ","Selected PDFs: ")).append(selected.size()).append(L10n.t("개",""));
        for (int i = 0; i < Math.min(12, selected.size()); i++) {
            sb.append("\n").append(i + 1).append(". ").append(selected.get(i).name);
        }
        if (selected.size() > 12) sb.append(L10n.t("\n… 외 ","\n… plus ")).append(selected.size() - 12).append(L10n.t("개",""));
        selectedText.setText(sb.toString());
    }

    private void refreshFolder() {
        if (outputTree == null) {
            folderText.setText(L10n.t("저장 폴더가 지정되지 않았습니다.","No output folder selected.")); return;
        }
        String name = null;
        try {
            Uri documentUri = DocumentsContract.buildDocumentUriUsingTree(outputTree,
                    DocumentsContract.getTreeDocumentId(outputTree));
            try (Cursor cursor = getContentResolver().query(documentUri,
                    new String[]{DocumentsContract.Document.COLUMN_DISPLAY_NAME}, null, null, null)) {
                if (cursor != null && cursor.moveToFirst()) name = cursor.getString(0);
            }
        } catch (Exception ignored) { }
        folderText.setText(L10n.t("저장 위치: ","Save to: ") + (name != null ? name : outputTree.toString()));
    }

    private void startConversion() {
        if (converting || outputTree == null || selected.isEmpty()) return;
        int[] dpis = {150, 200, 300};
        PdfConversionEngine.Options options = new PdfConversionEngine.Options(
                formatGroup.getCheckedRadioButtonId() != jpgButton.getId(),
                dpis[Math.max(0, Math.min(2, dpiSpinner.getSelectedItemPosition()))],
                70 + qualitySlider.getProgress(), pagesEdit.getText().toString().trim(),
                rawJpegButton.isChecked());
        List<PdfConversionEngine.InputPdf> batch = new ArrayList<>(selected);
        Uri folder = outputTree;
        converting = true;
        cancelFlag = new AtomicBoolean(false);
        AtomicBoolean runCancel = cancelFlag;
        progressBar.setProgress(0);
        resultText.setText("");
        progressText.setText(L10n.t("변환 시작…","Starting conversion…"));
        refreshEnabled();
        executor.execute(() -> {
            PdfConversionEngine.Result result = options.originalJpeg
                    ? OriginalJpegExtractor.extract(getContentResolver(), getCacheDir(), batch,
                            folder, options, runCancel, (value, message) -> runOnUiThread(() -> {
                                if (!isFinishing()) { progressBar.setProgress(value); progressText.setText(message); }
                            }))
                    : PdfConversionEngine.convert(getContentResolver(),
                    getCacheDir(), batch, folder, options, runCancel,
                    (value, message) -> runOnUiThread(() -> {
                        if (!isFinishing()) {
                            progressBar.setProgress(value);
                            progressText.setText(message);
                        }
                    }));
            runOnUiThread(() -> {
                if (isFinishing()) return;
                converting = false;
                resultText.setText(result.describe());
                if (!result.cancelled) progressBar.setProgress(1000);
                progressText.setText(result.cancelled ? L10n.t("사용자가 취소했습니다.","Cancelled by user.") : L10n.t("작업 완료","Finished"));
                cancelButton.setEnabled(true);
                refreshEnabled();
                if (result.totalFailed == 0 && result.totalSaved > 0) {
                    toast(L10n.t("이미지 ","Saved ") + result.totalSaved + L10n.t("장 저장 완료"," images"));
                }
            });
        });
    }

    private void refreshEnabled() {
        if (selectButton == null) return;
        selectButton.setEnabled(!converting);
        clearButton.setEnabled(!converting && !selected.isEmpty());
        folderButton.setEnabled(!converting);
        formatGroup.setEnabled(!converting);
        for (int i = 0; i < formatGroup.getChildCount(); i++) {
            formatGroup.getChildAt(i).setEnabled(!converting);
        }
        dpiSpinner.setEnabled(!converting);
        pagesEdit.setEnabled(!converting);
        qualitySlider.setEnabled(!converting);
        boolean ready = !converting && !selected.isEmpty() && outputTree != null;
        convertButton.setEnabled(ready);
        convertButton.setAlpha(ready ? 1f : 0.45f);
        cancelButton.setVisibility(converting ? View.VISIBLE : View.GONE);
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        ArrayList<String> uris = new ArrayList<>();
        ArrayList<String> names = new ArrayList<>();
        for (PdfConversionEngine.InputPdf p : selected) {
            uris.add(p.uri.toString());
            names.add(p.name);
        }
        state.putStringArrayList("pdfUris", uris);
        state.putStringArrayList("pdfNames", names);
        state.putString("folder", outputTree == null ? null : outputTree.toString());
        state.putBoolean("jpg", formatGroup.getCheckedRadioButtonId() == jpgButton.getId());
        state.putBoolean("rawJpeg", rawJpegButton.isChecked());
        state.putInt("quality", qualitySlider.getProgress());
        state.putInt("dpi", dpiSpinner.getSelectedItemPosition());
        state.putString("pages", pagesEdit.getText().toString());
    }

    private void restoreState(Bundle state) {
        ArrayList<String> uris = state.getStringArrayList("pdfUris");
        ArrayList<String> names = state.getStringArrayList("pdfNames");
        if (uris != null && names != null) {
            for (int i = 0; i < Math.min(uris.size(), names.size()); i++) {
                selected.add(new PdfConversionEngine.InputPdf(Uri.parse(uris.get(i)), names.get(i)));
            }
        }
        String folder = state.getString("folder");
        if (folder != null) outputTree = Uri.parse(folder);
        if (state.getBoolean("jpg", false)) jpgButton.setChecked(true);
        if (state.getBoolean("rawJpeg", false)) rawJpegButton.setChecked(true);
        qualitySlider.setProgress(state.getInt("quality", 25));
        dpiSpinner.setSelection(Math.max(0, Math.min(2, state.getInt("dpi", 1))));
        pagesEdit.setText(state.getString("pages", ""));
    }

    @Override protected void onDestroy() {
        cancelFlag.set(true);
        executor.shutdownNow();
        super.onDestroy();
    }

    private LinearLayout card() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(18), dp(18), dp(18), dp(18));
        layout.setBackground(round(Color.WHITE, 18, Color.rgb(226, 233, 238)));
        layout.setElevation(dp(2));
        return layout;
    }
    private LinearLayout row() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.HORIZONTAL);
        l.setGravity(Gravity.CENTER_VERTICAL);
        return l;
    }
    private TextView label(String value, int sp, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }
    private Button action(String value, boolean primary) {
        Button button = new Button(this);
        button.setText(value);
        button.setAllCaps(false);
        button.setTextSize(14);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setTextColor(primary ? Color.WHITE : ACCENT);
        button.setPadding(dp(8), 0, dp(8), 0);
        button.setBackground(round(primary ? ACCENT : Color.rgb(236, 248, 247),
                11, primary ? ACCENT : Color.rgb(195, 226, 224)));
        return button;
    }
    private GradientDrawable round(int fill, float radius, int stroke) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(fill);
        d.setCornerRadius(dp(radius));
        d.setStroke(dp(1), stroke);
        return d;
    }
    private LinearLayout.LayoutParams space(int w, int h, int left, int top) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.leftMargin = dp(left); p.topMargin = dp(top);
        return p;
    }
    private int dp(float dip) { return Math.round(dip * getResources().getDisplayMetrics().density); }
    private void toast(String message) { Toast.makeText(this, message, Toast.LENGTH_SHORT).show(); }
}
