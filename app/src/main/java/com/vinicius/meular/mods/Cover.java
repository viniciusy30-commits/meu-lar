package com.vinicius.meular.mods;

/** Quais triângulos do corpo ficam por baixo de uma peça (para a pele não furar o tecido). */
public final class Cover {
    private Cover() {}

    /** [mark] (um boolean por triângulo do corpo) recebe true nos triângulos cobertos. */
    public static void mark(float[] bpos, int[] bidx, float[] ppos, float[] pnor, float radius, boolean[] mark) {
        mark(bpos, bidx, ppos, pnor, radius, mark, Float.MAX_VALUE);
    }

    /** [ymax]: triângulos do corpo acima dessa altura (pescoço/cabeça) nunca são escondidos. */
    public static void mark(float[] bpos, int[] bidx, float[] ppos, float[] pnor, float radius, boolean[] mark, float ymax) {
        if (ppos.length == 0) return;
        Grid g = new Grid(ppos, radius);
        int nt = bidx.length / 3;
        float[] d2 = new float[1];
        float r2 = radius * radius;
        for (int t = 0; t < nt && t < mark.length; t++) {
            int a = bidx[t * 3] * 3, b = bidx[t * 3 + 1] * 3, c = bidx[t * 3 + 2] * 3;
            float x = (bpos[a] + bpos[b] + bpos[c]) / 3f, y = (bpos[a + 1] + bpos[b + 1] + bpos[c + 1]) / 3f, z = (bpos[a + 2] + bpos[b + 2] + bpos[c + 2]) / 3f;
            if (y > ymax) continue;
            int i = g.nearest(x, y, z, 1, d2);
            if (i < 0 || d2[0] > r2) continue;
            // o ponto do corpo precisa estar atrás da superfície do tecido
            float side = (x - ppos[i * 3]) * pnor[i * 3] + (y - ppos[i * 3 + 1]) * pnor[i * 3 + 1] + (z - ppos[i * 3 + 2]) * pnor[i * 3 + 2];
            if (side < 0.6f) mark[t] = true;
        }
    }

    /**
     * Versão com faixa vertical e proteção por pesos de osso.
     * Evita que mangas apaguem mãos/dedos e que calças apaguem pés/tornozelos.
     */
    public static void mark(float[] bpos, int[] bidx, float[] ppos, float[] pnor,
                            float radius, boolean[] mark, float ymin, float ymax,
                            int[] bodyBones, float[] bodyWeights, int[] protectedBones, float sideLimit) {
        if (ppos.length == 0) return;
        Grid g = new Grid(ppos, radius);
        int nt = bidx.length / 3;
        float[] d2 = new float[1];
        float r2 = radius * radius;
        for (int t = 0; t < nt && t < mark.length; t++) {
            int ia = bidx[t * 3], ib = bidx[t * 3 + 1], ic = bidx[t * 3 + 2];
            int a = ia * 3, b = ib * 3, c = ic * 3;
            float x = (bpos[a] + bpos[b] + bpos[c]) / 3f;
            float y = (bpos[a + 1] + bpos[b + 1] + bpos[c + 1]) / 3f;
            float z = (bpos[a + 2] + bpos[b + 2] + bpos[c + 2]) / 3f;
            if (y < ymin || y > ymax) continue;

            boolean protectedTriangle = false;
            if (protectedBones != null && bodyBones != null && bodyWeights != null) {
                int[] vertices = {ia, ib, ic};
                for (int vertex : vertices) {
                    int base = vertex * 4;
                    for (int k = 0; k < 4; k++) {
                        if (bodyWeights[base + k] < 0.15f) continue;
                        int bone = bodyBones[base + k];
                        for (int protectedBone : protectedBones) {
                            if (bone == protectedBone) {
                                protectedTriangle = true;
                                break;
                            }
                        }
                        if (protectedTriangle) break;
                    }
                    if (protectedTriangle) break;
                }
            }
            if (protectedTriangle) continue;

            int i = g.nearest(x, y, z, 1, d2);
            if (i < 0 || d2[0] > r2) continue;
            float side = (x - ppos[i * 3]) * pnor[i * 3]
                    + (y - ppos[i * 3 + 1]) * pnor[i * 3 + 1]
                    + (z - ppos[i * 3 + 2]) * pnor[i * 3 + 2];
            if (side < sideLimit) mark[t] = true;
        }
    }

    /**
     * Cobertura precisa pela superfície dos triângulos da roupa.
     * A versão antiga usava apenas o vértice de roupa mais próximo; em bordas,
     * isso podia apagar pele fora da peça e abrir falhas claras na cintura.
     */
    public static void markSurface(float[] bpos, int[] bidx, float[] ppos, float[] pnor, int[] pidx,
                                   float maxDistance, boolean[] mark, float ymin, float ymax,
                                   int[] bodyBones, float[] bodyWeights, int[] protectedBones, float sideLimit) {
        if (ppos.length == 0 || pidx.length < 3) return;
        final int pnv = ppos.length / 3, pnt = pidx.length / 3;
        Grid grid = new Grid(ppos, 1.0f);
        int[] counts = new int[pnv];
        for (int t = 0; t < pnt; t++) {
            counts[pidx[t * 3]]++; counts[pidx[t * 3 + 1]]++; counts[pidx[t * 3 + 2]]++;
        }
        int[] offsets = new int[pnv + 1];
        for (int i = 0; i < pnv; i++) offsets[i + 1] = offsets[i] + counts[i];
        int[] cursor = offsets.clone(), incident = new int[pnt * 3];
        for (int t = 0; t < pnt; t++) for (int k = 0; k < 3; k++) {
            int v = pidx[t * 3 + k]; incident[cursor[v]++] = t;
        }
        int[] stamp = new int[pnt], near = new int[12];
        float[] nearD = new float[12], q = new float[6];
        float maxD2 = maxDistance * maxDistance;
        int nt = bidx.length / 3;
        for (int t = 0; t < nt && t < mark.length; t++) {
            int ia = bidx[t * 3], ib = bidx[t * 3 + 1], ic = bidx[t * 3 + 2];
            int a = ia * 3, b = ib * 3, cc = ic * 3;
            float x = (bpos[a] + bpos[b] + bpos[cc]) / 3f;
            float y = (bpos[a + 1] + bpos[b + 1] + bpos[cc + 1]) / 3f;
            float z = (bpos[a + 2] + bpos[b + 2] + bpos[cc + 2]) / 3f;
            if (y < ymin || y > ymax) continue;
            if (protectedBones != null && bodyBones != null && bodyWeights != null) {
                boolean protect = false;
                int[] verts = {ia, ib, ic};
                for (int v : verts) {
                    int base = v * 4;
                    for (int k = 0; k < 4; k++) if (bodyWeights[base + k] >= 0.15f) {
                        int bone = bodyBones[base + k];
                        for (int pb : protectedBones) if (bone == pb) { protect = true; break; }
                        if (protect) break;
                    }
                    if (protect) break;
                }
                if (protect) continue;
            }
            // Amostra centro e três vértices. Exigimos 3 de 4 pontos cobertos:
            // fecha pequenas frestas na borda sem apagar triângulos inteiros por um único vértice.
            int covered = 0;
            float[] sx = {x, bpos[a], bpos[b], bpos[cc]};
            float[] sy = {y, bpos[a + 1], bpos[b + 1], bpos[cc + 1]};
            float[] sz = {z, bpos[a + 2], bpos[b + 2], bpos[cc + 2]};
            for (int sample = 0; sample < 4; sample++) {
                if (sy[sample] < ymin || sy[sample] > ymax) continue;
                int got = grid.knn(sx[sample], sy[sample], sz[sample], 2, near.length, false, near, nearD);
                if (got == 0) continue;
                int token = (t + 1) * 4 + sample;
                float bestD2 = Float.MAX_VALUE, bestSide = Float.MAX_VALUE;
                for (int ni = 0; ni < got; ni++) {
                    int v = near[ni];
                    for (int at = offsets[v]; at < offsets[v + 1]; at++) {
                        int pt = incident[at];
                        if (stamp[pt] == token) continue;
                        stamp[pt] = token;
                        int p0 = pidx[pt * 3] * 3, p1 = pidx[pt * 3 + 1] * 3, p2 = pidx[pt * 3 + 2] * 3;
                        closest(sx[sample],sy[sample],sz[sample], ppos[p0],ppos[p0+1],ppos[p0+2], ppos[p1],ppos[p1+1],ppos[p1+2], ppos[p2],ppos[p2+1],ppos[p2+2], q);
                        float dx=sx[sample]-q[0], dy=sy[sample]-q[1], dz=sz[sample]-q[2], d2=dx*dx+dy*dy+dz*dz;
                        if (d2 >= bestD2) continue;
                        float nx=pnor[p0]*q[3]+pnor[p1]*q[4]+pnor[p2]*q[5];
                        float ny=pnor[p0+1]*q[3]+pnor[p1+1]*q[4]+pnor[p2+1]*q[5];
                        float nz=pnor[p0+2]*q[3]+pnor[p1+2]*q[4]+pnor[p2+2]*q[5];
                        float nl=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
                        float side=nl>1e-8f?(dx*nx+dy*ny+dz*nz)/nl:Float.MAX_VALUE;
                        // Borda aberta (barra, manga, cintura): o ponto mais próximo fica na quina e o vetor corre ao longo do tecido,
                        // não por baixo dele. Isso não é "coberto": sem este teste a pele abaixo da barra sumia em cunhas.
                        if (d2 > 0.04f && nl > 1e-8f && Math.abs(side) < 0.5f * (float) Math.sqrt(d2)) side = Float.MAX_VALUE;
                        bestD2=d2; bestSide=side;
                    }
                }
                if (bestD2 <= maxD2 && bestSide < sideLimit) covered++;
            }
            if (covered >= 3) mark[t] = true;
        }
    }

    // Ponto mais próximo em triângulo; q = posição xyz + coordenadas baricêntricas.
    private static void closest(float px,float py,float pz,
                                float ax,float ay,float az, float bx,float by,float bz, float cx,float cy,float cz,
                                float[] q) {
        float abx=bx-ax, aby=by-ay, abz=bz-az, acx=cx-ax, acy=cy-ay, acz=cz-az;
        float apx=px-ax, apy=py-ay, apz=pz-az;
        float d1=abx*apx+aby*apy+abz*apz, d2=acx*apx+acy*apy+acz*apz;
        float u,v,w;
        if (d1<=0f && d2<=0f) { u=1f; v=0f; w=0f; }
        else {
            float bpx=px-bx, bpy=py-by, bpz=pz-bz;
            float d3=abx*bpx+aby*bpy+abz*bpz, d4=acx*bpx+acy*bpy+acz*bpz;
            if (d3>=0f && d4<=d3) { u=0f; v=1f; w=0f; }
            else {
                float vc=d1*d4-d3*d2;
                if (vc<=0f && d1>=0f && d3<=0f) { float t=d1/(d1-d3); u=1f-t; v=t; w=0f; }
                else {
                    float cpx=px-cx, cpy=py-cy, cpz=pz-cz;
                    float d5=abx*cpx+aby*cpy+abz*cpz, d6=acx*cpx+acy*cpy+acz*cpz;
                    if (d6>=0f && d5<=d6) { u=0f; v=0f; w=1f; }
                    else {
                        float vb=d5*d2-d1*d6;
                        if (vb<=0f && d2>=0f && d6<=0f) { float t=d2/(d2-d6); u=1f-t; v=0f; w=t; }
                        else {
                            float va=d3*d6-d5*d4;
                            if (va<=0f && (d4-d3)>=0f && (d5-d6)>=0f) { float t=(d4-d3)/((d4-d3)+(d5-d6)); u=0f; v=1f-t; w=t; }
                            else { float inv=1f/(va+vb+vc); v=vb*inv; w=vc*inv; u=1f-v-w; }
                        }
                    }
                }
            }
        }
        q[0]=u*ax+v*bx+w*cx; q[1]=u*ay+v*by+w*cy; q[2]=u*az+v*bz+w*cz;
        q[3]=u; q[4]=v; q[5]=w;
    }

}
