"""Etapa 17 - troca SÓ o clipe de CORRER (índice 3) pela animação Running.fbx (Mixamo). Andar, parado, pulo e clipes 4-6 ficam idênticos.

Uso:  python3 etapa17_corrida.py <base.bin entrada> <Running.fbx> <base.bin saída>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from etapa11_retarget import Retarget, RUN
from etapa11_base import write_base

def main():
    base_in, run_fbx, base_out = sys.argv[1:4]
    rt = Retarget(base_in)
    Tr, cr, ir = rt.clip_from(run_fbx, 'run')
    lf = ir.pop('low_frames')
    print(ir)
    print('   pé mais baixo por quadro (cm): min %.2f  mediana %.2f  máx %.2f' % (lf.min() * 100, np.median(lf) * 100, lf.max() * 100))
    clips = [(l, d.copy()) for l, d in rt.base['clips']]
    clips[RUN] = (Tr, cr)
    if len(clips) > 6: clips[6] = (Tr, cr.copy())   # clipe de corrida masculino da etapa 14 (hoje sem uso, MALE_CLIPS=false): também sai o antigo
    write_base(base_out, rt.base, clips)
    print('gravado', base_out, [(round(l, 3), d.shape[0]) for l, d in clips])
    np.save('/home/claude/work/run_new.npy', cr)

if __name__ == '__main__':
    main()
