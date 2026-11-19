package com.twobornot.imageorder;
import java.util.*;
public class OriginalDeliveryTest {
    private static void same(Object a,Object b){ if(!Objects.equals(a,b))throw new AssertionError(a+" != "+b); }
    public static void main(String[] args){
        same("image/jpeg",OriginalDelivery.commonMime(Arrays.asList("image/jpeg","image/jpeg")));
        same("image/*",OriginalDelivery.commonMime(Arrays.asList("image/heic","image/png")));
        same("image/png",OriginalDelivery.commonMime(Collections.singletonList("image/png")));
        SequenceLedger s=new SequenceLedger();
        s.select("three");s.select("one");s.select("two");
        same(Arrays.asList("three","one","two"),s.snapshot());
        s.swap(0,2); same(Arrays.asList("two","one","three"),s.snapshot());
        boolean failed=false;try{OriginalDelivery.commonMime(Arrays.asList("image/png","text/plain"));}catch(IllegalArgumentException ex){failed=true;}
        if(!failed)throw new AssertionError("Non-image accepted");
        System.out.println("OriginalDeliveryTest PASS");
    }
}
