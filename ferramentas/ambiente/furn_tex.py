import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
from flora_lib import *
from textures import finish, dilate_rgb

def gray(name,a): save_tex(name,np.repeat(np.clip(a,0,1)[...,None]*255,3,2))

def grain(name,seed,size=256):
    warp=tnoise(size,10,40,seed)*2.2
    y,x=np.mgrid[0:size,0:size]
    rings=np.sin((x/size*10+warp)*math.pi)*0.5+0.5
    fine=tnoise(size,0.5,70,seed+2)
    t=0.76+0.10*rings+0.14*fine+0.03*tnoise(size,3,3,seed+3)
    gray(name,t)
def weave(name,seed,size=128,period=16):
    y,x=np.mgrid[0:size,0:size]
    a=(np.sin(x/size*period*2*math.pi)*0.5+0.5)*(np.sin(y/size*period*2*math.pi+math.pi)*0.5+0.5)
    b=np.abs(np.sin((x+y)/size*period*math.pi))
    t=0.78+0.14*a+0.06*b+0.05*tnoise(size,0.7,0.7,seed)
    gray(name,t)
def brushed(name,seed,size=128):
    n=tnoise(size,16,0.4,seed); gray(name,0.88+0.12*n)
def white(name):
    save_tex(name,np.full((8,8,3),255.0))
def leather(name,seed,size=128):
    n=tnoise(size,1.2,1.2,seed); m=tnoise(size,3,3,seed+1)
    gray(name,0.8+0.14*n+0.08*m)

def rug(name,seed,size=512):
    r=np.random.default_rng(seed); img=np.zeros((size,size,3),float)
    cream=np.array([232,220,196]); terra=np.array([176,84,58]); navy=np.array([40,58,92]); gold=np.array([208,170,86])
    y,x=np.mgrid[0:size,0:size]; u=(x+0.5)/size*2-1; v=(y+0.5)/size*2-1
    d=np.maximum(np.abs(u),np.abs(v))
    img[:]=cream
    img[d>0.84]=navy; img[(d>0.80)&(d<=0.84)]=cream; img[(d>0.72)&(d<=0.80)]=terra
    # padrao de losangos
    L1=(np.abs(u)+np.abs(v))
    cell=((np.floor((u+1)*5)+np.floor((v+1)*5))%2==0)
    img[(d<=0.72)]=np.where(cell[...,None],cream,np.array([222,206,176]))[d<=0.72]
    for k,col in ((0.55,navy),(0.40,terra),(0.24,gold),(0.10,navy)):
        ring=(np.abs(L1-k)<0.045); img[ring&(d<=0.72)]=col
    d2=np.hypot(u,v); img[(d2<0.08)]=terra
    # borda: pequenos triangulos
    t=(((np.floor((u+1)*14)+np.floor((v+1)*14))%2==0)&(d>0.72)&(d<=0.80)); img[t]=cream
    fib=tnoise(size,0.5,0.5,seed); img*=(0.9+0.14*fib)[...,None]
    save_tex(name,img)

def spine(name,size=64):
    im=Image.new('RGBA',(size,size),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,6,size,9],fill=(220,190,110,255)); d.rectangle([0,size-12,size,size-9],fill=(220,190,110,255))
    d.rectangle([size*0.22,size*0.3,size*0.78,size*0.62],fill=(240,232,210,255))
    for i in range(3): d.line([size*0.3,size*0.38+i*8,size*0.7,size*0.38+i*8],fill=(70,60,50,255),width=2)
    im.save(OUT+'tex/'+name)

def screen(name,size=256):
    img=np.zeros((size,size,3),float); y,x=np.mgrid[0:size,0:size]; u=x/size; v=y/size
    sky=lerpc((20,40,100),(250,150,90),np.clip(v*1.5,0,1)); img[:]=sky
    sun=np.hypot((u-0.65)*1.0,(v-0.55)*1.0)<0.07; img[sun]=(255,230,160)
    for k,(h,c) in enumerate(((0.62,(40,36,70)),(0.72,(24,26,52)),(0.82,(12,14,30)))):
        ridge=h+0.06*np.sin(u*(7+k*3)+k)+0.03*np.sin(u*23+k*2)
        img[v>ridge]=c
    img*=(0.96+0.06*tnoise(size,0.5,0.5,1))[...,None]
    save_tex(name,img)

def art(name,seed,size=128):
    r=np.random.default_rng(seed); img=np.zeros((size,size,3),float)
    y,x=np.mgrid[0:size,0:size]; v=y/size
    img[:]=lerpc((176,214,236),(240,236,214),v)
    img[v>0.6]=(110,150,100); 
    for i in range(3): 
        h=0.35+0.15*i; ridge=h+0.05*np.sin(x/size*(5+i)+i); img[(v>ridge)&(v<=0.62)]=(90+i*30,120+i*20,140+i*10)
    sun=np.hypot((x/size-0.7)*1.0,(v-0.28)*1.0)<0.08; img[sun]=(255,224,140)
    save_tex(name,img)

def sprite_big(name,seed,kind='fig',size=256):
    r=np.random.default_rng(seed); SS=1024; im=Image.new('RGBA',(SS,SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    base=(34,92,40) if kind=='fig' else (28,96,50); hi=(76,148,70) if kind=='fig' else (60,140,84)
    specs=[(SS*0.5,SS*0.97,-1.57+a,SS*r.uniform(0.34,0.5)) for a in (-0.9,-0.45,0.0,0.4,0.85)]
    for (sx,sy,a,ln) in specs:
        ex=sx+math.cos(a)*ln*0.55; ey=sy+math.sin(a)*ln*0.55
        d.line([(sx,sy),(ex,ey)],fill=(60,96,44,255),width=9)
        la=a
        L=ln*1.25; W=ln*0.52
        t=np.linspace(0,1,30); w=W*np.sin(np.pi*t**0.8)*(1-0.15*t)
        left=[(tt*L,-ww) for tt,ww in zip(t,w)]; right=[(tt*L,ww) for tt,ww in zip(t[::-1],w[::-1])]
        def tr(p,s=1.0): return [(ex+(px*math.cos(la)-py*s*math.sin(la)),ey+(px*math.sin(la)+py*s*math.cos(la))) for px,py in p]
        d.polygon(tr(left+right),fill=base+(255,))
        d.polygon(tr([(px*0.95+L*0.03,py*0.55) for px,py in left+right]),fill=hi+(255,))
        d.line(tr([(0,0),(L*0.97,0)]),fill=(190,206,140,255),width=5)
        for k in range(1,6):
            for sgn in (-1,1): d.line(tr([(L*k/6,0),(L*(k/6+0.12),sgn*W*0.8*np.sin(np.pi*(k/6+0.05)**0.8))]),fill=(70,128,64,255),width=3)
    finish(im,size,name)

if __name__=='__main__':
    grain('grain.png',41); weave('weave.png',42); brushed('brushed.png',43); white('white.png'); leather('leather.png',44)
    rug('rug_a.png',45); spine('spine.png'); screen('screen.png'); art('art_a.png',46); sprite_big('leaf_fig.png',47)
    print('ok')
