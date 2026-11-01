import struct, zlib
class N:
    __slots__=('name','props','kids')
    def __init__(s,n): s.name=n; s.props=[]; s.kids=[]
    def get(s,n):
        for k in s.kids:
            if k.name==n: return k
    def all(s,n): return [k for k in s.kids if k.name==n]
def parse(path):
    b=open(path,'rb').read(); ver=struct.unpack_from('<I',b,23)[0]; big=ver>=7500
    def rec(o):
        if big: end,np_,pl=struct.unpack_from('<QQQ',b,o); o+=24
        else: end,np_,pl=struct.unpack_from('<III',b,o); o+=12
        nl=b[o]; o+=1
        if end==0: return None,o
        n=N(b[o:o+nl].decode('latin1')); o+=nl
        for _ in range(np_):
            t=chr(b[o]); o+=1
            if t=='Y': v=struct.unpack_from('<h',b,o)[0]; o+=2
            elif t=='C': v=b[o]; o+=1
            elif t=='I': v=struct.unpack_from('<i',b,o)[0]; o+=4
            elif t=='F': v=struct.unpack_from('<f',b,o)[0]; o+=4
            elif t=='D': v=struct.unpack_from('<d',b,o)[0]; o+=8
            elif t=='L': v=struct.unpack_from('<q',b,o)[0]; o+=8
            elif t in 'fdlib':
                ln,enc,cl=struct.unpack_from('<III',b,o); o+=12
                raw=b[o:o+cl]; o+=cl
                if enc==1: raw=zlib.decompress(raw)
                dt={'f':'<f4','d':'<f8','l':'<i8','i':'<i4','b':'u1'}[t]
                import numpy as np
                v=np.frombuffer(raw,dtype=dt)
            elif t in 'SR':
                ln=struct.unpack_from('<I',b,o)[0]; o+=4; v=b[o:o+ln]; o+=ln
                if t=='S': v=v.decode('latin1')
            n.props.append(v)
        while o<end:
            k,o=rec(o)
            if k: n.kids.append(k)
        return n,end
    root=N('root'); o=27
    while o<len(b)-30:
        k,o2=rec(o)
        if k is None: break
        root.kids.append(k); o=o2
    return root
