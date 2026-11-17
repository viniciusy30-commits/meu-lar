import sys, numpy as np
sys.path.insert(0, '/home/user/meu-lar/ferramentas')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from etapa118_piscina_clipes import read_clips, make_rt, joints
c = read_clips('/home/user/meu-lar/app/src/main/assets/cute/clips_am5.bin'); rt = make_rt(c[:11])
R, RUN = 0.20, 0.2135
ADV = {15: 0.427, 16: 0.379, 17: 0.429, 18: 0.392}
def tread(x, sg):
    k = np.floor(x / RUN); return k * R if sg > 0 else -k * R
res = {}
fig, axs = plt.subplots(4, 1, figsize=(14, 18))
for ax, ci in zip(axs, (15, 16, 17, 18)):
    sg = 1 if ci in (15, 17) else -1
    T, d = c[ci]; n = len(d); adv = ADV[ci]; sx = 2 * RUN / adv
    J = np.array([joints(rt, d[f]) * 0.01 for f in range(n)])
    feet = (19, 20, 23, 24)
    best = None
    for s0 in np.arange(0, 2 * RUN, 0.01):
        for off in np.arange(-0.25, 0.26, 0.01):
            tot = 0.0
            for rep in range(2):
                for f in range(0, n, 2):
                    x = s0 + (rep + f / (n - 1)) * 2 * RUN
                    ry = sg * R / RUN * x + off
                    fy = J[f, feet, 1] + ry; fx = J[f, feet, 2] * sx + x
                    e = fy - tread(fx, sg)
                    tot += 3 * np.clip(-e, 0, None).sum() + abs(e.min())   # nada abaixo do piso + pe de apoio encostado
            if best is None or tot < best[0]: best = (tot, s0, off)
    _, s0, off = best
    errs = []
    for rep in range(2):
        for f in range(0, n, 2):
            x = s0 + (rep + f / (n - 1)) * 2 * RUN; ry = sg * R / RUN * x + off
            fy = J[f, feet, 1] + ry; fx = J[f, feet, 2] * sx + x; e = fy - tread(fx, sg); errs.append(e.min())
            P = np.stack([J[f, :, 2] * sx + x, J[f, :, 1] + ry], 1); col = plt.cm.viridis(f / n)
            for (a, b) in ((0, 17), (17, 18), (18, 19), (19, 20), (0, 21), (21, 22), (22, 23), (23, 24)): ax.plot([P[a, 0], P[b, 0]], [P[a, 1], P[b, 1]], color=col, lw=0.6)
    for k in range(-2, 12):
        y = k * R * sg; ax.plot([k * RUN, (k + 1) * RUN], [y, y], 'k', lw=1.6); ax.plot([(k + 1) * RUN] * 2, [y, y + sg * R], 'k', lw=1.6)
    e = np.array(errs)
    res[ci] = (round(float(s0), 3), round(float(off), 3), round(float(e.min()) * 100, 1), round(float(np.median(np.abs(e))) * 100, 1))
    ax.set_aspect('equal'); ax.set_xlim(-0.3, 5 * RUN + 0.6); ax.set_title(f'clipe {ci}: fase {s0:.2f} m, altura {off:.2f} m | pior penetracao {e.min()*100:.1f} cm, contato mediano {np.median(np.abs(e))*100:.1f} cm')
plt.tight_layout(); plt.savefig(sys.argv[1], dpi=70); print(res)
