import numpy as np
from PIL import Image
base=np.asarray(Image.open('/home/claude/repo/viniciusy30-commits-meu-lar-66b7014/app/src/main/assets/cute/textures.png').convert('RGB')).astype(np.float64)
rc=np.asarray(Image.open('out/recolor.png')).astype(np.float64)
w0=rc[...,0]/255; w1=rc[...,1]/255; rid=rc[...,2].astype(int)
S=np.asarray(Image.open('out/recolor_s.png')).astype(np.float64)[...,0]/255*2
regs={}
for ln in open('out/recolor.txt'):
    if ln.startswith('#') or not ln.strip(): continue
    i,n,s0,s1,r0,r1=ln.strip().split('|'); regs[int(i)]=(int(s0),int(s1),np.array(r0.split(),float),np.array(r1.split(),float))
def hexc(h): return np.array([int(h[i:i+2],16) for i in (1,3,5)],float)
def run(cols):
    out=base.copy()
    for i,(s0,s1,r0,r1) in regs.items():
        m=rid==i
        def dl(s,r):
            c=cols.get(s)
            return (c-r) if (s>=0 and c is not None) else np.zeros(3)
        D0=dl(s0,r0); D1=dl(s1,r1)
        P0=np.maximum(D0,0); P1=np.maximum(D1,0)
        N0=np.minimum(D0/np.maximum(r0,1),0); N1=np.minimum(D1/np.maximum(r1,1),0)
        W0=w0[m][:,None]; W1=w1[m][:,None]; Sm=S[m][:,None]
        b=base[m]
        out[m]=(b+Sm*(W0*P0+W1*P1))*(1+W0*N0+W1*N1)
    return np.clip(out,0,255).astype(np.uint8)
ident=run({})
print('identidade max diff',np.abs(ident.astype(int)-base.astype(int)).max())
def lighten(c,k): return c+(255-c)*k
H=hexc('#1C1A1A')
V={0:hexc('#6B4430'),1:hexc('#3B7FD0'),2:H,3:lighten(H,0.25),4:hexc('#3E8EDE'),5:lighten(hexc('#3E8EDE'),0.25),6:hexc('#E5484D'),7:hexc('#FFFFFF'),8:hexc('#FFFFFF')}
H2=hexc('#EDEDED')
V2={0:hexc('#FFE0C4'),1:hexc('#3E9B5B'),2:H2,3:lighten(H2,0.25),4:hexc('#F4D35E'),5:lighten(hexc('#F4D35E'),0.25),6:hexc('#2E4A7D'),7:hexc('#1E2230'),8:hexc('#1E2230')}
H3=hexc('#3F6FD8')
V3={0:hexc('#8E5A3A'),2:H3,3:lighten(H3,0.25),4:hexc('#EE6FA6'),5:lighten(hexc('#EE6FA6'),0.25)}
sheet=np.concatenate([np.concatenate([base.astype(np.uint8),run(V)],1),np.concatenate([run(V2),run(V3)],1)],0)
Image.fromarray(sheet).resize((1536,1024)).save('sim.png')
