#!/usr/bin/env python3
"""Renderiza caminhada e corrida dos corpos Sims 4 masculino/feminino para comparar braços e mãos."""
import os, shutil, subprocess, sys, tempfile
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cu=os.path.join(root,"app/src/main/assets/cute")
out=os.path.join(root,"animation-fit")
os.makedirs(out,exist_ok=True)
preview=os.path.join(root,"ferramentas/etapa53_preview.py")
with tempfile.TemporaryDirectory() as clipdir:
    for grp,label in (("am","masculino"),("af","feminino")):
        shutil.copyfile(os.path.join(cu,f"clips_{grp}5.bin"),os.path.join(clipdir,f"clips_{grp}.bin"))
        for clip,move in ((1,"andar"),(3,"correr")):
            target=os.path.join(out,f"{label}_{move}.png")
            args=[sys.executable,preview,cu,clipdir,grp,target,str(clip),"12","5"]
            if grp == "am": args.append("male_adjusted")
            subprocess.run(args,check=True)
            print("RENDERED",target)
