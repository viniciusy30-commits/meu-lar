import struct, zlib, numpy as np, sys
from PIL import Image
sys.path.insert(0,'/home/claude/work/proto')
from render import rd
def dbpf2(ents, minor):
    # ents: list of (type, group, inst, data, compress)
    hdr=bytearray(96); hdr[0:4]=b'DBPF'; struct.pack_into('<II',hdr,4,2,minor)
    body=bytearray(); idx=[]
    for t,g,i,data,comp in ents:
        off=96+len(body)
        if comp: z=zlib.compress(data); raw=z; c=0x5A42
        else: raw=data; c=0
        body+=raw
        idx.append((t,g,i>>32,i&0xffffffff,off,len(raw)|0x80000000,len(data),c))
    ipos=96+len(body)
    ib=bytearray(struct.pack('<I',0))  # flags 0: everything explicit
    for t,g,ih,il,off,fs,ms,c in idx:
        ib+=struct.pack('<IIIIIIIHH',t,g,ih,il,off,fs,ms,c,1)
    struct.pack_into('<I',hdr,36,len(idx)); struct.pack_into('<I',hdr,40,ipos); struct.pack_into('<I',hdr,44,len(ib)); struct.pack_into('<I',hdr,64,ipos)
    return bytes(hdr)+bytes(body)+bytes(ib)
def geom(pos,nor,uv,idx):
    nv=len(pos)
    b=bytearray(b'GEOM'); b+=struct.pack('<IIII',12,0,0,0)   # ver, tgioff, tgisize, shader=0
    b+=struct.pack('<II',0,0)  # merge, sort
    b+=struct.pack('<II',nv,4)
    fm=[(1,1,12),(2,1,12),(3,1,8),(4,2,4)]
    for dt,st,bpe in fm: b+=struct.pack('<IIB',dt,st,bpe)
    for i in range(nv):
        b+=struct.pack('<3f',*pos[i]); b+=struct.pack('<3f',*nor[i]); b+=struct.pack('<2f',*uv[i]); b+=bytes([0,255,255,255])
    b+=struct.pack('<I',1); b+=bytes([2]); b+=struct.pack('<I',len(idx)*3)
    b+=np.asarray(idx,'<u2').tobytes()
    b+=struct.pack('<I',0)
    return bytes(b)
def dds32(w,h,pix):
    hdr=bytearray(128); hdr[0:4]=b'DDS '; struct.pack_into('<I',hdr,4,124); struct.pack_into('<I',hdr,8,0x1007)
    struct.pack_into('<II',hdr,12,h,w); struct.pack_into('<I',hdr,76,32); struct.pack_into('<I',hdr,80,0x41)
    struct.pack_into('<I',hdr,88,32); struct.pack_into('<IIII',hdr,92,0xff0000,0xff00,0xff,0xff000000)
    return bytes(hdr)+pix
body,bidx=rd('/home/claude/work/merged/app/src/main/assets/cute/p_body_am1.bin')
P=body['p'].astype(float); N=body['n'].astype(float); UV=body['uv']
# "calça": triangulos do corpo entre y=45 e y=100, empurrados 0.8cm para fora, em metros (escala do Sims 3: /96.8*0.9861... usa 1/98.2)
s0=96.8/0.9861
sel=(P[:,1]>45)&(P[:,1]<100)
tri=bidx[sel[bidx].all(1)]
used=np.unique(tri); remap=-np.ones(len(P),int); remap[used]=np.arange(len(used))
pp=(P[used]+N[used]*0.8)/s0; nn=N[used]; uv=UV[used]
g=geom(pp,nn,uv,remap[tri])
# textura: gradiente colorido 256x256 BGRA
w=h=256; px=bytearray()
for y in range(h):
    for x in range(w): px+=bytes([ (x*255//w), 80, (y*255//h), 255])   # B,G,R,A
img=dds32(w,h,bytes(px))
for minor,name,comp in [(0,'s3test.package',True),(1,'s4test.package',False)]:
    open('/tmp/'+name,'wb').write(dbpf2([(0x015A1849,0,0x1111,g,comp),(0x015A1849,0,0x2222,geom(pp[::1],nn,uv,remap[tri][:len(remap[tri])//2]),comp),(0x00B2D882,0,0x3333,img,comp)],minor))
print('ok',len(pp),len(tri))
