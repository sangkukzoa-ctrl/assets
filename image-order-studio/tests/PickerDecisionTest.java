package com.twobornot.imageorder;

public final class PickerDecisionTest {
    static void yes(boolean test) {if(!test)throw new AssertionError("Expected true");}
    static void no(boolean test) {if(test)throw new AssertionError("Expected false");}
    public static void main(String[] args) {
        no(PickerDecision.supportsPhotoPicker(26,0));
        yes(PickerDecision.supportsPhotoPicker(30,2));
        yes(PickerDecision.supportsPhotoPicker(33,0));
        no(PickerDecision.supportsOrderedPicker(34,11));
        yes(PickerDecision.supportsOrderedPicker(30,12));
        yes(PickerDecision.supportsOrderedPicker(35,0));
        yes(PickerDecision.trustNativeOrder(false,1));
        no(PickerDecision.trustNativeOrder(false,5));
        yes(PickerDecision.trustNativeOrder(true,166));
        no(PickerDecision.trustNativeOrder(true,0));
        no(PickerDecision.needsCombine(1,false));
        yes(PickerDecision.needsCombine(3,false));
        no(PickerDecision.needsCombine(3,true));
        System.out.println("PASS PickerDecision: photo picker support, verified order, attachment limits");
    }
}
