# Etapa 172: empacota a mobília do Hds com
#  - nomes oficiais em português (Localization do jogo), categorias e subcategorias do Hds
#  - ícones do próprio Hds (atlas de sprites) e ícones das categorias
#  - partes coloríveis (FurnitureViewSet): cada parte tem a lista de materiais/cores do jogo
import sys,io,json,struct,pickle,os,re,collections,shutil,csv
sys.path.insert(0,'/home/claude/tools')
import numpy as np
from PIL import Image
import export,scene

models,mlist,tlist=pickle.load(open('/home/claude/out/furn2.pkl','rb'))
LOC=json.load(open('/home/claude/out/loc.json'))
ICONS='/home/claude/out/icons'
OUT='/home/claude/out/mobilia2'; shutil.rmtree(OUT,ignore_errors=True)
for d in ('m','t','ic','cat'): os.makedirs(OUT+'/'+d)

# ---------------------------------------------------------------- texturas
tfile={}
for i,(n,im) in enumerate(tlist):
    if im.mode=='RGBA' and np.asarray(im.getchannel('A')).min()<250: fn='t%03d.png'%i; im.save(OUT+'/t/'+fn,'PNG',optimize=True)
    else: fn='t%03d.jpg'%i; im.convert('RGB').save(OUT+'/t/'+fn,'JPEG',quality=86,optimize=True)
    tfile[i]=fn

# ---------------------------------------------------------------- um modelo por nome
def rootname(n):
    d=export.F(n); g,t=scene.gos(d); return [g[v['go']][0] for k,v in t.items() if v['father'] not in t][0]
def vol(md):
    b=np.array(md['bbox'][1])-np.array(md['bbox'][0]); return float(np.prod(np.maximum(b,0.01)))
byn=collections.defaultdict(list)
for md in models:
    if 'Dirt' in md['name']: continue
    md['root']=rootname(md['file']); byn[md['name']].append(md)
uniq=[]; drop=[]
for nm,c in byn.items():
    if len(c)>1:
        v=[vol(x) for x in c]
        if max(v)/min(v)>3: best=min(c,key=vol)
        else: best=next((x for x in c if x['parts']),None) or next((x for x in c if x['root'].endswith('_View')),c[0])
    else: best=c[0]
    b=np.array(best['bbox'][1])-np.array(best['bbox'][0])
    if b.max()>8: drop.append((nm,b.round(1).tolist())); continue
    uniq.append(best)
models=uniq
print('removidos por tamanho absurdo:',drop)

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

# ---------------------------------------------------------------- categorias (Hds) e subcategorias
MAIN=[('Sala e quarto','shop_cat_room'),('Cozinha','shop_cat_kitchen'),('Escritório','shop_cat_office'),('Banheiro','shop_cat_bath'),
      ('Eletrodomésticos','shop_cat_tech'),('Iluminação','shop_cat_light'),('Decoração','shop_cat_decor'),('Passatempo','shop_cat_hobbies'),
      ('Jardim','shop_cat_backyard_2'),('Portas','build_cat_6_doors'),('Janelas','build_cat_7_windows'),('Outros','shop_cat_other')]
# (regex no nome sem números, principal, subcategoria) — a primeira que casar vale
R=[
 (r'^(SingleDoorway|DoubleDoorway)',9,'Batentes'),(r'^SlidingDoor',9,'Portas de correr'),(r'^Garagedoor',9,'Garagem'),(r'^EntranceDoor',9,'Entrada'),
 (r'^DoubleDoor',9,'Portas duplas'),(r'^SingleDoor',9,'Portas simples'),
 (r'^Panoramic',10,'Panorâmicas'),(r'^DoubleWindow',10,'Janelas duplas'),(r'^SingleWindow|Window',10,'Janelas simples'),
 (r'^(Sofa|Armchair|Chaise|Pouf)',0,'Sofás e poltronas'),(r'^(TvStand|TvTable)',0,'Suportes de TV'),(r'^(CoffeeTable|Table$|TableKotatsu)',0,'Mesas'),
 (r'^Bookshelf',0,'Estantes'),(r'(^Bed|KidsBed)',0,'Camas'),(r'^(Wardrobe|Cupboard)',0,'Armários'),(r'Nightstand',0,'Criados-mudos'),(r'^ChestOfDrawers',0,'Cômodas'),
 (r'^(KitchenTable)',1,'Mesas de cozinha'),(r'^KitchenChair',1,'Cadeiras de cozinha'),
 (r'(KitchenCabinet|KitchenCornerCabinet|ModernKitchen|KitchenHandles|KitchenRack|BuiltInKitchenSink)',1,'Conjunto de cozinha'),
 (r'(Fridge|Hob|Oven|Microwave|KitchenGasStove|KitchenHood|Smeg|Kettle|CoffeeMaker|Blender|Toaster|KitchenKnives|Dishwasher)',1,'Utensílios'),
 (r'^(Cup|Fork|Spoon|Knife|KnifeSet|Plate|Placemat|CuttingBoard|KitchenPan|KitchenSaucepan|KitchenLiquid|TeaSpoon|TeaBox|WineGlass|SugarJar|CoffeeJar|OilGlassBottle|OvenGloves|NapkinHolder|PaperHolder|SaltAndPepper|KetchupDispenser|MayonnaiseDispenser|MustardDispenser)',1,'Acessórios'),
 (r'(Burger|Burrito|Pizza|AsianNoodles)',11,'Comida'),
 (r'^OfficeDesk|^Desk',2,'Mesas de escritório'),(r'^OfficeChair',2,'Cadeiras de escritório'),(r'^Safe',2,'Cofres'),
 (r'^(Stapler|PenContainer|Briefcase|BagLarge|Typewriter|PaperBucket)',2,'Ferramentas'),
 (r'^(Bath|Jacuzzi)',3,'Banheiras'),(r'^Showercabin',3,'Chuveiros'),(r'^(Toilet$|Bidet|ToiletButton)',3,'Vasos sanitários'),(r'^SinkCabinet',3,'Armários'),
 (r'^Sink',3,'Pias'),(r'^Faucet',3,'Torneiras'),(r'^(Shampoo|Soap|Toothbrush|Toothpaste|Mouthwash|ToiletPaper|ToiletBrush|TowelHolder|ElectricToothbrush)',3,'Acessórios'),
 (r'^(TowelRadiator|Radiator|SplitAirConditioner|Boiler|CeilingFan|Ventilation)',4,'Clima'),
 (r'^(Tv|TvOld)$',4,'TVs'),(r'^(Loudspeaker|Soundbar|SmartSpeaker|VinylPlayer)',4,'Áudio'),
 (r'^(PlayStation|SonyPs|XBox|Nintendo|SuperNintendo|Gamepad)',4,'Consoles'),(r'^(AllInOne|Desktop|Laptop|Monitor|Keyboard|ComputerMouse)',4,'Computadores'),
 (r'^(Security|SmokeDetector)',4,'Segurança'),(r'^(WallSocket|WallSwitch|WallLanSocket|RobotVacuum|WashingMachine|Phone|Camera)',4,'Acessórios'),
 (r'^CeilingLamp',5,'Luzes de teto'),(r'^SpotLamp',5,'Spots'),(r'^WallLamp|JapaneseWallLantern',5,'Luzes de parede'),(r'^(TableLamp|KeroseneLamp)',5,'Luminárias de mesa'),
 (r'^Torchere',5,'Luminárias de chão'),(r'^(Japanese.*Lantern|JapaneseCeilingLantern)',5,'Especiais'),
 (r'^(Rug|JapaneseRug|JapaneseMat)',6,'Tapetes'),(r'(Curtains|Blinds)',6,'Cortinas e persianas'),(r'^Mirror',6,'Espelhos'),(r'^Painting',6,'Pinturas'),
 (r'^(FlowerPot|FlowerFloorPot|PotWith)',6,'Plantas'),(r'^Book',6,'Livros'),
 (r'^(Piano|Guitar|Drums|ElectricGuitar|Synthesizer)',7,'Instrumentos'),(r'^(Cat|Dog|Pet|Hamster|Parrot|Aquarium)',7,'Para animais'),
 (r'^(Kids|Dollhouse)',7,'Para crianças'),(r'^(Pooltable|CueRack|Darts|Basketball|SoccerBall|TennisBall|Volleyball|RugbyBall|GolfBall|Gymnastics)',7,'Esportes e jogos'),
 (r'^(Suitcase|Katana)',7,'Outros'),
 (r'^(Garden(Armchair|Chair|Sofa|Table|Pouf)|Backyard|Pergola|OutdoorFireplace|WoodenArch|OutdoorArbor|MetalSwing|GasGrill|AluminumChair|AluminumTable|Sandbox)',8,'Móveis de jardim'),
 (r'^GardenGnome',8,'Gnomos'),(r'^(GardenLamp|GardenLantern)',8,'Iluminação'),
 (r'^(Bush|CylinderBush|Spruce|Thuja|GardenBed)',8,'Plantas'),(r'^(Flower$|FlowerBed)',8,'Flores'),(r'^Pool(Blue|Grey|Wood)',8,'Piscinas'),
 (r'(Tile)',8,'Pisos'),
 (r'^(Vase|Globe|WorldMap|WallClock|GrandfatherClock|Hourglass|Fireplace|Christmas|KeyHolder|Hanger|PaintBucket|PuttyBucket|CarKey)',6,'Especiais'),
 (r'^(GarageRack|GarageToolbox|KidsCarGarage|PaperBox)',11,'Garagem e caixas'),
]
RC=[(re.compile(r),m,s) for r,m,s in R]
def classify(i):
    stem=re.sub(r'(_?\d+(_?\d+)*)+(x|Metal|Dark|Light|Blue|Grey|Red|Green|With.*)?$','',i) if False else re.sub(r'\d+.*$','',i) if re.match(r'^(Tile|Bed|Table|Desk|Book|Tv)',i) is None else i
    for rx,m,s in RC:
        if rx.search(i) or rx.search(stem): return m,s
    return 11,'Diversos'

# ---------------------------------------------------------------- nomes em português (Localization do Hds)
def snake(i):
    base=re.sub(r'_\d+$','',i)
    toks=re.findall(r'[A-Z][a-z]+|[A-Z]+(?![a-z])|\d+|[a-z]+',base)
    return '_'.join(t.lower() for t in toks)
def name_pt(i):
    s=snake(i); cands=[s]
    cands+= [s.replace('_1x','').replace('_2x',''), re.sub(r'_(view|container)$','',s)]
    for c in cands:
        for pre in ('item-','item-dirt_',''):
            v=LOC.get(pre+c)
            if v and v[0]: return v[0]
    # cai para o nome sem número final e junta o número
    m=re.match(r'^(.*?)_(\d+)$',s)
    if m:
        v=LOC.get('item-'+m.group(1))
        if v and v[0]: return '%s %s'%(v[0],m.group(2))
    return None
def title(s): return s[:1].upper()+s[1:] if s else s

# ---------------------------------------------------------------- ícones do Hds
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
icons={norm(f[:-9]):f for f in os.listdir(ICONS) if f.endswith('_icon.png')}
def find_icon(i):
    n=norm(i)
    for c in (n,re.sub(r'(view|container)$','',n),n+'metal',re.sub(r'(\d+)$',r'\g<1>',n)):
        if c in icons: return icons[c]
    s=norm(snake(i))
    return icons.get(s)

# ---------------------------------------------------------------- GLB
def swatch(m):
    mm=mlist[m]; col=np.array(mm['col'][:3])
    if mm['tex']>=0:
        im=tlist[mm['tex']][1].convert('RGBA').resize((8,8),Image.BILINEAR); a=np.asarray(im).astype(float)/255
        w=a[...,3:4]; avg=(a[...,:3]*w).sum((0,1))/max(w.sum(),1e-6); col=col*avg
    c=np.clip(col*255+0.5,0,255).astype(int); return 0xFF000000|(c[0]<<16)|(c[1]<<8)|c[2]
PTPART={'main':'Principal','additional':'Detalhes','countertop':'Bancada','mattress':'Colchão','handles':'Puxadores','body':'Corpo','pillow':'Travesseiro','facade':'Frente','seat':'Assento',
 'table_legs':'Pés','knob':'Botões','led_backlight':'Luz de fundo','bed_body':'Cama','bed_cover':'Cobertor','bed':'Cama','decor':'Decoração','door':'Porta','details':'Detalhes','cloth':'Tecido','switch':'Interruptor','shelf':'Prateleira','main_body':'Corpo'}
def write(md,path):
    keys=sorted(md['prims']); parts=md.get('parts',[])
    pr=[]; keyprim={}
    for k in keys:
        a=md['prims'][k]
        if len(np.concatenate(a[0]))>=65536: continue
        keyprim[k]=len(pr); pr.append(k)
    if not pr: return None
    matset=[]
    for k in pr:
        if k[1] not in matset: matset.append(k[1])
    for p in parts:
        for o in p['opts']:
            if o not in matset: matset.append(o)
    mr={m:j for j,m in enumerate(matset)}
    tu=sorted(set(mlist[m]['tex'] for m in matset if mlist[m]['tex']>=0)); tr={t:k for k,t in enumerate(tu)}
    bin=bytearray(); bvs=[]; acc=[]
    def ab(arr,tg):
        while len(bin)%4: bin.append(0)
        st=len(bin); bin.extend(arr.tobytes()); bvs.append(dict(buffer=0,byteOffset=st,byteLength=arr.nbytes,target=tg)); return len(bvs)-1
    imgs=[dict(uri='t/'+tfile[t]) for t in tu]; textures=[dict(source=k,sampler=0) for k in range(len(tu))]
    gm=[]
    for m in matset:
        mm=mlist[m]; pm=dict(baseColorFactor=mm['col']+[1.0],metallicFactor=0.0,roughnessFactor=0.9)
        if mm['tex']>=0: pm['baseColorTexture']=dict(index=tr[mm['tex']])
        gm.append(dict(name=mm['name'],pbrMetallicRoughness=pm,doubleSided=True,**({'alphaMode':'MASK','alphaCutoff':0.5} if mm['cut'] else {})))
    prs=[]
    for j,k in enumerate(pr):
        a=md['prims'][k]
        P=np.concatenate(a[0]); N=np.concatenate(a[1]); UV=np.concatenate(a[2]); I=np.concatenate(a[3])
        b0=len(acc)
        acc+=[dict(bufferView=ab(P,34962),componentType=5126,count=len(P),type='VEC3',min=P.min(0).tolist(),max=P.max(0).tolist()),
              dict(bufferView=ab(N,34962),componentType=5126,count=len(N),type='VEC3'),
              dict(bufferView=ab(UV,34962),componentType=5126,count=len(UV),type='VEC2'),
              dict(bufferView=ab(I.astype(np.uint16),34963),componentType=5123,count=len(I),type='SCALAR')]
        prs.append(dict(attributes=dict(POSITION=b0,NORMAL=b0+1,TEXCOORD_0=b0+2),indices=b0+3,material=mr[k[1]]))
    cor=[]
    for p in parts:
        idx=[keyprim[k] for k in pr if k[0]==p['i']]
        if not idx: continue
        bases=set(k[1] for k in pr if k[0]==p['i'])
        d=p['opts'].index(list(bases)[0]) if len(bases)==1 and list(bases)[0] in p['opts'] else -1
        if len(p['opts'])<2: continue
        cor.append(dict(n=PTPART.get(p['n'],title(p['n'].replace('_',' '))),p=idx,o=[mr[o] for o in p['opts']],d=d,s=[swatch(o) for o in p['opts']]))
    node=dict(name=md['id'],mesh=0)
    if cor: node['extras']=dict(cor=cor)
    js=dict(asset=dict(version='2.0'),scene=0,scenes=[dict(nodes=[0])],nodes=[node],meshes=[dict(primitives=prs)],materials=gm,textures=textures,images=imgs,samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)],accessors=acc,bufferViews=bvs,buffers=[dict(byteLength=len(bin))])
    j=json.dumps(js,separators=(',',':'),default=lambda o:o.item() if hasattr(o,'item') else str(o)).encode()
    while len(j)%4: j+=b' '
    while len(bin)%4: bin.append(0)
    open(path,'wb').write(struct.pack('<III',0x46546C67,2,12+8+len(j)+8+len(bin))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(bin),0x004E4942)+bytes(bin))
    return len(cor)

# ---------------------------------------------------------------- miniatura de reserva (sem ícone do Hds)
yaw=np.radians(38); pit=np.radians(24)
Ry=np.array([[np.cos(yaw),0,np.sin(yaw)],[0,1,0],[-np.sin(yaw),0,np.cos(yaw)]])
Rx=np.array([[1,0,0],[0,np.cos(pit),-np.sin(pit)],[0,np.sin(pit),np.cos(pit)]])
RR=Rx@Ry; LL=np.array([-0.4,0.8,0.45]); LL/=np.linalg.norm(LL)
from PIL import ImageDraw
TA={}
def tarr(i):
    if i not in TA: TA[i]=np.asarray(tlist[i][1].convert('RGBA')).astype(np.float32)/255
    return TA[i]
def thumb(md,PX=128,S=3):
    from collections import defaultdict
    tris=[]
    for (pp,m),a in md['prims'].items():
        P=np.concatenate(a[0]).astype(float); N=np.concatenate(a[1]).astype(float); UV=np.concatenate(a[2]); I=np.concatenate(a[3]).reshape(-1,3)
        mm=mlist[m]; base=np.array(mm['col'][:3])
        if len(I)>6000: I=I[::int(np.ceil(len(I)/6000))]
        A,B,C=P[I[:,0]],P[I[:,1]],P[I[:,2]]
        nrm=(N[I[:,0]]+N[I[:,1]]+N[I[:,2]]); nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)+1e-9
        lam=np.clip(nrm@LL,0,1)*0.55+0.55
        if mm['tex']>=0:
            T=tarr(mm['tex']); h,w=T.shape[:2]; uv=(UV[I[:,0]]+UV[I[:,1]]+UV[I[:,2]])/3
            px=np.clip((np.mod(uv[:,0],1)*w).astype(int),0,w-1); py=np.clip((np.mod(uv[:,1],1)*h).astype(int),0,h-1)
            tc=T[py,px]; col=tc[:,:3]*base; al=tc[:,3]
        else: col=np.tile(base,(len(I),1)); al=np.ones(len(I))
        col=np.clip(col*lam[:,None],0,1)
        pa=np.stack([A,B,C],1)@RR.T
        for k in range(len(I)):
            if mm['cut'] and al[k]<0.5: continue
            tris.append((pa[k,:,2].mean(),pa[k,:,:2],col[k]))
    if not tris: return None
    allv=np.concatenate([t[1] for t in tris]); lo=allv.min(0); hi=allv.max(0); sc=(PX*S*0.86)/max(hi-lo); off=(PX*S-(hi-lo)*sc)/2
    tris.sort(key=lambda t:t[0])
    img=Image.new('RGBA',(PX*S,PX*S),(0,0,0,0)); dr=ImageDraw.Draw(img)
    for z,v,c in tris:
        dr.polygon([((x-lo[0])*sc+off[0],PX*S-((y-lo[1])*sc+off[1])) for x,y in v],fill=tuple(int(x*255) for x in c)+(255,))
    return img.resize((PX,PX),Image.LANCZOS)

# ---------------------------------------------------------------- monta tudo
index=[]; sem_icone=[]; sem_nome=[]; ncor=0
for md in models:
    nc=write(md,OUT+'/m/%s.glb'%md['id'])
    if nc is None: continue
    ncor+= 1 if nc else 0
    w,d,h=md['size'][0],md['size'][2],md['size'][1]
    mi,sub=classify(md['id'])
    nm=name_pt(md['id'])
    if not nm: sem_nome.append(md['id']); nm=re.sub(r'(?<=[a-z])(?=[A-Z0-9])',' ',md['id'])
    ic=find_icon(md['id'])
    if ic:
        Image.open(ICONS+'/'+ic).convert('RGBA').resize((128,128),Image.LANCZOS).save(OUT+'/ic/%s.webp'%md['id'],'WEBP',quality=82,method=6)
    else:
        sem_icone.append(md['id']); im=thumb(md)
        if im: im.save(OUT+'/ic/%s.webp'%md['id'],'WEBP',quality=82,method=6)
    index.append(dict(id=md['id'],n=title(nm),c=mi,s=sub,w=max(1,int(np.ceil(w-0.1))),h=max(1,int(np.ceil(d-0.1))),a=round(h,2),sx=round(w,2),sz=round(d,2),k=1 if nc else 0))
# subcategorias por principal, em ordem de aparição
subs=[[] for _ in MAIN]
for m in index:
    if m['s'] not in subs[m['c']]: subs[m['c']].append(m['s'])
cats=[dict(n=n,i=ic,s=subs[k]) for k,(n,ic) in enumerate(MAIN)]
for n,ic in MAIN:
    Image.open(ICONS+'/'+ic+'.png').convert('RGBA').resize((96,96),Image.LANCZOS).save(OUT+'/cat/%s.png'%ic,optimize=True)
index.sort(key=lambda m:(m['c'],m['s'],m['n'].lower()))
json.dump(dict(cats=cats,m=index),open(OUT+'/mobilia.json','w'),ensure_ascii=False,separators=(',',':'),default=lambda o:o.item() if hasattr(o,'item') else str(o))
tot=sum(os.path.getsize(os.path.join(dp,f)) for dp,_,fs in os.walk(OUT) for f in fs)
print(len(index),'modelos; com cores:',ncor,'; total',tot//1024//1024,'MB')
print(collections.Counter(cats[m['c']]['n'] for m in index))
print('sem ícone do Hds:',len(sem_icone),sem_icone[:60]); print('sem nome oficial:',len(sem_nome),sem_nome[:60])
print('diversos:',[m['id'] for m in index if m['s']=='Diversos'][:40])
