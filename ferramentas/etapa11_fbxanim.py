"""Etapa 11 - leitor de animação FBX (Mixamo) com cinemática direta.

Lê esqueleto (hierarquia, PreRotation, Lcl T/R/S) e curvas de animação de um FBX binário
e devolve, para qualquer tempo, a posição e a rotação MUNDIAL de cada osso.
Usa o leitor fbxr.py do projeto (não precisa de SDK nenhum).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from fbxr import parse

KTIME = 46186158000.0  # unidades FBX por segundo


def _euler(order, rx, ry, rz):
    """Matriz de rotação de ângulos (graus) no padrão FBX (ordem XYZ => Rz*Ry*Rx)."""
    a, b, c = np.radians([rx, ry, rz])
    ca, sa, cb, sb, cc, sc = np.cos(a), np.sin(a), np.cos(b), np.sin(b), np.cos(c), np.sin(c)
    X = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    Y = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    Z = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    if order == 0:
        return Z @ Y @ X
    if order == 1:   # XZY
        return Y @ Z @ X
    if order == 2:   # YZX
        return X @ Z @ Y
    if order == 3:   # YXZ
        return Z @ X @ Y
    if order == 4:   # ZXY
        return Y @ X @ Z
    if order == 5:   # ZYX
        return X @ Y @ Z
    return Z @ Y @ X


def _prop(m, name, default):
    p70 = m.get('Properties70')
    if p70 is None:
        return default
    for p in p70.kids:
        if p.props and p.props[0] == name:
            vals = p.props[4:]
            return vals[0] if len(vals) == 1 else np.array(vals, float)
    return default


class Anim:
    def __init__(self, path):
        r = parse(path)
        ob = r.get('Objects')
        con = r.get('Connections')
        self.models = {}
        for k in ob.kids:
            if k.name == 'Model':
                nm = k.props[1].split('\x00')[0].replace('mixamorig:', '')
                self.models[k.props[0]] = dict(
                    name=nm, id=k.props[0], parent=None,
                    T=np.array(_prop(k, 'Lcl Translation', np.zeros(3)), float),
                    R=np.array(_prop(k, 'Lcl Rotation', np.zeros(3)), float),
                    pre=np.array(_prop(k, 'PreRotation', np.zeros(3)), float),
                    order=int(_prop(k, 'RotationOrder', 0)),
                    curves={})
        curve_nodes = {k.props[0]: k for k in ob.kids if k.name == 'AnimationCurveNode'}
        curves = {k.props[0]: k for k in ob.kids if k.name == 'AnimationCurve'}
        cn_target = {}   # curve node -> (model id, propname)
        cn_curves = {}   # curve node -> {axis: curve}
        for c in con.kids:
            t, a, b = c.props[0], c.props[1], c.props[2]
            if t == 'OO' and a in self.models and b in self.models:
                self.models[a]['parent'] = b
            if t == 'OP' and a in curve_nodes and b in self.models:
                cn_target[a] = (b, c.props[3])
            if t == 'OP' and a in curves and b in curve_nodes:
                cn_curves.setdefault(b, {})[c.props[3]] = curves[a]
        for cid, (mid, pname) in cn_target.items():
            ch = {}
            for ax, cv in cn_curves.get(cid, {}).items():
                kt = cv.get('KeyTime').props[0].astype(np.float64) / KTIME
                kv = cv.get('KeyValueFloat').props[0].astype(np.float64)
                ch[ax[-1]] = (kt, kv)
            self.models[mid]['curves'][pname] = ch
        self.by_name = {m['name']: m for m in self.models.values()}
        # ordem topológica
        self.order = []
        seen = set()

        def visit(i):
            if i in seen:
                return
            p = self.models[i]['parent']
            if p in self.models:
                visit(p)
            seen.add(i)
            self.order.append(i)
        for i in self.models:
            visit(i)
        self.names = [self.models[i]['name'] for i in self.order]
        t0, t1 = 1e9, -1e9
        for m in self.models.values():
            for ch in m['curves'].values():
                for kt, _ in ch.values():
                    t0 = min(t0, kt.min())
                    t1 = max(t1, kt.max())
        self.t0, self.t1 = t0, t1

    def _val(self, m, prop, base, t):
        ch = m['curves'].get(prop)
        out = np.array(base, float)
        if not ch:
            return out
        for i, ax in enumerate('XYZ'):
            if ax in ch:
                kt, kv = ch[ax]
                out[i] = np.interp(t, kt, kv)
        return out

    def local(self, m, t, animated=True):
        T = self._val(m, 'Lcl Translation', m['T'], t) if animated else m['T']
        R = self._val(m, 'Lcl Rotation', m['R'], t) if animated else m['R']
        Rm = _euler(0, *m['pre']) @ _euler(m['order'], *R)
        return T, Rm

    def world(self, t, animated=True):
        """dict nome -> (R 3x3, pos 3) mundiais, no tempo t (s)."""
        W = {}
        for i in self.order:
            m = self.models[i]
            T, Rl = self.local(m, t, animated)
            p = m['parent']
            if p in self.models:
                Rp, Pp = W[self.models[p]['name']]
                W[m['name']] = (Rp @ Rl, Pp + Rp @ T)
            else:
                W[m['name']] = (Rl, T.copy())
        return W


if __name__ == '__main__':
    for f in sys.argv[1:]:
        a = Anim(f)
        print(f, 'tempo', a.t0, a.t1, 'ossos', len(a.names))
        print(a.names)
        W = a.world(0, animated=False)
        for n in ['Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'Spine2', 'Head', 'LeftArm', 'LeftForeArm', 'LeftHand']:
            print(n, np.round(W[n][1], 2))
