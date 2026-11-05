import struct, zlib, collections
def refpack(d):
    # Sims 4 internal compression (RefPack)
    p=0; flags=d[0]; p=2
    sz=4 if flags&0x80 else 3
    n=int.from_bytes(d[p:p+sz],'big'); p+=sz
    o=bytearray()
    while p<len(d):
        b0=d[p]
        if b0<0x80:
            b1=d[p+1]; pl=b0&3; cl=((b0>>2)&7)+3; off=((b0&0x60)<<3)+b1+1; p+=2
        elif b0<0xC0:
            b1,b2=d[p+1],d[p+2]; pl=b1>>6; cl=(b0&0x3f)+4; off=((b1&0x3f)<<8)+b2+1; p+=3
        elif b0<0xE0:
            b1,b2,b3=d[p+1:p+4]; pl=b0&3; cl=((b0&0xC)<<6)+b3+5; off=((b0&0x10)<<12)+(b1<<8)+b2+1; p+=4
        elif b0<0xFC:
            pl=((b0&0x1f)<<2)+4; cl=0; off=0; p+=1
        else:
            pl=b0&3; cl=0; off=0; p+=1
        o+=d[p:p+pl]; p+=pl
        for _ in range(cl): o.append(o[-off])
        if b0>=0xFC: break
    return bytes(o)
def read(path):
    d=open(path,'rb').read()
    cnt=struct.unpack_from('<I',d,36)[0]; off=struct.unpack_from('<I',d,64)[0]
    p=off; flags=struct.unpack_from('<I',d,p)[0]; p+=4
    const={}
    names=['t','g','ih']
    for i,nm in enumerate(names):
        if flags&(1<<i): const[nm]=struct.unpack_from('<I',d,p)[0]; p+=4
    res=[]
    for _ in range(cnt):
        e={}
        for nm in names:
            if nm in const: e[nm]=const[nm]
            else: e[nm]=struct.unpack_from('<I',d,p)[0]; p+=4
        il,pos,fs,ms=struct.unpack_from('<IIII',d,p); p+=16
        comp=0
        if fs&0x80000000: comp,=struct.unpack_from('<H',d,p); p+=4
        e['inst']=(e['ih']<<32)|il
        raw=d[pos:pos+(fs&0x7fffffff)]
        e['comp']=comp; e['raw']=raw; e['size']=ms
        res.append(e)
    return res
def data(e):
    if e['comp']==0x5A42: return zlib.decompress(e['raw'])
    if e['comp']==0xFFFF: return refpack(e['raw'])
    return e['raw']
