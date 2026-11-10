import struct,os
class R:
    def __init__(s,b,p=0,be=False): s.b=b; s.p=p; s.e='>' if be else '<'
    def _u(s,f,n): v=struct.unpack_from(s.e+f,s.b,s.p)[0]; s.p+=n; return v
    def u8(s): return s._u('B',1)
    def i16(s): return s._u('h',2)
    def u16(s): return s._u('H',2)
    def i32(s): return s._u('i',4)
    def u32(s): return s._u('I',4)
    def i64(s): return s._u('q',8)
    def u64(s): return s._u('Q',8)
    def f32(s): return s._u('f',4)
    def cstr(s):
        e=s.b.index(b'\0',s.p); v=s.b[s.p:e].decode('utf8','replace'); s.p=e+1; return v
    def str(s):
        n=s.u32(); v=s.b[s.p:s.p+n].decode('utf8','replace'); s.p+=n; s.align(); return v
    def align(s): s.p=(s.p+3)&~3
    def raw(s,n): v=s.b[s.p:s.p+n]; s.p+=n; return v
def parse(path,b):
    r=R(b,0,True)
    r.u32(); r.u32(); ver=r.u32(); r.u32()
    assert ver>=22,ver
    msize=r.u64(); fsize=r.u64(); doff=r.u64(); r.u64()
    r.e='<' if False else '>'
    unity=r.cstr(); r.e='<'
    plat=r.u32(); tt=r.u8()
    n=r.u32(); types=[]
    for _ in range(n):
        cid=r.i32(); strip=r.u8(); sidx=r.i16()
        if cid==114: r.raw(16)
        r.raw(16)
        if tt: raise Exception('typetree')
        types.append((cid,sidx))
    n=r.u32(); r.align(); objs=[]
    for _ in range(n):
        r.align(); pid=r.i64(); off=r.u64(); sz=r.u32(); ti=r.i32()
        objs.append((pid,doff+off,sz,ti,types[ti][0]))
    n=r.u32()
    for _ in range(n): r.i32(); r.i64()   # script types (fileId,pathId) simplified
    n=r.u32(); ext=[]
    for _ in range(n):
        r.cstr(); r.raw(16); r.i32(); ext.append(r.cstr())
    return dict(path=path,data=b,objs=objs,ext=ext,unity=unity,types=types)
