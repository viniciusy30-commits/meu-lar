#!/usr/bin/env python3
"""Renderiza a prévia do Dunk High no corpo am5 usando a mesma projeção/rasterização de Thumb.kt."""
from pathlib import Path
import json, math, struct
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "app/src/main/assets/cute"
SKATE = ASSETS / "skate"
OUT = ROOT / "imagens-dunk-high"
OUT.mkdir(exist_ok=True)

def read_cup(path):
    b = path.read_bytes()
    if b[:4] != b"CUP1":
        raise ValueError(f"CUP1 inválido: {path}")
    nv, ni, _ = struct.unpack_from("<III", b, 4)
    dt = np.dtype([
        ("pos", "<f4", (3,)), ("nor", "<f4", (3,)), ("uv", "<f4", (2,)),
        ("rgba", "u1", (4,)), ("bi", "u1", (4,)), ("bw", "u1", (4,))
    ])
    v = np.frombuffer(b, dtype=dt, count=nv, offset=16)
    idx = np.frombuffer(b, dtype="<u2", count=ni, offset=16 + nv * 44).reshape(-1, 3).astype(np.int32)
    if idx.size and int(idx.max()) >= nv:
        raise ValueError(f"Índice fora da malha: {path}")
    hide = np.empty(0, dtype=np.int32)
    if struct.unpack_from("<I", b, 12)[0] & 1:
        off = 16 + nv * 44 + ni * 2
        nh = struct.unpack_from("<I", b, off)[0]
        hide = np.frombuffer(b, dtype="<u2", count=nh, offset=off + 4).astype(np.int32)
    return {"pos": v["pos"].copy(), "nor": v["nor"].copy(), "uv": v["uv"].copy(), "idx": idx, "hide": hide}

def render(parts, yaw=-0.62, pitch=0.30, size=256):
    ss = 2
    W = size * ss
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    projected = []
    for part in parts:
        pos = part["mesh"]["pos"]
        x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        y2 = y * cp - z1 * sp
        z2 = y * sp + z1 * cp
        projected.append(np.column_stack((x1, y2, z2)))

    xs, ys = [], []
    for i, part in enumerate(parts):
        if part.get("support"):
            continue
        used = np.unique(part["mesh"]["idx"].ravel())
        xs.extend(projected[i][used, 0])
        ys.extend(projected[i][used, 1])
    if not xs or not ys:
        raise ValueError("A malha não tem triângulos para enquadrar.")
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = max(x1 - x0, y1 - y0) * 1.12
    scale = W / span
    cx, cyy = (x0 + x1) / 2, (y0 + y1) / 2

    color = np.zeros((W, W, 4), dtype=np.uint8)
    zbuf = np.full((W, W), -1e9, dtype=np.float32)
    lx, ly, lz = 0.35, 0.55, 0.76
    light_len = math.sqrt(lx * lx + ly * ly + lz * lz)

    for i, part in enumerate(parts):
        mesh = part["mesh"]
        P = projected[i]
        n0 = mesh["nor"]
        nx = n0[:, 0] * cy + n0[:, 2] * sy
        nz = -n0[:, 0] * sy + n0[:, 2] * cy
        N = np.column_stack((nx, n0[:, 1] * cp - nz * sp, n0[:, 1] * sp + nz * cp))
        sx = W / 2 + (P[:, 0] - cx) * scale
        syy = W / 2 - (P[:, 1] - cyy) * scale
        tex = part.get("tex")
        for tri in mesh["idx"]:
            a, b, c = map(int, tri)
            xa, xb, xc = sx[a], sx[b], sx[c]
            ya, yb, yc = syy[a], syy[b], syy[c]
            mnx = max(0, int(math.floor(min(xa, xb, xc))))
            mxx = min(W - 1, int(math.ceil(max(xa, xb, xc))))
            mny = max(0, int(math.floor(min(ya, yb, yc))))
            mxy = min(W - 1, int(math.ceil(max(ya, yb, yc))))
            if mxx < mnx or mxy < mny:
                continue
            den = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
            if abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(mnx, mxx + 1) + 0.5, np.arange(mny, mxy + 1) + 0.5)
            wa = ((yb - yc) * (gx - xc) + (xc - xb) * (gy - yc)) / den
            wb = ((yc - ya) * (gx - xc) + (xa - xc) * (gy - yc)) / den
            wc = 1 - wa - wb
            mask = (wa >= -0.001) & (wb >= -0.001) & (wc >= -0.001)
            z = wa * P[a, 2] + wb * P[b, 2] + wc * P[c, 2]
            subz = zbuf[mny:mxy + 1, mnx:mxx + 1]
            mask &= z > subz
            if not mask.any():
                continue
            if tex is not None:
                uv = mesh["uv"]
                u = wa * uv[a, 0] + wb * uv[b, 0] + wc * uv[c, 0]
                v = wa * uv[a, 1] + wb * uv[b, 1] + wc * uv[c, 1]
                tx = np.clip((u * tex.shape[1]).astype(int), 0, tex.shape[1] - 1)
                ty = np.clip((v * tex.shape[0]).astype(int), 0, tex.shape[0] - 1)
                px = tex[ty, tx].copy()
                if part.get("cut"):
                    mask &= px[:, :, 3] >= 115
            else:
                rgba = np.array(part.get("color", (227, 191, 162, 255)), dtype=np.uint8)
                px = np.broadcast_to(rgba, (mask.shape[0], mask.shape[1], 4)).copy()
            nnx = wa * N[a, 0] + wb * N[b, 0] + wc * N[c, 0]
            nny = wa * N[a, 1] + wb * N[b, 1] + wc * N[c, 1]
            nnz = wa * N[a, 2] + wb * N[b, 2] + wc * N[c, 2]
            nl = np.maximum(np.sqrt(nnx * nnx + nny * nny + nnz * nnz), 1e-6)
            diffuse = np.abs(nnx * lx + nny * ly + nnz * lz) / (nl * light_len)
            shade = np.minimum(0.55 + 0.55 * diffuse, 1.1)
            px[:, :, :3] = np.clip(px[:, :, :3].astype(np.float32) * shade[:, :, None], 0, 255).astype(np.uint8)
            subc = color[mny:mxy + 1, mnx:mxx + 1]
            subc[mask] = px[mask]
            subz[mask] = z[mask]

    # Mesmo downsample 2x2 e contorno fino usados em Thumb.kt.
    out = np.zeros((size, size, 4), dtype=np.uint8)
    for y in range(size):
        for x in range(size):
            block = color[y * ss:y * ss + ss, x * ss:x * ss + ss]
            al = block[:, :, 3]
            valid = al > 0
            count = int(valid.sum())
            if count:
                out[y, x, 3] = int(round(al.sum() / (ss * ss)))
                out[y, x, :3] = np.rint(block[:, :, :3][valid].mean(axis=0)).astype(np.uint8)
    result = out.copy()
    alpha = out[:, :, 3]
    for y in range(size):
        for x in range(size):
            if alpha[y, x] > 40:
                continue
            near = 0
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < size and 0 <= yy < size and alpha[yy, xx] > 200:
                        near += 1
            if near:
                result[y, x] = (75, 99, 120, min(150, 40 + near * 14))
    return Image.fromarray(result, "RGBA")

def main():
    body = read_cup(ASSETS / "p_body_am5.bin")
    shoe = read_cup(SKATE / "dunk_high_am5.cup")
    # Reproduz a máscara que CuteChar.rebuildActive aplica ao corpo quando o tênis está vestido.
    if len(shoe["hide"]):
        keep = np.ones(len(body["idx"]), dtype=bool)
        keep[shoe["hide"]] = False
        body["idx"] = body["idx"][keep]
    tex = np.asarray(Image.open(SKATE / "dunk_high_am5.png").convert("RGBA"))
    thumb = render([
        {"mesh": body, "color": (227, 191, 162, 255), "support": True},
        {"mesh": shoe, "tex": tex}
    ], size=256)
    thumb.save(ASSETS / "thumbs/dunk_high_am5.png")
    thumb.save(OUT / "thumbnail.png")
    render([
        {"mesh": body, "color": (227, 191, 162, 255), "support": True},
        {"mesh": shoe, "tex": tex}
    ], yaw=0.0, pitch=0.04, size=512).save(OUT / "front.png")
    render([
        {"mesh": body, "color": (227, 191, 162, 255), "support": True},
        {"mesh": shoe, "tex": tex}
    ], yaw=1.5708, pitch=0.04, size=512).save(OUT / "side.png")
    render([
        {"mesh": body, "color": (227, 191, 162, 255), "support": True},
        {"mesh": shoe, "tex": tex}
    ], yaw=-0.62, pitch=0.30, size=512).save(OUT / "three-quarter.png")

    pos = shoe["pos"]
    report = {
        "slot": "feet",
        "vertices": int(len(pos)),
        "triangles": int(len(shoe["idx"])),
        "bounds_cm": {"x": [float(pos[:, 0].min()), float(pos[:, 0].max())],
                      "y": [float(pos[:, 1].min()), float(pos[:, 1].max())],
                      "z": [float(pos[:, 2].min()), float(pos[:, 2].max())]},
        "uv_bounds": {"u": [float(shoe["uv"][:, 0].min()), float(shoe["uv"][:, 0].max())],
                      "v": [float(shoe["uv"][:, 1].min()), float(shoe["uv"][:, 1].max())]},
        "texture": [int(tex.shape[1]), int(tex.shape[0])],
        "texture_alpha_pixels": int(np.sum(tex[:, :, 3] < 255)),
        "hidden_body_triangles": int(len(shoe["hide"])),
        "body_triangles_after_hide": int(len(body["idx"])),
        "render": "OK"
    }
    (OUT / "diagnostico.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, ensure_ascii=False))
    print("DUNK_HIGH_RENDER_OK")

if __name__ == "__main__":
    main()
