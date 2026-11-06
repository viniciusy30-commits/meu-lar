import struct, numpy as np
def _leb(b,p):
    v=0;s=0
    while True:
        x=b[p];p+=1;v|=(x&0x7f)<<s;s+=7
        if x<0x80:return v,p
def decode(d, mip=0):
    assert d[:8]==b'LRLEV002'
    w,h,mc=struct.unpack_from('<HHI',d,8)
    offs=struct.unpack_from('<%dI'%mc,d,16)
    p=16+4*mc
    N,=struct.unpack_from('<I',d,p)
    pal=np.frombuffer(d,np.uint8,count=4*N,offset=p+4).reshape(N,4)
    ds=p+4+4*N
    ends=list(offs[1:])+[len(d)-ds]
    b=d[ds+offs[mip]:ds+ends[mip]]
    mw,mh=max(1,w>>mip),max(1,h>>mip)
    total=mw*mh
    idx=np.zeros(total,np.uint32)
    pos=0;p=0;L=len(b)
    while p<L and pos<total:
        v,p=_leb(b,p)
        k=v&3;n=v>>2
        if k==1:
            for _ in range(n):
                x,p=_leb(b,p);idx[pos]=x;pos+=1
        elif k==0:
            n=v>>3;x=b[p]|(b[p+1]<<8);p+=2;idx[pos:pos+n]=x;pos+=n
        elif k==2:
            n=v>>3;x=b[p];p+=1;idx[pos:pos+n]=x;pos+=n
        else: raise ValueError('op3')
    im=pal[np.minimum(idx,N-1)]
    if mw>=4 and mh>=4:
        im=im.reshape(mh//4,mw//4,4,4,4).transpose(0,2,1,3,4).reshape(mh,mw,4)
    else:
        im=im.reshape(mh,mw,4)
    return im,pos,total,p,L
