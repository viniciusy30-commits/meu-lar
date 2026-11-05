import numpy as np, math
from PIL import Image, ImageDraw
from scipy import ndimage
from flora_lib import *

def dilate_rgb(arr):
    a=arr[...,3]>8
    idx=ndimage.distance_transform_edt(~a,return_distances=False,return_indices=True)
    out=arr.copy(); out[...,:3]=arr[idx[0],idx[1],:3]; return out

def finish(img,size,name):
    im=img.resize((size,size),Image.LANCZOS); arr=np.asarray(im).copy()
    arr=dilate_rgb(arr); Image.fromarray(arr).save(OUT+'tex/'+name)

def leaf_poly(L,W,lobes=0,seed=0):
    t=np.linspace(0,1,24); w=W*np.sin(np.pi*t**0.75)*(1-0.2*t)
    if lobes: w=w*(1+0.28*np.sin(t*lobes*math.pi+seed))
    left=[(tt*L,-ww) for tt,ww in zip(t,w)]; right=[(tt*L,ww) for tt,ww in zip(t[::-1],w[::-1])]
    return left+right

def draw_leaf(d,x,y,ang,L,W,base,hi,lobes=0,rng=None,S=1.0):
    c,s=math.cos(ang),math.sin(ang)
    def tr(pts,scale=1.0): return [(x+(px*c-py*s*scale if False else px*c-py*s),y+(px*s+py*c)) for px,py in pts]
    poly=leaf_poly(L,W,lobes,rng.uniform(0,6) if rng else 0)
    d.polygon(tr(poly),fill=tuple(base)+(255,))
    inner=[(px,py*0.5) for px,py in poly]; inner=[(px*0.92+L*0.04,py) for px,py in inner]
    d.polygon(tr(inner),fill=tuple(hi)+(255,))
    d.line(tr([(0,0),(L*0.95,0)]),fill=tuple(int(v*0.7) for v in base)+(255,),width=max(2,int(3*S)))

def sprite_leaves(name,seed,kind='oak',size=256):
    r=np.random.default_rng(seed); SS=1024; im=Image.new('RGBA',(SS,SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    pal={'oak':((46,98,38),(96,156,58),9,120,40),'bush':((40,104,48),(88,160,70),0,92,38),'maple':((54,112,40),(120,170,56),0,130,56),'sage':((70,110,66),(130,160,100),0,110,34)}[kind]
    base0,hi0,lobes,Lf,Wf=pal
    stems=[(SS*0.5,SS*0.97,-math.pi/2+a) for a in (-0.55,-0.2,0.15,0.5)] if kind!='bush' else [(SS*0.5,SS*0.97,-math.pi/2+a) for a in (-0.9,-0.45,0,0.45,0.9)]
    leaves=[]
    for (sx,sy,sa) in stems:
        ln=SS*r.uniform(0.5,0.72); n=7
        for i in range(n):
            t=(i+1)/n; px=sx+math.cos(sa)*ln*t; py=sy+math.sin(sa)*ln*t
            for sgn in (-1,1):
                la=sa+sgn*r.uniform(0.7,1.1); leaves.append((py,px,py,la))
        leaves.append((0,sx+math.cos(sa)*ln,sy+math.sin(sa)*ln,sa))
        d.line([(sx,sy),(sx+math.cos(sa)*ln,sy+math.sin(sa)*ln)],fill=(70,52,34,255),width=7)
    leaves.sort()
    for _,x,y,a in leaves:
        k=r.uniform(0.75,1.2); v=r.uniform(0.85,1.15)
        b=[min(255,int(c*v)) for c in base0]; h=[min(255,int(c*v)) for c in hi0]
        draw_leaf(d,x,y,a,Lf*k*1.15,Wf*k*1.0,b,h,lobes,r,S=2)
    finish(im,size,name)

def sprite_pine(name,seed,size=256):
    r=np.random.default_rng(seed); SS=1024; im=Image.new('RGBA',(SS,SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    x0=SS*0.5; d.line([(x0,SS),(x0,0)],fill=(80,58,38,255),width=9)
    for i in range(70):
        y=SS*(0.98-0.96*i/70); ln=SS*0.46*(1-0.55*(i/70)**1.3)
        for sgn in (-1,1):
            for j in range(3):
                a=-math.pi/2+sgn*(1.0+j*0.12-0.6*(i/70)); 
                col=(int(30+r.uniform(0,22)),int(86+r.uniform(0,40)),int(48+r.uniform(0,22)),255)
                ex=x0+math.cos(a)*ln*r.uniform(0.8,1.0); ey=y+math.sin(a)*ln*r.uniform(0.8,1.0)*0.5
                d.line([(x0,y),(ex,ey)],fill=col,width=6)
    finish(im,size,name)

def sprite_blossom(name,seed,size=256,petal=(255,196,214),center=(214,92,128),leafy=0.25):
    r=np.random.default_rng(seed); SS=1024; im=Image.new('RGBA',(SS,SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    for sx,ang in ((SS*0.5,-0.7),(SS*0.5,-0.15),(SS*0.5,0.4),(SS*0.5,0.9)):
        a=-math.pi/2+ang; ln=SS*r.uniform(0.35,0.5); sy=SS*0.97
        d.line([(sx,sy),(sx+math.cos(a)*ln,sy+math.sin(a)*ln)],fill=(110,84,78,255),width=5)
    items=[]
    for i in range(46):
        x=r.uniform(0.1,0.9)*SS; y=r.uniform(0.08,0.92)*SS; items.append((y,x))
    items.sort()
    for y,x in items:
        if r.random()<leafy:
            draw_leaf(d,x,y,r.uniform(-math.pi,math.pi),70,24,(70,120,64),(110,160,86),0,r,S=2)
        else:
            R=r.uniform(26,40); v=r.uniform(0.9,1.04)
            for k in range(5):
                a=k*2*math.pi/5+r.uniform(0,0.4); px=x+math.cos(a)*R*0.62; py=y+math.sin(a)*R*0.62
                c=tuple(min(255,int(q*v)) for q in petal)+(255,); d.ellipse([px-R*0.58,py-R*0.58,px+R*0.58,py+R*0.58],fill=c)
            d.ellipse([x-R*0.28,y-R*0.28,x+R*0.28,y+R*0.28],fill=center+(255,))
    finish(im,size,name)

def sprite_grass(name,seed,size=256,hue=(1.0,1.0,1.0)):
    r=np.random.default_rng(seed); SS=1024; im=Image.new('RGBA',(SS,SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    for i in range(26):
        bx=SS*(0.5+r.normal()*0.12); h=SS*r.uniform(0.45,0.95); lean=r.normal()*0.2; w=r.uniform(14,26)
        pts=[]; N=14
        L=[];R=[]
        for k in range(N+1):
            t=k/N; x=bx+lean*h*t*t+math.sin(t*2+i)*8; y=SS-t*h; ww=w*(1-t)**0.8
            L.append((x-ww,y)); R.append((x+ww,y))
        g=r.uniform(0.8,1.15); base=(int(34*g*hue[0]),int(92*g*hue[1]),int(30*g*hue[2]))
        d.polygon(L+R[::-1],fill=base+(255,))
        d.line([(bx+0,SS),(bx+lean*h,SS-h)],fill=(min(255,base[0]+34),min(255,base[1]+50),min(255,base[2]+22),255),width=3)
    finish(im,size,name)

def sprite_flowers(name,seed,kind,size=256):
    r=np.random.default_rng(seed); SS=1024; im=Image.new('RGBA',(SS,SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    pet={'daisy':((250,250,246),(246,196,40)),'tulip':((226,60,84),(120,30,40)),'lav':((150,110,214),(120,80,190)),'poppy':((238,92,52),(40,30,30)),'yellow':((250,208,52),(210,140,30))}[kind]
    # folhas
    for i in range(9):
        x=SS*(0.5+r.normal()*0.16); draw_leaf(d,x,SS*0.99,-math.pi/2+r.normal()*0.5,SS*r.uniform(0.25,0.4),22,(44,104,40),(88,150,60),0,r,S=2)
    stems=[]
    for i in range(6):
        sx=SS*(0.5+r.normal()*0.16); h=SS*r.uniform(0.45,0.86); lean=r.normal()*0.12
        d.line([(sx,SS),(sx+lean*h,SS-h)],fill=(50,110,44,255),width=7)
        stems.append((sx+lean*h,SS-h))
    for x,y in stems:
        R=r.uniform(42,58)
        if kind=='daisy':
            for k in range(12):
                a=k*math.pi/6; d.ellipse([x+math.cos(a)*R*0.8-R*0.34,y+math.sin(a)*R*0.8-R*0.34,x+math.cos(a)*R*0.8+R*0.34,y+math.sin(a)*R*0.8+R*0.34],fill=pet[0]+(255,))
            d.ellipse([x-R*0.42,y-R*0.42,x+R*0.42,y+R*0.42],fill=pet[1]+(255,))
        elif kind=='tulip':
            d.polygon([(x-R*0.6,y-R*0.4),(x-R*0.3,y+R*0.9),(x+R*0.3,y+R*0.9),(x+R*0.6,y-R*0.4),(x+R*0.25,y-R*0.1),(x,y-R*0.7),(x-R*0.25,y-R*0.1)],fill=pet[0]+(255,))
        elif kind=='lav':
            for k in range(9): d.ellipse([x-R*0.2,y+k*R*0.3-R*0.22,x+R*0.2,y+k*R*0.3+R*0.1],fill=pet[(k%2)]+(255,))
        else:
            for k in range(5):
                a=k*2*math.pi/5; d.ellipse([x+math.cos(a)*R*0.55-R*0.55,y+math.sin(a)*R*0.55-R*0.55,x+math.cos(a)*R*0.55+R*0.55,y+math.sin(a)*R*0.55+R*0.55],fill=pet[0]+(255,))
            d.ellipse([x-R*0.2,y-R*0.2,x+R*0.2,y+R*0.2],fill=pet[1]+(255,))
    finish(im,size,name)

def bark(name,seed,base=((52,38,28),(122,96,70)),vert=(1.0,16),fiss=0.55,size=256):
    n=tnoise(size,*vert,seed); m=tnoise(size,3,3,seed+1); f=tnoise(size,0.8,2.5,seed+2)
    ridge=np.abs(n-0.5)*2; crev=np.clip(1-ridge*3.0,0,1)
    t=np.clip(0.35+0.55*m+0.25*(f-0.5)-fiss*crev,0,1)
    save_tex(name,lerpc(base[0],base[1],t))

def birch(name,seed,size=256):
    n=tnoise(size,2,10,seed); t=0.8+0.18*n
    img=lerpc((205,200,190),(243,240,232),t)
    r=np.random.default_rng(seed); 
    for i in range(14):
        y=r.integers(0,size); x=r.integers(0,size); w=r.integers(20,70); h=r.integers(3,8)
        for dx in range(w):
            img[(y+r.integers(-1,2))%size:(y+h)%size+1 if (y+h)%size>y%size else y,(x+dx)%size]=(40,36,34)
    save_tex(name,img)

def paint_wood(name,seed,col=(246,243,234),size=128,grain=0.07):
    n=tnoise(size,0.8,24,seed); m=tnoise(size,2,2,seed+1)
    t=1-grain*(n-0.5)*2-0.03*(m-0.5)
    img=np.array(col,float)[None,None,:]*t[...,None]
    save_tex(name,img)

if __name__=='__main__':
    sprite_leaves('leaf_oak.png',3,'oak'); sprite_leaves('leaf_bush.png',5,'bush'); sprite_leaves('leaf_maple.png',9,'maple')
    sprite_pine('leaf_pine.png',4); sprite_blossom('leaf_cherry.png',6); sprite_blossom('flw_pinkbush.png',8,petal=(250,120,150),center=(250,220,90),leafy=0.5)
    sprite_blossom('flw_whitebush.png',10,petal=(252,252,248),center=(240,200,80),leafy=0.5)
    sprite_grass('grass_a.png',11); 
    for k,sd in (('daisy',12),('tulip',13),('lav',14),('poppy',15),('yellow',16)): sprite_flowers(f'flw_{k}.png',sd,k)
    bark('bark_oak.png',21); bark('bark_cherry.png',22,base=((60,48,48),(128,108,104)),fiss=0.4); bark('bark_pine.png',23,base=((70,44,30),(142,92,60)),vert=(1.2,10),fiss=0.7)
    birch('bark_birch.png',24); paint_wood('fence_white.png',31)
    paint_wood('wood_dark.png',32,col=(98,64,42),grain=0.18)
    print('texturas ok')
