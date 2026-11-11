import numpy as np, json, math
from scipy.ndimage import gaussian_filter, map_coordinates, distance_transform_edt
rng=np.random.default_rng(7)
WX,WZ=3200.0,2400.0; G=8.0
NX,NZ=int(WX/G)+1,int(WZ/G)+1
xs=np.arange(NX)*G; zs=np.arange(NZ)*G
X,Z=np.meshgrid(xs,zs)
def gauss(cx,cz,r,h): return h*np.exp(-(((X-cx)**2+(Z-cz)**2)/(2*(r/2)**2)))
def smooth_noise(s,a):
    r=gaussian_filter(rng.standard_normal(X.shape),s/G,mode='reflect'); return a*r/r.std()

# ---------- relevo ----------
terr=16-6*(Z/WZ)+gauss(620,520,600,48)+gauss(2700,470,520,26)+gauss(1700,230,380,12)+gauss(260,1300,380,14)+gauss(2950,1500,420,18)
terr-=gauss(1500,1500,560,7)
terr+=smooth_noise(90,5)+smooth_noise(40,2)+smooth_noise(18,.7)
# costa irregular (sul e sudeste) + baía
coast=1950+260*np.sin(X/430+1.0)+150*np.sin(X/170+2.2)+gauss(1450,2400,500,-300)*0+ (X>2300)*( (X-2300)*-0.28)
coast-=gauss(1250,2300,420,420)      # baía funda
coast+=gauss(2500,2100,300,200)      # península
sea=Z>coast
terr=np.where(sea,np.minimum(terr,-3-(Z-coast)*0.02),terr)
# rio sinuoso do NE até a baía
def meander(p0,p1,amp,freq,n=160,ph=0):
    t=np.linspace(0,1,n); P=np.outer(1-t,p0)+np.outer(t,p1); v=np.array(p1)-np.array(p0); nv=np.array([-v[1],v[0]])/np.linalg.norm(v)
    off=amp*np.sin(t*freq*2*math.pi+ph)*np.sin(t*math.pi)**.6
    return P+np.outer(off,nv)
river=meander((2250,60),(1480,2260),150,2.4,ph=0.6)
Rd=np.full(X.shape,1e9)
for (a,b) in river[::2]:
    Rd=np.minimum(Rd,np.hypot(X-a,Z-b))
rw=np.interp(np.linspace(0,1,len(river)),[0,1],[22,50])  # largura crescendo
Rwid=np.full(X.shape,28.0)
riv_mask=Rd<26
terr=terr-18*np.exp(-(Rd/46)**2)       # vale
terr=np.where(riv_mask,np.minimum(terr,0.2),terr)
# lago
lake_c=(2250,1300);lake_r=150
Ld=np.hypot((X-lake_c[0])/1.3,(Z-lake_c[1]))
lake=Ld<lake_r
terr=np.where(lake,0.2,terr-6*np.exp(-(Ld/(lake_r*1.5))**2)*(~lake))
terr=np.clip(terr,0.5,None)
water=sea|riv_mask|lake
terr=np.where(water,np.minimum(terr,0.0),terr)
water_d=distance_transform_edt(~water)*G

def terr_at(px,pz): return float(map_coordinates(terr,[[pz/G],[px/G]],order=1,mode='nearest')[0])
def is_water(px,pz,margin=0):
    if not(0<=px<=WX and 0<=pz<=WZ): return True
    ix=int(px/G);iz=int(pz/G);return water_d[min(iz,NZ-1),min(ix,NX-1)]<=margin
def slope_at(px,pz):
    ix=int(np.clip(px/G,1,NX-2));iz=int(np.clip(pz/G,1,NZ-2))
    gx=(terr[iz,ix+1]-terr[iz,ix-1])/(2*G);gz=(terr[iz+1,ix]-terr[iz-1,ix])/(2*G);return math.hypot(gx,gz)


