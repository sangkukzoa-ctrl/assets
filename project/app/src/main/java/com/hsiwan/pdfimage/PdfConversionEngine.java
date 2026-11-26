package com.hsiwan.pdfimage;

import android.content.ContentResolver;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.pdf.PdfRenderer;
import android.net.Uri;
import android.os.ParcelFileDescriptor;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.Closeable;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CancellationException;
import java.util.concurrent.atomic.AtomicBoolean;

final class PdfConversionEngine {
    static final class InputPdf {
        final Uri uri;
        final String name;
        InputPdf(Uri uri, String name) { this.uri = uri; this.name = name; }
    }

    static final class Options {
        final boolean png;
        final int dpi;
        final int jpegQuality;
        final String pages;
        final boolean originalJpeg;
        Options(boolean png, int dpi, int jpegQuality, String pages, boolean originalJpeg) {
            this.png = png;
            this.dpi = dpi;
            this.jpegQuality = jpegQuality;
            this.pages = pages;
            this.originalJpeg = originalJpeg;
        }
    }

    static final class Result {
        int totalSaved;
        int totalFailed;
        int completedDocuments;
        boolean cancelled;
        final List<String> errors = new ArrayList<>();
        String describe() {
            String status = cancelled ? L10n.t("변환 취소됨","Conversion cancelled") : L10n.t("변환 종료","Conversion finished");
            String msg = status + L10n.t("\n성공 ","\nSaved ") + totalSaved + L10n.t("장 · 실패 "," images · Failed ") + totalFailed
                    + L10n.t("장 · 처리한 PDF "," images · Processed PDFs ") + completedDocuments + L10n.t("개","");
            if (!errors.isEmpty()) {
                msg += L10n.t("\n\n오류 내역:","\n\nErrors:");
                for (int i = 0; i < Math.min(8, errors.size()); i++) {
                    msg += "\n• " + errors.get(i);
                }
                if (errors.size() > 8) msg += L10n.t("\n… 외 ","\n… plus ") + (errors.size() - 8) + L10n.t("건"," more");
            }
            return msg;
        }
    }

    interface Progress { void update(int permille, String message); }

    static Result convert(ContentResolver resolver, File cacheDir,
                          List<InputPdf> inputs, Uri destination, Options options,
                          AtomicBoolean cancel, Progress progress) {
        Result result = new Result();
        DocumentStorage storage;
        try {
            storage = new DocumentStorage(resolver, destination);
        } catch (Exception e) {
            result.totalFailed++;
            result.errors.add(L10n.t("저장 폴더에 접근할 수 없습니다: ","Cannot access output folder: ") + readable(e));
            return result;
        }
        String extension = options.png ? ".png" : ".jpg";
        String mime = options.png ? "image/png" : "image/jpeg";
        Bitmap.CompressFormat format = options.png
                ? Bitmap.CompressFormat.PNG : Bitmap.CompressFormat.JPEG;

        for (int pdfIndex = 0; pdfIndex < inputs.size(); pdfIndex++) {
            if (cancel.get()) { result.cancelled = true; break; }
            InputPdf input = inputs.get(pdfIndex);
            String baseName = DocumentStorage.cleanBaseName(input.name);
            progress.update(1000 * pdfIndex / inputs.size(),
                    L10n.t("PDF 열기 ","Opening PDF ") + (pdfIndex + 1) + "/" + inputs.size() + " · " + input.name);
            try (OpenedPdf opened = openPdf(resolver, input.uri, cacheDir, cancel)) {
                PdfRenderer renderer = opened.renderer;
                List<Integer> pages = PageSelection.parse(options.pages, renderer.getPageCount());
                Uri folder = storage.root();
                Set<String> folderNames = storage.rootNames();
                // Avoid dumping many separate page images into the selected folder.
                if (pages.size() > 1) {
                    folder = storage.createPdfFolder(baseName + "_" + (options.png ? "PNG" : "JPG"));
                    folderNames = storage.newFolderNames();
                }
                final int pageCount = pages.size();
                int padding = Math.max(3, Integer.toString(renderer.getPageCount()).length());
                for (int pageIndex = 0; pageIndex < pages.size(); pageIndex++) {
                    if (cancel.get()) { result.cancelled = true; break; }
                    int pageNo = pages.get(pageIndex);
                    String outName = pageCount == 1 ? baseName + extension
                            : baseName + "_" + String.format(java.util.Locale.ROOT,
                                    "%0" + padding + "d", pageNo + 1) + extension;
                    Uri createdFile = null;
                    try (PdfRenderer.Page page = renderer.openPage(pageNo)) {
                        Bitmap bitmap = render(page, options.dpi);
                        try {
                            if (cancel.get()) { result.cancelled = true; break; }
                            createdFile = storage.createFile(folder, folderNames, outName, mime);
                            try (OutputStream stream = new BufferedOutputStream(
                                    requireOutputStream(resolver, createdFile), 65536)) {
                                if (!bitmap.compress(format,
                                        options.png ? 100 : options.jpegQuality, stream)) {
                                    throw new IOException(L10n.t("이미지 인코딩에 실패했습니다.","Image encoding failed."));
                                }
                                stream.flush();
                            }
                            result.totalSaved++;
                        } finally {
                            bitmap.recycle();
                        }
                    } catch (OutOfMemoryError oom) {
                        result.totalFailed++;
                        result.errors.add(input.name + " " + (pageNo + 1)
                                + L10n.t("쪽: 메모리 부족. 해상도를 낮춰 다시 시도하세요."," page: Out of memory. Try a lower DPI."));
                        storage.deleteIfPossible(createdFile);
                        // A subsequent page might work, but large A0 PDFs usually won't.
                        System.gc();
                    } catch (Exception e) {
                        result.totalFailed++;
                        result.errors.add(input.name + " " + (pageNo + 1)
                                + L10n.t("쪽: "," page: ") + readable(e));
                        storage.deleteIfPossible(createdFile);
                    }
                    int permille = (int) ((pdfIndex + (pageIndex + 1d) / pageCount)
                            * 1000 / inputs.size());
                    progress.update(permille, (pdfIndex + 1) + "/" + inputs.size()
                            + L10n.t(" 문서 · "," document · ") + (pageIndex + 1) + "/" + pageCount
                            + L10n.t(" 페이지 · 저장 "," pages · Saved ") + result.totalSaved + L10n.t("장"," images"));
                }
                result.completedDocuments++;
                if (result.cancelled) break;
            } catch (CancellationException cancelled) {
                result.cancelled = true;
                break;
            } catch (Exception e) {
                result.totalFailed++;
                result.errors.add(input.name + ": " + readable(e));
                progress.update(1000 * (pdfIndex + 1) / inputs.size(),
                        L10n.t("문서를 열거나 처리하지 못했습니다: ","Could not open or process document: ") + input.name);
            }
        }
        if (!result.cancelled && !cancel.get()) progress.update(1000, L10n.t("변환 작업 종료","Conversion completed"));
        if (cancel.get()) result.cancelled = true;
        return result;
    }

    private static OutputStream requireOutputStream(ContentResolver resolver, Uri file)
            throws IOException {
        OutputStream stream = resolver.openOutputStream(file, "w");
        if (stream == null) throw new IOException(L10n.t("파일을 쓸 수 없습니다.","Could not write output file."));
        return stream;
    }

    private static Bitmap render(PdfRenderer.Page page, int dpi) {
        double scale = dpi / 72.0;
        double origW = page.getWidth();
        double origH = page.getHeight();
        // Limit large page sizes to 18 megapixels (~72 MiB ARGB) to avoid OOM.
        double pixels = origW * origH * scale * scale;
        if (pixels > 18_000_000.0) scale *= Math.sqrt(18_000_000.0 / pixels);
        int width = (int) Math.max(1, Math.round(origW * scale));
        int height = (int) Math.max(1, Math.round(origH * scale));
        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        bitmap.eraseColor(Color.WHITE); // JPG has no alpha; white PDF background.
        Matrix matrix = new Matrix();
        matrix.setScale((float) (width / origW), (float) (height / origH));
        try {
            page.render(bitmap, null, matrix, PdfRenderer.Page.RENDER_MODE_FOR_PRINT);
            return bitmap;
        } catch (RuntimeException | Error ex) {
            bitmap.recycle();
            throw ex;
        }
    }

    private static String readable(Throwable e) {
        String message = e.getMessage();
        return message != null && !message.isEmpty()
                ? message : e.getClass().getSimpleName();
    }

    /** Some document providers deliver non-seekable descriptors; fall back to private cache. */
    private static OpenedPdf openPdf(ContentResolver resolver, Uri pdfUri,
                                     File cacheDir, AtomicBoolean cancel) throws IOException {
        ParcelFileDescriptor pfd = null;
        try {
            pfd = resolver.openFileDescriptor(pdfUri, "r");
            if (pfd == null) throw new IOException(L10n.t("PDF 읽기 핸들을 가져오지 못했습니다.","Could not get PDF file descriptor."));
            return new OpenedPdf(new PdfRenderer(pfd), pfd, null);
        } catch (Exception originalError) {
            if (pfd != null) try { pfd.close(); } catch (IOException ignored) { }
            if (cancel.get()) throw new CancellationException();
            File local = File.createTempFile("pdf_image_", ".pdf", cacheDir);
            try {
                try (InputStream is = resolver.openInputStream(pdfUri);
                     OutputStream os = new BufferedOutputStream(new FileOutputStream(local), 65536)) {
                    if (is == null) throw new IOException(L10n.t("PDF 원본 스트림을 열 수 없습니다.","Could not open source PDF stream."));
                    byte[] buffer = new byte[65536];
                    int n;
                    while ((n = is.read(buffer)) != -1) {
                        if (cancel.get()) throw new CancellationException();
                        os.write(buffer, 0, n);
                    }
                }
                ParcelFileDescriptor localPfd = ParcelFileDescriptor.open(local,
                        ParcelFileDescriptor.MODE_READ_ONLY);
                try {
                    return new OpenedPdf(new PdfRenderer(localPfd), localPfd, local);
                } catch (Exception ex) {
                    localPfd.close();
                    throw ex;
                }
            } catch (Exception e) {
                //noinspection ResultOfMethodCallIgnored
                local.delete();
                if (e instanceof CancellationException) throw (CancellationException) e;
                throw new IOException(L10n.t("PDF를 열 수 없습니다: ","Could not open PDF: ") + readable(e), e);
            }
        }
    }

    private static final class OpenedPdf implements Closeable {
        final PdfRenderer renderer;
        final ParcelFileDescriptor pfd;
        final File local;
        OpenedPdf(PdfRenderer renderer, ParcelFileDescriptor pfd, File local) {
            this.renderer = renderer; this.pfd = pfd; this.local = local;
        }
        @Override public void close() throws IOException {
            try { renderer.close(); }
            finally {
                try { pfd.close(); }
                finally { if (local != null) { //noinspection ResultOfMethodCallIgnored
                    local.delete();
                } }
            }
        }
    }
}
