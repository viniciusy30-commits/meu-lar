import sys; sys.path.insert(0,'/home/claude/w')
from common import *
import struct
HP='/home/claude/h/Aurum_HairstyleFMM_146_Lotus.package'
def tgi(d):
    off=struct.unpack_from('<I',d,4)[0]+8; n=d[off]
    return [struct.unpack_from('<QII',d,off+1+i*16) for i in range(n)]
