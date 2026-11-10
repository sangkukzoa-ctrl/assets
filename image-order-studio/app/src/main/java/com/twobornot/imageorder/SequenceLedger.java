package com.twobornot.imageorder;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Stable order model. No filename, MIME type, import time or provider order influences ranking. */
public final class SequenceLedger {
    private final ArrayList<String> ids = new ArrayList<>();

    public boolean select(String id) {
        if (id == null || id.isEmpty() || ids.contains(id)) return false;
        ids.add(id);
        return true;
    }
    public boolean deselect(String id) { return ids.remove(id); }
    public int rank(String id) { int idx = ids.indexOf(id); return idx < 0 ? 0 : idx + 1; }
    public int size() { return ids.size(); }
    public List<String> snapshot() { return Collections.unmodifiableList(new ArrayList<>(ids)); }
    public void clear() { ids.clear(); }
    public boolean swap(int from, int to) {
        if (from < 0 || from >= ids.size() || to < 0 || to >= ids.size()) return false;
        if (from == to) return true;
        Collections.swap(ids, from, to);
        return true;
    }
    public void restore(List<String> sequence, Set<String> valid) {
        ids.clear();
        Set<String> seen = new HashSet<>();
        for (String id : sequence) if (id != null && valid.contains(id) && seen.add(id)) ids.add(id);
    }
}
