package org.json;
import java.util.*;
public class JSONArray {
    public final List<Object> a;
    JSONArray(List<Object> l) { a = l; }
    public JSONArray() { a = new ArrayList<>(); }
    public int length() { return a.size(); }
    public Object opt(int i) { return i >= 0 && i < a.size() ? a.get(i) : null; }
    public JSONObject getJSONObject(int i) { return (JSONObject) a.get(i); }
    public JSONObject optJSONObject(int i) { Object o = opt(i); return o instanceof JSONObject ? (JSONObject) o : null; }
    public int getInt(int i) { return ((Number) a.get(i)).intValue(); }
    public double getDouble(int i) { return ((Number) a.get(i)).doubleValue(); }
    public double optDouble(int i) { return optDouble(i, Double.NaN); }
    public double optDouble(int i, double d) { Object o = opt(i); return o instanceof Number ? ((Number) o).doubleValue() : d; }
}
