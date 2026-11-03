def refpack(src):
    flags=src[0]; assert src[1]==0xFB, hex(src[1])
    p=2
    if flags&0x80: ln=int.from_bytes(src[p:p+4],'big'); p+=4
    else: ln=int.from_bytes(src[p:p+3],'big'); p+=3
    out=bytearray(); n=len(src)
    while p<n:
        c0=src[p]; p+=1
        if c0<0x80:
            c1=src[p]; p+=1; nl=c0&3
            out+=src[p:p+nl]; p+=nl
            ref=len(out)-1-(((c0&0x60)<<3)+c1); cnt=((c0&0x1C)>>2)+3
            for _ in range(cnt): out.append(out[ref]); ref+=1
        elif c0<0xC0:
            c1=src[p]; c2=src[p+1]; p+=2; nl=(c1>>6)&3
            out+=src[p:p+nl]; p+=nl
            ref=len(out)-1-(((c1&0x3F)<<8)+c2); cnt=(c0&0x3F)+4
            for _ in range(cnt): out.append(out[ref]); ref+=1
        elif c0<0xE0:
            c1=src[p]; c2=src[p+1]; c3=src[p+2]; p+=3; nl=c0&3
            out+=src[p:p+nl]; p+=nl
            ref=len(out)-1-(((c0&0x10)<<12)+(c1<<8)+c2); cnt=((c0&0x0C)<<6)+c3+5
            for _ in range(cnt): out.append(out[ref]); ref+=1
        elif c0<0xFC:
            nl=((c0&0x1F)<<2)+4
            out+=src[p:p+nl]; p+=nl
        else:
            nl=c0&3
            out+=src[p:p+nl]; p+=nl
            break
    return bytes(out), ln
