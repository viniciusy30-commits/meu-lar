#!/usr/bin/env python3
"""Renderiza caminhada e corrida dos corpos Sims 4 masculino/feminino para comparar braços e mãos."""
import os, subprocess, sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cu=os.path.join(root,"app/src/main/assets/cute")
out=os.path.join(root,"animation-fit")
os.makedirs(out,exist_ok=True)
preview=os.path.join(root,"ferramentas/etapa53_preview.py")
for grp,label in (("am","masculino"),("af","feminino")):
    for clip,move in ((1,"andar"),(3,"correr")):
        target=os.path.join(out,f"{label}_{move}.png")
        subprocess.run([sys.executable,preview,cu,cu,grp,target,str(clip),"12","5"],check=True)
        print("RENDERED",target)
