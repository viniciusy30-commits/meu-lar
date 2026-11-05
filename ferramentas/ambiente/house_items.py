import numpy as np, math
from furn_lib import *
WK=K('white',F['PLAIN']); WH=(0.97,0.96,0.93)
METK=K('metal',F['METAL']); WOODK=K('grain',F['WOOD'])
PAINT=K('fence_white.png',F['PLAIN'])   # madeira pintada de branco (veio suave)
GLASSK=K('white',F['GLASS'])
def pbox(A,c,s,r=0.008,col=WH,uv=1.0): rbox(A,PAINT,c,s,r,col,uv=uv,step=0.6)

def window(w,name):
    A=Asset(name); ya,yb=0.92,1.95; ym=(ya+yb)/2; hw=yb-ya; z=-0.075
    pbox(A,(-w/2+0.035,ym,z),(0.07,hw,0.19),0.012); pbox(A,(w/2-0.035,ym,z),(0.07,hw,0.19),0.012)
    pbox(A,(0,yb-0.035,z),(w,0.07,0.19),0.012); pbox(A,(0,ya+0.035,z),(w,0.07,0.19),0.012)
    # caixilho (folha) + travessas
    iw=w-0.14; ih=hw-0.14
    pbox(A,(0,ym,-0.07),(0.045,ih,0.05),0.008); pbox(A,(0,ya+0.07+ih*0.62,-0.07),(iw,0.04,0.05),0.008)
    for s in (-1,1): pbox(A,(s*(iw/2-0.012),ym,-0.07),(0.04,ih,0.05),0.008)
    # peitoril interno e externo, vergas
    pbox(A,(0,ya-0.01,0.065),(w+0.16,0.04,0.2),0.014); pbox(A,(0,ya-0.035,-0.20),(w+0.14,0.05,0.16),0.014)
    pbox(A,(0,yb+0.05,-0.19),(w+0.2,0.07,0.04),0.012); pbox(A,(0,yb+0.0,0.0),(w+0.12,0.05,0.06),0.01)
    # vidro
    A.add(GLASSK,[V(-iw/2,ya+0.07,-0.07),V(iw/2,ya+0.07,-0.07),V(iw/2,yb-0.07,-0.07),V(-iw/2,yb-0.07,-0.07)],[V(0,0,1)]*4,[(0.78,0.9,0.97,0.22)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    # trinco
    A.tube(METK,[V(0.03,ym-0.1,-0.04),V(0.03,ym-0.1,-0.01)],[0.01,0.01],sides=8,col=lambda p,t:BRASS+(1,))
    return A

def curtain(w,name):
    A=Asset(name); ya,yb=0.92,1.95; rodY=yb+0.25
    rbox(A,WOODK,(0,rodY,0.1),(w+0.9,0.032,0.032),0.014,(0.35,0.24,0.17),uv=2,step=0.6)
    for s in (-1,1): sphere(A,K('white',F['PLAIN']),(s*(w/2+0.47),rodY,0.1),0.045,(0.35,0.24,0.17),8)
    top=rodY-0.05; bot=ya-0.5; pw=w*0.30+0.4; nx=14; ny=6
    for side in (-1,1):
        inner=side*(w/2-w*0.30)
        P=[];N=[];C=[];UV=[];T=[]
        for i in range(nx+1):
            t=i/nx; x=inner+side*pw*t
            for j in range(ny+1):
                v=j/ny; y=top+(bot-top)*v
                z=0.085+0.032*math.sin(t*nx*1.55)*(0.55+0.45*v)+0.01*t
                dz=0.032*1.55*nx/ nx*math.cos(t*nx*1.55)*(0.55+0.45*v)/ (pw/nx)*0.0+ 0.0
                P.append(V(x,y,z)); 
                slope=0.032*math.cos(t*nx*1.55)*nx*1.55/pw*(0.55+0.45*v)*side
                N.append(nrm(V(-slope,0,1.0))); sh=0.84+0.16*math.cos(t*nx*1.55); C.append((sh,sh,sh,1)); UV.append((x*2.0,y*2.0))
        for i in range(nx):
            for j in range(ny):
                a=i*(ny+1)+j; T+=[(a,a+1,a+ny+1),(a+1,a+ny+2,a+ny+1)]
        A.add(K('weave',F['FABRIC']),P,N,C,UV,T)
    return A

def door(w,name,open_deg=105):
    A=Asset(name); dh=2.1; z=-0.075
    pbox(A,(-w/2+0.03,dh/2,z),(0.06,dh,0.19),0.01); pbox(A,(w/2-0.03,dh/2,z),(0.06,dh,0.19),0.01); pbox(A,(0,dh-0.03,z),(w,0.06,0.19),0.01)
    pbox(A,(0,dh+0.04,0.0),(w+0.14,0.07,0.05),0.01); pbox(A,(0,dh+0.04,-0.17),(w+0.14,0.07,0.04),0.01)
    rbox(A,K('stone',F['STONE']) if False else K('white',F['STONE']),(0,0.012,z),(w,0.024,0.19),0.008,(0.84,0.82,0.78),uv=1,step=0.6)
    # folha, aberta para fora, articulada no batente esquerdo
    lw=w-0.08; hx=-w/2+0.06; a=math.radians(open_deg)
    L=Asset('leaf'); lk=(0.62,0.44,0.32)
    rbox(L,WOODK,(lw/2,1.02,0.0),(lw,2.04,0.045),0.008,lk,uv=1.0,step=0.5)
    for (y,h) in ((0.55,0.7),(1.55,0.8)):
        for (x0,x1) in ((0.08,lw/2-0.04),(lw/2+0.04,lw-0.08)):
            rbox(L,WOODK,((x0+x1)/2,y,0.0225),(x1-x0,h,0.012),0.006,(lk[0]*1.08,lk[1]*1.08,lk[2]*1.08),uv=1.0,step=0.5)
    L.tube(METK,[V(lw-0.09,1.0,0.03),V(lw-0.09,1.0,0.085),V(lw-0.14,1.0,0.085)],[0.012]*3,sides=8,col=lambda p,t:BRASS+(1,))
    sphere(L,K('white',F['METAL']),(lw-0.09,1.0,0.095),0.03,BRASS,10)
    A.merge(L,t=(hx,0,-0.04),ry=a)   # gira em Y
    return A

def wainscot(name='wain_1'):
    A=Asset(name)
    pbox(A,(0.5,0.06,0.016),(1.0,0.12,0.03),0.006); pbox(A,(0.5,0.885,0.018),(1.0,0.04,0.036),0.008); pbox(A,(0.5,0.915,0.02),(1.0,0.02,0.04),0.006)
    for cx in (0.0,0.5,1.0): pbox(A,(cx,0.5,0.012),(0.07 if cx not in (0.0,1.0) else 0.035,0.76,0.022),0.004)
    for cx in (0.25,0.75): rbox(A,PAINT,(cx,0.5,0.011),(0.38,0.7,0.012),0.004,(0.93,0.92,0.89),uv=1,step=0.6)
    return A

if __name__=='__main__':
    for w in (1.9,1.25,1.6):
        n=str(int(round(w*100))); window(w,'win_'+n).write(OUT+'win_%s.bin'%n); curtain(w,'curt_'+n).write(OUT+'curt_%s.bin'%n)
    door(1.1,'door_110').write(OUT+'door_110.bin'); wainscot().write(OUT+'wain_1.bin')
    print('ok')
