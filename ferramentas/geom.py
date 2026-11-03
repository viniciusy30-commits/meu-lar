import struct, numpy as np
def parse_geom(b):
    o=b.find(b'GEOM'); b=b[o:]
    p=4
    ver,tgio,tgis=struct.unpack_from('<III',b,p); p+=12
    shader=struct.unpack_from('<I',b,p)[0]; p+=4
    mtnf=None
    if shader!=0:
        sz=struct.unpack_from('<I',b,p)[0]; p+=4
        mtnf=b[p:p+sz]; p+=sz
    merge,sortord,nv,nfmt=struct.unpack_from('<IIII',b,p); p+=16
    fmts=[]
    for _ in range(nfmt):
        dt,st,bpe=struct.unpack_from('<IIB',b,p); p+=9
        fmts.append((dt,st,bpe))
    verts={k:[] for k in [(a,s) for a,s,_ in fmts]}
    for i in range(nv):
        for dt,st,bpe in fmts:
            verts[(dt,st)].append(b[p:p+bpe]); p+=bpe
    nsub=struct.unpack_from('<I',b,p)[0]; p+=4
    bpf=b[p]; p+=1
    nfp=struct.unpack_from('<I',b,p)[0]; p+=4
    idx=np.frombuffer(b[p:p+nfp*bpf],dtype='<u2' if bpf==2 else '<u4'); p+=nfp*bpf
    return dict(ver=ver,shader=shader,mtnf=mtnf,nv=nv,fmts=fmts,verts=verts,idx=idx,rest=p,raw=b)
def arrays(G):
    V=G['verts']
    pos=np.array([struct.unpack('<3f',x) for x in V[(1,1)]],np.float32)
    nor=np.array([struct.unpack('<3f',x) for x in V[(2,1)]],np.float32)
    uv=np.array([struct.unpack('<2f',x) for x in V[(3,1)]],np.float32)
    bi=np.array([list(x) for x in V[(4,2)]],np.uint8) if (4,2) in V else None
    bw=np.array([list(x) for x in V[(5,2)]],np.uint8) if (5,2) in V else None
    idx=G['idx'].reshape(-1,3).astype(np.int64)
    return pos,nor,uv,bi,bw,idx
