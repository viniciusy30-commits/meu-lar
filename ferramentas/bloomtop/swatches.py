from common import *
import struct
r=dbpf.read(PK)
casp=[e for e in r if e['t']==0x034AEECB]
T={e['inst']&0xffffff:e for e in r if e['t']==0x3453CF95}
def tgi(d):
    off=struct.unpack_from('<I',d,4)[0]+8; n=d[off]
    return [struct.unpack_from('<QII',d,off+1+i*16) for i in range(n)]
order=[]
for e in casp:
    d=dbpf.data(e); t=tgi(d); k=t[5][0]&0xffffff
    order.append((e['inst']&0xffffffff,k))
import json; json.dump(order,open('order.json','w'))
# crop do torso (lado esquerdo da textura, metade de baixo) para amostra
tiles=[]
for i,(ci,k) in enumerate(order):
    im=rle2.rle2_mip0(dbpf.data(T[k])); W,H=im.size
    c=im.crop((0,H//2,int(W*0.5),H//2+int(H*0.25))).convert('RGBA')
    bg=Image.new('RGBA',c.size,(120,120,120,255)); bg.alpha_composite(c)
    tiles.append(bg.convert('RGB').resize((150,int(150*c.height/c.width))))
    print(i,hex(k),im.size,flush=True)
cols=8; rows=(len(tiles)+cols-1)//cols; h=tiles[0].height
sh=Image.new('RGB',(cols*150,rows*h),(0,0,0))
for i,t in enumerate(tiles): sh.paste(t,((i%cols)*150,(i//cols)*h))
sh.save('swatches.png'); print(sh.size)
