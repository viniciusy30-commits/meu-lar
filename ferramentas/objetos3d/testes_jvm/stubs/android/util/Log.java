package android.util;
public class Log { public static int e(String t, String m, Throwable e) { System.out.println("E/" + t + ": " + m + " " + e); return 0; } }
