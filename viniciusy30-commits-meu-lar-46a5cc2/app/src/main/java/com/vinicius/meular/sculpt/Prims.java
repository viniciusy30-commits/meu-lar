package com.vinicius.meular.sculpt;

/** Primitivas de escultura (distância assinada) e operações de mistura suave. Unidades em metros. */
public final class Prims {
    private Prims() {}

    public interface Field { float d(float x, float y, float z); }

    public static float smin(float a, float b, float k) {
        float h = Math.max(k - Math.abs(a - b), 0f) / k;
        return Math.min(a, b) - h * h * k * 0.25f;
    }

    public static float smax(float a, float b, float k) { return -smin(-a, -b, k); }

    public static float clamp(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

    public static float sstep(float a, float b, float v) {
        float t = clamp((v - a) / (b - a), 0f, 1f);
        return t * t * (3f - 2f * t);
    }

    public static float mixf(float a, float b, float t) { return a + (b - a) * t; }

    /** Elipsoide (opcionalmente girado: ordem Z, depois X, depois Y). */
    public static final class Ell {
        public final float cx, cy, cz, rx, ry, rz;
        private final boolean rot;
        private final float m00, m01, m02, m10, m11, m12, m20, m21, m22;
        public Ell(float cx, float cy, float cz, float rx, float ry, float rz) { this(cx, cy, cz, rx, ry, rz, 0f, 0f, 0f); }
        public Ell(float cx, float cy, float cz, float rx, float ry, float rz, float rotX, float rotY, float rotZ) {
            this.cx = cx; this.cy = cy; this.cz = cz; this.rx = rx; this.ry = ry; this.rz = rz;
            rot = rotX != 0f || rotY != 0f || rotZ != 0f;
            // matriz inversa (mundo -> local) = transposta de R = Ry * Rx * Rz
            float cxr = (float) Math.cos(rotX), sxr = (float) Math.sin(rotX);
            float cyr = (float) Math.cos(rotY), syr = (float) Math.sin(rotY);
            float czr = (float) Math.cos(rotZ), szr = (float) Math.sin(rotZ);
            // R = Ry*Rx*Rz
            float r00 = cyr * czr + syr * sxr * szr, r01 = -cyr * szr + syr * sxr * czr, r02 = syr * cxr;
            float r10 = cxr * szr, r11 = cxr * czr, r12 = -sxr;
            float r20 = -syr * czr + cyr * sxr * szr, r21 = syr * szr + cyr * sxr * czr, r22 = cyr * cxr;
            m00 = r00; m01 = r10; m02 = r20; m10 = r01; m11 = r11; m12 = r21; m20 = r02; m21 = r12; m22 = r22;
        }
        public float d(float x, float y, float z) {
            float dx = x - cx, dy = y - cy, dz = z - cz;
            if (rot) {
                float lx = m00 * dx + m01 * dy + m02 * dz;
                float ly = m10 * dx + m11 * dy + m12 * dz;
                float lz = m20 * dx + m21 * dy + m22 * dz;
                dx = lx; dy = ly; dz = lz;
            }
            float qx = dx / rx, qy = dy / ry, qz = dz / rz;
            float k0 = (float) Math.sqrt(qx * qx + qy * qy + qz * qz);
            float ax = qx / rx, ay = qy / ry, az = qz / rz;
            float k1 = (float) Math.sqrt(ax * ax + ay * ay + az * az);
            if (k1 < 1e-9f) return -Math.min(rx, Math.min(ry, rz));
            return k0 * (k0 - 1f) / k1;
        }
    }

    /** Cone arredondado (cápsula com raios diferentes), distância exata. */
    public static final class Cone {
        private final float ax, ay, az, bax, bay, baz, l2, rr, a2, il2, r1, r2;
        public Cone(float ax, float ay, float az, float bx, float by, float bz, float r1, float r2) {
            this.ax = ax; this.ay = ay; this.az = az;
            bax = bx - ax; bay = by - ay; baz = bz - az;
            l2 = bax * bax + bay * bay + baz * baz;
            rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1f / l2;
            this.r1 = r1; this.r2 = r2;
        }
        public float d(float x, float y, float z) {
            float pax = x - ax, pay = y - ay, paz = z - az;
            float yy = pax * bax + pay * bay + paz * baz;
            float zz = yy - l2;
            float xvx = pax * l2 - bax * yy, xvy = pay * l2 - bay * yy, xvz = paz * l2 - baz * yy;
            float x2 = xvx * xvx + xvy * xvy + xvz * xvz;
            float y2 = yy * yy * l2, z2 = zz * zz * l2;
            float k = Math.signum(rr) * rr * rr * x2;
            if (Math.signum(zz) * a2 * z2 > k) return (float) Math.sqrt(x2 + z2) * il2 - r2;
            if (Math.signum(yy) * a2 * y2 < k) return (float) Math.sqrt(x2 + y2) * il2 - r1;
            return ((float) Math.sqrt(x2 * a2 * il2) + yy * rr) * il2 - r1;
        }
    }

    /** Caixa arredondada alinhada aos eixos (centro, meia-medidas, raio do canto). */
    public static final class Box {
        private final float cx, cy, cz, hx, hy, hz, r;
        public Box(float cx, float cy, float cz, float hx, float hy, float hz, float r) {
            this.cx = cx; this.cy = cy; this.cz = cz; this.hx = hx - r; this.hy = hy - r; this.hz = hz - r; this.r = r;
        }
        public float d(float x, float y, float z) {
            float qx = Math.abs(x - cx) - hx, qy = Math.abs(y - cy) - hy, qz = Math.abs(z - cz) - hz;
            float ox = Math.max(qx, 0f), oy = Math.max(qy, 0f), oz = Math.max(qz, 0f);
            return (float) Math.sqrt(ox * ox + oy * oy + oz * oz) + Math.min(Math.max(qx, Math.max(qy, qz)), 0f) - r;
        }
    }

    /** Ruído de valor 3D suave (determinístico), faixa aproximada -1..1. */
    public static float noise(float x, float y, float z) {
        int xi = (int) Math.floor(x), yi = (int) Math.floor(y), zi = (int) Math.floor(z);
        float fx = x - xi, fy = y - yi, fz = z - zi;
        fx = fx * fx * (3f - 2f * fx); fy = fy * fy * (3f - 2f * fy); fz = fz * fz * (3f - 2f * fz);
        float c000 = hash(xi, yi, zi), c100 = hash(xi + 1, yi, zi), c010 = hash(xi, yi + 1, zi), c110 = hash(xi + 1, yi + 1, zi);
        float c001 = hash(xi, yi, zi + 1), c101 = hash(xi + 1, yi, zi + 1), c011 = hash(xi, yi + 1, zi + 1), c111 = hash(xi + 1, yi + 1, zi + 1);
        float a = mixf(mixf(c000, c100, fx), mixf(c010, c110, fx), fy);
        float b = mixf(mixf(c001, c101, fx), mixf(c011, c111, fx), fy);
        return mixf(a, b, fz);
    }

    private static float hash(int x, int y, int z) {
        int h = x * 374761393 + y * 668265263 + z * 1274126177;
        h = (h ^ (h >>> 13)) * 1274126177;
        h ^= h >>> 16;
        return ((h & 0xFFFF) / 32767.5f) - 1f;
    }
}
