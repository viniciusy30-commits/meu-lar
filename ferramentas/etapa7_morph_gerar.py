import pickle,struct,numpy as np,os
hmap,shapes,HV=pickle.load(open('morph.pkl','rb'))
# canais do criador (ordem fixa = ordem em CuteChar.FACE_NAMES)
CH=[('Masculinidade',['BS_Gender_Face','BS_Gender_Neck']),
    ('Cílios',['BS_LashLength']),
    ('Sobrancelha grossa',['BSMC_Brows_Thickness']),
    ('Ponte do nariz',['BS_FaceShape_Nose_BridgeCurve']),
    ('Nariz largo',['BS_FaceShape_Nose_Width']),
    ('Nariz para baixo',['BS_FaceShape_Nose_TiltDown']),
    ('Nariz para cima',['BS_FaceShape_Nose_TiltUp']),
    ('Boca larga',['BSMC_FaceShape_Mouth_Wide']),
    ('Boca fina',['BSMC_FaceShape_Mouth_Thin']),
    ('Cantos dos olhos para baixo',['BS_FaceShape_Eyes_OuterCornersLow']),
    ('Cantos dos olhos para cima',['BS_FaceShape_Eyes_OuterCornersHigh']),
    ('Olhos quadrados',['BS_FaceShape_Eyes_Square']),
    ('Orelha élfica',['BS_FaceShape_Ears_Elf'])]
out=bytearray(b'CMF1'+struct.pack('<i',len(CH)))
tot=0
for nm,shs in CH:
    acc={}
    for s in shs:
        ix,dv=shapes[s]
        for i,d in zip(ix,dv):
            for bv in hmap[int(i)]:
                acc[bv]=acc.get(bv,np.zeros(3))+d
    # vértices coincidentes: mesma posição => mesmo delta (evita rachadura); remove deltas nulos
    items=sorted((k,v) for k,v in acc.items() if np.abs(v).max()>1e-6)
    out+=struct.pack('<i',len(items))
    for k,v in items: out+=struct.pack('<i3f',k,*v)
    tot+=len(items); print('%-30s %5d'%(nm,len(items)))
d='r/'+os.listdir('r')[0]+'/app/src/main/assets/cute/morph.bin'
open(d,'wb').write(out); print(len(out),'bytes ->',d)
