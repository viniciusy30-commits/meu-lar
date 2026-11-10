import sys,struct; sys.path.insert(0,'/home/claude/tools')
import sf,numpy as np
FMT={0:('f4',4),1:('f2',2),2:('u1',1),3:('i1',1),4:('u2',2),5:('i2',2),6:('u4',4),7:('i4',4)}
def mesh(f,off,sz):
    b=f['data']; r=sf.R(b,off); m={}
    m['name']=r.str()
    n=r.i32(); subs=[]
    for _ in range(n):
        fb=r.u32(); ic=r.u32(); top=r.i32(); bv=r.u32(); fv=r.u32(); vc=r.u32()
        r.raw(24)
        subs.append(dict(fb=fb,ic=ic,top=top,bv=bv,fv=fv,vc=vc))
    m['subs']=subs
    for _ in range(9):
        v=r.u32()
        assert v==0,'skinned/shapes mesh '+m['name']
    r.u8(); r.u8(); r.u8(); r.u8()   # compression, readable, keepV, keepI
    m['compressed']=b[r.p-4]
    m['ifmt']=r.i32()
    n=r.u32(); m['ib']=r.raw(n); r.align()
    m['vcount']=r.u32()
    nc=r.u32(); ch=[]
    for _ in range(nc): ch.append((r.u8(),r.u8(),r.u8(),r.u8()))
    m['ch']=ch
    n=r.u32(); m['vd']=r.raw(n); r.align()
    m['pos_after_vd']=r.p
    return m
def stream_layout(m):
    ch=m['ch']; vc=m['vcount']; streams={}
    for i,(st,off,fmt,dim) in enumerate(ch):
        if dim&0xF==0: continue
        streams.setdefault(st,[]).append((i,off,fmt,dim&0xF))
    pos=0; out={}
    for st in sorted(streams):
        items=streams[st]; stride=0
        for i,off,fmt,dim in items: stride=max(stride,off+dim*FMT[fmt][1])
        pos=(pos+15)&~15
        out[st]=(pos,stride,items); pos+=stride*vc
    return out
def decode(m,vd):
    vc=m['vcount']; res={}
    for st,(base,stride,items) in stream_layout(m).items():
        buf=np.frombuffer(vd,dtype=np.uint8,count=stride*vc,offset=base).reshape(vc,stride)
        for i,off,fmt,dim in items:
            dt,sz=FMT[fmt]
            a=np.ascontiguousarray(buf[:,off:off+dim*sz]).view('<'+dt).reshape(vc,dim)
            if fmt==2: a=a.astype(np.float32)/255.0
            elif fmt==1: a=a.astype(np.float32)
            else: a=a.astype(np.float32) if fmt==0 else a
            res[i]=a
    return res
def indices(m,s):
    w=2 if m['ifmt']==0 else 4
    a=np.frombuffer(m['ib'],dtype='<u2' if w==2 else '<u4',count=s['ic'],offset=s['fb'])
    if s['top']!=0: return None
    return a.reshape(-1,3)
def tex(f,off,sz):
    b=f['data']; r=sf.R(b,off); t={}
    t['name']=r.str(); r.u8(); r.u8(); r.align()
    t['w']=r.i32(); t['h']=r.i32(); t['csize']=r.u32(); r.i32()
    t['fmt']=r.i32(); t['mips']=r.i32()
    r.raw(16); t['imgc']=r.i32(); t['dim']=r.i32()
    r.raw(4*7); t['cs']=r.i32()
    n=r.u32(); r.raw(n); r.align()
    n=r.u32(); t['dlen']=n; t['data']=r.raw(n); r.align()
    t['so']=r.u64(); t['ss']=r.u32(); t['sp']=r.str()
    return t
def material(f,off,sz):
    b=f['data']; r=sf.R(b,off); m={}
    m['name']=r.str(); r.i32(); r.i64()           # shader
    for _ in range(2):
        n=r.i32()
        for _ in range(n): r.str()
    r.u32(); r.u8(); r.u8(); r.align(); m['queue']=r.i32()
    n=r.i32()
    for _ in range(n): r.str(); r.str()            # tag map
    n=r.i32()
    for _ in range(n): r.str()                     # disabled passes
    n=r.i32(); tex={}
    for _ in range(n):
        k=r.str(); fid=r.i32(); pid=r.i64(); r.raw(16); tex[k]=(fid,pid)
    m['tex']=tex
    n=r.i32(); ints={}
    for _ in range(n): k=r.str(); ints[k]=r.i32()
    n=r.i32(); fl={}
    for _ in range(n): k=r.str(); fl[k]=r.f32()
    n=r.i32(); col={}
    for _ in range(n): k=r.str(); col[k]=tuple(r.f32() for _ in range(4))
    m['ints']=ints; m['floats']=fl; m['colors']=col
    return m
def renderer_mats(d,off,sz,chk):
    """acha o vetor m_Materials (contagem + PPtrs) dentro do MeshRenderer"""
    b=d['data']; end=off+sz
    for p in range(off+12,end-16,4):
        n=struct.unpack_from('<i',b,p)[0]
        if not (1<=n<=16) or p+4+n*12>end: continue
        ok=True; out=[]
        for k in range(n):
            fid,pid=struct.unpack_from('<iq',b,p+4+k*12)
            if pid==0 or not chk(fid,pid): ok=False; break
            out.append((fid,pid))
        if ok: return out,p
    return None,None
