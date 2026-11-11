import sys,os,re
sys.path.insert(0,'/home/claude/tools')
import scene,sf
os.chdir('/home/claude/hds/Hds/assets/bin/Data')
for n in sorted(os.listdir('.')):
    if len(n)!=32: continue
    try: d=scene.load(n)
    except Exception: continue
    for pid,off,sz,ti,cid in d['objs']:
        if cid==49 and sz==984788:
            r=sf.R(d['data'],off); r.str(); l=r.u32(); txt=d['data'][r.p:r.p+l].decode('utf8','replace')
            open('/home/claude/out/localization.txt','w').write(txt); print(n,l); print(txt[:1500])