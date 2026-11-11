import pickle,numpy as np,math,collections
from scipy.spatial import cKDTree
st=pickle.load(open('state5.pkl','rb'));E=st['edges'];N=st['nodes']
# 1) ruas coladas sem ligação
pts=[];own=[]
for i,e in enumerate(E):
    if e['elev']: continue
    P=e['pts']
    for a,b in zip(P[:-1],P[1:]):
        L=np.hypot(*(b-a));n=max(1,int(L/6))
        for t in np.linspace(0,1,n,endpoint=False): pts.append(a+(b-a)*t);own.append(i)
pts=np.array(pts);own=np.array(own);T=cKDTree(pts);bad=collections.Counter()
nodes_of=[{e['a'],e['b']} for e in E]
for i,j in T.query_pairs(13.0):
    a,b=own[i],own[j]
    if a==b: continue
    if nodes_of[a]&nodes_of[b]: 
        # vizinhas que compartilham nó: só conta se longe do nó (>40 m)
        sh=list(nodes_of[a]&nodes_of[b])[0];c=np.array(N[sh])
        if np.hypot(*(pts[i]-c))<45: continue
    bad[(min(a,b),max(a,b))]+=1
print('pares de ruas coladas (<13 m) sem ligação:',[(E[a]['name'],E[b]['name'],n) for (a,b),n in bad.most_common(8) if n>3])
# 2) ângulos nos cruzamentos
inc=collections.defaultdict(list)
for e in E:
    if e['elev']: continue
    P=e['pts']
    inc[e['a']].append((P[min(3,len(P)-1)]-P[0]));inc[e['b']].append((P[max(len(P)-4,0)]-P[-1]))
ac=0
for k,L in inc.items():
    if len(L)<3: continue
    for x in range(len(L)):
        for y in range(x+1,len(L)):
            c=float(L[x]@L[y]/(np.hypot(*L[x])*np.hypot(*L[y])+1e-9))
            if c>0.80: ac+=1
print('cruzamentos com ângulo <37 graus:',ac)
# 3) grau e trechos curtos
deg=collections.Counter()
for e in E: deg[e['a']]+=1;deg[e['b']]+=1
print('graus:',sorted(collections.Counter(deg.values()).items()))
sh=[(e['name'],round(e['L'])) for e in E if e['L']<30 and not e['elev']]
print('trechos <30 m:',len(sh),sh[:8])
# 4) inclinação máxima das ruas
mx=0;worst=None
for e in E:
    P=e['pts'];z=e['z'];d=np.hypot(*np.diff(P,axis=0).T);s=np.abs(np.diff(z))/np.maximum(d,1e-3)
    if len(s) and s.max()>mx: mx=s.max();worst=e['name']
print('maior inclinação de rua: %.1f%% (%s)'%(mx*100,worst))
