import com.hsiwan.pdfimage.PageSelection;
import java.util.Arrays;
import java.util.List;

public class PageSelectionTest {
    static void ok(String spec, int count, Integer... expected) {
        List<Integer> got = PageSelection.parse(spec, count);
        if (!got.equals(Arrays.asList(expected))) throw new AssertionError(spec + " -> " + got);
    }
    static void bad(String spec, int count) {
        try { PageSelection.parse(spec, count); }
        catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("Expected error: " + spec);
    }
    public static void main(String[] args) {
        ok("1,3-5,3", 7, 0,2,3,4);
        ok("3 ~ 4", 4, 2,3);
        ok("4,2,1", 4, 0,1,3);
        ok("", 2, 0,1);
        ok("2", 2, 1);
        bad("1-8", 2); bad("3-2", 3); bad("", 0); bad("1,,2", 2); bad("abc", 3); bad("0", 3);
        System.out.println("PageSelection tests: PASS");
    }
}
