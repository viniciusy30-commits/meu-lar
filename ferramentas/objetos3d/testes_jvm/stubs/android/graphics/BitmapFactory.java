package android.graphics;
public class BitmapFactory {
    public static class Options { public boolean inPremultiplied = true; }
    public static Bitmap decodeByteArray(byte[] b, int o, int l, Options op) { return (b.length > 8 && b[1] == 'P' && b[2] == 'N' && b[3] == 'G') ? new Bitmap() : null; }
}
