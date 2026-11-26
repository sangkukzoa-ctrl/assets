package com.hsiwan.pdfimage;

import java.util.ArrayList;
import java.util.List;
import java.util.TreeSet;

/** Pages are zero-based internally. Input ranges are one-based and inclusive. */
public final class PageSelection {
    private PageSelection() { }

    public static List<Integer> parse(String input, int pageCount) {
        if (pageCount <= 0) throw new IllegalArgumentException(L10n.t("PDF에 페이지가 없습니다.","PDF has no pages."));
        ArrayList<Integer> all = new ArrayList<>();
        if (input == null || input.trim().isEmpty()) {
            for (int i = 0; i < pageCount; i++) all.add(i);
            return all;
        }
        TreeSet<Integer> selected = new TreeSet<>();
        String normalized = input.replace('，', ',').replace('～', '-').replace('~', '-');
        for (String part : normalized.split(",", -1)) {
            part = part.trim();
            if (part.isEmpty()) throw new IllegalArgumentException(L10n.t("페이지 범위에 빈 항목이 있습니다.","Page selection includes an empty entry."));
            try {
                if (part.contains("-")) {
                    String[] ends = part.split("-", -1);
                    if (ends.length != 2) throw new NumberFormatException();
                    int first = Integer.parseInt(ends[0].trim());
                    int last = Integer.parseInt(ends[1].trim());
                    if (first < 1 || last < first || last > pageCount) {
                        throw new IllegalArgumentException(L10n.t("페이지 범위가 잘못되었습니다: ","Invalid page range: ") + part + L10n.t(" (총 "," (total ") + pageCount + L10n.t("쪽)"," pages)"));
                    }
                    for (int n = first; n <= last; n++) selected.add(n - 1);
                } else {
                    int n = Integer.parseInt(part);
                    if (n < 1 || n > pageCount) {
                        throw new IllegalArgumentException(L10n.t("없는 페이지입니다: ","Page does not exist: ") + n + L10n.t(" (총 "," (total ") + pageCount + L10n.t("쪽)"," pages)"));
                    }
                    selected.add(n - 1);
                }
            } catch (NumberFormatException ex) {
                throw new IllegalArgumentException(L10n.t("페이지 표기 오류: ","Invalid page syntax: ") + part + L10n.t(" (예: 1,3-5)"," (e.g. 1,3-5)"));
            }
        }
        return new ArrayList<>(selected);
    }
}
