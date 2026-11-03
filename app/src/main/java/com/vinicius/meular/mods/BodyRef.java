package com.vinicius.meular.mods;

/** O corpo do Sims 3 em uso (repouso, em cm no espaço do app): serve de molde para encaixar e dar pesos às peças importadas. */
public final class BodyRef {
    public final float[] pos;   // 3 por vértice
    public final float[] nor;   // 3 por vértice
    public final int[] bi;      // 4 por vértice (índices de osso)
    public final float[] bw;    // 4 por vértice (pesos, soma 1)
    public final int[] idx;     // triângulos
    public final float[] rig;   // bodyrig.txt: ombro(0..2), cotovelo(3..5), mão(6..8), quadril(9..11), joelho(12..14), tornozelo(15..17), alturas peito/pescoço/cabeça (18..20)
    public final float s0;      // escala metros -> espaço do app para malhas do Sims 3 deste corpo

    public BodyRef(float[] pos, float[] nor, int[] bi, float[] bw, int[] idx, float[] rig, float s0) {
        this.pos = pos; this.nor = nor; this.bi = bi; this.bw = bw; this.idx = idx; this.rig = rig; this.s0 = s0;
    }

    public int nv() { return pos.length / 3; }
}
