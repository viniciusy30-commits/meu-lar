package com.vinicius.meular.sculpt;

import com.vinicius.meular.sculpt.Prims.Cone;
import com.vinicius.meular.sculpt.Prims.Ell;
import com.vinicius.meular.sculpt.Prims.Field;

import static com.vinicius.meular.sculpt.Prims.smax;
import static com.vinicius.meular.sculpt.Prims.smin;

/** Pele: corpo inteiro (cabeca, rosto, tronco, bracos, maos, pernas) como uma unica superficie continua. */
public final class Body implements Field {
    // centro e raio dos blocos de detalhe
    public static final float HEAD_Y = 1.445f;
    public static final float HEAD_R = 0.155f;
    public static final float HAND_R = 0.125f;

    public final boolean female;
    public final int build;
    /** Medidas expostas para roupas e acessorios. */
    public float hw, shW, legX, wScale;
    public float[] shoulderL, elbowL;

    // tronco
    private final Ell chest, waist, pelvis, bustL, bustR, glutL, glutR;
    private final Cone neck, trapL, trapR;
    private final Ell deltL, deltR;
    // pernas / bracos
    private final Cone thighL, thighR, shinL, shinR, footL, footR, upL, upR, foreL, foreR;
    private final Ell calfL, calfR, bicL, bicR;
    // cabeca
    private final Ell skull, jaw, chin, cheekL, cheekR, brow, templeL, templeR;
    private final Ell noseBridge, noseTip, wingL, wingR, nostrilL, nostrilR;
    private final Ell lipU, lipL, groove, philtrum;
    private final Ell eyeCutL, eyeCutR, lidL, lidR, sockL, sockR;
    private final Ell earL, earR, earInL, earInR;
    // maos
    public final Hand handL, handR;
    public final float[] wristL, wristR;

    public Body(boolean female, int build) {
        this.female = female; this.build = build;
        float w = build == 0 ? 0.93f : (build == 2 ? 1.10f : 1.0f);   // largura
        float dz = 0.55f + 0.45f * w;                                    // profundidade
        float lim = build == 2 ? 1.12f : (build == 0 ? 0.92f : 1.0f);   // grossura de membros
        float f = female ? 1f : 0f;

        float sh = (female ? 0.150f : 0.172f) * w;     // meia-largura dos ombros
        shW = sh; wScale = w;
        chest = new Ell(0, 1.105f, -0.004f, (female ? 0.128f : 0.150f) * w, 0.118f, (female ? 0.086f : 0.094f) * dz);
        waist = new Ell(0, 0.950f, 0, (female ? 0.098f : 0.118f) * w, 0.108f, (female ? 0.071f : 0.080f) * dz);
        pelvis = new Ell(0, 0.822f, -0.003f, (female ? 0.150f : 0.140f) * w, 0.100f, (female ? 0.098f : 0.094f) * dz);
        bustL = new Ell(0.050f * w, 1.115f, 0.066f * dz, 0.052f, 0.050f, 0.044f);
        bustR = new Ell(-0.050f * w, 1.115f, 0.066f * dz, 0.052f, 0.050f, 0.044f);
        glutL = new Ell(0.060f * w, 0.800f, -0.060f, 0.070f, 0.078f, 0.062f);
        glutR = new Ell(-0.060f * w, 0.800f, -0.060f, 0.070f, 0.078f, 0.062f);
        float nr = (female ? 0.034f : 0.041f) * (0.92f + 0.08f * w);
        neck = new Cone(0, 1.215f, -0.006f, 0, 1.385f, 0.010f, nr * 1.22f, nr);
        trapL = new Cone(0.02f, 1.255f, -0.010f, sh * 0.92f, 1.200f, -0.006f, 0.030f, 0.042f * lim);
        trapR = new Cone(-0.02f, 1.255f, -0.010f, -sh * 0.92f, 1.200f, -0.006f, 0.030f, 0.042f * lim);
        deltL = new Ell(sh + 0.006f, 1.182f, -0.005f, 0.050f * lim, 0.056f * lim, 0.048f * lim);
        deltR = new Ell(-sh - 0.006f, 1.182f, -0.005f, 0.050f * lim, 0.056f * lim, 0.048f * lim);

        float lx = 0.080f * w;
        legX = lx;
        float tr = (female ? 0.080f : 0.078f) * lim * (0.95f + 0.05f * w);
        thighL = new Cone(lx, 0.800f, 0.000f, lx + 0.004f, 0.445f, 0.012f, tr, 0.050f * lim);
        thighR = new Cone(-lx, 0.800f, 0.000f, -lx - 0.004f, 0.445f, 0.012f, tr, 0.050f * lim);
        shinL = new Cone(lx + 0.004f, 0.445f, 0.012f, lx + 0.002f, 0.100f, -0.004f, 0.049f * lim, 0.030f);
        shinR = new Cone(-lx - 0.004f, 0.445f, 0.012f, -lx - 0.002f, 0.100f, -0.004f, 0.049f * lim, 0.030f);
        calfL = new Ell(lx + 0.004f, 0.320f, -0.016f, 0.044f * lim, 0.085f, 0.046f * lim);
        calfR = new Ell(-lx - 0.004f, 0.320f, -0.016f, 0.044f * lim, 0.085f, 0.046f * lim);
        footL = new Cone(lx + 0.002f, 0.085f, -0.004f, lx + 0.004f, 0.040f, 0.100f, 0.032f, 0.022f);
        footR = new Cone(-lx - 0.002f, 0.085f, -0.004f, -lx - 0.004f, 0.040f, 0.100f, 0.032f, 0.022f);

        // bracos: ombro -> cotovelo -> pulso
        float ar = (female ? 0.038f : 0.043f) * lim;
        float[] sL = {sh + 0.004f, 1.180f, -0.004f}, eL = {sh + 0.040f, 0.915f, -0.014f}, wL = {sh + 0.056f, 0.690f, 0.026f};
        upL = new Cone(sL[0], sL[1], sL[2], eL[0], eL[1], eL[2], ar * 1.08f, ar * 0.86f);
        foreL = new Cone(eL[0], eL[1], eL[2], wL[0], wL[1], wL[2], ar * 0.88f, ar * 0.60f);
        upR = new Cone(-sL[0], sL[1], sL[2], -eL[0], eL[1], eL[2], ar * 1.08f, ar * 0.86f);
        foreR = new Cone(-eL[0], eL[1], eL[2], -wL[0], wL[1], wL[2], ar * 0.88f, ar * 0.60f);
        bicL = new Ell(sh + 0.024f, 1.060f, 0.006f, 0.040f * lim, 0.080f, 0.040f * lim);
        bicR = new Ell(-sh - 0.024f, 1.060f, 0.006f, 0.040f * lim, 0.080f, 0.040f * lim);
        wristL = wL; wristR = new float[]{-wL[0], wL[1], wL[2]};
        shoulderL = sL; elbowL = eL;
        handL = new Hand(wL[0], wL[1], wL[2], eL, 1f, female);
        handR = new Hand(-wL[0], wL[1], wL[2], new float[]{-eL[0], eL[1], eL[2]}, -1f, female);

        // cabeca (proporcao fofinha-natural: craneo cheio, rosto curto, olhos grandes, nariz pequeno)
        float hy = HEAD_Y;
        float hw = female ? 0.0785f : 0.0825f;
        this.hw = hw;
        skull = new Ell(0, hy + 0.028f, -0.014f, hw, 0.092f, 0.100f);
        jaw = new Ell(0, hy - 0.034f, 0.008f, hw * (female ? 0.90f : 0.95f), 0.080f, 0.082f);
        chin = new Ell(0, hy - 0.086f, 0.044f, female ? 0.031f : 0.036f, 0.026f, 0.030f);
        cheekL = new Ell(0.050f, hy - 0.040f, 0.042f, 0.029f, 0.028f, 0.030f);
        cheekR = new Ell(-0.050f, hy - 0.040f, 0.042f, 0.029f, 0.028f, 0.030f);
        brow = new Ell(0, hy + 0.030f, 0.080f, 0.060f, 0.010f, 0.016f);
        templeL = new Ell(0.0f, hy, 0f, 0.001f, 0.001f, 0.001f);
        templeR = templeL;
        noseBridge = new Ell(0, hy - 0.012f, 0.080f, 0.0062f, 0.020f, 0.0095f, -0.25f, 0f, 0f);
        noseTip = new Ell(0, hy - 0.0345f, 0.0905f, 0.0100f, 0.0085f, 0.0098f);
        wingL = new Ell(0.0100f, hy - 0.0365f, 0.0855f, 0.0062f, 0.0066f, 0.0062f);
        wingR = new Ell(-0.0100f, hy - 0.0365f, 0.0855f, 0.0062f, 0.0066f, 0.0062f);
        nostrilL = new Ell(0.0056f, hy - 0.0418f, 0.0905f, 0.0024f, 0.0026f, 0.0040f, -0.5f, 0f, 0f);
        nostrilR = new Ell(-0.0056f, hy - 0.0418f, 0.0905f, 0.0024f, 0.0026f, 0.0040f, -0.5f, 0f, 0f);
        float ly = hy + LIP_DY;
        lipU = new Ell(0, ly + 0.0046f, 0.0745f, 0.0235f, 0.0054f, 0.0082f, 0.15f, 0f, 0f);
        lipL = new Ell(0, ly - 0.0056f, 0.0740f, 0.0205f, 0.0066f, 0.0092f, 0.0f, 0f, 0f);
        groove = new Ell(0, ly, 0.088f, 0.0200f, 0.0009f, 0.0130f);
        philtrum = new Ell(0, ly + 0.0125f, 0.080f, 0.0038f, 0.0065f, 0.0045f);
        float ex = EYE_X, ey = hy + EYE_DY;
        eyeCutL = new Ell(ex, ey, 0.082f, EYE_RX, EYE_RY, 0.0200f, 0f, 0f, EYE_TILT);
        eyeCutR = new Ell(-ex, ey, 0.082f, EYE_RX, EYE_RY, 0.0200f, 0f, 0f, -EYE_TILT);
        lidL = new Ell(ex, ey + 0.010f, 0.078f, 0.0200f, 0.0075f, 0.014f, 0f, 0f, EYE_TILT);
        lidR = new Ell(-ex, ey + 0.010f, 0.078f, 0.0200f, 0.0075f, 0.014f, 0f, 0f, -EYE_TILT);
        sockL = new Ell(ex, ey - 0.001f, 0.080f, 0.021f, 0.0088f, 0.0135f);
        sockR = new Ell(-ex, ey - 0.001f, 0.080f, 0.021f, 0.0088f, 0.0135f);
        earL = new Ell(hw + 0.002f, hy - 0.004f, -0.008f, 0.0072f, 0.026f, 0.018f, 0f, 0.12f, 0.10f);
        earR = new Ell(-hw - 0.002f, hy - 0.004f, -0.008f, 0.0072f, 0.026f, 0.018f, 0f, -0.12f, -0.10f);
        earInL = new Ell(hw + 0.0080f, hy - 0.005f, -0.005f, 0.0048f, 0.016f, 0.0105f, 0f, 0.12f, 0.10f);
        earInR = new Ell(-hw - 0.0080f, hy - 0.005f, -0.005f, 0.0048f, 0.016f, 0.0105f, 0f, -0.12f, -0.10f);
    }

    public static final float LIP_DY = -0.077f;
    public static final float EYE_X = 0.0335f, EYE_DY = 0.004f, EYE_RX = 0.0160f, EYE_RY = 0.0072f, EYE_TILT = 0.10f;

    /** Cabeca sem detalhes finos (usada tambem para prender cabelo e barba). */
    public float headBase(float x, float y, float z) {
        float h = smin(skull.d(x, y, z), jaw.d(x, y, z), 0.055f);
        h = smin(h, chin.d(x, y, z), 0.034f);
        h = smin(h, cheekL.d(x, y, z), 0.040f);
        h = smin(h, cheekR.d(x, y, z), 0.040f);
        return h;
    }

    public float d(float x, float y, float z) {
        // tronco
        float d = smin(chest.d(x, y, z), waist.d(x, y, z), 0.075f);
        d = smin(d, pelvis.d(x, y, z), 0.075f);
        if (female) {
            d = smin(d, bustL.d(x, y, z), 0.035f);
            d = smin(d, bustR.d(x, y, z), 0.035f);
            d = smin(d, glutL.d(x, y, z), 0.04f);
            d = smin(d, glutR.d(x, y, z), 0.04f);
        }
        d = smin(d, neck.d(x, y, z), 0.04f);
        d = smin(d, trapL.d(x, y, z), 0.035f);
        d = smin(d, trapR.d(x, y, z), 0.035f);
        d = smin(d, deltL.d(x, y, z), 0.035f);
        d = smin(d, deltR.d(x, y, z), 0.035f);
        // pernas
        float legs = smin(thighL.d(x, y, z), shinL.d(x, y, z), 0.03f);
        legs = smin(legs, calfL.d(x, y, z), 0.03f);
        legs = smin(legs, footL.d(x, y, z), 0.02f);
        float legR = smin(thighR.d(x, y, z), shinR.d(x, y, z), 0.03f);
        legR = smin(legR, calfR.d(x, y, z), 0.03f);
        legR = smin(legR, footR.d(x, y, z), 0.02f);
        legs = Math.min(legs, legR);
        d = smin(d, legs, 0.055f);
        // bracos
        float armL = smin(upL.d(x, y, z), foreL.d(x, y, z), 0.028f);
        armL = smin(armL, bicL.d(x, y, z), 0.03f);
        float armR = smin(upR.d(x, y, z), foreR.d(x, y, z), 0.028f);
        armR = smin(armR, bicR.d(x, y, z), 0.03f);
        d = smin(d, Math.min(armL, armR), 0.03f);
        // maos
        d = smin(d, handL.d(x, y, z), 0.018f);
        d = smin(d, handR.d(x, y, z), 0.018f);
        // cabeca
        float dx = x, dy = y - HEAD_Y, dz = z;
        float r2 = dx * dx + dy * dy + dz * dz;
        float head = headBase(x, y, z);
        if (r2 < HEAD_R * HEAD_R * 1.3f) head = face(x, y, z, head);
        d = smin(d, head, 0.02f);
        return d;
    }

    private float face(float x, float y, float z, float h) {
        h = smin(h, brow.d(x, y, z), 0.022f);
        // nariz
        float n = smin(noseBridge.d(x, y, z), noseTip.d(x, y, z), 0.014f);
        n = smin(n, wingL.d(x, y, z), 0.010f);
        n = smin(n, wingR.d(x, y, z), 0.010f);
        h = smin(h, n, 0.012f);
        h = smax(h, -nostrilL.d(x, y, z), 0.003f);
        h = smax(h, -nostrilR.d(x, y, z), 0.003f);
        // boca
        h = smin(h, philtrum.d(x, y, z), 0.008f);
        h = smin(h, lipU.d(x, y, z), 0.006f);
        h = smin(h, lipL.d(x, y, z), 0.007f);
        h = smax(h, -groove.d(x, y, z), 0.0018f);
        // orelhas
        float ear = smax(earL.d(x, y, z), -earInL.d(x, y, z), 0.004f);
        h = smin(h, ear, 0.008f);
        ear = smax(earR.d(x, y, z), -earInR.d(x, y, z), 0.004f);
        h = smin(h, ear, 0.008f);
        // orbitas e abertura dos olhos
        h = smax(h, -sockL.d(x, y, z) + 0.0f, 0.009f) ;
        h = smax(h, -sockR.d(x, y, z) + 0.0f, 0.009f) ;
        h = smax(h, -eyeCutL.d(x, y, z), 0.0035f);
        h = smax(h, -eyeCutR.d(x, y, z), 0.0035f);
        return h;
    }


    /** Distancia aos labios (para pintar). */
    public float lipDist(float x, float y, float z) { return Math.min(lipU.d(x, y, z), lipL.d(x, y, z)); }

    /** Distancia a abertura do olho (side +1 = x positivo). */
    public float eyeCut(float x, float y, float z, int side) { return side > 0 ? eyeCutL.d(x, y, z) : eyeCutR.d(x, y, z); }

    /** Profundidade z da pele da cabeca (sem os olhos) em (x,y), por bisseccao no eixo z. */
    public float surfaceZ(float x, float y) {
        float lo = 0f, hi = 0.2f;
        for (int i = 0; i < 28; i++) {
            float m = 0.5f * (lo + hi);
            if (headBase(x, y, m) < 0f) lo = m; else hi = m;
        }
        return 0.5f * (lo + hi);
    }

    /** Centro dos olhos (para posicionar as bolas dos olhos). */
    public float eyeX() { return EYE_X; }
    public float eyeY() { return HEAD_Y + EYE_DY; }

    // ------------------------------------------------------------------ mao
    /** Mao relaxada: palma + 4 dedos + polegar, num referencial local preso ao pulso. */
    public static final class Hand {
        private final float ox, oy, oz;                 // pulso (mundo)
        private final float ux, uy, uz, vx, vy, vz, wx, wy, wz; // eixos locais (u=dedos, v=lateral, w=dorso)
        private final Ell palm;
        private final Cone[] seg = new Cone[18];
        private final int nseg;
        public final float cx, cy, cz;                   // centro p/ blocos

        Hand(float wxp, float wyp, float wzp, float[] elbow, float side, boolean female) {
            ox = wxp; oy = wyp; oz = wzp;
            // dedos seguem o antebraco
            float ax = wxp - elbow[0], ay = wyp - elbow[1], az = wzp - elbow[2];
            float al = (float) Math.sqrt(ax * ax + ay * ay + az * az);
            ax /= al; ay /= al; az /= al;
            ux = ax; uy = ay; uz = az;
            // w: dorso da mao aponta para fora do corpo (+x*side), ortogonalizado
            float tx = side, ty = 0f, tz = 0f;
            float dp = tx * ax + ty * ay + tz * az;
            float qx = tx - dp * ax, qy = ty - dp * ay, qz = tz - dp * az;
            float ql = (float) Math.sqrt(qx * qx + qy * qy + qz * qz);
            wx = qx / ql; wy = qy / ql; wz = qz / ql;
            // v = u x w * side  (polegar para a frente, +z)
            float rx = uy * wz - uz * wy, ry = uz * wx - ux * wz, rz = ux * wy - uy * wx;
            float s = rz * 1f >= 0 ? 1f : -1f;
            vx = rx * s; vy = ry * s; vz = rz * s;
            cx = ox + ux * 0.075f; cy = oy + uy * 0.075f; cz = oz + uz * 0.075f;
            float sc = female ? 0.95f : 1f;
            palm = new Ell(0f, 0.044f * sc, 0f, 0.0335f * sc, 0.046f * sc, 0.0150f * sc);
            int n = 0;
            // dedos: posicao lateral, comprimentos e abertura
            float[] fv = {0.0225f, 0.0075f, -0.0085f, -0.0235f};
            float[] fl1 = {0.034f, 0.037f, 0.034f, 0.027f};
            float[] fl2 = {0.021f, 0.023f, 0.021f, 0.017f};
            float[] fl3 = {0.019f, 0.020f, 0.019f, 0.016f};
            float[] fr = {0.0078f, 0.0080f, 0.0076f, 0.0068f};
            float[] spread = {0.10f, 0.02f, -0.07f, -0.17f};
            float[] curl = {0.20f, 0.26f, 0.32f, 0.38f};
            for (int i = 0; i < 4; i++) {
                float px = fv[i] * sc, py = 0.088f * sc, pw = 0f;
                float ang = 0f;
                float r0 = fr[i] * sc;
                float[] ls = {fl1[i] * sc, fl2[i] * sc, fl3[i] * sc};
                float[] rs = {r0, r0 * 0.88f, r0 * 0.78f, r0 * 0.66f};
                float dirV = (float) Math.sin(spread[i]), dirU = (float) Math.cos(spread[i]);
                float cvx = px, cuy = py, cw = pw;
                for (int k = 0; k < 3; k++) {
                    ang += curl[i] * (k == 0 ? 0.8f : 1.2f);
                    float su = dirU * (float) Math.cos(ang), sv = dirV, sw = -(float) Math.sin(ang);
                    float sl = (float) Math.sqrt(su * su + sv * sv + sw * sw);
                    su /= sl; sv /= sl; sw /= sl;
                    float nxv = cvx + sv * ls[k], nyu = cuy + su * ls[k], nww = cw + sw * ls[k];
                    seg[n++] = new Cone(cvx, cyu(cuy), cw, nxv, cyu(nyu), nww, rs[k], rs[k + 1]);
                    cvx = nxv; cuy = nyu; cw = nww;
                }
            }
            // polegar
            float[] t0 = {0.026f * sc, 0.020f * sc, -0.003f * sc};
            float[] t1 = {0.040f * sc, 0.047f * sc, -0.012f * sc};
            float[] t2 = {0.046f * sc, 0.073f * sc, -0.022f * sc};
            float[] t3 = {0.046f * sc, 0.092f * sc, -0.030f * sc};
            seg[n++] = new Cone(cyu(t0[0]), t0[1], t0[2], t1[0], t1[1], t1[2], 0.0125f * sc, 0.0100f * sc);
            seg[n++] = new Cone(t1[0], t1[1], t1[2], t2[0], t2[1], t2[2], 0.0100f * sc, 0.0085f * sc);
            seg[n++] = new Cone(t2[0], t2[1], t2[2], t3[0], t3[1], t3[2], 0.0085f * sc, 0.0070f * sc);
            nseg = n;
        }

        private static float cyu(float v) { return v; }

        /** Distancia da mao (campo local). Fora da esfera de influencia devolve um limite inferior barato. */
        public float d(float x, float y, float z) {
            float px = x - cx, py = y - cy, pz = z - cz;
            float r2 = px * px + py * py + pz * pz;
            if (r2 > HAND_R * HAND_R) return (float) Math.sqrt(r2) - 0.10f;
            float qx = x - ox, qy = y - oy, qz = z - oz;
            // local: (lateral v, dedos u, dorso w) -> Ell/Cone usam (x=v, y=u, z=w)
            float lv = qx * vx + qy * vy + qz * vz;
            float lu = qx * ux + qy * uy + qz * uz;
            float lw = qx * wx + qy * wy + qz * wz;
            float d = palm.d(lv, lu, lw);
            // base do pulso para fundir com o antebraco
            for (int i = 0; i < nseg; i++) d = smin(d, seg[i].d(lv, lu, lw), 0.0085f);
            return d;
        }
    }
}
