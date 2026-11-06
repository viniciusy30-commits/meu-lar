from common import *
from scipy.spatial import cKDTree
import struct
def _fnv(s):
    h=0x811C9DC5
    for c in s.lower().encode(): h=(h*0x01000193)&0xffffffff; h^=c
    return h
NAMES=['b__ROOT__','b__ROOT_bind__','b__Pelvis__','b__Spine0__','b__Spine1__','b__Spine2__','b__Neck__','b__Head__','b__CAS_L_Breast__','b__CAS_R_Breast__']
for _s in 'LR':
    NAMES+=['b__%s_%s__'%(_s,x) for x in ['Clavicle','UpperArm','ShoulderTwist','Elbow','ForeArmTwist','Forearm','Hand','Thigh','ThighTwist','Calf','Foot','Toe','Index0','Index1','Index2','Mid0','Mid1','Mid2','Ring0','Ring1','Ring2','Pinky0','Pinky1','Pinky2','Thumb0','Thumb1','Thumb2']]
HN={_fnv(n):n for n in NAMES}
APP={'b__Pelvis__':0,'b__Spine0__':3,'b__Spine1__':4,'b__Spine2__':5,'b__Neck__':6,'b__Head__':8,'b__CAS_L_Breast__':4,'b__CAS_R_Breast__':4,'b__ROOT_bind__':0,'b__ROOT__':0}
for _s,_o,_f in (('L',0,25),('R',4,40)):
    APP.update({'b__%s_Clavicle__'%_s:9+_o,'b__%s_UpperArm__'%_s:10+_o,'b__%s_ShoulderTwist__'%_s:10+_o,'b__%s_Elbow__'%_s:11+_o,
                'b__%s_ForeArmTwist__'%_s:11+_o,'b__%s_Forearm__'%_s:11+_o,'b__%s_Hand__'%_s:12+_o})
    _l=17 if _s=='L' else 21
    APP.update({'b__%s_Thigh__'%_s:_l,'b__%s_ThighTwist__'%_s:_l,'b__%s_Calf__'%_s:_l+1,'b__%s_Foot__'%_s:_l+2,'b__%s_Toe__'%_s:_l+3})
    for _k,_fn in enumerate(['Index','Mid','Ring','Pinky','Thumb']):
        for _j in range(3): APP['b__%s_%s%d__'%(_s,_fn,_j)]=_f+_k*3+_j
def geom_bones(b):
    i=b.find(b'GEOM'); v,tgo=struct.unpack_from('<2I',b,i+4); end=i+12+tgo
    for nb in range(1,300):
        p=end-4*nb-4
        if struct.unpack_from('<I',b,p)[0]==nb: return [HN.get(h,'?%08X'%h) for h in struct.unpack_from('<%dI'%nb,b,p+4)]
