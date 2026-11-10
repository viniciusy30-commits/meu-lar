import export,scene,numpy as np,math
from collections import defaultdict
S=np.diag([1,1,-1.,1])
def classify(level):
    d=export.F('level%d'%level); g,t=scene.gos(d); goT={v['go']:k for k,v in t.items()}
    def path(tid):
        p=[]
        while True:
            v=t[tid]; p.append(g[v['go']][0].split(' (')[0])
            if v['father'] not in t: break
            tid=v['father']
        return p[::-1]
    out=[]
    for it in export.scene_items('level%d'%level):
        p=path(goT[it['go']]); it['path']=p; it['M']=S@it['W']@S; out.append(it)
    return out
def bbox(its):
    import numpy as np
    pts=[it['M'][:3,3] for it in its]; a=np.array(pts); return a.min(0).round(1),a.max(0).round(1)
if __name__=='__main__':
    import sys
    its=classify(int(sys.argv[1]))
    grp=defaultdict(list)
    for it in its: grp[it['path'][0]+('/'+it['path'][1] if len(it['path'])>1 and it['path'][0] in('HouseRoot','EnvironmentRoot') else '')].append(it)
    for k,v in grp.items(): 
        if len(v)>1 or k.startswith('House'): print('%-34s n=%4d'%(k,len(v)),*bbox(v))
    ex=[it for it in its if it['name'].startswith('road_car_exit')]
    for e in ex: print('exit',e['M'][:3,3].round(1),round(math.degrees(math.atan2(e['M'][0,2],e['M'][0,0])),0),e['path'][:2])
