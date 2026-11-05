import numpy as np, math
from flora_lib import *
GR=MT['GRASS']; WD=MT['WOOD']; PL=MT['PLAIN']
def nrm(v): return v/(np.linalg.norm(v)+1e-9)

def rot_toward(d,rng,ang,up=0.0):
    p=np.cross(d,rng.normal(size=3)); p=nrm(p)
    nd=d*math.cos(ang)+p*math.sin(ang); nd[1]+=up; return nrm(nd)

def grow(A,bark,rng,p,d,L,r0,r1,depth,maxd,leafpts,P):
    m=max(4,int(L/0.22)); pts=[np.array(p,float)]; rad=[r0]; d=nrm(np.array(d,float))
    for i in range(1,m+1):
        d=nrm(d+rng.normal(size=3)*P['wob']+np.array([0,P['up'] if depth<=1 else P['up']*0.3-P['sag']*depth*0.1,0]))
        pts.append(pts[-1]+d*L/m); rad.append(r0+(r1-r0)*i/m)
    def col(pt,t): 
        v=min(1.0,0.82+0.25*pt[1]/4.0); return (v,v,v,1)
    A.tube((bark,WD,0),pts,rad,sides=8 if r0>0.08 else 6 if r0>0.035 else 5,vscale=1/0.55,uscale=1.0,col=col)
    if depth<maxd:
        nch=P['kids'][depth]
        for k in range(nch):
            t=rng.uniform(0.4,0.95) if k>0 else 1.0
            i=int(t*m); base=pts[i]; dd=pts[min(i+1,m)]-pts[max(i-1,0)]; dd=nrm(dd)
            cd=rot_toward(dd,rng,rng.uniform(*P['ang']),P['up']*0.5)
            grow(A,bark,rng,base,cd,L*P['shrink']*rng.uniform(0.8,1.1),rad[i]*0.72,rad[i]*0.72*0.45,depth+1,maxd,leafpts,P)
    else:
        leafpts.append(pts[-1].copy())
        if m>=3: leafpts.append(pts[m//2+1].copy())

def canopy(A,leafkey,leafpts,rng,ncards,size,P,fx=None):
    lp=np.array(leafpts); c0=lp.mean(0); R=np.linalg.norm(lp-c0,axis=1).max()+0.3
    ymin,ymax=lp[:,1].min(),lp[:,1].max()
    cen=[];nor=[];col=[]
    for i in range(ncards):
        base=lp[rng.integers(len(lp))]+rng.normal(size=3)*P['spread']
        n=nrm(base-c0+np.array([0,-0.15*R,0]))
        h=(base[1]-ymin)/(ymax-ymin+1e-6); out=np.linalg.norm(base-c0)/R
        b=P.get('bmin',0.66)+P.get('bgain',0.42)*min(1,out*0.9+0.25*h)
        tint=(1.0+0.05*h,1.0,0.88+0.1*(1-h))
        j=rng.uniform(0.93,1.07)
        cen.append(base); nor.append(n); col.append((min(1.1,b*j*tint[0]),min(1.1,b*j*tint[1]),min(1.1,b*j*tint[2]),1))
    A.cards(leafkey,cen,size,nor,col,rng)
    return c0,R

def roots(A,bark,rng,r,n=5):
    for i in range(n):
        a=i*2*math.pi/n+rng.uniform(-0.3,0.3); dd=np.array([math.cos(a),-0.35,math.sin(a)])
        p0=np.array([0,0.30,0]); pts=[p0+np.array([math.cos(a)*r*0.55,0,math.sin(a)*r*0.55])]
        for k in range(1,6): pts.append(pts[-1]+nrm(dd*np.array([1,1.9,1])+np.array([0,0.1*k,0]))*0.08*(1.0-0.1*k)+np.array([math.cos(a)*0.035,0,math.sin(a)*0.035]))
        pts=[np.array([p[0],max(p[1],-0.04),p[2]]) for p in pts]
        A.tube((bark,WD,0),pts,np.linspace(r*0.5,r*0.1,6),sides=6,vscale=1/0.55,col=lambda pt,t:(0.8,0.8,0.8,1))

def make_oak(name,seed,scale=1.0,leaf='leaf_oak.png',bark='bark_oak.png',ncards=380,csize=1.05,trunk_h=2.0,spread=1.0,tall=1.0,maxd=2,bmin=0.66,bgain=0.42):
    rng=np.random.default_rng(seed); A=Asset(name)
    P=dict(wob=0.16,up=0.10,sag=0.35,kids=[4,3,3],ang=(0.45,0.95),shrink=0.62,spread=0.32*scale,bmin=bmin,bgain=bgain)
    # tronco
    pts=[np.array([0,-0.05,0.0])]; d=np.array([0.04,1.0,0.02])
    for i in range(1,9):
        d=nrm(d+rng.normal(size=3)*0.05+np.array([0,0.05,0])); pts.append(pts[-1]+d*trunk_h/8)
    rad=np.linspace(0.26*scale,0.15*scale,9)
    A.tube((bark,WD,0),pts,rad,sides=10,vscale=1/0.55,col=lambda pt,t:(0.72+0.28*min(1,pt[1]/1.2),)*3+(1,))
    roots(A,bark,rng,0.26*scale)
    top=pts[-1]; leafpts=[]
    nb=5
    for k in range(nb):
        a=k*2*math.pi/nb+rng.uniform(-0.3,0.3)
        dd=nrm(np.array([math.cos(a)*0.85*spread,0.9*tall,math.sin(a)*0.85*spread]))
        grow(A,bark,rng,top-np.array([0,0.05,0]),dd,(1.5+rng.uniform(-0.2,0.3))*scale,0.15*scale,0.07*scale,0,maxd,leafpts,P)
    for kk in range(2):
        grow(A,bark,rng,top,nrm(np.array([rng.normal()*0.3,1,rng.normal()*0.3])),1.4*scale*tall,0.12*scale,0.06*scale,0,maxd,leafpts,P)
    c0,R=canopy(A,(leaf,GR,1),leafpts,rng,ncards,csize*scale,P)
    return A

def make_cherry(name,seed,scale=1.0):
    A=make_oak(name,seed,scale,leaf='leaf_cherry.png',bark='bark_cherry.png',ncards=330,csize=0.9,trunk_h=1.4,spread=1.5,tall=0.7,bmin=0.9,bgain=0.15)
    return A

def make_pine(name,seed,scale=1.0):
    rng=np.random.default_rng(seed); A=Asset(name); bark='bark_pine.png'; H=4.6*scale
    pts=[np.array([0,-0.05,0])+np.array([0.015*math.sin(i),i*H/10,0.015*math.cos(i)]) for i in range(11)]
    A.tube((bark,WD,0),pts,np.linspace(0.14*scale,0.015,11),sides=8,vscale=1/0.55,col=lambda pt,t:(0.75+0.25*t,)*3+(1,))
    roots(A,bark,rng,0.13*scale,4)
    cen=[];
    y=0.85*scale; k=0
    while y<H-0.2:
        t=(y)/H; L=(1.7*(1-t)**0.9+0.22)*scale; nb=7 if t<0.6 else 5
        off=rng.uniform(0,6.28)
        for b in range(nb):
            a=off+b*2*math.pi/nb+rng.uniform(-0.2,0.2); dd=np.array([math.cos(a),-0.28+0.1*t,math.sin(a)]); dd=nrm(dd)
            p0=np.array([0,y,0])
            wid=L*0.62
            # dois cartões cruzados ao longo do galho (horizontal e vertical)
            side=nrm(np.cross(dd,[0,1,0]))
            ao=0.55+0.5*(0.35+0.65*t)
            for (nv,wv) in ((np.array([0,1.0,0]),side),(nrm(np.cross(dd,side)*-1+np.array([0,0.2,0])),np.array([0,1.0,0])*0.55)):
                w=wv*wid/2 if nv[1]>0.9 else wv*wid/2
                P=[p0+w*-1,p0+w,p0+dd*L+w,p0+dd*L-w]
                P=[np.array(q) for q in P]
                nn=[nrm(np.array([dd[0]*0.6,0.7,dd[2]*0.6]))]*4
                c=(min(1.05,ao*rng.uniform(0.92,1.08)),)*3+(1,)
                # UV: base do galho embaixo do sprite
                A.add(('leaf_pine.png',GR,1),P,nn,[c]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
        y+=0.25*scale*(0.9+0.2*rng.random())
    # topo
    A.add(('leaf_pine.png',GR,1),[np.array([-0.18,H-0.9,0]),np.array([0.18,H-0.9,0]),np.array([0.18,H+0.15,0]),np.array([-0.18,H+0.15,0])]*1,[np.array([0,0.7,0.7])]*4,[(0.9,0.9,0.9,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    return A

def make_bush(name,seed,scale=1.0,leaf='leaf_bush.png',flower=None,n=70,dome=(0.62,0.5,0.62)):
    rng=np.random.default_rng(seed); A=Asset(name)
    for i in range(5):
        a=rng.uniform(0,6.28); A.tube(('bark_oak.png',WD,0),[np.array([math.cos(a)*0.05,-0.03,math.sin(a)*0.05]),np.array([math.cos(a)*0.12,0.15,math.sin(a)*0.12]),np.array([math.cos(a)*0.22,0.3,math.sin(a)*0.22])],[0.03,0.022,0.012],sides=5,col=lambda pt,t:(0.7,0.7,0.7,1))
    cen=[];nor=[];col=[]
    for i in range(n):
        v=rng.normal(size=3); v[1]=abs(v[1]); v=nrm(v)*rng.uniform(0.55,1.0)
        p=np.array([v[0]*dome[0],0.08+v[1]*dome[1]*1.05,v[2]*dome[2]])*scale
        nn=nrm(np.array([v[0],v[1]*0.9+0.2,v[2]])); h=p[1]/(dome[1]*scale+0.1); out=np.linalg.norm(v)
        b=0.62+0.45*min(1,out*0.8+0.3*h); j=rng.uniform(0.93,1.07)
        cen.append(p);nor.append(nn);col.append((b*j*(1+0.04*h),b*j,b*j*0.92,1))
    A.cards((leaf,GR,1),cen,0.62*scale,nor,col,rng)
    if flower:
        cen=[];nor=[];col=[]
        for i in range(int(n*0.35)):
            v=rng.normal(size=3); v[1]=abs(v[1])+0.2; v=nrm(v)
            p=np.array([v[0]*dome[0]*1.02,0.1+v[1]*dome[1]*1.05,v[2]*dome[2]*1.02])*scale
            cen.append(p);nor.append(nrm(np.array([v[0],v[1]*0.8+0.3,v[2]])));col.append((1,1,1,1))
        A.cards((flower,GR,1),cen,0.5*scale,nor,col,rng)
    return A

def make_hedge(name,seed,L=2.0,H=0.85,D=0.7,leaf='leaf_bush.png'):
    rng=np.random.default_rng(seed); A=Asset(name)
    cen=[];nor=[];col=[]
    n=int(L*H*D*95)+60
    for i in range(n):
        x=rng.uniform(-L/2,L/2); y=rng.uniform(0.08,H); z=rng.uniform(-D/2,D/2)
        # empurra para a superfície de uma caixa arredondada
        q=np.array([x/(L/2),(y-H/2)/(H/2),z/(D/2)]); mx=np.argmax(np.abs(q)*np.array([0.6,1.0,1.4])); 
        s=np.array([0,0,0.]); 
        if rng.random()<0.8:
            q2=q.copy(); q2[mx]=np.sign(q[mx])*rng.uniform(0.9,1.0); x,y,z=q2[0]*L/2,H/2+q2[1]*H/2,q2[2]*D/2
        nv=nrm(np.array([q[0]*0.25,(q[1]*1.0 if mx==1 else q[1]*0.4),q[2]*(1.0 if mx==2 else 0.5)])+np.array([0,0.15,0])); 
        out=min(1,np.linalg.norm(q)/1.3); h=y/H; b=0.62+0.46*min(1,out*0.7+0.4*h); j=rng.uniform(0.93,1.07)
        cen.append(np.array([x,y,z]));nor.append(nv);col.append((b*j,b*j,b*j*0.92,1))
    A.cards((leaf,GR,1),cen,0.5,nor,col,rng)
    return A

def make_grass(name,seed,n=5,R=0.45,tex='grass_a.png',size=0.5,aspect=1.0):
    rng=np.random.default_rng(seed); A=Asset(name)
    for i in range(n):
        a=rng.uniform(0,math.pi); p=np.array([rng.normal()*R*0.4,0,rng.normal()*R*0.4]); s=size*rng.uniform(0.7,1.2)
        ax=np.array([math.cos(a),0,math.sin(a)])*s/2; up=np.array([0,s*aspect,0])
        P=[p-ax,p+ax,p+ax+up,p-ax+up]
        nn=[np.array([0,1.0,0])]*4; c=[(0.62,0.62,0.62,1),(0.62,0.62,0.62,1),(1.0,1.0,1.0,1),(1.0,1.0,1.0,1)]
        A.add((tex,GR,1),P,nn,c,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    return A

def make_flowerpatch(name,seed,tex,n=6,R=0.4,size=0.45):
    return make_grass(name,seed,n,R,tex,size,aspect=1.0)

def make_fence_panel(name,L=2.0,H=0.95,seed=3):
    rng=np.random.default_rng(seed); A=Asset(name); key=('fence_white.png',WD,0)
    n=int(L/0.19); pw=0.11
    for rz in (0.28,0.7):
        A.box(key,(L/2,rz,-0.045),(L,0.08,0.035),col=(0.93,0.93,0.9,1),uv=1.2)
    for i in range(n):
        x=0.1+i*(L-0.2)/(n-1); h=H*(1+rng.uniform(-0.015,0.015))
        A.box(key,(x,h/2-0.01,0),(pw,h,0.028),col=(1,1,1,1),uv=1.4)
        # ponta triangular
        tipy=h-0.01
        P=[(x-pw/2,tipy,0.014),(x+pw/2,tipy,0.014),(x,tipy+0.07,0.014),(x-pw/2,tipy,-0.014),(x+pw/2,tipy,-0.014),(x,tipy+0.07,-0.014)]
        N=[(0,0,1)]*3+[(0,0,-1)]*3
        A.add(key,P,N,[(1,1,1,1)]*6,[(0.1,0.1),(0.9,0.1),(0.5,0.4)]*2,[(0,1,2),(3,5,4),(0,2,5),(0,5,3),(1,4,5),(1,5,2)])
        # sombra de contato na base (escurece)
    return A

def make_fence_post(name,H=1.12):
    A=Asset(name); key=('fence_white.png',WD,0)
    A.box(key,(0,H/2,0),(0.13,H,0.13),col=(0.97,0.97,0.94,1),uv=1.3)
    A.box(key,(0,H+0.02,0),(0.17,0.04,0.17),col=(0.92,0.92,0.9,1))
    P=[(-0.085,H+0.04,-0.085),(0.085,H+0.04,-0.085),(0.085,H+0.04,0.085),(-0.085,H+0.04,0.085),(0,H+0.12,0)]
    s=0.5
    N=[(-s,0.6,-s),(s,0.6,-s),(s,0.6,s),(-s,0.6,s),(0,1,0)]
    A.add(key,P,N,[(1,1,1,1)]*5,[(0,0),(1,0),(1,1),(0,1),(0.5,0.5)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
    return A

if __name__=='__main__':
    import sys
    which=sys.argv[1:]
    for nm,fn in (('oak_a',lambda:make_oak('oak_a',11)),('oak_b',lambda:make_oak('oak_b',23,1.08,leaf='leaf_maple.png',ncards=300,csize=1.0)),('cherry_a',lambda:make_cherry('cherry_a',5)),('pine_a',lambda:make_pine('pine_a',7)),
                  ('bush_a',lambda:make_bush('bush_a',2)),('bush_b',lambda:make_bush('bush_b',3,1.1,leaf='leaf_maple.png',n=60)),('bush_pink',lambda:make_bush('bush_pink',4,1.0,flower='flw_pinkbush.png')),('bush_white',lambda:make_bush('bush_white',6,0.95,flower='flw_whitebush.png')),
                  ('hedge',lambda:make_hedge('hedge',8)),('grass_a',lambda:make_grass('grass_a',1,5)),('grass_b',lambda:make_grass('grass_b',2,3,0.3,size=0.35)),
                  ('fl_daisy',lambda:make_flowerpatch('fl_daisy',1,'flw_daisy.png')),('fl_tulip',lambda:make_flowerpatch('fl_tulip',2,'flw_tulip.png')),('fl_lav',lambda:make_flowerpatch('fl_lav',3,'flw_lav.png')),('fl_poppy',lambda:make_flowerpatch('fl_poppy',4,'flw_poppy.png')),('fl_yellow',lambda:make_flowerpatch('fl_yellow',5,'flw_yellow.png')),
                  ('fence_panel',lambda:make_fence_panel('fence_panel')),('fence_post',lambda:make_fence_post('fence_post'))):
        if which and nm not in which: continue
        A=fn(); A.write(); print(nm,A.stats())
