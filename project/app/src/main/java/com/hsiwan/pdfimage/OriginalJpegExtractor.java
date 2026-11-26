package com.hsiwan.pdfimage;

import android.content.ContentResolver;
import android.net.Uri;

import com.tom_roush.pdfbox.cos.COSName;
import com.tom_roush.pdfbox.cos.COSStream;
import com.tom_roush.pdfbox.pdmodel.PDDocument;
import com.tom_roush.pdfbox.pdmodel.PDPage;
import com.tom_roush.pdfbox.pdmodel.PDResources;
import com.tom_roush.pdfbox.pdmodel.graphics.PDXObject;
import com.tom_roush.pdfbox.pdmodel.graphics.form.PDFormXObject;
import com.tom_roush.pdfbox.pdmodel.graphics.image.PDImageXObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CancellationException;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Extracts only unmodified JPEG/DCTDecode image XObject bytes from PDF page resources.
 * Does not rasterize pages, decompress/re-encode JPEGs, or include overlays/text.
 * Not a general-purpose pdfimages replacement: no inline/non-JPEG images.
 */
final class OriginalJpegExtractor {
    private OriginalJpegExtractor() { }

    private static final class JpegEntry {
        final int page; // zero-based
        final COSStream stream;
        JpegEntry(int page, COSStream stream) { this.page = page; this.stream = stream; }
    }

    static PdfConversionEngine.Result extract(ContentResolver resolver, File cacheDir,
            List<PdfConversionEngine.InputPdf> files, Uri output,
            PdfConversionEngine.Options options, AtomicBoolean cancelled,
            PdfConversionEngine.Progress progress) {
        PdfConversionEngine.Result result = new PdfConversionEngine.Result();
        DocumentStorage storage;
        try {
            storage = new DocumentStorage(resolver, output);
        } catch (Exception err) {
            result.totalFailed++;
            result.errors.add(L10n.t("저장 폴더 오류: ","Output folder error: ") + reason(err));
            return result;
        }

        for (int docIndex = 0; docIndex < files.size(); docIndex++) {
            if (cancelled.get()) { result.cancelled = true; break; }
            PdfConversionEngine.InputPdf source = files.get(docIndex);
            progress.update(1000 * docIndex / files.size(),
                    L10n.t("원본 JPEG 검색 ","Searching original JPEGs ") + (docIndex + 1) + "/" + files.size() + " · " + source.name);
            File temp = null;
            try {
                // PDDocument.load(File) needs a local random-access file. Never use shared storage.
                temp = File.createTempFile("source_pdf_", ".pdf", cacheDir);
                try (InputStream in = resolver.openInputStream(source.uri);
                     OutputStream out = new BufferedOutputStream(new FileOutputStream(temp))) {
                    if (in == null) throw new IOException(L10n.t("원본 PDF 열기 실패","Could not open source PDF"));
                    byte[] buffer = new byte[65536];
                    int count;
                    while ((count = in.read(buffer)) != -1) {
                        if (cancelled.get()) throw new CancellationException();
                        out.write(buffer, 0, count);
                    }
                }
                try (PDDocument pdf = PDDocument.load(temp)) {
                    List<Integer> pages = PageSelection.parse(options.pages, pdf.getNumberOfPages());
                    List<JpegEntry> images = new ArrayList<>();
                    for (int p : pages) {
                        if (cancelled.get()) throw new CancellationException();
                        PDPage page = pdf.getPage(p);
                        // Deduplicate multiple resource aliases of one image on a page.
                        Set<COSStream> seenImages = Collections.newSetFromMap(
                                new IdentityHashMap<COSStream, Boolean>());
                        Set<COSStream> seenForms = Collections.newSetFromMap(
                                new IdentityHashMap<COSStream, Boolean>());
                        scan(page.getResources(), p, images, seenImages, seenForms, cancelled);
                    }
                    if (images.isEmpty()) {
                        result.errors.add(source.name + L10n.t(": 내장 원본 JPEG(DCTDecode) 없음 · 출력 0장",": No embedded DCTDecode JPEG found · 0 images exported"));
                    } else {
                        String base = DocumentStorage.cleanBaseName(source.name);
                        Uri folder = images.size() > 1
                                ? storage.createPdfFolder(base + "_OriginalJPEG") : storage.root();
                        Set<String> used = images.size() > 1
                                ? storage.newFolderNames() : storage.rootNames();
                        for (int index = 0; index < images.size(); index++) {
                            if (cancelled.get()) throw new CancellationException();
                            JpegEntry img = images.get(index);
                            String name = images.size() == 1 ? base + ".jpg"
                                    : String.format(java.util.Locale.ROOT,
                                            "%s_p%03d_img%03d.jpg", base, img.page + 1, index + 1);
                            Uri created = null;
                            try {
                                created = storage.createFile(folder, used, name, "image/jpeg");
                                try (InputStream jpeg = new BufferedInputStream(img.stream.createRawInputStream());
                                     OutputStream dest = new BufferedOutputStream(
                                             requireOutput(resolver, created), 65536)) {
                                    byte[] buffer = new byte[65536];
                                    int n;
                                    while ((n = jpeg.read(buffer)) != -1) {
                                        if (cancelled.get()) throw new CancellationException();
                                        dest.write(buffer, 0, n);
                                    }
                                }
                                result.totalSaved++;
                            } catch (Exception err) {
                                storage.deleteIfPossible(created);
                                if (err instanceof CancellationException) throw (CancellationException) err;
                                result.totalFailed++;
                                result.errors.add(source.name + " · JPEG " + (index + 1)
                                        + ": " + reason(err));
                            }
                            int permille = (int) ((docIndex + (index + 1d) / images.size())
                                    * 1000 / files.size());
                            progress.update(permille,
                                    L10n.t("문서 ","Document ") + (docIndex + 1) + "/" + files.size()
                                            + L10n.t(" · 원본 JPEG "," · Original JPEG ") + (index + 1) + "/" + images.size());
                        }
                    }
                }
                result.completedDocuments++;
            } catch (CancellationException stop) {
                result.cancelled = true;
                break;
            } catch (Exception err) {
                result.totalFailed++;
                result.errors.add(source.name + ": " + reason(err));
            } finally {
                if (temp != null && temp.exists()) {
                    //noinspection ResultOfMethodCallIgnored
                    temp.delete();
                }
            }
        }
        if (!result.cancelled && !cancelled.get()) progress.update(1000, L10n.t("JPEG 추출 완료","JPEG extraction completed"));
        if (cancelled.get()) result.cancelled = true;
        return result;
    }

    private static void scan(PDResources resources, int page, List<JpegEntry> images,
            Set<COSStream> seenImages, Set<COSStream> seenForms, AtomicBoolean cancelled)
            throws IOException {
        if (resources == null) return;
        for (COSName key : resources.getXObjectNames()) {
            if (cancelled.get()) throw new CancellationException();
            PDXObject obj = resources.getXObject(key);
            if (obj instanceof PDImageXObject) {
                COSStream stream = ((PDImageXObject) obj).getStream().getCOSObject();
                List<COSName> filters = ((PDImageXObject) obj).getStream().getFilters();
                if (filters != null && filters.size() == 1
                        && COSName.DCT_DECODE.equals(filters.get(0)) && seenImages.add(stream)) {
                    images.add(new JpegEntry(page, stream));
                }
            } else if (obj instanceof PDFormXObject) {
                COSStream formStream = (COSStream) ((PDFormXObject) obj).getCOSObject();
                if (seenForms.add(formStream)) {
                    scan(((PDFormXObject) obj).getResources(), page,
                            images, seenImages, seenForms, cancelled);
                }
            }
        }
    }

    private static OutputStream requireOutput(ContentResolver resolver, Uri destination)
            throws IOException {
        OutputStream stream = resolver.openOutputStream(destination, "w");
        if (stream == null) throw new IOException(L10n.t("저장 스트림 열기 실패","Could not open output stream"));
        return stream;
    }

    private static String reason(Throwable e) {
        return e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
    }
}
