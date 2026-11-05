import numpy as np, math
from PIL import Image, ImageDraw
from scipy import ndimage
from flora_lib import *
S=512
def tn(sx,sy,seed): return tnoise(S,sx,sy,seed)
def rgb(a): return np.clip(a,0,255)

def planks(name,seed,base,var=0.16,bw=7,gap=(40,28,20)):
    r=np.random.default_rng(seed); img=np.zeros((S,S,3)); bh=S//bw
    gx=tn(60,0.7,seed+1); gy=tn(30,1.2,seed+2); wav=tn(8,3,seed+3)
    for i in range(bw):
        y0=i*bh; joints=sorted(r.choice(np.arange(60,S-60),size=2,replace=False)); 
        off=int(r.integers(0,S)); segs=[0]+list(joints)+[S]
        for a,b in zip(segs[:-1],segs[1:]):
            k=1+var*(r.random()*2-1); col=np.array(base,float)*k*(1+0.06*(r.random()-0.5))
            xs=np.arange(a,b)
            blk=np.zeros((bh,b-a,3))
            streak=0.90+0.12*gx[y0:y0+bh,a:b]*1.0+0.06*np.sin((np.arange(bh)[:,None]*0.35+wav[y0:y0+bh,a:b]*9))
            blk[:]=col[None,None,:]*streak[...,None]
            # bordas
            blk[:2]=np.array(gap); blk[-2:]=np.array(gap)*1.3; blk[:,:2]=np.array(gap); 
            blk[2:4]=col*1.12*streak[2:4,:,None]
            img[y0:y0+bh,a:b]=blk
    img*= (0.97+0.05*tn(3,3,seed+9))[...,None]
    save_tex(name,rgb(img)); 

def tile(name,seed,base=(232,230,224),n=2,grout=(150,148,144)):
    img=np.zeros((S,S,3)); t=S//n; r=np.random.default_rng(seed)
    y,x=np.mgrid[0:S,0:S]
    for i in range(n):
        for j in range(n):
            k=0.96+0.06*r.random(); img[i*t:(i+1)*t,j*t:(j+1)*t]=np.array(base)*k
    warp=tn(4,4,seed+1)*6
    vein=np.abs(np.sin((x+y*0.7)/S*9+warp*1.5)); vein=np.clip(1-vein*7,0,1)*0.10
    img*= (1-vein)[...,None]; img*=(0.97+0.05*tn(1.5,1.5,seed+2))[...,None]
    g=np.zeros((S,S),bool)
    for k in range(n): g[k*t:k*t+3,:]=True; g[:,k*t:k*t+3]=True
    img[g]=grout
    save_tex(name,rgb(img))

def grass(name,seed):
    r=np.random.default_rng(seed)
    big=tn(3,3,seed+1); mid=tn(10,10,seed+2); fine=tn(1.0,1.0,seed+3)
    base=lerpc((52,112,34),(96,158,48),np.clip(0.35+0.5*big+0.25*(mid-0.5),0,1))*(0.9+0.2*fine)[...,None]
    im=Image.fromarray(rgb(base).astype(np.uint8)); d=ImageDraw.Draw(im)
    for i in range(9000):
        x=r.uniform(0,S); y=r.uniform(0,S); L=r.uniform(6,16); a=-math.pi/2+r.normal()*0.5
        g=r.uniform(0.7,1.25); col=(int(46*g),int(104*g),int(30*g)) if r.random()<0.55 else (int(96*g),int(160*g),int(50*g))
        for ox in (-S,0,S):
            for oy in (-S,0,S):
                if -20<x+ox<S+20 and -20<y+oy<S+20: d.line([(x+ox,y+oy),(x+ox+math.cos(a)*L,y+oy+math.sin(a)*L)],fill=col,width=1)
    for i in range(70):
        x=r.uniform(0,S); y=r.uniform(0,S); d.ellipse([x,y,x+3,y+3],fill=(235,235,215))
    Image.fromarray(np.asarray(im)).save(OUT+'tex/mat_grass.png')

def paver(name,seed):
    r=np.random.default_rng(seed); img=np.zeros((S,S,3)); img[:]=(138,126,108)
    rows=4; rh=S//rows
    for i in range(rows):
        x=int(r.integers(0,120)); 
        while x<S+200:
            w=int(r.integers(130,230)) if True else 150; x0=x; x1=x+w
            base=np.array((206,192,168))*(0.9+0.16*r.random())*np.array((1,1,1))*(1+0.05*(r.random()-0.5))
            for xx in range(x0+4,min(x1-4,S+0)):
                pass
            xs=np.arange(x0+4,x1-4)%S
            blk=np.zeros((rh-8,len(xs),3)); blk[:]=base
            blk[:3]*=1.12; blk[-3:]*=0.82
            img[i*rh+4:(i+1)*rh-4,xs]=blk
            x=x1
    img*=(0.94+0.1*tn(0.8,0.8,seed+1))[...,None]; img*=(0.96+0.08*tn(6,6,seed+2))[...,None]
    save_tex(name,rgb(img))

def ashlar(name,seed):
    r=np.random.default_rng(seed); img=np.zeros((S,S,3)); img[:]=(196,190,180)
    rows=4; rh=S//rows
    for i in range(rows):
        x=int(r.integers(0,200)); 
        while x<S+300:
            w=int(r.integers(160,300)); xs=np.arange(x+5,x+w-5)%S
            base=np.array((168,160,148))*(0.88+0.2*r.random())
            blk=np.zeros((rh-10,len(xs),3)); blk[:]=base; blk[:4]*=1.1; blk[-4:]*=0.8
            img[i*rh+5:(i+1)*rh-5,xs]=blk; x+=w
    img*=(0.9+0.2*tn(1.5,1.5,seed+1))[...,None]; img*=(0.95+0.1*tn(0.5,0.5,seed+2))[...,None]
    save_tex(name,rgb(img))

def plaster(name,seed):
    n=tn(2,2,seed); m=tn(0.8,0.8,seed+1); s=tn(14,1.2,seed+2)
    t=0.93+0.045*n+0.02*m+0.02*s; save_tex(name,np.repeat(rgb(t[...,None]*255),3,2))

def siding(name,seed,n=5):
    img=np.zeros((S,S,3)); bh=S//n; y=np.arange(bh)[:,None]; streak=tn(60,0.6,seed)*0.05+tn(8,1,seed+1)*0.03
    prof=np.ones(bh); prof[:int(bh*0.06)]=1.08; prof[int(bh*0.06):int(bh*0.12)]=1.0
    prof[-int(bh*0.10):]=np.linspace(0.86,0.62,int(bh*0.10)); prof[-3:]=0.45
    for i in range(n):
        board=np.repeat(prof[:,None],S,1)*(0.97+0.05*np.random.default_rng(seed+i).random())
        img[i*bh:(i+1)*bh]=(board+streak[i*bh:(i+1)*bh]*0.8)[...,None]*255*0.97
    save_tex(name,rgb(img))

def roof(name,seed):
    r=np.random.default_rng(seed); img=np.zeros((S,S,3)); rows=8; rh=S//rows; img[:]=(36,36,42)
    for i in range(rows):
        x=int(r.integers(0,100))-(i%2)*50
        while x<S+100:
            w=100; xs=np.arange(x+2,x+w-2)%S
            base=np.array((92,94,108))*(0.84+0.3*r.random()); blk=np.zeros((rh-3,len(xs),3)); blk[:]=base
            blk[:int(rh*0.3)]*=0.8; blk[-5:]*=0.6; blk*=(0.96+0.08*np.linspace(0,1,rh-3))[:,None,None]
            img[i*rh:(i+1)*rh-3,xs]=blk; x+=w
    img*=(0.93+0.12*tn(0.7,0.7,seed+1))[...,None]
    save_tex(name,rgb(img))

def copyg(src,dst):
    im=Image.open(OUT+'tex/'+src).convert('RGB').resize((S,S) if src in('grain.png',) else (256,256)); im.save(OUT+'tex/'+dst)

if __name__=='__main__':
    planks('mat_floor_l.png',5,(222,178,122)); planks('mat_floor_d.png',6,(112,72,46),var=0.12)
    tile('mat_tile.png',7); grass('mat_grass.png',8); paver('mat_paver.png',9); ashlar('mat_stone.png',10); plaster('mat_plaster.png',11)
    siding('mat_siding.png',12); roof('mat_roof.png',13)
    for s,d in (('grain.png','mat_wood.png'),('weave.png','mat_fabric.png'),('brushed.png','mat_metal.png')): copyg(s,d)
    print('ok')
