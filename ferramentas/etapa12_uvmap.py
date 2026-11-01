"""Etapa 12 - mapeia pontos 3D da frente do rosto (pose de referência) para pixels do atlas textures.png."""
import numpy as np
from etapa11_base import read_base

class FaceUV:
    def __init__(self, base_path):
        bs = read_base(base_path); v = bs['ver']
        self.pos = v['pos'].astype(float); self.uv = v['uv'].astype(float) * [2048, 1024]
        idx = bs['idx'].astype(int).reshape(-1, 3)
        p = self.pos[idx]                               # (nt,3,3)
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        keep = (n[:, 2] > 0) & (p[:, :, 2].min(1) > 3) & (np.abs(p[:, :, 0]).max(1) < 14) & (p[:, :, 1].min(1) > 140) & (p[:, :, 1].max(1) < 180)
        # só triângulos cuja UV cai no tile do rosto
        u = self.uv[idx]
        keep &= (u[:, :, 0].min(1) > 500) & (u[:, :, 0].max(1) < 980) & (u[:, :, 1].min(1) > 40) & (u[:, :, 1].max(1) < 440)
        self.tri = idx[keep]
    def to_px(self, x, y):
        best = None
        for t in self.tri:
            a, b, c = self.pos[t]
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9: continue
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) < -1e-6: continue
            z = l1 * a[2] + l2 * b[2] + l3 * c[2]
            if best is None or z > best[0]:
                best = (z, l1 * self.uv[t[0]] + l2 * self.uv[t[1]] + l3 * self.uv[t[2]])
        return None if best is None else (best[1][0], best[1][1], best[0])

if __name__ == '__main__':
    import sys
    f = FaceUV(sys.argv[1]); print('triângulos da frente do rosto', len(f.tri))
    for (x, y) in [(4.08, 164.4), (4.08, 168), (1.7, 167.6), (6.6, 167.9), (-4.08, 168), (0, 164.4)]:
        print((x, y), f.to_px(x, y))
