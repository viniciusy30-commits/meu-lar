package org.json;
import java.util.*;
public class JSONObject {
    final Map<String, Object> m;
    JSONObject(Map<String, Object> mm) { m = mm; }
    public JSONObject() { m = new LinkedHashMap<>(); }
    public JSONObject(String s) { int[] p = {0}; m = ((JSONObject) val(s, p)).m; }
    static void ws(String s, int[] p) { while (p[0] < s.length() && Character.isWhitespace(s.charAt(p[0]))) p[0]++; }
    static Object val(String s, int[] p) {
        ws(s, p); char c = s.charAt(p[0]);
        if (c == '{') { p[0]++; Map<String, Object> mm = new LinkedHashMap<>(); ws(s, p);
            if (s.charAt(p[0]) == '}') { p[0]++; return new JSONObject(mm); }
            while (true) { ws(s, p); String k = (String) val(s, p); ws(s, p); p[0]++; Object v = val(s, p); mm.put(k, v); ws(s, p); char d = s.charAt(p[0]++); if (d == '}') break; }
            return new JSONObject(mm); }
        if (c == '[') { p[0]++; List<Object> l = new ArrayList<>(); ws(s, p);
            if (s.charAt(p[0]) == ']') { p[0]++; return new JSONArray(l); }
            while (true) { l.add(val(s, p)); ws(s, p); char d = s.charAt(p[0]++); if (d == ']') break; }
            return new JSONArray(l); }
        if (c == '"') { StringBuilder b = new StringBuilder(); p[0]++;
            while (true) { char d = s.charAt(p[0]++); if (d == '"') break; if (d == '\\') { char e = s.charAt(p[0]++); if (e == 'u') { b.append((char) Integer.parseInt(s.substring(p[0], p[0] + 4), 16)); p[0] += 4; } else b.append(e == 'n' ? '\n' : e == 't' ? '\t' : e); } else b.append(d); }
            return b.toString(); }
        if (s.startsWith("true", p[0])) { p[0] += 4; return Boolean.TRUE; }
        if (s.startsWith("false", p[0])) { p[0] += 5; return Boolean.FALSE; }
        if (s.startsWith("null", p[0])) { p[0] += 4; return null; }
        int st = p[0]; while (p[0] < s.length() && "+-0123456789.eE".indexOf(s.charAt(p[0])) >= 0) p[0]++;
        String n = s.substring(st, p[0]); if (n.contains(".") || n.contains("e") || n.contains("E")) return Double.parseDouble(n); return Long.parseLong(n);
    }
    public boolean has(String k) { return m.containsKey(k); }
    public Object opt(String k) { return m.get(k); }
    public JSONArray getJSONArray(String k) { return (JSONArray) m.get(k); }
    public JSONArray optJSONArray(String k) { Object o = m.get(k); return o instanceof JSONArray ? (JSONArray) o : null; }
    public JSONObject getJSONObject(String k) { return (JSONObject) m.get(k); }
    public JSONObject optJSONObject(String k) { Object o = m.get(k); return o instanceof JSONObject ? (JSONObject) o : null; }
    public int getInt(String k) { return ((Number) m.get(k)).intValue(); }
    public int optInt(String k, int d) { Object o = m.get(k); return o instanceof Number ? ((Number) o).intValue() : d; }
    public double getDouble(String k) { return ((Number) m.get(k)).doubleValue(); }
    public double optDouble(String k, double d) { Object o = m.get(k); return o instanceof Number ? ((Number) o).doubleValue() : d; }
    public String optString(String k) { return optString(k, ""); }
    public String optString(String k, String d) { Object o = m.get(k); return o == null ? d : o.toString(); }
    public boolean optBoolean(String k, boolean d) { Object o = m.get(k); return o instanceof Boolean ? (Boolean) o : d; }
}
