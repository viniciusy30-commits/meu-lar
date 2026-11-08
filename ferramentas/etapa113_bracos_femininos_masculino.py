#!/usr/bin/env python3
"""Etapa 113 — aplica ao corpo masculino os mesmos movimentos de braços/mãos do feminino.

Preserva as animações masculinas de tronco, cabeça e pernas. Para clavículas, braços,
punhos e dedos, transfere as rotações locais dos clipes femininos para o rig masculino
e recalcula as posições por cinemática direta usando os comprimentos masculinos.

Uso: python3 ferramentas/etapa113_bracos_femininos_masculino.py app/src/main/assets/cute
"""
from __future__ import annotations
import argparse
import math
import struct
from pathlib import Path
import numpy as np

SCALE = 0.0082  # escala uniforme das matrizes CLP1 para a malha em centímetros
ARM_BONES = set([9, 10, 11, 12, 13, 14, 15, 16] + list(range(25, 55)))
PARENTS = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 5, 9, 10, 11, 5, 13, 14, 15, 0, 17, 18, 19, 0, 21, 22, 23, 12, 25, 26, 12, 28, 29, 12, 31, 32, 12, 34, 35, 12, 37, 38, 16, 40, 41, 16, 43, 44, 16, 46, 47, 16, 49, 50, 16, 52, 53]


def read_clp(path: Path):
    raw = path.read_bytes()
    if raw[:4] != b"CLP1":
        raise ValueError(f"Cabeçalho CLP1 inválido: {path}")
    nb, nc = struct.unpack_from("<ii", raw, 4)
    off = 12
    clips = []
    for _ in range(nc):
        length, nf = struct.unpack_from("<fi", raw, off)
        off += 8
        count = nf * nb * 12
        data = np.frombuffer(raw, dtype="<f4", count=count, offset=off).copy().reshape(nf, nb, 3, 4)
        off += count * 4
        clips.append((length, data))
    if off != len(raw):
        raise ValueError(f"Bytes excedentes/truncados em {path}: {off}/{len(raw)}")
    return nb, clips


def write_clp(path: Path, nb: int, clips):
    out = bytearray(b"CLP1" + struct.pack("<ii", nb, len(clips)))
    for length, data in clips:
        d = np.asarray(data, dtype="<f4", order="C")
        out += struct.pack("<fi", float(length), int(d.shape[0]))
        out += d.tobytes(order="C")
    path.write_bytes(out)


def read_rig(cute: Path):
    skel = {}
    for line in (cute / "skel_s4.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split("|")
        skel[p[1]] = np.asarray([float(x) for x in p[3:6]], dtype=np.float64)
    bodyrig = {}
    for line in (cute / "bodyrig.txt").read_text().splitlines():
        if "|" not in line:
            continue
        key, values = line.split("|", 1)
        bodyrig[key] = np.asarray([float(x) for x in values.split(",")], dtype=np.float64)
    return skel, bodyrig


def joints55(cute: Path, group: str):
    skel, bodyrig = read_rig(cute)
    br = bodyrig[group + "5"]
    names = ["b__L_UpperArm__", "b__L_Forearm__", "b__L_Hand__", "b__L_Thigh__", "b__L_Calf__", "b__L_Foot__"]
    target = np.asarray([br[0:3], br[3:6], br[6:9], br[9:12], br[12:15], br[15:18]])
    source = np.asarray([skel[n] for n in names])
    sx = source.mean(axis=0)
    sy = target.mean(axis=0)
    scale = float(np.sum((source - sx) * (target - sy)) / np.sum((source - sx) ** 2))
    offset = sy - scale * sx
    w = lambda name: skel[name] * scale + offset

    J = np.zeros((55, 3), dtype=np.float64)
    J[0] = w("b__Pelvis__")
    J[2] = w("b__Spine0__")
    J[1] = (J[0] + J[2]) * 0.5
    J[3] = (w("b__Spine0__") + w("b__Spine1__")) * 0.5
    J[4] = w("b__Spine1__")
    J[5] = w("b__Spine2__")
    J[6] = w("b__Neck__")
    J[8] = w("b__Head__")
    J[7] = (J[6] + J[8]) * 0.5
    for side, off, leg0, finger0 in (("L", 0, 17, 25), ("R", 4, 21, 40)):
        J[9 + off] = w(f"b__{side}_Clavicle__")
        J[10 + off] = w(f"b__{side}_UpperArm__")
        J[11 + off] = w(f"b__{side}_Forearm__")
        J[12 + off] = w(f"b__{side}_Hand__")
        J[leg0] = w(f"b__{side}_Thigh__")
        J[leg0 + 1] = w(f"b__{side}_Calf__")
        J[leg0 + 2] = w(f"b__{side}_Foot__")
        J[leg0 + 3] = w(f"b__{side}_Toe__")
        for fi, finger in enumerate(("Index", "Mid", "Ring", "Pinky", "Thumb")):
            for joint in range(3):
                J[finger0 + fi * 3 + joint] = w(f"b__{side}_{finger}{joint}__")
    return J, scale, offset


def transform_clip(female: np.ndarray, male: np.ndarray, Jm: np.ndarray):
    """Copia rotações locais femininas para os ossos de braço do clipe masculino."""
    nf = male.shape[0]
    if female.shape != male.shape:
        raise ValueError(f"Clipes incompatíveis: feminino {female.shape}, masculino {male.shape}")

    Af = female[:, :, :, :3].astype(np.float64) / SCALE
    Am = male[:, :, :, :3].astype(np.float64) / SCALE
    tm = male[:, :, :, 3].astype(np.float64) / SCALE
    Pm = np.einsum("fbxy,by->fbx", Am, Jm) + tm

    Anew = Am.copy()
    Pnew = Pm.copy()
    tnew = tm.copy()

    for b, parent in enumerate(PARENTS):
        if b not in ARM_BONES:
            continue
        if parent < 0:
            raise ValueError(f"Osso de braço sem pai: {b}")
        # Matriz local = inversa do pai feminino * matriz do osso feminino.
        # A inversa (em vez de transposta) também preserva o pequeno resíduo de
        # interpolação do último quadro dos clipes, sem acumular torção nos dedos.
        local = np.linalg.inv(Af[:, parent]) @ Af[:, b]
        # A mesma rotação local aplicada sobre a orientação do pai masculino.
        Anew[:, b] = np.einsum("fij,fjk->fik", Anew[:, parent], local)
        # Recalcula a junta usando os comprimentos de osso masculinos.
        offset = Jm[b] - Jm[parent]
        Pnew[:, b] = Pnew[:, parent] + np.einsum("fij,j->fi", Anew[:, parent], offset)
        tnew[:, b] = Pnew[:, b] - np.einsum("fij,j->fi", Anew[:, b], Jm[b])

    result = male.copy()
    for b in sorted(ARM_BONES):
        result[:, b, :, :3] = (Anew[:, b] * SCALE).astype(np.float32)
        result[:, b, :, 3] = (tnew[:, b] * SCALE).astype(np.float32)
    return result


def validate(female, male_before, male_after, Jm, clip_index):
    if not np.isfinite(male_after).all():
        raise AssertionError(f"NaN/Inf no clipe {clip_index}")
    Af = female[:, :, :, :3].astype(np.float64) / SCALE
    Am = male_after[:, :, :, :3].astype(np.float64) / SCALE
    max_local = 0.0
    max_len = 0.0
    for b, parent in enumerate(PARENTS):
        if b not in ARM_BONES:
            if not np.array_equal(male_after[:, b], male_before[:, b]):
                raise AssertionError(f"Osso não solicitado foi alterado: {b} no clipe {clip_index}")
            continue
        local_f = np.linalg.inv(Af[:, parent]) @ Af[:, b]
        local_m = np.linalg.inv(Am[:, parent]) @ Am[:, b]
        max_local = max(max_local, float(np.max(np.abs(local_f - local_m))))
        # As posições das juntas devem manter exatamente o comprimento do rig masculino.
        tm = male_after[:, :, :, 3].astype(np.float64) / SCALE
        P = np.einsum("fbxy,by->fbx", Am, Jm) + tm
        got = np.linalg.norm(P[:, b] - P[:, parent], axis=1)
        want = float(np.linalg.norm(Jm[b] - Jm[parent]))
        max_len = max(max_len, float(np.max(np.abs(got - want))))
    if max_local > 2e-5:
        raise AssertionError(f"Rotações locais divergiram ({max_local}) no clipe {clip_index}")
    if max_len > 5e-2:
        raise AssertionError(f"Comprimento de osso alterado ({max_len} cm) no clipe {clip_index}")
    return max_local, max_len


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("assets", type=Path, help="app/src/main/assets/cute")
    ap.add_argument("--out", type=Path, default=None, help="pasta de saída; por padrão sobrescreve clips_am5.bin")
    args = ap.parse_args()
    cute = args.assets.resolve()
    out = (args.out.resolve() if args.out else cute)
    out.mkdir(parents=True, exist_ok=True)

    nb_f, female = read_clp(cute / "clips_af5.bin")
    nb_m, male = read_clp(cute / "clips_am5.bin")
    if nb_f != 55 or nb_m != 55 or len(female) != len(male):
        raise ValueError("Os dois conjuntos precisam ter 55 ossos e a mesma quantidade de clipes")
    Jm, k, off = joints55(cute, "am")
    new_clips = []
    for ci, ((lf, df), (lm, dm)) in enumerate(zip(female, male)):
        if df.shape != dm.shape or abs(lf - lm) > 1e-5:
            raise ValueError(f"Duração/quadros diferentes no clipe {ci}")
        new = transform_clip(df, dm, Jm)
        max_local, max_len = validate(df, dm, new, Jm, ci)
        new_clips.append((lm, new))
        print(f"clip {ci:02d}: {new.shape[0]:3d} quadros | erro rotação local={max_local:.2e} | erro osso={max_len:.3e} cm")

    target = out / "clips_am5.bin"
    write_clp(target, nb_m, new_clips)
    # Reabre para validar o cabeçalho e o tamanho final.
    nb2, check = read_clp(target)
    if nb2 != 55 or len(check) != len(male):
        raise AssertionError("CLP1 de saída inválido")
    print(f"OK: {target} ({target.stat().st_size} bytes); escala rig masculino={k:.6f}; offset={off.round(4).tolist()}")


if __name__ == "__main__":
    main()
