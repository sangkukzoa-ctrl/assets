package com.hsiwan.pdfimage;

import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;

import java.io.IOException;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Create-only SAF storage. Existing files are never opened for writing. */
final class DocumentStorage {
    private final ContentResolver resolver;
    private final Uri treeUri;
    private final Uri rootUri;
    private final Set<String> rootNames;

    DocumentStorage(ContentResolver resolver, Uri treeUri) {
        this.resolver = resolver;
        this.treeUri = treeUri;
        String id = DocumentsContract.getTreeDocumentId(treeUri);
        this.rootUri = DocumentsContract.buildDocumentUriUsingTree(treeUri, id);
        this.rootNames = collectNames(rootUri);
    }

    Uri root() { return rootUri; }

    Set<String> newFolderNames() { return new HashSet<>(); }

    Uri createPdfFolder(String base) throws IOException {
        String candidate = unique(base, rootNames);
        Uri result = DocumentsContract.createDocument(resolver, rootUri,
                DocumentsContract.Document.MIME_TYPE_DIR, candidate);
        if (result == null) throw new IOException(L10n.t("출력 폴더 생성에 실패했습니다: ","Could not create output folder: ") + candidate);
        rootNames.add(candidate.toLowerCase(Locale.ROOT));
        return result;
    }

    Uri createFile(Uri parent, Set<String> usedNames, String requested, String mime) throws IOException {
        String candidate = unique(requested, usedNames);
        Uri result = DocumentsContract.createDocument(resolver, parent, mime, candidate);
        if (result == null) throw new IOException(L10n.t("파일 생성에 실패했습니다: ","Could not create file: ") + candidate);
        usedNames.add(candidate.toLowerCase(Locale.ROOT));
        return result;
    }

    Set<String> rootNames() { return rootNames; }

    void deleteIfPossible(Uri file) {
        if (file == null) return;
        try { DocumentsContract.deleteDocument(resolver, file); }
        catch (Exception ignored) { /* Some SAF providers do not support delete. */ }
    }

    private Set<String> collectNames(Uri parentUri) {
        Set<String> names = new HashSet<>();
        try {
            String id = DocumentsContract.getDocumentId(parentUri);
            Uri childUri = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, id);
            try (Cursor cursor = resolver.query(childUri,
                    new String[]{DocumentsContract.Document.COLUMN_DISPLAY_NAME},
                    null, null, null)) {
                if (cursor != null) {
                    while (cursor.moveToNext()) {
                        String name = cursor.getString(0);
                        if (name != null) names.add(name.toLowerCase(Locale.ROOT));
                    }
                }
            }
        } catch (Exception ignored) {
            // Some cloud document providers do not allow children queries.
            // createDocument still uses create-only semantics, never overwrites via this app.
        }
        return names;
    }

    private static String unique(String requested, Set<String> existing) {
        String safe = requested.trim();
        if (!existing.contains(safe.toLowerCase(Locale.ROOT))) return safe;
        int dot = safe.lastIndexOf('.');
        String stem = dot > 0 ? safe.substring(0, dot) : safe;
        String suffix = dot > 0 ? safe.substring(dot) : "";
        for (int n = 2; n < Integer.MAX_VALUE; n++) {
            String candidate = stem + " (" + n + ")" + suffix;
            if (!existing.contains(candidate.toLowerCase(Locale.ROOT))) return candidate;
        }
        throw new IllegalStateException(L10n.t("사용 가능한 파일명을 찾지 못했습니다.","Could not find a free filename."));
    }

    static String cleanBaseName(String fileName) {
        String s = fileName == null ? L10n.t("문서","Document") : fileName.trim();
        if (s.toLowerCase(Locale.ROOT).endsWith(".pdf")) {
            s = s.substring(0, s.length() - 4);
        }
        s = s.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]", "_").trim();
        s = s.replaceAll("[. ]+$", "").trim();
        return s.isEmpty() ? L10n.t("문서","Document") : s;
    }
}
