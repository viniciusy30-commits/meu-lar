import sys,struct,collections
sys.path.insert(0,'/home/claude/proj/codigo/ferramentas'); sys.path.insert(0,'/home/claude/proj/codigo/ferramentas/sims4')
import dbpf,geom,numpy as np
PK='/home/claude/sk/GoldFish Autumn Grace.package'
r=dbpf.read(PK)
print(collections.Counter(hex(e['t']) for e in r))
for e in r:
    if e['t']==0x015A1849:
        raw=dbpf.data(e); g=geom.parse(raw); p=g['pos']
        print('GEOM',hex(e['g']),hex(e['inst']),len(p),len(g['idx']),p.min(0).round(3),p.max(0).round(3),'uvsets',len(g['uv']),'ver',hex(g['ver']))
for e in r:
    if e['t'] in (0x3453CF95,0xB2D882,0xBA856C78): d=dbpf.data(e); print('tex',hex(e['t']),hex(e['inst']&0xffffffff),len(d),d[:8])
print(sum(1 for e in r if e['t']==0x034AEECB),'CASP')
