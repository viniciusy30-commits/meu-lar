import numpy as np, math
from furn_lib import *
from furn_items import mug, plate, ceramic
WOODK=K('grain',F['WOOD']); FABK=K('weave',F['FABRIC']); METK=K('metal',F['METAL']); PLK=K('white',F['PLAIN']); LEATH=K('leather',F['FABRIC'])
DARK=lambda c,k=0.7:tuple(v*k for v in c)
TURN=[(0.72,0),(0.84,0.02),(0.62,0.06),(0.66,0.1),(0.95,0.16),(0.64,0.23),(0.54,0.3),(0.5,0.55),(0.56,0.7),(0.92,0.78),(0.66,0.84),(1.0,0.9),(0.95,0.98),(0.0,1.0)]
def turned(A,key,x,z,y0,h,r,col,sides=14,prof=TURN,ao=True):
    pr=[(r*a,y0+h*t) for a,t in prof]
    A.lathe(key,(x,0,z),pr,sides=sides,col=tuple(col)+(1,),uscale=1.0,vscale=1.5)
def rect_path(cx,cy,cz,w,d,rad,n=6):
    pts=[]
    for (sx,sz,a0) in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
        ccx=cx+sx*(w/2-rad); ccz=cz+sz*(d/2-rad)
        for i in range(n+1):
            a=math.radians(a0+90*i/n); pts.append(V(ccx+rad*math.cos(a),cy,ccz+rad*math.sin(a)))
    pts.append(pts[0]); return pts
def piping(A,key,cx,cy,cz,w,d,r,col,rad=0.03):
    pts=rect_path(cx,cy,cz,w,d,rad); A.tube(key,pts,[r]*len(pts),sides=6,col=lambda p,t:tuple(col)+(1,))
def cushion(A,c,size,col,pip=None,uv=3.0,puff=0.03,r=0.05,rot=0.0,step=0.12):
    rbox(A,FABK,c,size,r,col,uv=uv,puff=puff,step=step,rot=rot)
    if pip is not None and rot==0.0:
        x,y,z=c; w,h,d=size
        piping(A,FABK,x,y+h/2-r*0.55,z,w-0.012,d-0.012,0.0075,pip,rad=r)
        piping(A,FABK,x,y-h/2+r*0.55,z,w-0.012,d-0.012,0.0075,pip,rad=r)
def button(A,x,y,z,r=0.012,col=(0.2,0.2,0.2)):
    sphere(A,PLK,(x,y,z),r,col,7,sy=0.6)
def knob(A,x,y,z,col=BRASS,r=0.018):
    A.lathe(METK,(x,y,z),[(0,0),(0.004,0),(0.006,0.008),(0.006,0.014)],sides=10,col=col+(1,))
    sphere(A,METK,(x,y,z+0.0),r,col,9)
def knob_z(A,x,y,z,col=BRASS,r=0.018):
    A.tube(METK,[V(x,y,z),V(x,y,z+0.02)],[0.006,0.006],sides=8,col=lambda p,t:col+(1,))
    sphere(A,METK,(x,y,z+0.026),r,col,10,sy=0.8)
def pull(A,x,y,z,w=0.1,col=BRASS):
    """puxador de gaveta: espelho + barra em arco"""
    rbox(A,METK,(x,y,z),(w+0.03,0.03,0.005),0.002,DARK(col,0.85),uv=1,step=1)
    pts=[V(x-w/2,y,z+0.003),V(x-w/2,y,z+0.022),V(x-w/4,y-0.012,z+0.03),V(x+w/4,y-0.012,z+0.03),V(x+w/2,y,z+0.022),V(x+w/2,y,z+0.003)]
    A.tube(METK,pts,[0.0055]*6,sides=8,col=lambda p,t:col+(1,))
def molding(A,key,x0,x1,y,z0,z1,col,layers=3,h=0.03,out=0.014):
    for i in range(layers):
        o=out*(i+1)/layers
        rbox(A,key,((x0+x1)/2,y+i*h*0.7,(z0+z1)/2),((x1-x0)+2*o,h,(z1-z0)+2*o),0.008,tuple(v*(1.0-0.04*i) for v in col),uv=1.0,step=0.5)
def pleated_shade(A,c,r0,r1,h,col,n=40,key=None,emit=False):
    key=key or K('weave',F['PLAIN'])
    x,y,z=c; P=[];N=[];C=[];UV=[];T=[]
    for i in range(n):
        a0=2*math.pi*i/n; a1=2*math.pi*(i+1)/n; am=(a0+a1)/2
        f=1.0+(0.03 if i%2==0 else -0.0)
        verts=[]
        for (a,rr,yy,u,v) in ((a0,r0,0,i/n*6,0),(a1,r0,0,(i+1)/n*6,0),(a1,r1,h,(i+1)/n*6,1),(a0,r1,h,i/n*6,1)):
            ff=1.0 if (i%2==1) else 1.04
            verts.append((x+math.cos(a)*rr*ff,y+yy,z+math.sin(a)*rr*ff,u,v))
        nn=np.array([math.cos(am),(r0-r1)/h,math.sin(am)]); nn/=np.linalg.norm(nn)
        b=len(P)
        for (px,py,pz,u,v) in verts:
            P.append((px,py,pz)); N.append(nn); C.append(tuple(col)+(1,)); UV.append((u,v))
        T+=[(b,b+1,b+2),(b,b+2,b+3)]
    A.add(key,P,N,C,UV,T)
def fruit(A,x,y,z,r,col,stem=True):
    sphere(A,PLK,(x,y+r*0.9,z),r,col,10,sy=0.92)
    if stem: A.tube(PLK,[V(x,y+r*1.8,z),V(x+0.003,y+r*2.15,z)],[0.0025]*2,sides=5,col=lambda p,t:(0.3,0.2,0.1,1))
def fork(A,x,y,z,ang=0.0,col=(0.85,0.87,0.9)):
    c,s=math.cos(ang),math.sin(ang)
    def P(dx,dz): return V(x+dx*c-dz*s,y,z+dx*s+dz*c)
    A.tube(METK,[P(0,-0.09),P(0,0.02)],[0.003,0.0035],sides=6,col=lambda p,t:col+(1,))
    for dx in (-0.007,-0.0024,0.0024,0.007): A.tube(METK,[P(dx,0.02),P(dx,0.065)],[0.0012]*2,sides=5,col=lambda p,t:col+(1,))
def knife(A,x,y,z,ang=0.0,col=(0.85,0.87,0.9)):
    c,s=math.cos(ang),math.sin(ang)
    def P(dx,dz): return V(x+dx*c-dz*s,y,z+dx*s+dz*c)
    A.tube(METK,[P(0,-0.09),P(0,0.0)],[0.005,0.0045],sides=6,col=lambda p,t:(0.2,0.2,0.22,1))
    rbox(A,METK,(x+0.0*c,y,z+0.045*c),(0.008,0.003,0.09),0.0015,col,uv=1,step=1,rot=-ang)
def glass(A,x,y,z,s=1.0):
    A.lathe(PLK,(x,y,z),[(0,0),(0.032*s,0),(0.034*s,0.004*s),(0.004*s,0.008*s),(0.004*s,0.08*s),(0.03*s,0.11*s),(0.036*s,0.17*s),(0.03*s,0.2*s),(0.027*s,0.19*s),(0.032*s,0.17*s),(0.026*s,0.115*s),(0.0,0.1*s)],sides=20,col=(0.86,0.93,0.98,1))
def book_stack(A,x,y,z,items,rng=None):
    for i,(w,d,h,col,rot) in enumerate(items):
        rbox(A,FABK,(x,y+h/2,z),(w,h,d),0.006,col,uv=3,step=0.4,rot=rot)
        rbox(A,PLK,(x,y+h/2,z+0.003),(w-0.014,h-0.01,d-0.008),0.002,(0.96,0.94,0.88),uv=1,step=1,rot=rot)
        y+=h
