import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa3d import Viewer
pre = sys.argv[1]; v = Viewer(); O = json.load(open('out/orla.json')); outs = []
def add(name, eye, at):
    o = f'{pre}_{name}.png'; v.shot(o, eye, at, w=960, h=600); outs.append(o)
pa = O['paths'][3]; x, z, sx, sz = pa['x'], pa['z'], pa['sx'], pa['sz']; y = v.ground_y(x, z)
tx, tz = -sz, sx
add('travessia', (x - sx * 30 + tx * 25, y + 14, z - sz * 30 + tz * 25), (x + sx * 10, y, z + sz * 10))
add('travessia_chao', (x - sx * 14 + tx * 4, y + 1.8, z - sz * 14 + tz * 4), (x + sx * 20, y + 1, z + sz * 20))
p = O['piers'][0]; x, z = p['x'], p['z']; dx, dz = p['dx'], p['dz']
add('pier', (x - dx * 10 + dz * 70, 12, z - dz * 10 - dx * 70), (x + dx * 60, 1, z + dz * 60))
s = O['stairs'][5]; x, z = s['x'], s['z']; dx, dz = s['dx'], s['dz']
add('escada', (x + dx * 18 + dz * 10, 4, z + dz * 18 - dx * 10), (x, 1.8, z))
add('orla_alto', (x + dx * 60 - dz * 90, 45, z + dz * 60 + dx * 90), (x - dx * 30, 2, z - dz * 30))
v.run(); print(' '.join(outs))
