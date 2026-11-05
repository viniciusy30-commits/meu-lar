import numpy as np, math
from detail_lib import *
from furn_items import vase_flowers
ITEMS2={}
def reg(n):
    def d(f): ITEMS2[n]=f; return f
    return d
@reg('sofa')
def sofa(seed=4):
    A=Asset('f_sofa'); tl=(0.19,0.50,0.50); tl2=(0.23,0.58,0.57); dk=(0.15,0.40,0.41); wood=(0.55,0.36,0.24)
    # pés torneados
    for x in (0.16,1.84):
        for z in (0.17,0.84): turned(A,WOODK,x,z,0.0,0.15,0.03,wood,sides=14)
    # estrutura e base
    rbox(A,WOODK,(1.0,0.18,0.5),(1.84,0.06,0.78),0.01,wood,uv=1.5,step=0.5)
    rbox(A,FABK,(1.0,0.26,0.52),(1.9,0.14,0.84),0.05,dk,uv=2.5,puff=0.01,step=0.3,ao=gao(0.3,0.7))
    piping(A,FABK,1.0,0.325,0.52,1.9,0.84,0.008,(0.1,0.3,0.3),rad=0.05)
    # costas com capitonê
    rbox(A,FABK,(1.0,0.68,0.13),(1.64,0.66,0.2),0.07,tl,uv=2.5,puff=0.02,step=0.2)
    for r_ in range(3):
        for c_ in range(7):
            bx=0.38+c_*0.21+(0.105 if r_%2 else 0); by=0.5+r_*0.17
            if bx>1.64 or bx<0.36: continue
            button(A,bx,by,0.238,0.012,(0.1,0.28,0.29))
    for r_ in range(2):
        for c_ in range(6):
            bx=0.485+c_*0.21; by=0.585+r_*0.17
            A.tube(FABK,[V(bx-0.105,by-0.085,0.236),V(bx,by,0.24)],[0.0035]*2,sides=5,col=lambda p,t:(0.1,0.3,0.3,1))
    # braços enrolados
    for sx in (0.1,1.9):
        rbox(A,FABK,(sx,0.45,0.52),(0.2,0.34,0.84),0.07,tl,uv=2.5,puff=0.02,step=0.2)
        A.tube(FABK,[V(sx,0.66,0.1),V(sx,0.66,0.52),V(sx,0.66,0.92)],[0.095]*3,sides=18,col=lambda p,t:tl+(1,),uscale=3,vscale=3)
        sphere(A,FABK,(sx,0.66,0.93),0.095,tl,14,uv=3); sphere(A,FABK,(sx,0.66,0.1),0.095,tl,14,uv=3)
        for z in np.linspace(0.18,0.84,8): sphere(A,METK,(sx+(0.1 if sx<1 else -0.1)*-1.0*0+((-0.1) if sx<1 else 0.1),0.5,z),0.0065,BRASS,6)
    # almofadas do assento
    for x in (0.6,1.4):
        cushion(A,(x,0.44,0.61),(0.76,0.16,0.64),tl2,pip=(0.12,0.33,0.33),puff=0.04,r=0.06)
        A.tube(FABK,[V(x-0.34,0.505,0.62),V(x,0.515,0.62),V(x+0.34,0.505,0.62)],[0.003]*3,sides=5,col=lambda p,t:(0.12,0.34,0.34,1)) if False else None
    for x in (0.6,1.4):
        cushion(A,(x,0.7,0.3),(0.76,0.42,0.17),tl2,pip=(0.12,0.33,0.33),puff=0.05,r=0.07)
        button(A,x,0.72,0.395,0.011,(0.1,0.28,0.29))
    # almofadas decorativas e manta
    rbox(A,FABK,(0.4,0.7,0.52),(0.3,0.3,0.1),0.05,(0.93,0.62,0.28),uv=3,puff=0.055,step=0.1,rot=0.25)
    rbox(A,FABK,(1.62,0.7,0.52),(0.3,0.3,0.1),0.05,(0.96,0.92,0.82),uv=3,puff=0.055,step=0.1,rot=-0.3)
    rbox(A,FABK,(1.7,0.72,0.56),(0.24,0.24,0.08),0.04,(0.82,0.4,0.32),uv=3,puff=0.05,step=0.1,rot=0.1)
    rbox(A,FABK,(1.2,0.56,0.6),(0.6,0.035,0.46),0.016,(0.94,0.86,0.7),uv=3,puff=0.015,step=0.12,rot=0.18)
    rbox(A,FABK,(1.22,0.585,0.62),(0.5,0.03,0.4),0.014,(0.9,0.8,0.62),uv=3,puff=0.015,step=0.12,rot=0.1)
    return A
@reg('chair')
def chair(seed=1):
    A=Asset('f_chair'); wd=(0.86,0.64,0.42); wd2=(0.78,0.56,0.36); cu=(0.82,0.32,0.28)
    # pernas dianteiras torneadas, traseiras retas que sobem ate o encosto
    for x in (0.28,0.72): turned(A,WOODK,x,0.74,0.0,0.46,0.026,wd,sides=14)
    for x in (0.28,0.72):
        A.tube(WOODK,[V(x,0.0,0.27),V(x,0.46,0.265),V(x,0.98,0.235)],[0.022,0.021,0.016],sides=10,vscale=2,col=lambda p,t:tuple(wd[i]*(0.72+0.28*min(1,p[1]/0.3)) for i in range(3))+(1,))
    # travessas
    for (y,z0,z1) in ((0.2,0.27,0.74),):
        for x in (0.28,0.72): A.tube(WOODK,[V(x,y,z0),V(x,y,z1)],[0.011,0.011],sides=8,col=lambda p,t:wd2+(1,))
    A.tube(WOODK,[V(0.28,0.24,0.5),V(0.72,0.24,0.5)],[0.011,0.011],sides=8,col=lambda p,t:wd2+(1,))
    # avental do assento e assento
    rbox(A,WOODK,(0.5,0.425,0.505),(0.46,0.07,0.47),0.014,wd2,uv=2)
    rbox(A,WOODK,(0.5,0.47,0.505),(0.5,0.028,0.5),0.012,wd,uv=2,ao=gao(0.5,0.85))
    cushion(A,(0.5,0.51,0.515),(0.43,0.065,0.42),cu,pip=(0.6,0.2,0.18),puff=0.02,r=0.026)
    for dx in (-0.14,0.14):
        for dz in (-0.13,0.13): button(A,0.5+dx,0.546,0.515+dz,0.008,(0.55,0.18,0.16))
    # encosto: travessa curva no alto, ripas torneadas e travessa do meio
    rbox(A,WOODK,(0.5,0.94,0.245),(0.5,0.1,0.034),0.016,wd,uv=2)
    A.lathe(WOODK,(0.5,0.0,0.245),[(0,0.99),(0.0,0.99)],sides=4)
    rbox(A,WOODK,(0.5,1.0,0.245),(0.34,0.03,0.028),0.012,wd,uv=2)
    rbox(A,WOODK,(0.5,0.62,0.255),(0.43,0.04,0.026),0.011,wd2,uv=2)
    for x in (0.37,0.5,0.63):
        turned(A,WOODK,x,0.255,0.64,0.26,0.012,wd,sides=10,prof=[(0.8,0),(1.0,0.2),(0.7,0.5),(1.0,0.8),(0.8,1.0),(0,1.0)])
        turned(A,WOODK,x,0.255,0.56,0.08,0.012,wd,sides=8,prof=[(0.8,0),(1.0,0.5),(0.8,1.0),(0,1.0)])
    for x in (0.28,0.72): sphere(A,WOODK,(x,0.995,0.235),0.02,wd,10)
    return A
@reg('table')
def table(seed=2):
    A=Asset('f_table'); wd=(0.88,0.66,0.44); dk=(0.66,0.46,0.3)
    for x in (0.2,1.8):
        for z in (0.19,0.81): turned(A,WOODK,x,z,0.0,0.74,0.036,dk,sides=16)
    # tampo com borda boleada e avental com friso
    rbox(A,WOODK,(1.0,0.775,0.5),(1.94,0.045,0.94),0.02,wd,uv=1.0,ao=lambda w:1.0)
    rbox(A,WOODK,(1.0,0.742,0.5),(1.96,0.02,0.96),0.008,dk,uv=1.0)
    rbox(A,WOODK,(1.0,0.68,0.19),(1.58,0.09,0.03),0.008,dk,uv=1.2); rbox(A,WOODK,(1.0,0.68,0.81),(1.58,0.09,0.03),0.008,dk,uv=1.2)
    for x in (0.21,1.79): rbox(A,WOODK,(x,0.68,0.5),(0.03,0.09,0.58),0.008,dk,uv=1.2)
    for z in (0.19,0.81):
        for x in np.linspace(0.45,1.55,9): sphere(A,WOODK,(x,0.68,z+(0.017 if z>0.5 else -0.017)),0.007,dk,6)
    rbox(A,WOODK,(1.0,0.775,0.5),(0.006,0.047,0.92),0.001,(0.45,0.3,0.2),uv=1,step=1)  # emenda do tampo
    # trilho de mesa bordado
    rbox(A,FABK,(1.0,0.8,0.5),(1.56,0.006,0.3),0.003,(0.92,0.88,0.78),uv=3,step=0.5)
    for z in (0.36,0.64): rbox(A,FABK,(1.0,0.803,z),(1.56,0.002,0.012),0.0008,(0.7,0.28,0.24),uv=2,step=1)
    for x in (0.38,1.62): rbox(A,FABK,(x,0.803,0.5),(0.012,0.002,0.3),0.0008,(0.7,0.28,0.24),uv=2,step=1)
    # pratos, talheres e copos
    for x in (0.5,1.5):
        for (z,s) in ((0.8,1),(0.2,-1)):
            plate(A,x,0.8,z+(-0.04*s),0.13)
            ceramic(A,(x,0.8,z+(-0.04*s)),[(0.0,0.004),(0.07,0.006),(0.085,0.02),(0.0,0.012)],(0.88,0.92,0.95),22)
            fork(A,x-0.19,0.8,z-0.04*s,0.0 if s>0 else math.pi); knife(A,x+0.19,0.8,z-0.04*s,0.0 if s>0 else math.pi)
            glass(A,x+0.12,0.8,z-0.19*s,1.0)
            rbox(A,FABK,(x,0.804,z-0.0*s+(0.12 if s>0 else -0.12)),(0.1,0.006,0.1),0.003,(0.7,0.28,0.24),uv=2,step=1) if False else None
    # centro: jarro, tigela de frutas e velas
    vase_flowers(A,1.0,0.8,0.5,1.0,'flw_daisy.png')
    ceramic(A,(0.7,0.8,0.5),[(0,0),(0.07,0),(0.09,0.015),(0.15,0.075),(0.155,0.08),(0.14,0.082),(0.085,0.03),(0,0.025)],(0.9,0.88,0.82),24)
    for (dx,dz,c) in ((0,0,(0.86,0.2,0.18)),(0.06,0.02,(0.95,0.78,0.2)),(-0.05,0.04,(0.5,0.72,0.25)),(0.01,-0.06,(0.95,0.5,0.15)),(-0.03,-0.03,(0.86,0.2,0.18))): fruit(A,0.7+dx,0.835+(0.01 if dx==0 else 0),0.5+dz,0.032,c)
    for x in (1.3,1.42):
        ceramic(A,(x,0.8,0.5),[(0,0),(0.032,0),(0.034,0.01),(0.012,0.025),(0.012,0.1),(0.026,0.11),(0.0,0.11)],(0.78,0.65,0.35),14)
        A.lathe(PLK,(x,0.89,0.5),[(0.0,0.0),(0.01,0.0),(0.01,0.1),(0.0,0.1)],sides=10,col=(0.96,0.94,0.88,1))
        A.lathe(PLK,(x,0.99,0.5),[(0.0,0.0),(0.004,0.0),(0.0,0.035)],sides=8,col=(1.0,0.75,0.2,1))
    return A
@reg('bed')
def bed(seed=3):
    A=Asset('f_bed'); wd=(0.5,0.33,0.22); wl=(0.62,0.42,0.28); lin=(0.95,0.94,0.9)
    for x in (0.06,0.94):
        for z in (0.05,1.95): turned(A,WOODK,x,z,0.0,0.22,0.036,wd,sides=14)
    # cabeceira estofada alta com colunas
    for x in (0.06,0.94): turned(A,WOODK,x,0.05,0.2,1.0,0.034,wd,sides=14)
    for x in (0.06,0.94): sphere(A,WOODK,(x,1.24,0.05),0.04,wd,12)
    rbox(A,WOODK,(0.5,0.92,0.05),(0.9,0.08,0.05),0.02,wd,uv=1.2); rbox(A,WOODK,(0.5,0.34,0.05),(0.9,0.12,0.05),0.02,wd,uv=1.2)
    rbox(A,FABK,(0.5,0.64,0.075),(0.78,0.5,0.06),0.035,(0.38,0.46,0.58),uv=3,puff=0.03,step=0.12)
    for r_ in range(3):
        for c_ in range(4):
            button(A,0.275+c_*0.15,0.48+r_*0.15,0.108,0.011,(0.22,0.28,0.4))
    # pe da cama baixo e laterais
    rbox(A,WOODK,(0.5,0.42,1.96),(0.9,0.2,0.05),0.02,wd,uv=1.2); turned(A,WOODK,0.06,1.95,0.2,0.34,0.034,wd,sides=14); turned(A,WOODK,0.94,1.95,0.2,0.34,0.034,wd,sides=14)
    for x in (0.045,0.955): rbox(A,WOODK,(x,0.3,1.0),(0.04,0.14,1.86),0.012,wl,uv=1.2)
    rbox(A,WOODK,(0.5,0.28,1.0),(0.88,0.025,1.86),0.006,wl,uv=1.5)
    # colchao com vivo, lencol e edredom dobrado
    rbox(A,FABK,(0.5,0.4,1.02),(0.88,0.2,1.84),0.06,(0.97,0.96,0.93),uv=3,puff=0.012,step=0.25)
    piping(A,FABK,0.5,0.485,1.02,0.88,1.84,0.008,(0.8,0.8,0.78),rad=0.06)
    piping(A,FABK,0.5,0.32,1.02,0.88,1.84,0.008,(0.8,0.8,0.78),rad=0.06)
    rbox(A,FABK,(0.5,0.52,1.36),(0.92,0.07,1.36),0.04,(0.34,0.5,0.72),uv=2.5,puff=0.025,step=0.2)
    for z in np.linspace(0.75,1.95,9): rbox(A,FABK,(0.5,0.558,z),(0.9,0.006,0.012),0.003,(0.26,0.4,0.62),uv=1,step=1)
    rbox(A,FABK,(0.5,0.58,0.78),(0.94,0.06,0.3),0.03,(0.92,0.9,0.86),uv=2.5,puff=0.03,step=0.15)   # dobra do lençol
    rbox(A,FABK,(0.5,0.57,1.82),(0.9,0.05,0.4),0.025,(0.88,0.66,0.3),uv=2.5,puff=0.025,step=0.15)  # manta
    for z in np.linspace(1.64,2.0,6): rbox(A,FABK,(0.5,0.6,z),(0.9,0.005,0.01),0.002,(0.74,0.54,0.22),uv=1,step=1)
    for x,rz in ((0.27,0.05),(0.73,-0.04)): rbox(A,FABK,(x,0.62,0.4),(0.38,0.13,0.28),0.05,(0.98,0.97,0.94),uv=3,puff=0.06,step=0.12,rot=rz)
    for x,rz in ((0.27,0.0),(0.73,0.0)): rbox(A,FABK,(x,0.7,0.27),(0.36,0.14,0.2),0.05,(0.8,0.85,0.92),uv=3,puff=0.06,step=0.12,rot=rz)
    return A
@reg('shelf')
def shelf(seed=5):
    A=Asset('f_shelf'); wd=(0.7,0.48,0.32); dk=(0.52,0.34,0.22); r=np.random.default_rng(seed)
    # corpo: laterais com friso, tampo com cornija, base com rodapé recortado, fundo
    for x in (0.045,1.955): rbox(A,WOODK,(x,0.95,0.2),(0.09,1.9,0.4),0.012,wd,uv=1.2,step=0.5)
    for x in (0.0,2.0): pass
    rbox(A,WOODK,(1.0,0.96,0.012),(1.84,1.76,0.024),0.002,dk,uv=1.0,step=0.6)
    rbox(A,WOODK,(1.0,1.88,0.2),(2.0,0.05,0.42),0.014,wd,uv=1.2,step=0.5)
    molding(A,WOODK,0.0,2.0,1.9,0.0,0.4,wd,layers=3,h=0.028,out=0.03)
    rbox(A,WOODK,(1.0,0.07,0.2),(1.82,0.14,0.4),0.01,dk,uv=1.2,step=0.5)
    rbox(A,WOODK,(1.0,0.02,0.4),(1.9,0.04,0.025),0.006,wd,uv=1.2)
    rbox(A,WOODK,(1.0,0.145,0.205),(1.86,0.02,0.41),0.008,wd,uv=1.2,step=0.5)
    ys=[0.5,0.92,1.34]
    for y in ys:
        rbox(A,WOODK,(1.0,y,0.2),(1.82,0.032,0.38),0.008,wd,uv=1.2,step=0.5)
        rbox(A,WOODK,(1.0,y,0.395),(1.82,0.036,0.01),0.004,dk,uv=1.2,step=0.5)
        for x in (0.15,1.85):
            sphere(A,METK,(x,y-0.03,0.34),0.008,BRASS,6)
    # prateleira 1 (0.16-0.5): livros em fileira e um estojo
    levels=[0.151,0.516,0.936,1.356]
    books(A,(0.12,levels[0],0.2),1.0,r,0.3,0.22)
    rbox(A,FABK,(1.28,levels[0]+0.12,0.2),(0.28,0.24,0.28),0.03,(0.78,0.45,0.32),uv=3,puff=0.01,step=0.3)
    rbox(A,FABK,(1.28,levels[0]+0.245,0.2),(0.3,0.03,0.3),0.014,(0.66,0.36,0.26),uv=3)
    rbox(A,FABK,(1.62,levels[0]+0.12,0.2),(0.28,0.24,0.28),0.03,(0.36,0.52,0.7),uv=3,puff=0.01,step=0.3)
    rbox(A,FABK,(1.62,levels[0]+0.245,0.2),(0.3,0.03,0.3),0.014,(0.28,0.42,0.6),uv=3)
    # prateleira 2: livros deitados + inclinados
    books(A,(0.12,levels[1],0.2),0.8,r,0.3,0.22)
    book_stack(A,1.1,levels[1],0.2,[(0.26,0.2,0.04,(0.6,0.22,0.2),0.1),(0.24,0.19,0.035,(0.2,0.45,0.35),-0.08),(0.22,0.18,0.03,(0.9,0.7,0.25),0.05)])
    sphere(A,PLK,(1.1,levels[1]+0.135,0.2),0.03,(0.8,0.4,0.3),8)
    # globo
    A.lathe(METK,(1.55,levels[1],0.2),[(0,0),(0.07,0),(0.07,0.012),(0.012,0.025),(0.012,0.08)],sides=16,col=BRASS+(1,))
    sphere(A,PLK,(1.55,levels[1]+0.18,0.2),0.1,(0.35,0.58,0.78),20)
    A.tube(METK,[V(1.55,levels[1]+0.08,0.2)+V(-0.1,0,0.02)*0,V(1.55,levels[1]+0.3,0.2)],[0.003,0.003],sides=6,col=lambda p,t:BRASS+(1,))
    ring_pts=[V(1.55+0.115*math.cos(a),levels[1]+0.18+0.115*math.sin(a),0.2) for a in np.linspace(-1.1,1.9,18)]
    A.tube(METK,ring_pts,[0.004]*len(ring_pts),sides=6,col=lambda p,t:BRASS+(1,))
    # prateleira 3: vaso com planta, porta-retratos, relógio
    ceramic(A,(0.3,levels[2],0.2),[(0,0),(0.06,0),(0.09,0.12),(0.1,0.15),(0.0,0.15)],(0.76,0.4,0.24),22)
    for i in range(9):
        a=i*0.7; A.add(('leaf_fig.png',F['GRASS'],1),[V(0.3,levels[2]+0.16,0.2)+V(math.cos(a)*0.03,0,math.sin(a)*0.03)-V(0.1,0,0),V(0.3,levels[2]+0.16,0.2)+V(math.cos(a)*0.03,0,math.sin(a)*0.03)+V(0.1,0,0),V(0.3,levels[2]+0.16,0.2)+V(math.cos(a)*0.13,0.22,math.sin(a)*0.13)+V(0.12,0,0),V(0.3,levels[2]+0.16,0.2)+V(math.cos(a)*0.13,0.22,math.sin(a)*0.13)-V(0.12,0,0)],[nrm(V(math.cos(a),0.6,math.sin(a)))]*4,[(0.8,0.8,0.8,1)]*2+[(1,1,1,1)]*2,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    rbox(A,WOODK,(0.75,levels[2]+0.14,0.24),(0.2,0.26,0.02),0.008,(0.28,0.2,0.15),uv=2)
    A.add(('art_a.png',F['PLAIN'],0),[V(0.67,levels[2]+0.06,0.251),V(0.83,levels[2]+0.06,0.251),V(0.83,levels[2]+0.22,0.251),V(0.67,levels[2]+0.22,0.251)],[V(0,0,1)]*4,[(1,1,1,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    rbox(A,WOODK,(1.15,levels[2]+0.1,0.2),(0.2,0.2,0.12),0.014,(0.66,0.46,0.3),uv=2)
    A.lathe(PLK,(1.15,levels[2]+0.1,0.262),[(0,0),(0.075,0),(0.075,0.004),(0,0.004)],sides=24,col=(0.96,0.94,0.9,1))
    rbox(A,PLK,(1.15,levels[2]+0.1,0.263),(0.006,0.05,0.001),0.0005,(0.1,0.1,0.12),uv=1,step=1); rbox(A,PLK,(1.15,levels[2]+0.12,0.263),(0.04,0.005,0.001),0.0005,(0.1,0.1,0.12),uv=1,step=1)
    vase_flowers(A,1.6,levels[2],0.2,0.8,'flw_tulip.png',col=(0.88,0.6,0.35))
    # prateleira de cima: caixas de tecido, quadro e livros
    for x,cl in ((0.28,(0.8,0.4,0.3)),(0.66,(0.36,0.52,0.7)),(1.04,(0.88,0.74,0.4))):
        rbox(A,FABK,(x,levels[3]+0.09,0.2),(0.32,0.18,0.3),0.03,cl,uv=3,puff=0.01,step=0.3)
        rbox(A,FABK,(x,levels[3]+0.185,0.2),(0.34,0.02,0.32),0.012,tuple(v*0.85 for v in cl),uv=3)
        rbox(A,PLK,(x,levels[3]+0.1,0.36),(0.1,0.04,0.012),0.008,(0.3,0.26,0.22),uv=1)
    rbox(A,WOODK,(1.55,levels[3]+0.19,0.24),(0.3,0.36,0.025),0.01,(0.3,0.2,0.15),uv=2)
    A.add(('art_a.png',F['PLAIN'],0),[V(1.42,levels[3]+0.06,0.2565),V(1.68,levels[3]+0.06,0.2565),V(1.68,levels[3]+0.32,0.2565),V(1.42,levels[3]+0.32,0.2565)],[V(0,0,1)]*4,[(1,1,1,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    return A
@reg('plant')
def plant(seed=6):
    A=Asset('f_plant'); r=np.random.default_rng(seed)
    prof=[(0,0),(0.13,0),(0.15,0.02),(0.19,0.30),(0.215,0.33),(0.225,0.355),(0.23,0.4),(0.22,0.42),(0.2,0.42),(0.19,0.385),(0,0.38)]
    ceramic(A,(0.5,0.0,0.5),prof,(0.82,0.46,0.3),32)
    for y in (0.1,0.2): ceramic(A,(0.5,y,0.5),[(0.1+0.07*y/0.2+0.0,0),(0.17+0.045*y/0.2,0.0),(0.175+0.045*y/0.2,0.008),(0.1,0.01)],(0.7,0.38,0.24),32)
    ceramic(A,(0.5,0.0,0.5),[(0.2,0),(0.27,0.0),(0.285,0.02),(0.27,0.03),(0.2,0.025)],(0.74,0.4,0.26),32)
    A.lathe(K('white',F['PLAIN']),(0.5,0.375,0.5),[(0,0),(0.19,0)],sides=24,col=(0.22,0.15,0.1,1))
    for i in range(26):
        a=r.uniform(0,6.28); d=r.uniform(0.05,0.17); sphere(A,PLK,(0.5+d*math.cos(a),0.378,0.5+d*math.sin(a)),r.uniform(0.01,0.018),(0.6+r.uniform(0,0.2),)*3 if False else (0.62,0.58,0.52),6,sy=0.6)
    cen=[];nor=[];col=[];stems=[]
    for i in range(7):
        a=i*2*math.pi/7+r.uniform(0,0.6); lean=r.uniform(0.05,0.2); h=r.uniform(0.75,1.2)
        pts=[V(0.5,0.38,0.5),V(0.5+math.cos(a)*lean*0.4,0.38+h*0.5,0.5+math.sin(a)*lean*0.4),V(0.5+math.cos(a)*lean,0.38+h,0.5+math.sin(a)*lean)]
        A.tube(WOODK,pts,[0.017,0.012,0.008],sides=6,col=lambda p,t:(0.5,0.4,0.28,1)); stems.append(pts[-1])
    for i in range(62):
        s=stems[i%7]; t=r.uniform(0.25,1.0); base=V(0.5,0.38,0.5)+(s-V(0.5,0.38,0.5))*t
        a=r.uniform(0,6.28); out=V(math.cos(a),r.uniform(0.15,0.8),math.sin(a)); c=base+out*0.08
        h=(c[1]-0.38)/1.0; b=0.6+0.45*min(1,h*1.2)
        cen.append(c);nor.append(nrm(out+V(0,0.3,0)));col.append((b,b,b*0.95,1))
    A.cards(('leaf_fig.png',F['GRASS'],1),cen,0.42,nor,col,r,aspect=1.0)
    return A
@reg('rug')
def rug(seed=7):
    A=Asset('f_rug')
    rbox(A,K('weave',F['RUG']),(1.0,0.011,1.0),(1.84,0.022,1.84),0.008,(0.55,0.5,0.46),uv=3,step=0.5)
    A.add(('rug_a.png',F['RUG'],0),[V(0.08,0.0222,1.92),V(1.92,0.0222,1.92),V(1.92,0.0222,0.08),V(0.08,0.0222,0.08)],[V(0,1,0)]*4,[(1,1,1,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    # franjas nas duas pontas
    for x in np.linspace(0.1,1.9,38):
        for z0,sg in ((0.08,-1),(1.92,1)):
            A.tube(FABK_,[V(x,0.012,z0),V(x,0.01,z0+sg*0.05),V(x,0.006,z0+sg*0.09)],[0.004,0.0035,0.003],sides=4,col=lambda p,t:(0.9,0.86,0.76,1)) if False else A.tube(K('weave',F['RUG']),[V(x,0.012,z0),V(x,0.01,z0+sg*0.05),V(x,0.006,z0+sg*0.09)],[0.004,0.0035,0.003],sides=4,col=lambda p,t:(0.92,0.88,0.78,1))
    return A
@reg('tv')
def tv(seed=8):
    A=Asset('f_tv'); wd=(0.62,0.42,0.28); dk=(0.46,0.3,0.2); lt=(0.7,0.5,0.34)
    for x in (0.16,1.84):
        for z in (0.3,0.7): turned(A,WOODK,x,z,0.0,0.16,0.026,dk,sides=12,prof=[(1.0,0),(0.7,0.2),(0.9,0.5),(0.6,0.8),(1.0,1.0),(0,1.0)])
    rbox(A,WOODK,(1.0,0.34,0.5),(1.9,0.36,0.52),0.02,wd,uv=1.2,step=0.4,ao=gao(0.4,0.8))
    rbox(A,WOODK,(1.0,0.535,0.5),(1.96,0.03,0.56),0.014,dk,uv=1.2,step=0.4)
    rbox(A,WOODK,(1.0,0.155,0.5),(1.86,0.03,0.5),0.008,dk,uv=1.2,step=0.4)
    # 2 portas de venezianas + 2 gavetas centrais
    for cx in (0.42,1.58):
        rbox(A,WOODK,(cx,0.34,0.771),(0.74,0.3,0.016),0.01,lt,uv=1.2,step=0.4)
        for y in np.linspace(0.22,0.46,9): rbox(A,WOODK,(cx,y,0.782),(0.64,0.012,0.012),0.004,dk,uv=1.2,step=1)
        for x in (cx-0.33,cx+0.33): rbox(A,WOODK,(x,0.34,0.782),(0.026,0.3,0.012),0.004,dk,uv=1.2,step=1)
        pull(A,cx+(0.3 if cx<1 else -0.3),0.34,0.782,0.05)
    for dy,hh in ((0.43,0.12),(0.27,0.12)):
        rbox(A,WOODK,(1.0,dy,0.771),(0.34,hh,0.016),0.008,lt,uv=1.2,step=0.4)
        rbox(A,WOODK,(1.0,dy,0.781),(0.26,hh-0.05,0.006),0.003,dk,uv=1.2,step=1)
        pull(A,1.0,dy,0.782,0.07)
    # TV: moldura fina, pé em V, tela, barra de som
    rbox(A,METK,(1.0,0.585,0.5),(0.56,0.015,0.22),0.008,(0.1,0.11,0.13),uv=2)
    A.tube(METK,[V(0.84,0.585,0.5),V(0.9,0.64,0.5),V(0.92,0.7,0.5)],[0.012]*3,sides=8,col=lambda p,t:(0.1,0.11,0.13,1)); A.tube(METK,[V(1.16,0.585,0.5),V(1.1,0.64,0.5),V(1.08,0.7,0.5)],[0.012]*3,sides=8,col=lambda p,t:(0.1,0.11,0.13,1))
    rbox(A,METK,(1.0,1.04,0.5),(1.52,0.88,0.028),0.012,(0.07,0.075,0.085),uv=1.5)
    rbox(A,METK,(1.0,1.04,0.486),(1.48,0.84,0.03),0.008,(0.12,0.13,0.15),uv=1.5)
    A.add(('screen.png',F['PLAIN'],0),[V(0.27,0.62,0.5155),V(1.73,0.62,0.5155),V(1.73,1.43,0.5155),V(0.27,1.43,0.5155)],[V(0,0,0)]*4,[(1,1,1,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    rbox(A,METK,(1.0,0.575,0.66),(1.1,0.045,0.07),0.02,(0.1,0.1,0.12),uv=2)
    for x in np.linspace(0.55,1.45,22): sphere(A,PLK,(x,0.576,0.696),0.004,(0.35,0.35,0.38),5)
    sphere(A,PLK,(1.5,0.578,0.697),0.005,(0.3,0.9,0.4),5,emit=True)
    # decoracao: planta pequena e livros
    ceramic(A,(0.28,0.55,0.5),[(0,0),(0.05,0),(0.07,0.09),(0.0,0.09)],(0.9,0.88,0.82),16)
    for i in range(6):
        a=i*1.05; A.add(('leaf_fig.png',F['GRASS'],1),[V(0.28,0.64,0.5)-V(0.07,0,0),V(0.28,0.64,0.5)+V(0.07,0,0),V(0.28,0.64,0.5)+V(math.cos(a)*0.08,0.16,math.sin(a)*0.08)+V(0.08,0,0),V(0.28,0.64,0.5)+V(math.cos(a)*0.08,0.16,math.sin(a)*0.08)-V(0.08,0,0)],[nrm(V(math.cos(a),0.6,math.sin(a)))]*4,[(0.8,0.8,0.8,1)]*2+[(1,1,1,1)]*2,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    book_stack(A,1.74,0.55,0.5,[(0.28,0.2,0.04,(0.6,0.22,0.2),0.15),(0.25,0.19,0.035,(0.2,0.4,0.6),-0.1),(0.23,0.18,0.03,(0.9,0.75,0.3),0.07)])
    return A
@reg('fridge')
def fridge(seed=9):
    A=Asset('f_fridge'); st=(0.84,0.86,0.89); sd=(0.74,0.76,0.8)
    for x in (0.1,0.9): A.lathe(PLK,(x,0,0.12),[(0,0),(0.035,0),(0.035,0.04),(0,0.04)],sides=12,col=(0.15,0.15,0.17,1)); A.lathe(PLK,(x,0,0.78),[(0,0),(0.035,0),(0.035,0.04),(0,0.04)],sides=12,col=(0.15,0.15,0.17,1))
    rbox(A,METK,(0.5,0.97,0.46),(0.88,1.86,0.74),0.04,sd,uv=1.5,step=0.3)
    # portas: freezer embaixo (gaveta) e duas portas francesas em cima
    for cx in (0.255,0.745):
        rbox(A,METK,(cx,1.38,0.83),(0.43,0.95,0.04),0.02,st,uv=1.5,step=0.3)
        rbox(A,METK,(cx,1.38,0.853),(0.38,0.88,0.006),0.01,tuple(v*1.04 for v in st),uv=1.5,step=0.4)
    rbox(A,METK,(0.5,0.58,0.83),(0.86,0.52,0.04),0.02,st,uv=1.5,step=0.3)
    rbox(A,METK,(0.5,0.22,0.83),(0.86,0.38,0.04),0.02,st,uv=1.5,step=0.3)
    for y in (0.905,0.395): rbox(A,PLK,(0.5,y,0.835),(0.86,0.006,0.03),0.002,(0.1,0.1,0.12),uv=1,step=1)
    rbox(A,PLK,(0.5,1.38,0.835),(0.006,0.95,0.03),0.002,(0.1,0.1,0.12),uv=1,step=1)
    # dispenser de agua/gelo
    rbox(A,PLK,(0.255,1.5,0.852),(0.16,0.3,0.008),0.012,(0.1,0.11,0.13),uv=1)
    rbox(A,PLK,(0.255,1.43,0.858),(0.1,0.15,0.004),0.006,(0.18,0.2,0.24),uv=1)
    rbox(A,PLK,(0.255,1.49,0.86),(0.07,0.025,0.006),0.003,(0.4,0.8,0.95),uv=1)
    # puxadores verticais em barra
    for (x,y0,y1) in ((0.44,1.2,1.7),(0.56,1.2,1.7),(0.82,0.67,0.85),(0.82,0.28,0.14+0.12)):
        A.tube(METK,[V(x,y0,0.85),V(x,y0,0.905),V(x,y1,0.905),V(x,y1,0.85)],[0.012]*4,sides=10,col=lambda p,t:(0.92,0.93,0.96,1))
    # ima, lista e fotos
    rbox(A,PLK,(0.7,1.62,0.857),(0.12,0.16,0.003),0.002,(0.98,0.97,0.9),uv=1)
    for y in (1.66,1.62,1.58): rbox(A,PLK,(0.7,y,0.8585),(0.09,0.004,0.001),0.0005,(0.25,0.25,0.3),uv=1,step=1)
    for (x,y,c) in ((0.66,1.7,(0.9,0.3,0.28)),(0.74,1.55,(0.3,0.55,0.85)),(0.62,1.5,(0.95,0.8,0.2))): sphere(A,PLK,(x,y,0.859),0.014,c,8,sy=0.5)
    rbox(A,PLK,(0.45,1.32,0.857),(0.1,0.14,0.003),0.002,(0.7,0.82,0.9),uv=1)
    # grade traseira na parte de cima (não visível), logotipo
    rbox(A,METK,(0.5,0.34,0.8545),(0.1,0.02,0.002),0.001,(0.7,0.72,0.76),uv=1)
    return A
@reg('stove')
def stove(seed=10):
    A=Asset('f_stove'); st=(0.88,0.89,0.91)
    for x in (0.07,0.93):
        for z in (0.12,0.78): A.lathe(PLK,(x,0,z),[(0,0),(0.03,0),(0.03,0.025),(0,0.025)],sides=10,col=(0.14,0.14,0.16,1))
    rbox(A,METK,(0.5,0.45,0.47),(0.9,0.84,0.78),0.025,st,uv=1.5,step=0.3)
    rbox(A,PLK,(0.5,0.885,0.47),(0.9,0.026,0.78),0.014,(0.07,0.075,0.085),uv=1,step=0.3)
    # bocas de fogao: base, tampa, grelha em cruz e chama
    for bx,bz,sc in ((0.27,0.3,1.0),(0.73,0.3,0.8),(0.27,0.64,0.8),(0.73,0.64,1.0)):
        ceramic(A,(bx,0.898,bz),[(0.05*sc,0),(0.085*sc,0.0),(0.085*sc,0.008),(0.05*sc,0.012)],(0.15,0.15,0.16),24)
        ceramic(A,(bx,0.898,bz),[(0,0),(0.045*sc,0),(0.05*sc,0.016),(0,0.02)],(0.2,0.2,0.22),20)
        ceramic(A,(bx,0.918,bz),[(0,0),(0.035*sc,0),(0.037*sc,0.006),(0,0.008)],(0.5,0.5,0.55),20)
        for ang in (0,math.pi/2): A.tube(METK,[V(bx-0.11*math.cos(ang),0.935,bz-0.11*math.sin(ang)),V(bx+0.11*math.cos(ang),0.935,bz+0.11*math.sin(ang))],[0.008]*2,sides=6,col=lambda p,t:(0.1,0.1,0.11,1))
    for gx in (0.27,0.73):
        for gz in (0.3,0.64):
            pass
    # grelha continua de ferro (duas)
    for z in (0.3,0.64):
        A.tube(METK,[V(0.1,0.935,z-0.12),V(0.9,0.935,z-0.12)],[0.007]*2,sides=6,col=lambda p,t:(0.1,0.1,0.11,1)); A.tube(METK,[V(0.1,0.935,z+0.12),V(0.9,0.935,z+0.12)],[0.007]*2,sides=6,col=lambda p,t:(0.1,0.1,0.11,1))
    # painel de controle com botoes e visor
    rbox(A,METK,(0.5,0.82,0.862),(0.84,0.11,0.04),0.02,(0.78,0.8,0.84),uv=1.5)
    for kx in (0.17,0.3,0.7,0.83):
        A.lathe(PLK,(kx,0.82,0.882),[(0.0,0.0),(0.03,0.0),(0.03,0.032),(0.026,0.036),(0,0.036)],sides=16,col=(0.12,0.13,0.15,1))
        rbox(A,PLK,(kx,0.832,0.9185),(0.004,0.02,0.001),0.0005,(0.9,0.9,0.92),uv=1,step=1)
        A.lathe(PLK,(kx,0.82,0.879),[(0.034,0),(0.034,0.003),(0.03,0.003)],sides=16,col=(0.7,0.72,0.76,1))
    rbox(A,PLK,(0.5,0.82,0.884),(0.17,0.06,0.003),0.004,(0.04,0.05,0.06),uv=1)
    for i in range(4): rbox(A,PLK,(0.45+i*0.034,0.82,0.886),(0.016,0.03,0.001),0.0005,(0.3,0.95,0.55),uv=1,step=1)
    # porta do forno com visor, puxador e dobradicas
    rbox(A,METK,(0.5,0.4,0.865),(0.8,0.54,0.04),0.02,(0.8,0.82,0.86),uv=1.5)
    rbox(A,PLK,(0.5,0.4,0.887),(0.6,0.34,0.006),0.01,(0.06,0.07,0.09),uv=1)
    A.add(K('white',F['PLAIN']),[V(0.24,0.28,0.8905),V(0.46,0.28,0.8905),V(0.54,0.5,0.8905),V(0.28,0.5,0.8905)],[V(0,0,0)]*4,[(0.22,0.25,0.3,1)]*4,[(0,1),(1,1),(1,0),(0,0)],[(0,1,2),(0,2,3)])
    A.tube(METK,[V(0.18,0.69,0.89),V(0.18,0.69,0.945),V(0.82,0.69,0.945),V(0.82,0.69,0.89)],[0.014]*4,sides=10,col=lambda p,t:(0.92,0.94,0.97,1))
    rbox(A,METK,(0.5,0.12,0.865),(0.78,0.14,0.04),0.015,(0.76,0.78,0.82),uv=1.5)   # gaveta de baixo
    pull(A,0.5,0.14,0.887,0.2,(0.85,0.87,0.9))
    # coifa/painel traseiro com visor e saidas
    rbox(A,METK,(0.5,1.1,0.06),(0.9,0.38,0.06),0.02,(0.8,0.82,0.85),uv=1.5)
    rbox(A,PLK,(0.5,1.14,0.093),(0.2,0.06,0.003),0.004,(0.04,0.05,0.06),uv=1)
    for i in range(3): rbox(A,PLK,(0.46+i*0.045,1.14,0.0945),(0.02,0.035,0.001),0.0005,(0.4,0.95,0.6),uv=1,step=1)
    for x in np.linspace(0.2,0.8,13): rbox(A,PLK,(x,1.02,0.093),(0.02,0.04,0.002),0.0005,(0.15,0.15,0.17),uv=1,step=1)
    return A
@reg('lamp')
def lamp(seed=11):
    A=Asset('f_lamp')
    # base em tripe de madeira e haste de latao torneada
    A.lathe(K('white',F['METAL']),(0.5,0,0.5),[(0,0),(0.2,0),(0.21,0.012),(0.2,0.03),(0.12,0.05),(0.04,0.08),(0.03,0.1)],sides=36,col=(0.16,0.17,0.19,1))
    A.lathe(K('white',F['METAL']),(0.5,0,0.5),[(0.205,0.012),(0.215,0.018),(0.2,0.026)],sides=36,col=BRASS+(1,))
    turned(A,METK,0.5,0.5,0.08,1.12,0.02,BRASS,sides=16,prof=[(1.0,0),(1.3,0.03),(0.8,0.07),(0.7,0.2),(1.1,0.28),(0.7,0.34),(0.6,0.6),(0.9,0.68),(0.6,0.74),(0.55,1.0),(0.0,1.0)])
    sphere(A,METK,(0.5,1.215,0.5),0.032,BRASS,12)
    # soquete e lampada acesa
    A.lathe(METK,(0.5,1.21,0.5),[(0,0),(0.026,0),(0.026,0.05)],sides=14,col=BRASS+(1,))
    sphere(A,K('white',F['PLAIN']),(0.5,1.32,0.5),0.06,(1.0,0.95,0.8),14,emit=True)
    # cupula plissada com friso superior e inferior
    pleated_shade(A,(0.5,1.2,0.5),0.27,0.14,0.4,(1.0,0.9,0.68),n=48)
    ring_pts=[V(0.5+0.275*math.cos(2*math.pi*i/48),1.2,0.5+0.275*math.sin(2*math.pi*i/48)) for i in range(49)]
    A.tube(METK,ring_pts,[0.006]*49,sides=6,col=lambda p,t:(0.85,0.65,0.35,1))
    ring_pts=[V(0.5+0.145*math.cos(2*math.pi*i/48),1.6,0.5+0.145*math.sin(2*math.pi*i/48)) for i in range(49)]
    A.tube(METK,ring_pts,[0.006]*49,sides=6,col=lambda p,t:(0.85,0.65,0.35,1))
    for a in (0,2.09,4.19): A.tube(METK,[V(0.5,1.215,0.5),V(0.5+0.14*math.cos(a),1.38,0.5+0.14*math.sin(a))],[0.0035,0.0035],sides=5,col=lambda p,t:BRASS+(1,))
    return A
@reg('night')
def night(seed=12):
    A=Asset('f_night'); wd=(0.74,0.54,0.36); lt=(0.82,0.62,0.44); dk=(0.58,0.4,0.27)
    for x,z in ((0.26,0.3),(0.74,0.3),(0.26,0.7),(0.74,0.7)): turned(A,WOODK,x,z,0.0,0.18,0.026,dk,sides=12)
    rbox(A,WOODK,(0.5,0.4,0.5),(0.56,0.42,0.46),0.018,wd,uv=1.5,step=0.3,ao=gao(0.3,0.82))
    rbox(A,WOODK,(0.5,0.63,0.5),(0.62,0.036,0.52),0.016,lt,uv=1.5)
    molding(A,WOODK,0.2,0.8,0.595,0.25,0.75,dk,layers=2,h=0.016,out=0.01)
    # 2 gavetas com frente em relevo e puxadores
    for y in (0.5,0.3):
        rbox(A,WOODK,(0.5,y,0.735),(0.5,0.18,0.02),0.01,lt,uv=1.5,step=0.4)
        rbox(A,WOODK,(0.5,y,0.747),(0.4,0.12,0.008),0.005,wd,uv=1.5,step=0.5)
        knob_z(A,0.5,y,0.745,BRASS,0.018)
        A.tube(METK,[V(0.5-0.03,y,0.745),V(0.5+0.03,y,0.745)],[0.0] * 2,sides=4,col=lambda p,t:BRASS+(1,)) if False else None
    # abajur com base de ceramica
    ceramic(A,(0.34,0.648,0.52),[(0,0),(0.075,0),(0.085,0.03),(0.065,0.08),(0.025,0.13),(0.016,0.2),(0.02,0.24),(0,0.245)],(0.95,0.93,0.88),22)
    pleated_shade(A,(0.34,0.86,0.52),0.12,0.07,0.17,(1.0,0.9,0.68),n=28)
    sphere(A,K('white',F['PLAIN']),(0.34,0.95,0.52),0.025,(1.0,0.95,0.8),8,emit=True)
    # livros, relogio, copo, celular
    rbox(A,FABK,(0.68,0.665,0.5),(0.24,0.03,0.17),0.006,(0.2,0.42,0.66),uv=2); rbox(A,PLK,(0.68,0.665,0.503),(0.22,0.024,0.15),0.002,(0.96,0.94,0.88),uv=1,step=1)
    rbox(A,FABK,(0.68,0.695,0.5),(0.22,0.028,0.15),0.006,(0.88,0.68,0.22),uv=2); rbox(A,PLK,(0.68,0.695,0.503),(0.2,0.022,0.13),0.002,(0.96,0.94,0.88),uv=1,step=1)
    rbox(A,PLK,(0.68,0.72,0.5),(0.12,0.028,0.07),0.006,(0.3,0.2,0.2),uv=1)
    rbox(A,METK,(0.66,0.777,0.5),(0.12,0.06,0.04),0.01,(0.88,0.86,0.82),uv=1) if False else None
    A.lathe(PLK,(0.58,0.634,0.36),[(0,0),(0.03,0),(0.034,0.005),(0.034,0.02),(0.002,0.02)],sides=18,col=(0.2,0.2,0.22,1))
    rbox(A,PLK,(0.68,0.74,0.32),(0.07,0.11,0.01),0.01,(0.08,0.08,0.1),uv=1) if False else None
    glass(A,0.72,0.648,0.36,0.9)
    rbox(A,PLK,(0.64,0.722,0.34),(0.07,0.006,0.14),0.01,(0.08,0.08,0.1),uv=1,rot=0.3)
    return A
@reg('coffee')
def coffee(seed=13):
    A=Asset('f_coffee'); wd=(0.84,0.64,0.42); dk=(0.56,0.38,0.26)
    for x in (0.4,1.6):
        for z in (0.22,0.78): turned(A,WOODK,x,z,0.0,0.43,0.03,dk,sides=14)
    rbox(A,WOODK,(1.0,0.45,0.5),(1.46,0.04,0.74),0.02,wd,uv=1.2)
    rbox(A,WOODK,(1.0,0.42,0.5),(1.48,0.025,0.76),0.008,dk,uv=1.2)
    rbox(A,WOODK,(1.0,0.16,0.5),(1.2,0.025,0.5),0.01,dk,uv=1.2,ao=lambda w:0.8)
    for x in (0.4,1.6):
        A.tube(WOODK,[V(x,0.175,0.22),V(x,0.175,0.78)],[0.012]*2,sides=8,col=lambda p,t:dk+(1,))
    for z in (0.22,0.78): A.tube(WOODK,[V(0.4,0.175,z),V(1.6,0.175,z)],[0.012]*2,sides=8,col=lambda p,t:dk+(1,))
    # bandeja com revistas, vela e livro; tigela de plantas
    rbox(A,WOODK,(0.7,0.478,0.5),(0.5,0.014,0.32),0.006,(0.34,0.24,0.18),uv=2)
    for sx in (0.46,0.94): rbox(A,WOODK,(sx-0.24+0.02,0.49,0.5),(0.012,0.025,0.32),0.004,(0.34,0.24,0.18),uv=2) if False else None
    rbox(A,FABK,(0.66,0.505,0.5),(0.3,0.03,0.22),0.006,(0.2,0.36,0.56),uv=3); rbox(A,FABK,(0.66,0.535,0.5),(0.26,0.028,0.19),0.006,(0.84,0.64,0.2),uv=3,rot=0.1)
    rbox(A,PLK,(0.66,0.56,0.5),(0.2,0.004,0.14),0.002,(0.95,0.93,0.88),uv=1,rot=0.1)
    ceramic(A,(0.84,0.485,0.45),[(0,0),(0.04,0),(0.042,0.04),(0.0,0.04)],(0.92,0.9,0.85),16)
    A.lathe(PLK,(0.84,0.52,0.45),[(0.0,0.0),(0.003,0.0),(0.0,0.02)],sides=6,col=(1.0,0.78,0.2,1))
    mug(A,0.9,0.485,0.62,(0.92,0.92,0.9))
    vase_flowers(A,1.3,0.47,0.55,0.9,'flw_lav.png',col=(0.9,0.62,0.3))
    ceramic(A,(1.2,0.47,0.34),[(0,0),(0.08,0),(0.1,0.03),(0.095,0.06),(0.0,0.05)],(0.88,0.86,0.8),22)
    for i in range(7):
        a=i*0.9; sphere(A,PLK,(1.2+0.04*math.cos(a),0.53+(i%2)*0.01,0.34+0.04*math.sin(a)),0.022,(0.32+0.05*(i%3),0.6,0.3),7)
    for i in range(4): sphere(A,PLK,(1.2+0.02*i-0.03,0.52,0.34),0.012,(0.95,0.7,0.78),6)
    # prateleira de baixo: cesto e revistas
    rbox(A,FABK,(0.7,0.2,0.5),(0.34,0.025,0.24),0.005,(0.82,0.4,0.3),uv=3); rbox(A,FABK,(0.7,0.225,0.5),(0.3,0.025,0.21),0.005,(0.3,0.5,0.4),uv=3,rot=0.1)
    A.lathe(K('weave',F['FABRIC']),(1.3,0.17,0.5),[(0,0),(0.14,0),(0.16,0.1),(0.17,0.18),(0.16,0.18),(0.0,0.02)],sides=22,col=(0.84,0.66,0.42,1),uscale=6,vscale=6)
    return A
@reg('wardrobe')
def wardrobe(seed=14):
    A=Asset('f_wardrobe'); wd=(0.82,0.62,0.42); lt=(0.9,0.72,0.52); dk=(0.52,0.36,0.24)
    # sapatas torneadas, rodape recortado e base
    for x in (0.16,1.84):
        for z in (0.1,0.65): turned(A,WOODK,x,z,0.0,0.09,0.04,dk,sides=14,prof=[(0.8,0),(1.0,0.2),(0.7,0.5),(1.0,0.8),(0.9,1.0),(0,1.0)])
    rbox(A,WOODK,(1.0,0.125,0.37),(1.86,0.07,0.68),0.01,dk,uv=1.2)
    rbox(A,WOODK,(1.0,0.17,0.37),(1.9,0.04,0.7),0.008,wd,uv=1.0)
    # corpo
    rbox(A,WOODK,(1.0,1.1,0.37),(1.92,1.86,0.72),0.016,wd,uv=0.9,step=0.4,ao=gao(0.35,0.8))
    # cornija em camadas com friso
    molding(A,WOODK,0.0,2.0,2.03,0.0,0.74,wd,layers=3,h=0.035,out=0.04)
    rbox(A,WOODK,(1.0,2.145,0.37),(1.96,0.04,0.74),0.014,lt,uv=0.9,step=0.5)
    rbox(A,WOODK,(1.0,2.085,0.755),(1.9,0.04,0.02),0.008,dk,uv=1.0)
    # duas portas com painéis em relevo (moldura + painel elevado)
    for cx in (0.5,1.5):
        rbox(A,WOODK,(cx,1.12,0.742),(0.94,1.62,0.028),0.012,lt,uv=1.1,step=0.4)
        for (yy,hh) in ((1.62,0.74),(0.78,0.5)):
            rbox(A,WOODK,(cx,yy,0.758),(0.7,hh,0.012),0.006,dk,uv=1.1,step=0.4)
            rbox(A,WOODK,(cx,yy,0.765),(0.62,hh-0.08,0.014),0.012,wd,uv=1.1,step=0.4)
            rbox(A,WOODK,(cx,yy,0.771),(0.5,hh-0.2,0.005),0.008,lt,uv=1.1,step=0.4)
    rbox(A,PLK,(1.0,1.12,0.7435),(0.012,1.62,0.003),0.001,(0.3,0.2,0.14),uv=1)
    # gavetas na base com puxadores
    for cx in (0.5,1.5):
        rbox(A,WOODK,(cx,0.3,0.742),(0.94,0.2,0.028),0.012,lt,uv=1.1,step=0.4)
        rbox(A,WOODK,(cx,0.3,0.76),(0.8,0.13,0.01),0.006,wd,uv=1.1,step=0.5)
        pull(A,cx,0.3,0.768,0.14)
    # macanetas torneadas e escudos de fechadura
    for x in (0.9,1.1):
        A.lathe(METK,(x,1.12,0.756),[(0,0),(0.016,0),(0.016,0.006),(0.006,0.01),(0.006,0.02),(0.02,0.03),(0.02,0.04),(0.0,0.045)],sides=14,col=BRASS+(1,))
        rbox(A,METK,(x+(0.04 if x>1 else -0.04),1.12,0.7565),(0.02,0.07,0.003),0.003,BRASS,uv=1)
    rbox(A,METK,(0.9,1.02,0.7565),(0.026,0.05,0.003),0.002,DARK(BRASS,0.8),uv=1)
    # dobradiças aparentes
    for cx,sd in ((0.04,-1),(1.96,1)):
        for y in (0.5,1.12,1.74): A.tube(METK,[V(cx,y-0.05,0.756),V(cx,y+0.05,0.756)],[0.007,0.007],sides=8,col=lambda p,t:BRASS+(1,))
    return A
