import export,roots,numpy as np,json,struct,io,os,math,random
from PIL import Image
YSH=-9.9
RES=(1,0)
HOUSES=[(2,'House1'),(3,'House2'),(4,'House3'),(5,'House4'),(6,'House5'),(7,'House6'),(8,'House7'),(9,'House8'),(10,'House10'),(11,'House11'),(12,'House12'),(17,'House13'),(18,'House14'),(19,'House17'),(20,'House18'),(21,'House19'),(22,'House20')]
def Ry(a):
    c,s=math.cos(a),math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def skip(n): return n.startswith('Clouds') or '_lod_1' in n or '_lod_2' in n
class Reg:
    def __init__(s): s.pieces={};s.plist=[];s.matkeys={};s.mats=[];s.texs={};s.timgs=[];s.md={};s.inst=[]
    def matid(s,mt):
        k=(mt['name'],mt['tp'])
        if k in s.matkeys: return s.matkeys[k]
        ti=-1
        if mt['tex']:
            tn,im=mt['tex']
            if tn not in s.texs:
                if max(im.size)>512: im=im.resize((min(512,im.size[0]),min(512,im.size[1])),Image.LANCZOS)
                s.texs[tn]=len(s.timgs); s.timgs.append((tn,im))
            ti=s.texs[tn]
        cut=False
        if ti>=0 and s.timgs[ti][1].mode=='RGBA': cut=bool((np.asarray(s.timgs[ti][1].getchannel('A'))<128).mean()>0.02)
        s.mats.append(dict(name=mt['name'],col=[round(float(c),4) for c in mt['col'][:3]],tex=ti,cut=cut)); s.matkeys[k]=len(s.mats)-1; return s.matkeys[k]
    def piece_from(s,it):
        mk=(id(it['f']),it['mo'][0])
        if mk not in s.md: s.md[mk]=export.mesh_data(it['f'],it['mo'])
        m=s.md[mk]
        if not m: return None
        mt=[export.get_mat(it['d'],x) for x in it['mats']]; mids=tuple(s.matid(x) if x else -1 for x in mt)
        mir=bool(np.linalg.det(it['W'][:3,:3])<0); pk=(mk,mids,mir)
        if pk not in s.pieces:
            subs=[]
            for si,ix in enumerate(m['subs']):
                if si>=len(mids) or mids[si]<0: continue
                used=np.unique(ix); rm=np.full(len(m['P']),-1); rm[used]=np.arange(len(used))
                P=m['P'][used].copy(); P[:,2]*=-1
                N=m['N'][used].copy() if m['N'] is not None else np.tile([0,1,0.],(len(used),1)); N[:,2]*=-1
                UV=m['UV'][used].copy() if m['UV'] is not None else np.zeros((len(used),2),np.float32); UV[:,1]=1-UV[:,1]
                tri=rm[ix]; tri=tri[:,[0,1,2]] if mir else tri[:,[0,2,1]]
                subs.append((mids[si],P.astype(np.float32),N.astype(np.float32),UV.astype(np.float32),tri.reshape(-1).astype(np.uint32)))
            s.pieces[pk]=len(s.plist); s.plist.append(dict(name=m['name'],subs=subs))
        return s.pieces[pk]
    def custom(s,name,subs):
        s.plist.append(dict(name=name,subs=subs)); return len(s.plist)-1
    def add(s,pi,M,kind=0,plot=-1):
        s.inst.append([pi]+[round(float(x),4) for x in M[:3,:].reshape(-1)]+[kind,plot])
def mat4(R,t):
    M=np.eye(4); M[:3,:3]=R; M[:3,3]=t; return M
def quad(x0,z0,x1,z1,y,uvf):
    P=np.array([[x0,y,z0],[x1,y,z0],[x1,y,z1],[x0,y,z1]],np.float32); N=np.tile([0,1,0.],(4,1)).astype(np.float32)
    UV=np.array([uvf(p[0],p[2]) for p in P],np.float32)
    I=np.array([0,2,1,0,3,2],np.uint32)   # normal +y
    return P,N,UV,I

def build(NX=3,NZ=2,BLK=120.0,seed=7):
    rnd=random.Random(seed)
    R=Reg()
    # ---- road kit from level2
    base=roots.classify(2); kit={}
    for it in base:
        n=it['name'].split(' (')[0]
        if n in('road_20_m_model','road_turn_r_model','road_turn_l_model','plane_40_m','lamp_street_high_lod_0','mailbox_dummy_prefab','fire_hydrant_dummy_prefab','simple_tree_model','trashbin_lod_0','bush_wall_10m','ford_focus_3_model') and n not in kit: kit[n]=it
    pst=R.piece_from(kit['road_20_m_model']); ptn=R.piece_from(kit['road_turn_r_model'])
    # material ids
    def mid(it,name):
        for x in it['mats']:
            mt=export.get_mat(it['d'],x)
            if mt and mt['name']==name: return R.matid(mt)
    M_AS=mid(kit['road_20_m_model'],'asphalt_material'); M_CO=mid(kit['road_20_m_model'],'concrete_plates_material'); M_GR=mid(kit['road_20_m_model'],'grass_terrain_tile_material'); M_LN=mid(kit['road_20_m_model'],'road_marking_line_material')
    gu=lambda x,z:(0.5*x,-0.5*z)
    # ---- city geometry
    CELL=40.0; PITCH=BLK+CELL
    xr=[i*PITCH for i in range(NX+1)]; zr=[j*PITCH for j in range(NZ+1)]   # road centerlines
    X0,X1,Z0,Z1=xr[0]-20,xr[-1]+20,zr[0]-20,zr[-1]+20
    # junction/turn cells
    cell_info={}
    for i,x in enumerate(xr):
        for j,z in enumerate(zr):
            arms=dict(W=i>0,E=i<NX,N=j<NZ,S=j>0)   # N = +z, S = -z
            cell_info[(i,j)]=arms
    def straight(cx,cz,along):   # one 20 m piece centered at (cx,cz); along='x' or 'z'
        # piece local (flipped kit space): spans z in [-20,0], center local (0,0,-10)
        yaw=0.0 if along=='z' else math.pi/2
        Rm=Ry(yaw); t=np.array([cx,YSH*0,cz])-Rm@np.array([0,0,-10.0])
        R.add(pst,mat4(Rm,t),0,-1)
    # straight segments between junction cells
    for j,z in enumerate(zr):
        for i in range(NX):
            xa=xr[i]+20; xb=xr[i+1]-20; n=int((xb-xa)/20)
            for k in range(n): straight(xa+10+20*k,z,'x')
    for i,x in enumerate(xr):
        for j in range(NZ):
            za=zr[j]+20; zb=zr[j+1]-20; n=int((zb-za)/20)
            for k in range(n): straight(x,za+10+20*k,'z')
    # junction tiles (custom) and corner turns (real piece)
    def junction(cx,cz,arms):
        subs={M_GR:[],M_CO:[],M_AS:[]}
        def add(m,x0,z0,x1,z1,y,uvf):
            P,N,UV,I=quad(x0,z0,x1,z1,y,uvf); subs[m].append((P,N,UV,I))
        add(M_GR,cx-20,cz-20,cx+20,cz+20,0.0,gu)
        cu=lambda x,z:(0.325*(x+z),1-0.6057); au=lambda x,z:(0.1625*(x+z),1-0.84)
        add(M_CO,cx-8,cz-8,cx+8,cz+8,0.02,cu); add(M_AS,cx-5.2,cz-5.2,cx+5.2,cz+5.2,0.04,au)
        if arms['E']: add(M_CO,cx+8,cz-8,cx+20,cz+8,0.02,cu); add(M_AS,cx+5.2,cz-5.2,cx+20,cz+5.2,0.04,au)
        if arms['W']: add(M_CO,cx-20,cz-8,cx-8,cz+8,0.02,cu); add(M_AS,cx-20,cz-5.2,cx-5.2,cz+5.2,0.04,au)
        if arms['N']: add(M_CO,cx-8,cz+8,cx+8,cz+20,0.02,cu); add(M_AS,cx-5.2,cz+5.2,cx+5.2,cz+20,0.04,au)
        if arms['S']: add(M_CO,cx-8,cz-20,cx+8,cz-8,0.02,cu); add(M_AS,cx-5.2,cz-20,cx+5.2,cz-5.2,0.04,au)
        out=[]
        for m,l in subs.items():
            if not l: continue
            Ps=[];Ns=[];Us=[];Is=[];o=0
            for P,N,UV,I in l: Ps.append(P);Ns.append(N);Us.append(UV);Is.append(I+o);o+=len(P)
            out.append((m,np.concatenate(Ps),np.concatenate(Ns),np.concatenate(Us),np.concatenate(Is)))
        pi=R.custom('junction',out); R.add(pi,np.eye(4),0,-1)
    for (i,j),arms in cell_info.items():
        cx,cz=xr[i],zr[j]; n=sum(arms.values())
        if n==2 and ((arms['E'] and arms['W']) or (arms['N'] and arms['S'])): continue
        if n==2:
            # corner: real turn piece. local: enters at (0,0,0)->heads local -z' (flipped), exits toward +x at (20,0,-20)? find by test mapping later
            key=''.join(sorted(k for k,v in arms.items() if v)); yaw={'EN':0,'ES':90,'SW':180,'NW':270}[key]
            Rm=Ry(math.radians(yaw)); t=np.array([cx,0,cz])-Rm@np.array([0,0,-20.0]); R.add(ptn,mat4(Rm,t),0,-1)
        else: junction(cx,cz,arms)
    R.ctx=dict(xr=xr,zr=zr,kit=kit,M=dict(AS=M_AS,CO=M_CO,GR=M_GR),pst=pst,ptn=ptn,R=R,gu=gu,X=(X0,X1,Z0,Z1))
    return R

def templates(R):
    """plot templates: houses (real, with interior)"""
    T=[]
    for L,name in HOUSES:
        its=roots.classify(L); sel=[]
        for it in its:
            p=it['path']
            if skip(it['name']): continue
            if it['name'].startswith(('GridView','GeneratedTerrain')) or 'ConstructionGrid' in p or 'GeneratedTerrainGrassTile' in p: continue
            if p[0] in('HouseRoot','around_fence','front_fence') or p[:2]==['EnvironmentRoot','PlayersFence']: sel.append(it)
        ff=[it for it in its if it['path'][0]=='front_fence']
        if not sel: print('vazia',name); continue
        if ff:
            xs=[it['M'][0,3] for it in ff]; zf=float(np.mean([it['M'][2,3] for it in ff])); xc=(min(xs)+max(xs))/2
        else:
            hx=[it['M'][0,3] for it in sel]; zf=float(min(it['M'][2,3] for it in sel))-3.0; xc=(min(hx)+max(hx))/2
        xmin=min(it['M'][0,3] for it in sel); xmax=max(it['M'][0,3] for it in sel); zmax=max(it['M'][2,3] for it in sel)
        T.append(dict(name=name,L=L,items=sel,xc=xc,zf=zf,w=xmax-xmin+4,d=zmax-zf+4))
    return T

import re
def kind_of(n):
    n=n.lower()
    if re.search(r'ceil|celing|cailing|roof|attic_floor',n) or re.match(r'house_\d+(_model)?$',n): return 2
    if re.search(r'wall|fence|post|house_\d+$|house_\d+_model|garage_house',n) and 'gate_move' not in n: return 1
    return 0
def mscale(Rm,s): return Rm*s
def finish(R,T):
    ctx=R.ctx; xr,zr,kit=ctx['xr'],ctx['zr'],ctx['kit']; rnd=random.Random(11)
    NX=len(xr)-1; NZ=len(zr)-1
    # fallback House17
    for t in T: pass
    # edges: blocks, S edge then N edge, houses packed
    order=sorted(T,key=lambda t:(t['name']!='House1',-t['w']))
    # alternate wide/narrow for variety
    hs=[order[0]]+[o for k,o in enumerate(order[1:]) if True]
    slots=[]
    for bj in range(NZ):
        for bi in range(NX):
            if (bi,bj)==RES: continue
            xa=xr[bi]+20; xb=xr[bi+1]-20
            slots.append((bi,bj,'S',xa,xb,zr[bj])); slots.append((bi,bj,'N',xa,xb,zr[bj+1]))
    ptr=0; placed=[]; marks=[]
    rnd.shuffle(slots[2:]) if False else None
    for (bi,bj,side,xa,xb,zc) in slots:
        if ptr>=len(hs): break
        avail=xb-xa-8; group=[]; used=0
        while ptr<len(hs) and used+hs[ptr]['w']+(6 if group else 0)<=avail and len(group)<2:
            used+=hs[ptr]['w']+(6 if group else 0); group.append(hs[ptr]); ptr+=1
        if not group: continue
        x=(xa+xb)/2-used/2
        n=np.array([0,0,-1.0]) if side=='S' else np.array([0,0,1.0])
        yaw=math.atan2(-n[0],-n[2]); Rm=Ry(yaw)
        for t in group:
            xc_w=x+t['w']/2; x+=t['w']+6
            Pc=np.array([xc_w,0,zc]); Pf=Pc-n*10
            F=mat4(Rm,Pf)@mat4(np.eye(3),np.array([-t['xc'],0,-t['zf']]))
            plot=len(placed)
            for it in t['items']:
                pi=R.piece_from(it)
                if pi is None: continue
                M=F@it['M']; M[1,3]+=YSH
                R.add(pi,M,kind_of(it['name']),plot)
            placed.append(dict(name=t['name'],x=float(Pf[0]),z=float(Pf[2])))
            # mailbox + lamp near plot
        ctx.setdefault('edges',[]).append((bi,bj,side))
    return placed

def extras(R,placed):
    ctx=R.ctx; xr,zr,kit=ctx['xr'],ctx['zr'],ctx['kit']; M=ctx['M']; rnd=random.Random(5)
    X0,X1,Z0,Z1=ctx['X']
    # grama: quarteirões + faixa externa
    def grass(x0,z0,x1,z1,y=0.0):
        P,N,UV,I=quad(x0,z0,x1,z1,y,ctx['gu']); return R.custom('grama',[(M['GR'],P,N,UV,I)])
    for bj in range(len(zr)-1):
        for bi in range(len(xr)-1):
            R.add(grass(xr[bi]+20,zr[bj]+20,xr[bi+1]-20,zr[bj+1]-20,-0.06 if (bi,bj)==RES else 0.0),np.eye(4),0,-1)
    B=260.0
    for (a,b,c,d) in [(X0-B,Z0-B,X1+B,Z0),(X0-B,Z1,X1+B,Z1+B),(X0-B,Z0,X0,Z1),(X1,Z0,X1+B,Z1)]:
        R.add(grass(a,b,c,d),np.eye(4),0,-1)
    # postes ao longo das ruas (alternando lados), a cada 40 m
    lamp=R.piece_from(kit['lamp_street_high_lod_0']); hyd=R.piece_from(kit['fire_hydrant_dummy_prefab']); tree=R.piece_from(kit['simple_tree_model']); mb=R.piece_from(kit['mailbox_dummy_prefab']); tb=R.piece_from(kit['trashbin_lod_0'])
    def face(dx,dz): return Ry(math.atan2(-dx,-dz))
    for j,z in enumerate(zr):
        for x in np.arange(xr[0]+20,xr[-1]-19,40):
            side=1 if int((x-xr[0])/40)%2==0 else -1
            if abs(((x-xr[0])%PITCH_)-0)<28 or abs(((x-xr[0])%PITCH_)-PITCH_)<28: pass
            p=np.array([x,0,z+side*6.0]); R.add(lamp,mat4(face(0,-side),p),0,-1)
    for i,x in enumerate(xr):
        for z in np.arange(zr[0]+20,zr[-1]-19,40):
            side=1 if int((z-zr[0])/40)%2==0 else -1
            p=np.array([x+side*6.0,0,z]); R.add(lamp,mat4(face(-side,0),p),0,-1)
    # hidrantes e lixeiras perto dos cruzamentos
    for x in xr:
        for z in zr:
            for (ox,oz) in [(9,9),(-9,-9)]:
                if rnd.random()<0.6: R.add(hyd,mat4(face(-ox,-oz),np.array([x+ox,0,z+oz])),0,-1)
            if rnd.random()<0.5: R.add(tb,mat4(face(-1,-1),np.array([x-9,0,z+9])),0,-1)
    # caixas de correio e árvores
    for pl in placed:
        R.add(mb,mat4(np.eye(3),np.array([pl['x']+6,0,pl['z']])),0,-1) if False else None
    # árvores nos quarteirões (fora das áreas das casas)
    taken=[(p['x'],p['z']) for p in placed]
    for bj in range(len(zr)-1):
        for bi in range(len(xr)-1):
            cx=(xr[bi]+xr[bi+1])/2; cz=(zr[bj]+zr[bj+1])/2
            for _ in range(0 if (bi,bj)==RES else 7):
                x=cx+rnd.uniform(-45,45); z=cz+rnd.uniform(-8,8)
                s=rnd.uniform(0.9,1.35); R.add(tree,mat4(Ry(rnd.uniform(0,6.28))*s,np.array([x,0,z])),0,-1)
    # árvores ao longo das calçadas (a cada ~26 m, lados alternados)
    for j,z in enumerate(zr):
        for x in np.arange(xr[0]+30,xr[-1]-29,26):
            if rnd.random()<0.45:
                s=rnd.uniform(0.85,1.2); R.add(tree,mat4(Ry(rnd.uniform(0,6.28))*s,np.array([x,0,z+rnd.choice([-1,1])*13.5])),0,-1)
PITCH_=160.0
