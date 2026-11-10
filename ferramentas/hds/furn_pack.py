# Etapa 171: empacota a mobília do Hds: um GLB pequeno por móvel (texturas compartilhadas em t/), índice com categorias
import sys,io,json,struct,pickle,os,re,collections,hashlib,shutil; sys.path.insert(0,'/home/claude/tools')
import numpy as np
models,mlist,tlist=pickle.load(open('/home/claude/out/furn.pkl','rb'))
OUT='/home/claude/out/mobilia'; shutil.rmtree(OUT,ignore_errors=True)
for d in('m','t'): os.makedirs(OUT+'/'+d)
# texturas
tfile={}
for i,(n,im) in enumerate(tlist):
    if im.mode=='RGBA' and np.asarray(im.getchannel('A')).min()<250: fn='t%03d.png'%i; im.save(OUT+'/t/'+fn,'PNG',optimize=True)
    else: fn='t%03d.jpg'%i; im.convert('RGB').save(OUT+'/t/'+fn,'JPEG',quality=86,optimize=True)
    tfile[i]=fn
# um modelo por nome: pares View/Template do mesmo móvel; o de tamanho absurdo (peças soltas longe) perde; senão vale o View
import export,scene
def rootname(n):
    d=export.F(n); g,t=scene.gos(d); return [g[v['go']][0] for k,v in t.items() if v['father'] not in t][0]
def vol(md):
    b=np.array(md['bbox'][1])-np.array(md['bbox'][0]); return float(np.prod(np.maximum(b,0.01)))
byn=collections.defaultdict(list)
for md in models: md['root']=rootname(md['file']); byn[md['name']].append(md)
uniq=[]; drop=[]
for nm,c in byn.items():
    if len(c)>1:
        v=[vol(x) for x in c]
        best=min(c,key=vol) if max(v)/min(v)>3 else (next((x for x in c if x['root'].endswith('_View')),c[0]))
    else: best=c[0]
    b=np.array(best['bbox'][1])-np.array(best['bbox'][0])
    if b.max()>8: drop.append((nm,b.round(1).tolist())); continue
    uniq.append(best)
print('removidos por tamanho absurdo:',drop)
models=uniq
# recentraliza
for md in models:
    lo=np.min([p.min(0) for a in md['prims'].values() for p in a[0]],0); hi=np.max([p.max(0) for a in md['prims'].values() for p in a[0]],0)
    sh=np.array([-(lo[0]+hi[0])/2,-lo[1],-(lo[2]+hi[2])/2],np.float32)
    for a in md['prims'].values():
        for k in range(len(a[0])): a[0][k]=(a[0][k]+sh).astype(np.float32)
    md['size']=(hi-lo).tolist()
cnt=collections.Counter()
for md in sorted(models,key=lambda m:(m['name'],m['file'])):
    cnt[md['name']]+=1; md['id']=re.sub(r'[^A-Za-z0-9_]','',md['name'])+('' if cnt[md['name']]==1 else '_%d'%cnt[md['name']])
models.sort(key=lambda m:m['id'].lower())
# categorias (a primeira que casar)
CATS=[('portas','Portas e janelas',r'Door|Window|Doorway|Garagedoor|Blinds'),
 ('banheiro','Banheiro',r'Bath|Toilet|Shower|Faucet|Towel|Toothbrush|Toothpaste|Soap|Shampoo|Mouthwash|Jacuzzi|WashingMachine|Bidet|SinkBathroom|Sink\d|^Sink'),
 ('cozinha','Cozinha',r'Kitchen|Fridge|Stove|Oven|Hob|Microwave|Range|Hood|Smeg|Toaster|Kettle|Coffee|Blender|Dishwasher|Knife|Knives|Fork|Spoon|Plate|Pan$|Pan\d|Pot\d|Cup|Glass|Bottle|Jar|Bowl|Cutting|Placemat|Napkin|Salt|Sugar|Tea|Dispenser|Wine|Container|Cooker|Frother|Gloves|Oil|Cabinet(Sink|Hob)'),
 ('sala','Sofás e poltronas',r'Sofa|Armchair|Pouf|Chaise|Couch|Bench|Ottoman|Lounger|Hammock'),
 ('mesas','Mesas e cadeiras',r'Table|Chair|Desk|Stool|Seat'),
 ('quarto','Quarto',r'Bed|Wardrobe|Nightstand|Chest|Dresser|Mattress|Cradle|Mirror|Hanger|Closet|Pillow|Blanket'),
 ('estantes','Estantes e armários',r'Shelf|Bookshelf|Rack|Cupboard|Cabinet|Bookcase|Drawer|Book|Stand|Locker'),
 ('luz','Iluminação',r'Lamp|Light|Chandelier|Torchere|Lantern|Sconce|Fan$|CeilingFan|Bulb'),
 ('eletro','Eletrônicos e música',r'Tv|Monitor|Desktop|Computer|Laptop|PlayStation|XBox|Nintendo|Phone|Camera|Speaker|Keyboard|Mouse|Gamepad|Joystick|Console|Typewriter|Vinyl|Guitar|Drums|Synthesizer|Piano|Amplifier|Radio|Printer|Router|Tablet|Vacuum|Conditioner|Radiator|Heater|Detector|Sensor|Security|Clock|Fireplace'),
 ('jardim','Jardim e área externa',r'Garden|Backyard|Bush|Tree|Flower|Pool|Fence|Arbor|Arch|Swing|Grill|Umbrella|Palm|Thuja|Spruce|Sandbox|Outdoor|Plant|Grass|Cactus|Gnome|Greenhouse|Playground|Slide|Metal'),
 ('pets','Pets',r'Dog|Cat|Pet|Parrot|Hamster|Aquarium|Fish'),
 ('esportes','Esportes e brinquedos',r'Ball|Basketball|Gymnastic|Kids|Toy|Dart|Pooltable|Cue|Bike|Bicycle|Ski|Yoga|Weights|Dumbbell|Treadmill|Doll|Game')]
CP=[(k,n,re.compile(r,re.I)) for k,n,r in CATS]
ci={k:i for i,(k,n,r) in enumerate(CATS)}; ci['decor']=len(CATS)
def cat_of(i):
    for k,n,r in CP:
        if r.search(i): return k
    return 'decor'
PT={'Single':'simples','Double':'dupla','Sliding':'de correr','Door':'Porta','Doorway':'Batente','Window':'Janela','Panoramic':'Panorâmica','Tinted':'fumê','Garagedoor':'Portão de garagem','Small':'pequeno','Big':'grande','Large':'grande','Medium':'médio',
'Sofa':'Sofá','Armchair':'Poltrona','Table':'Mesa','Chair':'Cadeira','Bed':'Cama','Desk':'Escrivaninha','Kitchen':'Cozinha','Fridge':'Geladeira','Stove':'Fogão','Oven':'Forno','Microwave':'Micro-ondas','Sink':'Pia','Toilet':'Vaso sanitário','Bath':'Banheiro','Bathtub':'Banheira','Shower':'Chuveiro','Faucet':'Torneira',
'Lamp':'Luminária','Light':'Luz','Chandelier':'Lustre','Mirror':'Espelho','Painting':'Quadro','Rug':'Tapete','Carpet':'Tapete','Curtains':'Cortinas','Blinds':'Persiana','Shelf':'Prateleira','Bookshelf':'Estante','Cabinet':'Armário','Cupboard':'Armário','Wardrobe':'Guarda-roupa','Nightstand':'Criado-mudo','Chest':'Cômoda','Drawers':'Gavetas',
'Tv':'TV','Monitor':'Monitor','Desktop':'Computador','Computer':'Computador','Phone':'Telefone','Plant':'Planta','Flower':'Flor','Pot':'Vaso','Bush':'Arbusto','Tree':'Árvore','Garden':'Jardim','Backyard':'Quintal','Pool':'Piscina','Fence':'Cerca','Swing':'Balanço','Grill':'Churrasqueira','Umbrella':'Guarda-sol','Hammock':'Rede',
'Pouf':'Pufe','Bench':'Banco','Stool':'Banqueta','Clock':'Relógio','Wall':'de parede','Wood':'madeira','Wooden':'de madeira','Metal':'metal','Red':'vermelho','Blue':'azul','Green':'verde','Grey':'cinza','Gray':'cinza','White':'branco','Black':'preto','Dark':'escuro','Light':'claro','Modern':'moderno','Japanese':'japonês','Kids':'infantil','Baby':'bebê',
'Book':'Livro','Books':'Livros','Ball':'Bola','Dog':'Cachorro','Cat':'Gato','Pet':'Pet','Bowl':'Tigela','House':'Casa','Fireplace':'Lareira','Piano':'Piano','Guitar':'Guitarra','Drums':'Bateria','Washing':'Lavadora','Machine':'Máquina','Coffee':'Café','Maker':'Cafeteira','Kettle':'Chaleira','Toaster':'Torradeira','Blender':'Liquidificador',
'Knife':'Faca','Knives':'Facas','Fork':'Garfo','Spoon':'Colher','Plate':'Prato','Cup':'Xícara','Glass':'Copo','Bottle':'Garrafa','Towel':'Toalha','Towels':'Toalhas','Soap':'Sabonete','Toothbrush':'Escova de dentes','Toilet':'Vaso sanitário','Paper':'Papel','Bag':'Bolsa','Box':'Caixa','Christmas':'Natal','Tree':'Árvore','Radiator':'Radiador','Fan':'Ventilador','Ceiling':'de teto','Corner':'de canto','Top':'alto','Wall':'de parede','Built':'embutido','In':'','Electric':'elétrico','Gas':'a gás','Hob':'Cooktop','Hood':'Coifa','Range':'Coifa','Cabinets':'Armários','Fridge':'Geladeira','Sofa':'Sofá','Mattress':'Colchão','Aquarium':'Aquário','Globe':'Globo','Map':'Mapa','World':'mundo','Vinyl':'Vinil','Player':'Toca-discos','Lantern':'Lanterna','Arbor':'Pérgola','Arch':'Arco','Sandbox':'Caixa de areia','Playground':'Playground'}
def nome(i):
    base=re.sub(r'_\d+$','',i); toks=re.findall(r'[A-Z][a-z]+|[A-Z]+(?![a-z])|\d+(?:_\d+)?|[a-z]+',base)
    out=[]; 
    for t in toks:
        w=PT.get(t,t)
        if w: out.append(w)
    s=' '.join(out); suf=re.search(r'_(\d+)$',i)
    if suf: s+=' (var. %s)'%suf.group(1)
    return s[:1].upper()+s[1:]
def write(md,path):
    mu=sorted(md['prims']); mr={m:k for k,m in enumerate(mu)}
    tu=sorted(set(mlist[m]['tex'] for m in mu if mlist[m]['tex']>=0)); tr={t:k for k,t in enumerate(tu)}
    bin=bytearray(); bvs=[]; acc=[]
    def ab(arr,tg):
        while len(bin)%4: bin.append(0)
        st=len(bin); bin.extend(arr.tobytes()); bvs.append(dict(buffer=0,byteOffset=st,byteLength=arr.nbytes,target=tg)); return len(bvs)-1
    imgs=[dict(uri='t/'+tfile[t]) for t in tu]; textures=[dict(source=k,sampler=0) for k in range(len(tu))]
    gm=[]
    for m in mu:
        mm=mlist[m]; pm=dict(baseColorFactor=mm['col']+[1.0],metallicFactor=0.0,roughnessFactor=0.9)
        if mm['tex']>=0: pm['baseColorTexture']=dict(index=tr[mm['tex']])
        gm.append(dict(name=mm['name'],pbrMetallicRoughness=pm,doubleSided=True,**({'alphaMode':'MASK','alphaCutoff':0.5} if mm['cut'] else {})))
    pr=[]
    for m,a in md['prims'].items():
        P=np.concatenate(a[0]); N=np.concatenate(a[1]); UV=np.concatenate(a[2]); I=np.concatenate(a[3])
        if len(P)>=65536: continue
        b0=len(acc)
        acc+=[dict(bufferView=ab(P,34962),componentType=5126,count=len(P),type='VEC3',min=P.min(0).tolist(),max=P.max(0).tolist()),
              dict(bufferView=ab(N,34962),componentType=5126,count=len(N),type='VEC3'),
              dict(bufferView=ab(UV,34962),componentType=5126,count=len(UV),type='VEC2'),
              dict(bufferView=ab(I.astype(np.uint16),34963),componentType=5123,count=len(I),type='SCALAR')]
        pr.append(dict(attributes=dict(POSITION=b0,NORMAL=b0+1,TEXCOORD_0=b0+2),indices=b0+3,material=mr[m]))
    if not pr: return False
    js=dict(asset=dict(version='2.0'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(name=md['id'],mesh=0)],meshes=[dict(primitives=pr)],materials=gm,textures=textures,images=imgs,samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)],accessors=acc,bufferViews=bvs,buffers=[dict(byteLength=len(bin))])
    j=json.dumps(js,separators=(',',':')).encode()
    while len(j)%4: j+=b' '
    while len(bin)%4: bin.append(0)
    open(path,'wb').write(struct.pack('<III',0x46546C67,2,12+8+len(j)+8+len(bin))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(bin),0x004E4942)+bytes(bin))
    return True
index=[]
for md in models:
    if not write(md,OUT+'/m/%s.glb'%md['id']): continue
    w,d,h=md['size'][0],md['size'][2],md['size'][1]
    c=cat_of(md['id'])
    index.append(dict(id=md['id'],n=nome(md['id']),c=ci[c],w=max(1,int(np.ceil(w-0.1))),h=max(1,int(np.ceil(d-0.1))),a=round(h,2),sx=round(w,2),sz=round(d,2)))
cats=[dict(k=k,n=n) for k,n,r in CATS]+[dict(k='decor',n='Decoração e objetos')]
json.dump(dict(cats=cats,m=index),open(OUT+'/mobilia.json','w'),ensure_ascii=False,separators=(',',':'))
tot=sum(os.path.getsize(os.path.join(dp,f)) for dp,_,fs in os.walk(OUT) for f in fs)
print(len(index),'modelos; total',tot//1024//1024,'MB; texturas',len(tfile))
print(collections.Counter(cats[m['c']]['n'] for m in index))
print([ (m['id'],m['n']) for m in index[:12]])
print('grandes:',[(m['id'],m['w'],m['h']) for m in index if m['w']>12 or m['h']>12][:10])


# ---- miniaturas (rasterizador simples: ortográfico, pintor, cor da textura no centro do triângulo)
from PIL import Image, ImageDraw
os.makedirs(OUT+'/th',exist_ok=True)
TA={}
def tarr(i):
    if i not in TA: TA[i]=np.asarray(tlist[i][1].convert('RGBA')).astype(np.float32)/255
    return TA[i]
yaw=np.radians(38); pit=np.radians(24)
Ry=np.array([[np.cos(yaw),0,np.sin(yaw)],[0,1,0],[-np.sin(yaw),0,np.cos(yaw)]])
Rx=np.array([[1,0,0],[0,np.cos(pit),-np.sin(pit)],[0,np.sin(pit),np.cos(pit)]])
R=Rx@Ry; L=np.array([-0.4,0.8,0.45]); L/=np.linalg.norm(L)
S=3; PX=96
def thumb(md):
    tris=[]
    for m,a in md['prims'].items():
        P=np.concatenate(a[0]).astype(float); N=np.concatenate(a[1]).astype(float); UV=np.concatenate(a[2]); I=np.concatenate(a[3]).reshape(-1,3)
        mm=mlist[m]; base=np.array(mm['col'][:3])
        if len(I)>6000: I=I[::int(np.ceil(len(I)/6000))]
        A,B,C=P[I[:,0]],P[I[:,1]],P[I[:,2]]
        cen=(A+B+C)/3; nrm=(N[I[:,0]]+N[I[:,1]]+N[I[:,2]]); nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)+1e-9
        lam=np.clip(nrm@L,0,1)*0.55+0.55
        if mm['tex']>=0:
            T=tarr(mm['tex']); h,w=T.shape[:2]; uv=(UV[I[:,0]]+UV[I[:,1]]+UV[I[:,2]])/3
            px=np.clip((np.mod(uv[:,0],1)*w).astype(int),0,w-1); py=np.clip((np.mod(uv[:,1],1)*h).astype(int),0,h-1)
            tc=T[py,px]; col=tc[:,:3]*base; al=tc[:,3]
        else: col=np.tile(base,(len(I),1)); al=np.ones(len(I))
        col=np.clip(col*lam[:,None],0,1)
        pa=np.stack([A,B,C],1)@R.T
        for k in range(len(I)):
            if mm['cut'] and al[k]<0.5: continue
            tris.append((pa[k,:,2].mean(),pa[k,:,:2],col[k]))
    if not tris: return None
    allv=np.concatenate([t[1] for t in tris]); lo=allv.min(0); hi=allv.max(0); sc=(PX*S*0.86)/max(hi-lo)
    off=(PX*S-(hi-lo)*sc)/2
    tris.sort(key=lambda t:t[0])  # z maior = mais longe? (câmera olha para -z após rotação): desenha do mais longe ao mais perto
    img=Image.new('RGBA',(PX*S,PX*S),(0,0,0,0)); dr=ImageDraw.Draw(img)
    for z,v,c in tris:
        pts=[((x-lo[0])*sc+off[0],PX*S-((y-lo[1])*sc+off[1])) for x,y in v]
        dr.polygon(pts,fill=tuple(int(x*255) for x in c)+(255,))
    return img.resize((PX,PX),Image.LANCZOS)
import time; t0=time.time(); nth=0
for md in models:
    if md['id'] not in {m['id'] for m in index[:0]} :
        pass
ids={m['id'] for m in index}
for md in models:
    if md['id'] not in ids: continue
    im=thumb(md)
    if im: im.save(OUT+'/th/%s.png'%md['id'],optimize=True); nth+=1
print('miniaturas',nth,'em',int(time.time()-t0),'s')
