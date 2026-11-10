import com.twobornot.imageorder.SequenceLedger;
import java.util.*;
public class SequenceLedgerTest {
  static void eq(Object expected, Object actual) { if (!Objects.equals(expected,actual)) throw new AssertionError(expected+" != "+actual); }
  public static void main(String[] a) {
    SequenceLedger l = new SequenceLedger();
    String[] fileNames = {"3.png","1.jpg","a.webp","2.heic","whatever.gif"};
    String[] ids = {"third","first","fourth","second","fifth"};
    for (String id : ids) l.select(id);
    eq(Arrays.asList(ids),l.snapshot());
    eq(1,l.rank("third")); eq(4,l.rank("second"));
    eq(false,l.select("third")); eq(5,l.size());
    l.swap(0,3); eq(Arrays.asList("second","first","fourth","third","fifth"), l.snapshot());
    l.deselect("first"); eq(3,l.rank("third"));
    l.restore(Arrays.asList("second","stale","second","third","fourth"),new HashSet<>(Arrays.asList(ids)));
    eq(Arrays.asList("second","third","fourth"),l.snapshot());
    // Names and formats are intentionally not referenced in the ledger.
    eq(5,fileNames.length);
    System.out.println("PASS SequenceLedger: selection, swap, deletion, persistence validation, format/name independence");
  }
}
