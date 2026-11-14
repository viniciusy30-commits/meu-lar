"""diferenca malha x terreno ORIGINAL (relevo5.bin) por material; agrupa os piores lugares"""
import sys, os, struct; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, app_export as A
f = open('out/relevo5.bin', 'rb'); nx, nz, g = struct.unpack('<iif', f.read(12)); hf = np.frombuffer(f.read(), dtype='<i2').reshape(nz, nx) / 100.0
G = A._read_ground('out/city5_ground.bin')
for m, V in G.items():
    T = V.reshape(-1, 3, 6); T = T[T[:, :, 4].mean(1) > 0.5]
    a, b, c = T[:, 0, :3], T[:, 1, :3], T[:, 2, :3]
    S = np.concatenate([a, b, c, (a + b + c) / 3])
    t, i, j, up = A._terr(hf, 8.0, S[:, 0], S[:, 2]); d = S[:, 1] - t
    print(m, len(S), 'malha-terreno pct1/5/50/95/99', np.percentile(d, [1, 5, 50, 95, 99]).round(2), ' abaixo(<-0.02):', round(float((d < -0.02).mean()), 3), ' >0.6:', round(float((d > 0.6).mean()), 3))
    for lo, hi in ((-50, -0.15), (0.6, 4)):
        mm = (d > lo) & (d < hi); P = S[mm]
        key = (P[:, 0] // 64).astype(int) * 1000 + (P[:, 2] // 64).astype(int)
        u, cnt = np.unique(key, return_counts=True); o = np.argsort(-cnt)[:6]
        print('   ', lo, hi, int(mm.sum()), [(int(u[k] // 1000 * 64 + 32), int(u[k] % 1000 * 64 + 32), int(cnt[k])) for k in o])
