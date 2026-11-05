import struct, numpy as np
def parse(b):
    p=0
    # RCOL header
    ver,pub,unk,ext,intc=struct.unpack_from('<5I',b,0); p=20
    p+=intc*16 if False else 0
    # internal TGIs (instance u64, type, group)
    p+= (intc+ext)*16
    p+= intc*8  # chunk positions
    i=b.find(b'GEOM')
    p=i+4
    v,tgo,tgs,emb=struct.unpack_from('<4I',b,p); p+=16
    if emb:
        sz=struct.unpack_from('<I',b,p)[0]; p+=4+sz
    mg,so,nv,fc=struct.unpack_from('<4I',b,p); p+=16
    fmts=[]
    for _ in range(fc):
        dt,st,bs=struct.unpack_from('<IIB',b,p); p+=9; fmts.append((dt,st,bs))
    stride=sum(f[2] for f in fmts)
    raw=b[p:p+nv*stride]; p+=nv*stride
    out={'uv':[]}
    off=0
    for dt,st,bs in fmts:
        col=np.frombuffer(raw,dtype=np.uint8).reshape(nv,stride)[:,off:off+bs].copy()
        if dt in(1,2,6): a=col.view('<f4').reshape(nv,3)
        elif dt==3: a=col.view('<f4').reshape(nv,2)
        elif dt in(4,5): a=col
        else: a=col
        k={1:'pos',2:'nor',4:'bi',5:'bw',6:'tan',7:'tag',10:'vid'}.get(dt)
        if dt==3: out['uv'].append(a)
        elif k: out[k]=a
        off+=bs
    ic,=struct.unpack_from('<I',b,p); p+=4
    bpi=b[p]; p+=1
    ni,=struct.unpack_from('<I',b,p); p+=4
    idx=np.frombuffer(b[p:p+ni*bpi],dtype='<u2' if bpi==2 else '<u4').reshape(-1,3); p+=ni*bpi
    out['idx']=idx; out['ver']=v; out['fmts']=fmts
    # bones at end: last section; find via tgi offset region is complex; parse tail
    return out
    sk,=struct.unpack_from('<I',b,p); p+=4
    if v>=0x0C:
        n,=struct.unpack_from('<I',b,p); p+=4
        for _ in range(n):
            p+=4; c,=struct.unpack_from('<I',b,p); p+=4+c*8
    if v>=0x0D:
        n,=struct.unpack_from('<I',b,p); p+=4+n*6
    n,=struct.unpack_from('<I',b,p); p+=4
    for _ in range(n):
        p+=4+3*2+3*4+2*4+3*4+1
        if v>=0x0C:
            pass
        # slotray layout uncertain; give up if nonzero
        raise Exception('slotrays %d'%n)
    nb,=struct.unpack_from('<I',b,p); p+=4
    out['bones']=list(struct.unpack_from('<%dI'%nb,b,p))
    return out
