exec(open('insp.py').read().split("print(collections")[0])
import struct,rle2
def tgi(d):
    off=struct.unpack_from('<I',d,4)[0]+8; n=d[off]
    return [struct.unpack_from('<QII',d,off+1+i*16) for i in range(n)]
T={e['inst']&0xffffff:e for e in r if e['t']==0x3453CF95}
for i,e in enumerate([e for e in r if e['t']==0x034AEECB]):
    d=dbpf.data(e); t=tgi(d)
    print(i,hex(e['inst']&0xffffffff),len(d),'ver',struct.unpack_from('<I',d,0)[0],[ (hex(a[1]),hex(a[0]&0xffffff)) for a in t])
    if i==0: print(d[:160].hex())
