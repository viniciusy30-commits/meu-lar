package com.vinicius.meular.mods;

/** Malha como veio do package (espaço do jogo de origem, ainda sem encaixe no corpo). */
public final class RawMesh {
    public String name = "";
    public int game;          // 2, 3 ou 4
    public float[] pos;       // 3 por vértice
    public float[] nor;       // 3 por vértice
    public float[] uv;        // 2 por vértice (como no arquivo)
    public int[] idx;         // triângulos
    public int nv() { return pos.length / 3; }
    public int nt() { return idx.length / 3; }
}
