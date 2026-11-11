import sys,os,struct,re,json
sys.path.insert(0,'/home/claude/tools')
import scene,sf,um,export
from PIL import Image
D='/home/claude/hds/Hds/assets/bin/Data'; os.chdir(D)
OUT='/home/claude/out/icons'; os.makedirs(OUT,exist_ok=True)
want=re.compile(r'(_icon$|^shop_cat_|^build_cat_|^action_|^bg_(furniture|shop|price|selection|rectangle|round|frame)|^selection_frame|^slot_selection|^label_(price|money|coins)|^t_(shop|furniture)|^ActionRotate|^button_|^btn_|^close|^checkmark|^cross|^furniture_|^furnish)')
AT={}; TX={}
def atlas(f,fid,pid):
    k=(f['name'] if 'name' in f else id(f),fid,pid)
    ff,p=export.ref(f,fid,pid)
    key=(id(ff),p)
    if key in AT: return AT[key]
    off,sz,cid=export.obj(ff,p)
    r=sf.R(ff['data'],off); r.str()
    cnt=r.i32()
    for _ in range(cnt): r.i32(); r.i64()
    cnt=r.i32()
    for _ in range(cnt): r.str()
    cnt=r.i32(); rd={}
    for k in range(cnt):
        g=tuple(r.u32() for _ in range(4)); sec=r.i64()
        tf=r.i32(); tp=r.i64(); af=r.i32(); ap=r.i64()
        rect=[r.f32() for _ in range(4)]; r.raw(16); r.raw(16); r.f32(); r.u32(); ns=r.i32()
        rd[(g,sec)]=(tf,tp,rect)
    AT[key]=(ff,rd); return AT[key]
def tex(ff,tp):
    k=(id(ff),tp)
    if k not in TX:
        t=export.get_tex(ff,(0,tp)); TX[k]=t[1] if t else None
    return TX[k]
done={}; fail=0
for n in sorted(os.listdir('.')):
    if len(n)!=32: continue
    try: f=export.F(n)
    except Exception: continue
    for pid,off,sz,ti,cid in f['objs']:
        if cid!=213: continue
        try:
            r=sf.R(f['data'],off); name=r.str()
            if not want.search(name) or name in done: continue
            r.raw(16+8+16+4+8); r.u32(); r.u8(); r.align()
            g=tuple(r.u32() for _ in range(4)); sec=r.i64()
            nt=r.i32()
            for _ in range(nt): r.str()
            fid=r.i32(); apid=r.i64()
            if apid==0: continue
            ff,rd=atlas(f,fid,apid)
            tf,tp,rect=rd[(g,sec)]
            im=tex(ff,tp)
            x,y,w,h=[int(round(v)) for v in rect]
            H=im.size[1]
            c=im.crop((x,H-y-h,x+w,H-y))
            c.save(OUT+'/'+name+'.png'); done[name]=1
        except Exception as e:
            fail+=1
print('ok',len(done),'fail',fail)
