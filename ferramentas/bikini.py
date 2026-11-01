#!/usr/bin/env python3
"""Biquíni procedural do Meu Lar: malha nova colada na superfície do corpo-base (Mary), com pesos de osso
interpolados do corpo (segue Idle/Walk/Jump sem ajuste). Peças: top/Bikini, bottom/Bikini, overall/Bikini (os dois juntos).
Texturas: 2 tiles recoloríveis do atlas extra.png (região 2 = top: Blusa/Detalhe; região 3 = baixo: Saia/Detalhe baixo).
Uso: python3 bikini.py <assets/cute (entrada e saída)> <base.bin>"""
import sys, os, struct
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree, Delaunay

REC = np.dtype([('pos','<f4',3),('nor','<f4',3),('uv','<f4',2),('col','u1',4),('bi','u1',4),('bw','u1',4)])
AW, AH, T, COLS = 2016, 1344, 224, 9
REFS = {2: ((200,200,206),(112,112,122)), 3: ((120,128,150),(70,74,90))}
TILE = {2: 52, 3: 53}
OFF = 0.5            # distância da malha à pele (unid. FBX)
ZC = 2.5             # eixo do tronco
SETS = [0,3,4,6,9,13,17,21]

def load_body(path):
    b = open(path,'rb').read(); nv, ni, nb, nc = struct.unpack_from('<4i', b, 4)
    v = np.frombuffer(b, REC, nv, 20); t = np.frombuffer(b, '<u2', ni, 20+nv*44).reshape(-1,3).astype(int)
    return v, t

class Surf:
    def __init__(self, v, t, step=0.45):
        self.v = v
        P = v['pos'].astype(float); N = v['nor'].astype(float)
        dom = v['bi'][np.arange(len(v)), np.argmax(v['bw'],1)]
        ok = np.isin(dom, SETS)
        sel = t[ok[t].all(1)]
        SP=[]; SN=[]; ST=[]; SB=[]
        for ti,(a,b,c) in enumerate(sel):
            pa,pb,pc = P[a],P[b],P[c]
            k = int(np.ceil(max(np.linalg.norm(pb-pa),np.linalg.norm(pc-pb),np.linalg.norm(pa-pc))/step)); k=max(1,min(k,20))
            for i in range(k+1):
                for j in range(k+1-i):
                    u,w = i/k, j/k; q = 1-u-w
                    SP.append(pa*q+pb*u+pc*w); SN.append(N[a]*q+N[b]*u+N[c]*w); ST.append((a,b,c)); SB.append((q,u,w))
        self.P=np.array(SP); n=np.array(SN); self.N=n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9)
        self.T=np.array(ST); self.B=np.array(SB)
        self.tree=cKDTree(self.P)
        self.tree2=None
    def weights(self, i):
        a,b,c = self.T[i]; q = self.B[i]
        acc = {}
        for vi,wq in zip((a,b,c),q):
            for bi_,bw_ in zip(self.v['bi'][vi], self.v['bw'][vi]):
                if bw_: acc[int(bi_)] = acc.get(int(bi_),0)+float(bw_)*wq
        it = sorted(acc.items(), key=lambda kv:-kv[1])[:4]
        tot = sum(w for _,w in it); bi = [k for k,_ in it]+[0]*(4-len(it)); bw = [w/tot*255 for _,w in it]+[0]*(4-len(it))
        bwi = np.round(bw).astype(int); bwi[0] += 255-bwi.sum()
        return bi, bwi
    def near(self, q):
        d,i = self.tree.query(q); return i
    def front(self, x, y, sign=1, r=1.6):
        """superfície vista de frente (sign=+1) ou de trás (-1) em (x,y): média suave da camada de cima. Devolve (pos, nor, idx_pesos)."""
        if self.tree2 is None: self.tree2 = cKDTree(self.P[:,:2])
        for rr in (r, r*2.0, r*4.0):
            ii = np.array(self.tree2.query_ball_point([x,y], rr))
            if len(ii)==0: continue
            ii = ii[sign*(self.P[ii,2]-ZC) > 0]
            if len(ii)==0: continue
            z = sign*self.P[ii,2]; top = z > z.max()-1.8
            ii = ii[top]
            d2 = ((self.P[ii,0]-x)**2+(self.P[ii,1]-y)**2)
            w = np.exp(-d2/(2*(rr*0.5)**2)); w/=w.sum()
            p = (self.P[ii]*w[:,None]).sum(0); p[0]=x; p[1]=y
            n = (self.N[ii]*w[:,None]).sum(0); n/=max(np.linalg.norm(n),1e-9)
            j = ii[np.argmin(d2)]
            return p, n, j
        return None

class Mesh:
    def __init__(self, S, region): self.S=S; self.region=region; self.pos=[]; self.nor=[]; self.uv=[]; self.bi=[]; self.bw=[]; self.ix=[]
    def vert(self, si, u, v=0.5, lift=OFF, p=None, n=None):
        S=self.S
        if p is None: p=S.P[si]
        if n is None: n=S.N[si]
        bi,bw = S.weights(si)
        self.pos.append(p+lift*n); self.nor.append(n); self.uv.append(self.tuv(u,v)); self.bi.append(bi); self.bw.append(bw)
        return len(self.pos)-1
    def tuv(self, u, v):
        x0 = (TILE[self.region] % COLS)*T; y0 = (TILE[self.region]//COLS)*T
        return ((x0+u*T)/AW, (y0+v*T)/AH)
    def tris(self, a): self.ix += list(a)

def inpoly(pts, poly):
    # ponto em polígono convexo/qualquer (ray casting)
    x,y = pts[:,0],pts[:,1]; n=len(poly); ins=np.zeros(len(pts),bool)
    j=n-1
    for i in range(n):
        xi,yi=poly[i]; xj,yj=poly[j]
        c=((yi>y)!=(yj>y)) & (x < (xj-xi)*(y-yi)/(yj-yi+1e-12)+xi)
        ins ^= c; j=i
    return ins

def resample(poly, step):
    out=[]; n=len(poly)
    for i in range(n):
        a=np.array(poly[i]); b=np.array(poly[(i+1)%n]); k=max(1,int(np.ceil(np.linalg.norm(b-a)/step)))
        for s in range(k): out.append(a+(b-a)*s/k)
    return np.array(out)

def panel(M, poly, sign, step=0.8, ushift=0.0):
    """painel liso com contorno (debrum): poly em (x,y) projetado pela frente (sign=+1) ou costas (-1)."""
    S=M.S; poly=np.array(poly,float)
    bd = resample(poly, step*0.8)
    xs=np.arange(poly[:,0].min(), poly[:,0].max()+1e-6, step); ys=np.arange(poly[:,1].min(), poly[:,1].max()+1e-6, step)
    G=np.array([(x,y) for x in xs for y in ys])
    G=G[inpoly(G,poly)]
    # afasta pontos internos muito perto do contorno
    d,_=cKDTree(bd).query(G); G=G[d>step*0.6]
    pts=np.vstack([bd,G]); nb=len(bd)
    tri=Delaunay(pts).simplices
    cen=pts[tri].mean(1); tri=tri[inpoly(cen,poly)]
    ids={}
    x0,x1=poly[:,0].min(),poly[:,0].max(); y0,y1=poly[:,1].min(),poly[:,1].max()
    out=[]
    for k,(x,y) in enumerate(pts):
        fr=S.front(x,y,sign)
        if fr is None: out.append(None); continue
        fp,fn_,si=fr
        edge = k<nb
        ppu = 76.0/max(x1-x0,1e-6)              # pixels do tile por unidade (mesma escala em u e v: bolinhas redondas)
        u = 0.9 if edge else 0.04+(x-x0)*ppu/T
        v = 0.5 if edge else 0.5+(y-(y0+y1)/2)*ppu/T
        out.append(M.vert(si,u,v,OFF,fp,fn_))
    for a,b,c in tri:
        if out[a] is None or out[b] is None or out[c] is None: continue
        # orientação: normal do triângulo alinhada à normal do corpo
        pa,pb,pc=[M.pos[o] for o in (out[a],out[b],out[c])]
        n=np.cross(np.array(pb)-pa,np.array(pc)-pa)
        if np.dot(n, M.nor[out[a]])<0: M.tris((out[a],out[c],out[b]))
        else: M.tris((out[a],out[b],out[c]))

def ribbon(M, path3, width, u=0.9, lift=OFF+0.1, wtaper=None):
    """fita seguindo uma curva 3D projetada na superfície. path3: pontos de controle."""
    S=M.S; path3=np.array(path3,float)
    # reamostra por comprimento
    seg=np.linalg.norm(np.diff(path3,axis=0),axis=1); L=np.concatenate([[0],np.cumsum(seg)]); n=max(3,int(L[-1]/0.7))
    ts=np.linspace(0,L[-1],n)
    pts=np.stack([np.interp(ts,L,path3[:,c]) for c in range(3)],1)
    # suaviza
    for _ in range(2): pts[1:-1]=(pts[:-2]+2*pts[1:-1]+pts[2:])/4
    sp=[S.near(p) for p in pts]; base=np.array([S.P[i] for i in sp]); nor=np.array([S.N[i] for i in sp])
    # suaviza projeção
    for _ in range(2): base[1:-1]=(base[:-2]+2*base[1:-1]+base[2:])/4
    tan=np.gradient(base,axis=0); tan/=np.maximum(np.linalg.norm(tan,axis=1,keepdims=True),1e-9)
    LR=[[],[]]; SI=[[],[]]
    for i in range(n):
        w = width if wtaper is None else width*wtaper(i/(n-1))
        side=np.cross(tan[i],nor[i]); side/=max(np.linalg.norm(side),1e-9)
        for k,sgn in enumerate((-1,1)):
            q=base[i]+side*sgn*w/2
            si=S.near(q); LR[k].append(S.P[si].copy()); SI[k].append(si)
    for k in (0,1):
        A=np.array(LR[k])
        for _ in range(4): A[1:-1]=(A[:-2]+2*A[1:-1]+A[2:])/4
        LR[k]=A
    ids=[]
    for i in range(n):
        pair=[]
        for k in (0,1):
            si=SI[k][i]; nn=S.N[si]
            pair.append(M.vert(si,u,0.5,lift,LR[k][i],nn))
        ids.append(pair)
    for i in range(n-1):
        a,b=ids[i]; c,d=ids[i+1]
        for tri in ((a,b,c),(b,d,c)):
            pa,pb,pc=[M.pos[o] for o in tri]; nn=np.cross(np.array(pb)-pa,np.array(pc)-pa)
            M.tris(tri if np.dot(nn,M.nor[tri[0]])>=0 else (tri[0],tri[2],tri[1]))

def bow(M, anchor, direction, size=1.0, sign=1):
    """laço: nó + 2 alças + 2 pontas, desenhado no plano tangente em 'anchor' (ponto 3D na pele); direction = vetor 3D 'para baixo' do laço."""
    S=M.S; si=S.near(anchor); p=S.P[si]; n=S.N[si]
    d=np.array(direction,float); d=d-n*np.dot(d,n); d/=max(np.linalg.norm(d),1e-9)
    r=np.cross(d,n); r/=max(np.linalg.norm(r),1e-9)
    def vtx(a,b): return M.vert(S.near(p+r*a*size+d*b*size),0.9,0.5,OFF+0.35)
    def quad(pts):
        ids=[vtx(a,b) for a,b in pts]
        for i in range(1,len(ids)-1):
            tri=(ids[0],ids[i],ids[i+1]); pa,pb,pc=[M.pos[o] for o in tri]; nn=np.cross(np.array(pb)-pa,np.array(pc)-pa)
            M.tris(tri if np.dot(nn,M.nor[tri[0]])>=0 else (tri[0],tri[2],tri[1]))
    # alças (losangos) à esquerda e à direita do nó
    quad([(-0.4,0.0),(-2.4,-1.1),(-3.0,0.0),(-2.4,1.1)])
    quad([(0.4,0.0),(2.4,-1.1),(3.0,0.0),(2.4,1.1)])
    # nó
    quad([(-0.55,-0.55),(0.55,-0.55),(0.55,0.55),(-0.55,0.55)])
    # pontas
    quad([(-0.4,0.4),(0.0,0.4),(-1.5,4.8),(-2.3,4.5)])
    quad([(0.0,0.4),(0.4,0.4),(2.3,4.5),(1.5,4.8)])

def top_mesh(S):
    M=Mesh(S,2)
    for s in (-1,1):
        # copo triangular: vértices (x,y)
        poly=[(s*1.0,125.2),(s*11.6,129.0),(s*10.8,131.2),(s*1.0,139.2)]
        # lado interno reto, borda de baixo e de cima levemente côncavas
        poly=[(s*1.1,125.0),(s*5.5,126.1),(s*9.3,127.6),(s*12.4,129.6),(s*9.6,132.4),(s*5.8,135.8),(s*2.6,138.0),(s*1.1,139.0),(s*1.1,132.0)]
        panel(M, poly[::s], 1, 0.75)
        # alça do pescoço (halter): do topo do copo, sobe pelo peito até a nuca
        ribbon(M, [(s*1.9,138.6,10.0),(s*2.8,143.0,8.2),(s*4.6,148.0,5.2),(s*5.4,151.2,1.0),(s*3.8,152.4,-3.2),(s*0.6,152.0,-4.9)], 1.2)
        # faixa das costas (a partir da ponta externa do copo, contorna o corpo)
        ang=np.linspace(0.0, 1.0, 14)
        pth=[]
        for a in ang:
            th=np.deg2rad(32+a*148)   # do lado frontal (32°) até as costas (180°) medidos do eixo z+
            rr=19.0
            pth.append((s*np.sin(th)*rr, 130.0-0.7*np.sin(a*np.pi)*0+ (0.0), ZC+np.cos(th)*rr))
        ribbon(M, pth, 1.3)
    # ponte central entre os copos (anel/trava)
    ribbon(M, [(-1.5,130.4,12.4),(0,130.6,12.7),(1.5,130.4,12.4)], 1.0, lift=OFF+0.35)
    # laço das costas (nuca e costas)
    bow(M, (0.0,129.8,-9.5), (0,-1,0), 1.35)
    bow(M, (0.0,152.0,-5.2), (0,-1,-0.4), 0.85)
    return M

def bottom_mesh(S):
    M=Mesh(S,3)
    # painel frontal (triângulo arredondado) e traseiro
    fr=[(-10.6,103.6),(-5.0,102.6),(0,102.0),(5.0,102.6),(10.6,103.6),(8.0,99.0),(4.6,95.8),(2.0,93.2),(0,92.3),(-2.0,93.2),(-4.6,95.8),(-8.0,99.0)]
    panel(M, fr, 1, 0.8)
    bk=[(-10.8,103.4),(-5.0,102.4),(0,102.0),(5.0,102.4),(10.8,103.4),(9.2,99.0),(6.0,95.6),(3.0,93.0),(0,92.2),(-3.0,93.0),(-6.0,95.6),(-9.2,99.0)]
    panel(M, bk, -1, 0.8)
    # entrepernas (une frente e costas por baixo)
    ribbon(M, [(0,93.2,8.5),(0,91.6,5.5),(0,90.6,2.4),(0,91.6,-1.0),(0,93.0,-4.8)], 4.4, u=0.12, lift=OFF)
    # tiras laterais do quadril (frente -> lado -> costas), com laço no quadril
    for s in (-1,1):
        pth=[]
        for a in np.linspace(0,1,12):
            th=np.deg2rad(28+a*112)          # frente(28°) -> costas(140°)
            rr=19.0
            pth.append((s*np.sin(th)*rr, 103.2-0.5*np.sin(a*np.pi), ZC+np.cos(th)*rr))
        ribbon(M, pth, 1.3)
        bow(M, (s*15.0,102.2,0.3), (0,-1,-0.35), 1.3)
    return M

def paint_tiles(atlas, a0, a1, sh, rid):
    yy,xx=np.mgrid[0:T,0:T]; u=xx/(T-1)
    for region,idx in TILE.items():
        x0=(idx%COLS)*T; y0=(idx//COLS)*T
        t=np.clip((u-0.46)/0.08,0,1); w1=t*t*(3-2*t)       # 0 = tecido, 1 = debrum/tiras
        # bolinhas no tecido (lado esquerdo do tile): bem visíveis em qualquer cor
        px=(xx%22)-11; py=(yy%22)-11
        dots=((px*px+py*py)<=22).astype(float)
        dots=np.where(u<0.44,dots,0.0)
        shade=1.0-0.22*dots+0.03*np.sin(yy/5.0)*(1-w1)       # leve textura de malha
        shade=np.where(w1>0.5, 1.0+0.06*np.sin(yy/3.0), shade)
        c0=np.array(REFS[region][0],float); c1=np.array(REFS[region][1],float)
        ref=(1-w1)[...,None]*c0+w1[...,None]*c1
        sl=(slice(y0,y0+T),slice(x0,x0+T))
        atlas[sl]=np.clip(ref*shade[...,None],0,255); a0[sl]=1-w1; a1[sl]=w1; sh[sl]=shade; rid[sl]=region

def write_cup1(path_, M):
    n=len(M.pos); r=np.zeros(n,REC)
    r['pos']=np.array(M.pos); r['nor']=np.array(M.nor); r['uv']=np.array(M.uv); r['col']=255; r['bi']=np.array(M.bi); r['bw']=np.array(M.bw)
    ix=np.array(M.ix,np.uint16)
    with open(path_,'wb') as f:
        f.write(b'CUP1'+struct.pack('<3i',n,len(ix),0)); f.write(r.tobytes()); f.write(ix.tobytes())

def merge(A,B):
    C=Mesh(A.S,2); off=len(A.pos)
    for k in ('pos','nor','uv','bi','bw'): getattr(C,k).extend(getattr(A,k)); getattr(C,k).extend(getattr(B,k))
    C.ix=list(A.ix)+[i+off for i in B.ix]; return C

def main(cute, basebin):
    v,t=load_body(basebin); S=Surf(v,t)
    tm=top_mesh(S); bm=bottom_mesh(S)
    write_cup1(os.path.join(cute,'p_top_bikini.bin'),tm)
    write_cup1(os.path.join(cute,'p_bottom_bikini.bin'),bm)
    write_cup1(os.path.join(cute,'p_overall_bikini.bin'),merge(tm,bm))
    for n,m in (('top',tm),('bottom',bm)): print(n,len(m.pos),'v',len(m.ix)//3,'tris')
    # atlas
    at=np.asarray(Image.open(os.path.join(cute,'extra.png')).convert('RGB')).astype(float)
    mk=np.asarray(Image.open(os.path.join(cute,'extra_recolor.png')).convert('RGB')).astype(float)
    ss=np.asarray(Image.open(os.path.join(cute,'extra_recolor_s.png')).convert('RGB'))[...,0].astype(float)
    a0=mk[...,0]/255; a1=mk[...,1]/255; rid=mk[...,2].astype(np.uint8); sh=ss*2/255
    paint_tiles(at,a0,a1,sh,rid)
    Image.fromarray(np.round(at).astype(np.uint8)).save(os.path.join(cute,'extra.png'),optimize=True)
    img=np.zeros((AH,AW,3),np.uint8); img[...,0]=np.round(a0*255); img[...,1]=np.round(a1*255); img[...,2]=rid
    Image.fromarray(img).save(os.path.join(cute,'extra_recolor.png'),optimize=True)
    g=np.round(np.clip(sh,0,2)/2*255).astype(np.uint8)
    Image.fromarray(np.stack([g]*3,-1)).save(os.path.join(cute,'extra_recolor_s.png'),optimize=True)
    # manifesto
    pf=os.path.join(cute,'pieces.txt'); L=open(pf).read().split('\n')
    L=[l for l in L if '|Bikini|' not in l]
    last=max(i for i,l in enumerate(L) if l and not l.startswith('#') and not l.startswith('outfit='))
    new=['top|Bikini|p_top_bikini.bin|extra.png','bottom|Bikini|p_bottom_bikini.bin|extra.png','overall|Bikini|p_overall_bikini.bin|extra.png']
    L[last+1:last+1]=new
    open(pf,'w').write('\n'.join(L))
if __name__=='__main__': main(sys.argv[1], sys.argv[2])
