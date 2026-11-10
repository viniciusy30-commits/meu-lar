import numpy as np
MOD=[[2,8,-2,-8],[5,17,-5,-17],[9,29,-9,-29],[13,42,-13,-42],[18,60,-18,-60],[24,80,-24,-80],[33,106,-33,-106],[47,183,-47,-183]]
DIST=[3,6,11,16,23,32,41,64]
EAC=[[-3,-6,-9,-15,2,5,8,14],[-3,-7,-10,-13,2,6,9,12],[-2,-5,-8,-13,1,4,7,12],[-2,-4,-6,-13,1,3,5,12],[-3,-6,-8,-12,2,5,7,11],[-3,-7,-9,-11,2,6,8,10],[-4,-7,-8,-11,3,6,7,10],[-3,-5,-8,-11,2,4,7,10],[-2,-6,-8,-10,1,5,7,9],[-2,-5,-8,-10,1,4,7,9],[-2,-4,-8,-10,1,3,7,9],[-2,-5,-7,-10,1,4,6,9],[-3,-4,-7,-10,2,3,6,9],[-1,-2,-3,-10,0,1,2,9],[-4,-6,-8,-9,3,5,7,8],[-3,-5,-7,-9,2,4,6,8]]
def c8(x): return 0 if x<0 else (255 if x>255 else x)
def ext4(x): return (x<<4)|x
def ext5(x): return (x<<3)|(x>>2)
def sx3(x): return x-8 if x>=4 else x
def blk_rgb(b,allow2):
    """returns 16 (r,g,b) in order i=x*4+y"""
    b0,b1,b2,b3,b4,b5,b6,b7=b
    diff=(b3>>1)&1; flip=b3&1
    if diff and allow2:
        R=b0>>3; dR=sx3(b0&7); G=b1>>3; dG=sx3(b1&7); B=b2>>3; dB=sx3(b2&7)
        if R+dR<0 or R+dR>31: mode='T'
        elif G+dG<0 or G+dG>31: mode='H'
        elif B+dB<0 or B+dB>31: mode='P'
        else: mode='D'
    else: mode='D'
    out=[None]*16
    msb=(b4<<8)|b5; lsb=(b6<<8)|b7
    if mode=='D':
        if diff:
            R=b0>>3; G=b1>>3; B=b2>>3
            c1=(ext5(R),ext5(G),ext5(B)); c2=(ext5(R+sx3(b0&7)),ext5(G+sx3(b1&7)),ext5(B+sx3(b2&7)))
        else:
            c1=(ext4(b0>>4),ext4(b1>>4),ext4(b2>>4)); c2=(ext4(b0&15),ext4(b1&15),ext4(b2&15))
        t1=MOD[(b3>>5)&7]; t2=MOD[(b3>>2)&7]
        for x in range(4):
            for y in range(4):
                i=x*4+y; p=(((msb>>i)&1)<<1)|((lsb>>i)&1)
                sub2=(y>=2) if flip else (x>=2)
                c=c2 if sub2 else c1; m=(t2 if sub2 else t1)[p]
                out[i]=(c8(c[0]+m),c8(c[1]+m),c8(c[2]+m))
        return out
    if mode=='T':
        R1=(((b0>>3)&3)<<2)|(b0&3); G1=b1>>4; B1=b1&15; R2=b2>>4; G2=b2&15; B2=b3>>4
        d=DIST[(((b3>>2)&3)<<1)|(b3&1)]
        C1=(ext4(R1),ext4(G1),ext4(B1)); C2=(ext4(R2),ext4(G2),ext4(B2))
        pal=[C1,tuple(c8(v+d) for v in C2),C2,tuple(c8(v-d) for v in C2)]
    elif mode=='H':
        R1=(b0>>3)&15; G1=((b0&7)<<1)|((b1>>4)&1); B1=(b1&8)|((b1&3)<<1)|((b2>>7)&1)
        R2=(b2>>3)&15; G2=((b2&7)<<1)|(b3>>7); B2=(b3>>3)&15
        di=((b3&4))|((b3&1)<<1)
        if ((R1<<8)|(G1<<4)|B1)>=((R2<<8)|(G2<<4)|B2): di|=1
        d=DIST[di]
        C1=(ext4(R1),ext4(G1),ext4(B1)); C2=(ext4(R2),ext4(G2),ext4(B2))
        pal=[tuple(c8(v+d) for v in C1),tuple(c8(v-d) for v in C1),tuple(c8(v+d) for v in C2),tuple(c8(v-d) for v in C2)]
    else:
        RO=(b0&0x7E)>>1; GO=((b0&1)<<6)|((b1&0x7E)>>1); BO=((b1&1)<<5)|(b2&0x18)|((b2&3)<<1)|((b3>>7)&1)
        RH=((b3&0x7C)>>1)|(b3&1); GH=(b4>>1)&0x7F; BH=((b4&1)<<5)|((b5>>3)&0x1F)
        RV=((b5&7)<<3)|((b6>>5)&7); GV=((b6&0x1F)<<2)|((b7>>6)&3); BV=b7&0x3F
        e6=lambda v:(v<<2)|(v>>4); e7=lambda v:(v<<1)|(v>>6)
        RO,RH,RV=e6(RO),e6(RH),e6(RV); GO,GH,GV=e7(GO),e7(GH),e7(GV); BO,BH,BV=e6(BO),e6(BH),e6(BV)
        for x in range(4):
            for y in range(4):
                out[x*4+y]=(c8((x*(RH-RO)+y*(RV-RO)+4*RO+2)>>2),c8((x*(GH-GO)+y*(GV-GO)+4*GO+2)>>2),c8((x*(BH-BO)+y*(BV-BO)+4*BO+2)>>2))
        return out
    for i in range(16):
        p=(((msb>>i)&1)<<1)|((lsb>>i)&1); out[i]=pal[p]
    return out
def blk_eac(b):
    base=b[0]; mult=b[1]>>4; tbl=EAC[b[1]&15]
    v=int.from_bytes(bytes(b[2:8]),'big'); out=[0]*16
    for i in range(16):
        idx=(v>>(45-3*i))&7; out[i]=c8(base+tbl[idx]*mult)
    return out
def decode(data,w,h,fmt):
    bw,bh=(w+3)//4,(h+3)//4
    img=np.zeros((bh*4,bw*4,4),np.uint8); img[...,3]=255
    if fmt==4:
        return np.frombuffer(data,np.uint8,w*h*4).reshape(h,w,4).copy()
    if fmt==7:
        v=np.frombuffer(data,'<u2',w*h).reshape(h,w).astype(np.uint32)
        o=np.zeros((h,w,4),np.uint8); o[...,0]=((v>>11)&31)*255//31; o[...,1]=((v>>5)&63)*255//63; o[...,2]=(v&31)*255//31; o[...,3]=255; return o
    bs=16 if fmt==47 else 8; pos=0
    for by in range(bh):
        for bx in range(bw):
            blk=data[pos:pos+bs]; pos+=bs
            if fmt==47: al=blk_eac(blk[:8]); px=blk_rgb(blk[8:],True)
            else: al=None; px=blk_rgb(blk,fmt!=34)
            for x in range(4):
                for y in range(4):
                    i=x*4+y; c=px[i]; yy=by*4+y; xx=bx*4+x
                    img[yy,xx,0]=c[0]; img[yy,xx,1]=c[1]; img[yy,xx,2]=c[2]
                    if al: img[yy,xx,3]=al[i]
    return img[:h,:w]
