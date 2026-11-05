package android.opengl;
public class Matrix {
    public static void multiplyMM(float[] r, int ro, float[] l, int lo, float[] rh, int rho) {
        float[] t = new float[16];
        for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) {
            float s = 0; for (int k = 0; k < 4; k++) s += l[lo + k * 4 + j] * rh[rho + i * 4 + k];
            t[i * 4 + j] = s;
        }
        System.arraycopy(t, 0, r, ro, 16);
    }
    public static void setIdentityM(float[] m, int o) { for (int i = 0; i < 16; i++) m[o + i] = 0; for (int i = 0; i < 16; i += 5) m[o + i] = 1; }
    public static void translateM(float[] m, int o, float x, float y, float z) {
        for (int i = 0; i < 4; i++) m[o + 12 + i] += m[o + i] * x + m[o + 4 + i] * y + m[o + 8 + i] * z;
    }
    public static void scaleM(float[] m, int o, float x, float y, float z) {
        for (int i = 0; i < 4; i++) { m[o + i] *= x; m[o + 4 + i] *= y; m[o + 8 + i] *= z; }
    }
    public static void setRotateM(float[] rm, int o, float a, float x, float y, float z) {
        rm[o + 3] = 0; rm[o + 7] = 0; rm[o + 11] = 0; rm[o + 12] = 0; rm[o + 13] = 0; rm[o + 14] = 0; rm[o + 15] = 1;
        a *= (float) (Math.PI / 180.0f);
        float s = (float) Math.sin(a), c = (float) Math.cos(a);
        float len = (float) Math.sqrt(x * x + y * y + z * z);
        if (len != 1f) { float r = 1f / len; x *= r; y *= r; z *= r; }
        float nc = 1f - c, xy = x * y, yz = y * z, zx = z * x, xs = x * s, ys = y * s, zs = z * s;
        rm[o] = x * x * nc + c; rm[o + 4] = xy * nc - zs; rm[o + 8] = zx * nc + ys;
        rm[o + 1] = xy * nc + zs; rm[o + 5] = y * y * nc + c; rm[o + 9] = yz * nc - xs;
        rm[o + 2] = zx * nc - ys; rm[o + 6] = yz * nc + xs; rm[o + 10] = z * z * nc + c;
    }
    public static void rotateM(float[] m, int o, float a, float x, float y, float z) {
        float[] r = new float[16]; setRotateM(r, 0, a, x, y, z); float[] t = new float[16];
        multiplyMM(t, 0, m, o, r, 0); System.arraycopy(t, 0, m, o, 16);
    }
}
