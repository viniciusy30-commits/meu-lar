#!/usr/bin/env python3
"""Cidade 6: python3 build6.py [saida]  -> tiles GLB + manifesto + GLB unico + previas"""
import sys, os, time, json
from mesh import Mesh
from plan6 import Plan, W, H
import roads6

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cidade6')
STAGE = os.environ.get('STAGE', 'all')


def build():
    t = time.time()
    P = Plan(); M = Mesh(W, H)
    G = roads6.Ground(P, M).build()
    print(f'chao: {M.ntri} triangulos ({time.time() - t:.1f}s)')
    import lots6
    L = lots6.Lots(P, G, M).build()
    print(f'lotes/construcoes: {M.ntri} triangulos ({time.time() - t:.1f}s)')
    return P, G, L, M


if __name__ == '__main__':
    P, G, L, M = build()
    print(M.stats())
