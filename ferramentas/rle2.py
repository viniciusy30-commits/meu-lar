import struct, io, numpy as np
from PIL import Image
def rle2_mip0(b):
    w,h,mc=struct.unpack_from('<HHH',b,8)
    offs=np.array(struct.unpack_from('<%dI'%(mc*5),b,16),dtype=np.int64).reshape(mc,5)
    nb=(w//4)*(h//4)
    def stream(k,mip=0):
        a=offs[mip][k]; e=offs[mip+1][k] if mip+1<mc else len(b)
        return b[a:e]
    cm=np.frombuffer(stream(0),'<u2'); s1=stream(1); s2=stream(2); s3=stream(3); s4=stream(4)
    out=np.zeros((nb,16),np.uint8)
    pos=0; ic=0; ia=0
    for c in cm:
        op=int(c)&3; n=int(c)>>2
        if op==0: pos+=n
        elif op==1:
            out[pos:pos+n,0:2]=np.frombuffer(s3,np.uint8,count=2*n,offset=2*ia).reshape(n,2)
            out[pos:pos+n,2:8]=np.frombuffer(s4,np.uint8,count=6*n,offset=6*ia).reshape(n,6)
            out[pos:pos+n,8:12]=np.frombuffer(s1,np.uint8,count=4*n,offset=4*ic).reshape(n,4)
            out[pos:pos+n,12:16]=np.frombuffer(s2,np.uint8,count=4*n,offset=4*ic).reshape(n,4)
            ia+=n; ic+=n; pos+=n
        elif op==2:
            out[pos:pos+n,0]=255; out[pos:pos+n,1]=255
            out[pos:pos+n,8:12]=np.frombuffer(s1,np.uint8,count=4*n,offset=4*ic).reshape(n,4)
            out[pos:pos+n,12:16]=np.frombuffer(s2,np.uint8,count=4*n,offset=4*ic).reshape(n,4)
            ic+=n; pos+=n
        else: raise Exception('op3')
    assert pos==nb,(pos,nb)
    hdr=bytearray(128); hdr[0:4]=b'DDS '; struct.pack_into('<I',hdr,4,124); struct.pack_into('<I',hdr,8,0x81007)
    struct.pack_into('<II',hdr,12,h,w); struct.pack_into('<I',hdr,20,nb*16); struct.pack_into('<I',hdr,28,1)
    struct.pack_into('<I',hdr,76,32); struct.pack_into('<I',hdr,80,4); hdr[84:88]=b'DXT5'; struct.pack_into('<I',hdr,108,0x1000)
    im=Image.open(io.BytesIO(bytes(hdr)+out.tobytes())).convert('RGBA'); im.load()
    return im
