import sys,os; sys.path.insert(0,'/home/claude/tools')
import sf
def load(path):
    if os.path.exists(path): b=open(path,'rb').read()
    else: b=b''.join(open(path+'.split%d'%i,'rb').read() for i in range(8) if os.path.exists(path+'.split%d'%i))
    return sf.parse(path,b)
def gos(d):
    b=d['data']; g={}; t={}
    for pid,off,sz,ti,cid in d['objs']:
        if cid==1:
            r=sf.R(b,off); n=r.i32()
            for _ in range(n): r.i32(); r.i64()
            layer=r.u32(); name=r.str(); tag=r.u16(); act=r.u8()
            g[pid]=(name,act,layer)
        elif cid==4:
            r=sf.R(b,off); r.i32(); go=r.i64()
            q=[r.f32() for _ in range(4)]; p=[r.f32() for _ in range(3)]; s=[r.f32() for _ in range(3)]
            n=r.i32()
            for _ in range(n): r.i32(); r.i64()
            r.i32(); fa=r.i64()
            t[pid]=dict(go=go,q=q,p=p,s=s,father=fa)
    return g,t
