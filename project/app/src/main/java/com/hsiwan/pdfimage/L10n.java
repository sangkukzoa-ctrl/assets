package com.hsiwan.pdfimage;

import java.util.Locale;

/** Korean / English strings follow the phone's language, with English fallback. */
final class L10n {
    private L10n() {}
    static String t(String ko, String en) {
        return "ko".equalsIgnoreCase(Locale.getDefault().getLanguage()) ? ko : en;
    }
}
