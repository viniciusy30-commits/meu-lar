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
    # cortina franzida e presa de lado (amarrilho); fica ao lado do caixilho, colada na parede, sem passar pelo peitoril
    A=Asset(name); yb=1.95; rodY=yb+0.24; z0=0.07
    dk=(0.35,0.24,0.17)
    pwid=0.50; gap=0.10; top=rodY-0.06; hem=0.58; tie=1.22
    nx=36; ny=24
    # barra presa na parede por suportes, com ponteiras
    rl=w+2*(gap+pwid)+0.16
    rbox(A,WOODK,(0,rodY,0.1),(rl,0.03,0.03),0.013,dk,uv=2,step=0.6)
    for s_ in (-1,1):
        sphere(A,K('white',F['PLAIN']),(s_*(rl/2+0.03),rodY,0.1),0.04,dk,10)
        rbox(A,METK,(s_*(rl/2-0.08),rodY,0.05),(0.025,0.025,0.1),0.008,(0.3,0.3,0.32),uv=1,step=0.6)
    for side in (-1,1):
        xo=side*(w/2+gap+pwid)     # borda de fora (junto à parede lateral)
        def e(v):                   # largura ocupada no ponto v (0 topo ... 1 barra)
            y=top+(hem-top)*v
            d=(y-tie)
            f=math.exp(-(d/0.34)**2)          # estreita no amarrilho
            fl=max(0.0,(0.9-y)/0.35)*0.12      # abre na barra
            return pwid*(1.0-0.50*f+fl)
        P=[];N=[];C=[];UV=[];grid=[]
        for i in range(nx+1):
            t=i/nx; row=[]
            for j in range(ny+1):
                v=j/ny; y=top+(hem-top)*v
                x=xo-side*e(v)*t
                d=(y-tie); f=math.exp(-(d/0.34)**2)
                fold=0.026+0.030*f+0.012*v
                z=z0+fold*math.sin(t*math.pi*2*5.5+0.9*v)*(0.6+0.4*math.sin(v*3.0+1.0))+0.05*f*(1-t)**0.7+0.025*(1-t)
                yy=y+0.025*math.sin(t*math.pi*2*5.5+1.7)*(v**3)       # barra ondulada
                row.append(np.array([x,yy,z]))
            grid.append(row)
        for i in range(nx+1):
            for j in range(ny+1):
                p=grid[i][j]
                pu=grid[min(i+1,nx)][j]-grid[max(i-1,0)][j]; pv=grid[i][min(j+1,ny)]-grid[i][max(j-1,0)]
                n=np.cross(pv,pu); n=n/(np.linalg.norm(n)+1e-9)
                if n[2]<0: n=-n
                sh=0.80+0.20*max(0.0,min(1.0,n[2]*0.8+0.3-abs(n[0])*0.4))
                P.append(p); N.append(n); C.append((sh,sh,sh,1)); UV.append((p[0]*2.0,p[1]*2.0))
        T=[]
        for i in range(nx):
            for j in range(ny):
                a_=i*(ny+1)+j; T+=[(a_,a_+1,a_+ny+1),(a_+1,a_+ny+2,a_+ny+1)]
        A.add(K('weave',F['FABRIC']),P,N,C,UV,T)
        # amarrilho: faixa em volta da cortina, com argola
        xc=xo-side*e((tie-top)/(hem-top))*0.5
        bw=e((tie-top)/(hem-top))*0.62
        rbox(A,K('weave',F['FABRIC']),(xc,tie,z0+0.055),(bw,0.045,0.11),0.02,(0.82,0.78,0.7),uv=3,step=0.5)
        sphere(A,K('white',F['PLAIN']),(xo-side*0.02,tie,z0+0.02),0.03,(0.75,0.62,0.35),8)
    return A

def door_frame(w,name):
    A=Asset(name); dh=2.1; z=-0.075
    pbox(A,(-w/2+0.03,dh/2,z),(0.06,dh,0.19),0.01); pbox(A,(w/2-0.03,dh/2,z),(0.06,dh,0.19),0.01); pbox(A,(0,dh-0.03,z),(w,0.06,0.19),0.01)
    # guarnições internas e externas (moldura larga em volta)
    for zz,th in ((0.02,0.04),(-0.17,0.04)):
        pbox(A,(-w/2-0.045,dh/2+0.03,zz),(0.09,dh+0.06,th),0.008); pbox(A,(w/2+0.045,dh/2+0.03,zz),(0.09,dh+0.06,th),0.008)
        pbox(A,(0,dh+0.045,zz),(w+0.18,0.09,th),0.008)
    pbox(A,(0,dh+0.10,0.03),(w+0.26,0.035,0.06),0.01); pbox(A,(0,dh+0.10,-0.18),(w+0.26,0.035,0.06),0.01)
    rbox(A,K('white',F['STONE']),(0,0.012,z),(w,0.024,0.19),0.008,(0.84,0.82,0.78),uv=1,step=0.6)
    # dobradiças no batente
    hx=-w/2+0.06
    for y in (0.25,1.05,1.85): A.lathe(METK,(hx-0.005,y-0.06,-0.04),[(0.0,0),(0.014,0),(0.014,0.12),(0.0,0.12)],sides=8,col=(0.8,0.7,0.35,1))
    return A

def door_leaf(w,name):
    # folha com origem na dobradiça (x=0,z=0); estende em +x; detalhes dos dois lados
    A=Asset(name); lw=w-0.08; lk=(0.62,0.44,0.32); lt=0.045
    sty=0.12
    rbox(A,WOODK,(sty/2,1.02,0),(sty,2.04,lt),0.008,lk,uv=1.0,step=0.5)
    rbox(A,WOODK,(lw-sty/2,1.02,0),(sty,2.04,lt),0.008,lk,uv=1.0,step=0.5)
    for y,h in ((0.1,0.2),(1.05,0.14),(1.98,0.12)):
        rbox(A,WOODK,(lw/2,y if y!=0.1 else 0.1,0),(lw-0.2,h,lt),0.008,lk,uv=1.0,step=0.5)
    pw=(lw-2*sty-0.04)/2
    for side in (-1,1):
        zf=side*(lt/2)
        for (y0,y1) in ((0.2,1.0),(1.12,1.92)):
            for k in range(2):
                x0=sty+0.02+k*(pw+0.0); x1=x0+pw
                cx=(x0+x1)/2; cy=(y0+y1)/2
                # painel central rebaixado e moldura em relevo
                rbox(A,WOODK,(cx,cy,zf*0.55),(pw-0.06,y1-y0-0.06,0.014),0.006,(lk[0]*0.92,lk[1]*0.92,lk[2]*0.92),uv=1.0,step=0.5)
                for (mx,my,sx,sy) in ((cx,y0+0.02,pw-0.02,0.03),(cx,y1-0.02,pw-0.02,0.03),(x0+0.02,cy,0.03,y1-y0-0.02),(x1-0.02,cy,0.03,y1-y0-0.02)):
                    rbox(A,WOODK,(mx,my,zf*1.18),(sx,sy,0.014),0.005,(lk[0]*1.12,lk[1]*1.1,lk[2]*1.08),uv=1.0,step=0.6)
    # maçanetas de alavanca dos dois lados + espelho + fechadura
    hxp=lw-0.075
    for side in (-1,1):
        zf=side*(lt/2)
        rbox(A,METK,(hxp,1.0,zf+side*0.006),(0.05,0.2,0.012),0.006,(0.82,0.72,0.4),uv=1,step=0.6)
        A.tube(METK,[V(hxp,1.0,zf+side*0.012),V(hxp,1.0,zf+side*0.06),V(hxp-0.04,1.0,zf+side*0.075),V(hxp-0.12,1.0,zf+side*0.075)],[0.011,0.011,0.011,0.009],sides=8,col=lambda p,t:(0.85,0.74,0.4,1))
        sphere(A,K('white',F['METAL']),(hxp-0.125,1.0,zf+side*0.075),0.013,(0.85,0.74,0.4),8)
        rbox(A,METK,(hxp,0.88,zf+side*0.005),(0.035,0.06,0.01),0.004,(0.78,0.68,0.36),uv=1,step=0.6)
    # dobradiças na folha
    for y in (0.25,1.05,1.85): A.lathe(METK,(0.0,y-0.06,0.0),[(0.0,0),(0.016,0),(0.016,0.12),(0.0,0.12)],sides=8,col=(0.8,0.7,0.35,1))
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
    door_frame(1.1,'door_frame_110').write(OUT+'door_frame_110.bin'); door_leaf(1.1,'door_leaf_110').write(OUT+'door_leaf_110.bin'); wainscot().write(OUT+'wain_1.bin')
    print('ok')
