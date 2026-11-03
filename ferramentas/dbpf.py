import struct, zlib, sys
def read_index(path):
    d=open(path,'rb').read()
    assert d[:4]==b'DBPF'
    count=struct.unpack_from('<I',d,36)[0]
    idxpos=struct.unpack_from('<I',d,64)[0]
    if idxpos==0: idxpos=struct.unpack_from('<I',d,40)[0]
    flags=struct.unpack_from('<I',d,idxpos)[0]; p=idxpos+4
    const=[0]*6
    for i in range(3):
        if flags&(1<<i):
            const[i]=struct.unpack_from('<I',d,p)[0]; p+=4
    ents=[]
    for _ in range(count):
        t=const[0]; g=const[1]; ih=const[2]
        if not flags&1: t=struct.unpack_from('<I',d,p)[0]; p+=4
        if not flags&2: g=struct.unpack_from('<I',d,p)[0]; p+=4
        if not flags&4: ih=struct.unpack_from('<I',d,p)[0]; p+=4
        il=struct.unpack_from('<I',d,p)[0]; p+=4
        off=struct.unpack_from('<I',d,p)[0]; p+=4
        fs=struct.unpack_from('<I',d,p)[0]&0x7fffffff; p+=4
        ms=struct.unpack_from('<I',d,p)[0]; p+=4
        comp,_=struct.unpack_from('<HH',d,p); p+=4
        ents.append(dict(type=t,group=g,inst=(ih<<32)|il,off=off,fsize=fs,msize=ms,comp=comp))
    return d,ents
def get(d,e):
    raw=d[e['off']:e['off']+e['fsize']]
    c=e['comp']
    if c==0: return raw
    if c==0x5a42: return zlib.decompress(raw)
    raise Exception('comp %x'%c)
