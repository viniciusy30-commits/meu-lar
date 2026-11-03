import numpy as np, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
FB='/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
FS='/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'
rng=np.random.default_rng(3)

def face(d,cx,cy,r,kind,rot=0.0):
    """rosto/máscara estilizado (original), traço branco sobre preto."""
    W=(236,236,230,255)
    # cabeça
    d.ellipse((cx-r*0.78,cy-r,cx+r*0.78,cy+r),outline=W,width=max(2,int(r*0.07)))
    # hachuras de sombra
    for k in range(7):
        x=cx-r*0.7+k*r*0.1
        d.line((x,cy+r*0.15,x+r*0.12,cy+r*0.85),fill=W,width=1)
    # olhos
    ey=cy-r*0.18
    for s in (-1,1):
        ex=cx+s*r*0.33
        if kind%3==0:   # olhos vazados
            d.ellipse((ex-r*0.17,ey-r*0.12,ex+r*0.17,ey+r*0.16),fill=W)
            d.ellipse((ex-r*0.07,ey-r*0.03,ex+r*0.07,ey+r*0.09),fill=(10,10,10,255))
        elif kind%3==1: # óculos escuros
            d.rounded_rectangle((ex-r*0.22,ey-r*0.1,ex+r*0.22,ey+r*0.14),radius=int(r*0.07),fill=W)
        else:           # X nos olhos
            d.line((ex-r*0.15,ey-r*0.12,ex+r*0.15,ey+r*0.14),fill=W,width=max(2,int(r*0.06)))
            d.line((ex-r*0.15,ey+r*0.14,ex+r*0.15,ey-r*0.12),fill=W,width=max(2,int(r*0.06)))
    # nariz
    d.line((cx,cy-r*0.05,cx-r*0.07,cy+r*0.22,cx+r*0.05,cy+r*0.25),fill=W,width=max(2,int(r*0.05)))
    # boca
    if kind%2==0:
        d.arc((cx-r*0.4,cy+r*0.28,cx+r*0.4,cy+r*0.7),10,170,fill=W,width=max(2,int(r*0.07)))
        for k in range(-3,4): d.line((cx+k*r*0.1,cy+r*0.45,cx+k*r*0.1,cy+r*0.55),fill=W,width=2)
    else:
        d.line((cx-r*0.35,cy+r*0.5,cx+r*0.35,cy+r*0.5),fill=W,width=max(3,int(r*0.07)))
    # cabelo / capuz / coroa
    if kind==0:
        for k in range(14):
            a=math.pi*(1.05+0.9*k/13); d.line((cx+math.cos(a)*r*0.7,cy+math.sin(a)*r*0.9,cx+math.cos(a)*r*1.18+rng.integers(-6,6),cy+math.sin(a)*r*1.35),fill=W,width=3)
    elif kind==1:
        d.polygon([(cx-r*0.8,cy-r*0.6),(cx-r*0.55,cy-r*1.35),(cx-r*0.2,cy-r*0.9),(cx,cy-r*1.45),(cx+r*0.2,cy-r*0.9),(cx+r*0.55,cy-r*1.35),(cx+r*0.8,cy-r*0.6)],outline=W)
    elif kind==2:
        d.arc((cx-r*1.0,cy-r*1.3,cx+r*1.0,cy+r*0.9),190,350,fill=W,width=int(r*0.1))
    elif kind==3:
        for k in range(10): d.line((cx-r*0.7+k*r*0.155,cy-r*0.9,cx-r*0.8+k*r*0.18,cy-r*1.35),fill=W,width=3)
    elif kind==4:
        d.ellipse((cx-r*0.95,cy-r*1.2,cx+r*0.95,cy-r*0.55),outline=W,width=int(r*0.08))

def make_chaos(size=1024):
    S=size
    im=Image.new('RGBA',(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
    W=(238,238,232,255)
    # linhas pequenas de texto no topo
    f=ImageFont.truetype(FB,int(S*0.034))
    t="ANARCHY  ·  NOISE  ·  DISORDER  ·  NO RULES"
    tw=d.textlength(t,font=f); d.text(((S-tw)/2,S*0.02),t,font=f,fill=W)
    # CHAOS grande
    fs=int(S*0.30); f2=ImageFont.truetype(FB,fs)
    tmp=Image.new('RGBA',(S*2,int(fs*1.4)),(0,0,0,0)); td=ImageDraw.Draw(tmp)
    letters="CHAOS"; x=20
    for i,ch in enumerate(letters):
        lw=td.textlength(ch,font=f2)
        lt=Image.new('RGBA',(int(lw)+60,int(fs*1.4)),(0,0,0,0)); ld=ImageDraw.Draw(lt)
        ld.text((30,0),ch,font=f2,fill=W)
        lt=lt.rotate(rng.uniform(-5,5),resample=Image.BICUBIC,center=(lt.width/2,lt.height/2))
        tmp.alpha_composite(lt,(int(x),int(rng.integers(-8,10)))); x+=lw*0.82
    bbox=tmp.getbbox(); tmp=tmp.crop(bbox); sc=(S*0.96)/tmp.width
    tmp=tmp.resize((int(tmp.width*sc),int(tmp.height*sc*0.82)),Image.LANCZOS)
    # contorno preto fino interno para dar volume
    mask=tmp.split()[3]; edge=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask)
    y_text=int(S*0.075); im.alpha_composite(tmp,((S-tmp.width)//2,y_text))
    # coleção de rostos
    base_y=y_text+tmp.height+int(S*0.02); band=int(S*0.52)
    cols=[(0.12,0.62,0.13),(0.30,0.42,0.12),(0.46,0.62,0.14),(0.62,0.40,0.11),(0.78,0.60,0.13),(0.90,0.42,0.10)]
    fx=ImageDraw.Draw(im)
    for k,(u,v,r) in enumerate(cols):
        face(fx,int(S*u),int(base_y+band*v),int(S*r*0.85),k)
    # texto pequeno inferior
    f3=ImageFont.truetype(FB,int(S*0.03)); t2="FEEL THE STATIC  —  BREAK THE SILENCE  —  EST. 2024"
    tw=fx.textlength(t2,font=f3); fx.text(((S-tw)/2,base_y+band+S*0.03),t2,font=f3,fill=W)
    # respingos
    for _ in range(90):
        x=rng.uniform(0,S); y=rng.uniform(0,S); r=rng.uniform(1,3.6); 
        if im.getpixel((int(x),int(y)))[3]==0 and rng.random()<0.35: fx.ellipse((x-r,y-r,x+r,y+r),fill=W)
    return im
if __name__=='__main__':
    im=make_chaos(1024); bg=Image.new('RGB',im.size,(14,14,16)); bg.paste(im,(0,0),im); bg.save('/tmp/chaos.png'); im.save('/home/claude/work/skate/chaos_art.png')
