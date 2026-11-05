"""Oclusão ambiente por vértice num conjunto de malhas (grade de voxels + raios no hemisfério da normal)."""
import numpy as np


def bake_arrays(arrs, voxel=0.012, rays=32, maxd=0.30, strength=0.6, seed=1, skip=None):
    allP = np.vstack([P for P, N, T in arrs]); lo = allP.min(0) - maxd; hi = allP.max(0) + maxd
    dims = np.ceil((hi - lo) / voxel).astype(int) + 1
    occ = np.zeros(dims, bool); rng = np.random.default_rng(seed)
    for P, N, T in arrs:
        a = P[T[:, 0]]; b = P[T[:, 1]]; c = P[T[:, 2]]
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
        n = np.clip((area / (voxel * voxel * 0.4)).astype(int) + 1, 1, 600)
        for k in np.unique(n):
            m = n == k
            u = rng.random((m.sum(), k, 1)); v = rng.random((m.sum(), k, 1)); f = u + v > 1; u = np.where(f, 1 - u, u); v = np.where(f, 1 - v, v)
            pts = a[m][:, None] + u * (b[m] - a[m])[:, None] + v * (c[m] - a[m])[:, None]
            pts = np.concatenate([pts.reshape(-1, 3), a[m], b[m], c[m]])
            ix = ((pts - lo) / voxel).astype(int); occ[ix[:, 0], ix[:, 1], ix[:, 2]] = True
    # o piso também faz sombra
    fy = int((0 - lo[1]) / voxel)
    if 0 <= fy < dims[1]: occ[:, :fy + 1, :] = True
    r1 = rng.random(rays); r2 = rng.random(rays); ph = 2 * np.pi * r2; rr = np.sqrt(r1)
    local = np.stack([rr * np.cos(ph), rr * np.sin(ph), np.sqrt(1 - r1)], 1)
    steps = np.arange(voxel * 2.2, maxd, voxel * 1.2)
    res = []
    for P, N, T in arrs:
        nl = np.linalg.norm(N, axis=1); ok = nl > 0.2
        n = np.where(ok[:, None], N / np.maximum(nl[:, None], 1e-9), np.array([0, 1., 0]))
        up = np.where(np.abs(n[:, 1:2]) < 0.9, np.array([0, 1., 0]), np.array([1., 0, 0]))
        t1 = np.cross(n, up); t1 /= np.linalg.norm(t1, axis=1, keepdims=True); t2 = np.cross(n, t1)
        D = local[None, :, 0:1] * t1[:, None] + local[None, :, 1:2] * t2[:, None] + local[None, :, 2:3] * n[:, None]
        org = P + n * voxel * 1.2
        hit = np.zeros((len(P), rays))
        for s_ in steps:
            q = org[:, None] + D * s_; ix = np.clip(((q - lo) / voxel).astype(int), 0, dims - 1)
            h = occ[ix[..., 0], ix[..., 1], ix[..., 2]]
            hit = np.maximum(hit, h * (1 - s_ / maxd) ** 0.7)
        o = hit.mean(1)
        res.append(np.where(ok, 1 - strength * np.clip(o * 1.5, 0, 1), 1.0))
    return res
