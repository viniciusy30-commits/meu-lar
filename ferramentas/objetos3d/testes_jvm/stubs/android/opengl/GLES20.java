package android.opengl;
public class GLES20 {
    public static final int GL_TEXTURE_2D=1, GL_TEXTURE_MIN_FILTER=2, GL_LINEAR_MIPMAP_LINEAR=3, GL_TEXTURE_MAG_FILTER=4, GL_LINEAR=5, GL_CLAMP_TO_EDGE=6, GL_REPEAT=7, GL_TEXTURE_WRAP_S=8, GL_TEXTURE_WRAP_T=9;
    static int n = 1;
    public static void glGenTextures(int c, int[] a, int o) { for (int i = 0; i < c; i++) a[o + i] = n++; }
    public static void glBindTexture(int a, int b) {}
    public static void glGenerateMipmap(int a) {}
    public static void glTexParameteri(int a, int b, int c) {}
}
