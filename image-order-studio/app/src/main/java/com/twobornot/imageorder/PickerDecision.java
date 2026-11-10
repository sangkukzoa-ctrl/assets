package com.twobornot.imageorder;

/** Pure-Java decisions shared by the Android picker and the regression tests. */
final class PickerDecision {
    private PickerDecision() {}
    static boolean supportsPhotoPicker(int api, int extension) {
        return api>=33 || (api>=30 && extension>=2);
    }
    static boolean supportsOrderedPicker(int api, int extension) {
        return api>=35 || (api>=30 && extension>=12);
    }
    static boolean trustNativeOrder(boolean orderedContract, int count) {
        return count==1 || (orderedContract && count>0);
    }
    static boolean needsCombine(int imageCount, boolean allowsMultiple) {
        return !allowsMultiple && imageCount>1;
    }
}
