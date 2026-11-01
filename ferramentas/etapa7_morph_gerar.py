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
    ('Orelha élfica',['BS_FaceShape_Ears_Elf']),
    # Etapa 8 (dinâmicos, canais 13..17): piscar e expressões
    ('Piscar',['BS_Eyes_UpperClosed_R','BS_Eyes_UpperClosed_L','BS_Eyes_LowerClosed_R','BS_Eyes_LowerClosed_L']),
    ('Feliz',['BS_Mouth_Happy_R','BS_Mouth_Happy_L',('BS_Eyes_LowerClosed_R',.35),('BS_Eyes_LowerClosed_L',.35),('BS_Brows_Raised_R',.25),('BS_Brows_Raised_L',.25)]),
    ('Triste',['BS_Mouth_Sad_R','BS_Mouth_Sad_L','BS_Brows_Sad_R','BS_Brows_Sad_L']),
    ('Brava',['BS_Brow_Angry_R','BS_Brow_Angry_L','BS_Mouth_Press_R','BS_Mouth_Press_L',('BS_Brows_Lowered_R',.5),('BS_Brows_Lowered_L',.5)]),
    ('Surpresa',['BS_Brows_Raised_R','BS_Brows_Raised_L','BS_Mouth_Oh_R','BS_Mouth_Oh_L',('BS_Jaw_Open',.35),'BS_Eyes_UpperOpen_R','BS_Eyes_UpperOpen_L'])]
out=bytearray(b'CMF1'+struct.pack('<i',len(CH)))
tot=0
for nm,shs in CH:
    acc={}
    for s in shs:
        w=1.0
        if isinstance(s,tuple): s,w=s
        ix,dv=shapes[s]
        for i,d in zip(ix,dv):
            for bv in hmap[int(i)]:
                acc[bv]=acc.get(bv,np.zeros(3))+d*w
    # vértices coincidentes: mesma posição => mesmo delta (evita rachadura); remove deltas nulos
    items=sorted((k,v) for k,v in acc.items() if np.abs(v).max()>1e-6)
    out+=struct.pack('<i',len(items))
    for k,v in items: out+=struct.pack('<i3f',k,*v)
    tot+=len(items); print('%-30s %5d'%(nm,len(items)))
d='r/'+os.listdir('r')[0]+'/app/src/main/assets/cute/morph.bin'
open(d,'wb').write(out); print(len(out),'bytes ->',d)
