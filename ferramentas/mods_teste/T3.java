import com.vinicius.meular.mods.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Conversor OFFLINE dos três CCs Minimalist. Não altera o importador do jogo. */
public final class T3 {
  static BodyRef body(Path p) throws Exception {
    ByteBuffer b=ByteBuffer.wrap(Files.readAllBytes(p)).order(ByteOrder.LITTLE_ENDIAN);
    if(b.getInt()!=0x31505543) throw new Exception("Corpo CUP1 inválido: "+p);
    int nv=b.getInt(), ni=b.getInt(); b.getInt();
    float[] pos=new float[nv*3], nor=new float[nv*3], bw=new float[nv*4];
    int[] bi=new int[nv*4];
    for(int v=0;v<nv;v++){
      for(int k=0;k<3;k++)pos[v*3+k]=b.getFloat();
      for(int k=0;k<3;k++)nor[v*3+k]=b.getFloat();
      b.getFloat(); b.getFloat(); b.position(b.position()+4);
      for(int k=0;k<4;k++)bi[v*4+k]=b.get()&255;
      for(int k=0;k<4;k++)bw[v*4+k]=(b.get()&255)/255f;
    }
    int[] idx=new int[ni]; for(int i=0;i<ni;i++)idx[i]=b.getShort()&65535;
    return new BodyRef(pos,nor,bi,bw,idx,null,96.8f/0.9861f);
  }

  static boolean refs(byte[] casp,Pkg.Ent e){
    int[] v={e.i1,e.i2,e.group,e.type};
    for(int p=0;p<=casp.length-16;p++){
      boolean ok=true;
      for(int k=0;k<4;k++){
        int q=p+k*4,x=v[k];
        if((casp[q]&255)!=(x&255)||(casp[q+1]&255)!=((x>>>8)&255)||(casp[q+2]&255)!=((x>>>16)&255)||(casp[q+3]&255)!=((x>>>24)&255)){ok=false;break;}
      }
      if(ok)return true;
    }
    return false;
  }
  static void dumpTextureCandidates(Pkg pkg, String id) throws Exception {
    java.util.List<Pkg.Ent> casps=pkg.ofType(0x034AEECB);
    if(casps.isEmpty()) return;
    byte[] casp=pkg.read(casps.get(0));
    Path dir=Paths.get("fit-minimalist","texture_candidates",id);
    Files.createDirectories(dir);
    int n=0;
    for(Pkg.Ent e:pkg.ofType(Tex.T_RLE2)) if(refs(casp,e)) {
      try { Img im=Tex.rle2(pkg.read(e)); Files.write(dir.resolve(String.format(java.util.Locale.ROOT,"%02d_rle2_%dx%d.png",n++,im.w,im.h)),im.png()); }
      catch(Exception ex) { System.out.println("TEXTURE_CANDIDATE_SKIP "+id+" RLE2 "+ex.getMessage()); }
    }
    for(Pkg.Ent e:pkg.ofType(Tex.T_IMG)) if(refs(casp,e)) {
      try { Img im=Tex.dds(pkg.read(e)); Files.write(dir.resolve(String.format(java.util.Locale.ROOT,"%02d_img_%dx%d.png",n++,im.w,im.h)),im.png()); }
      catch(Exception ex) { System.out.println("TEXTURE_CANDIDATE_SKIP "+id+" IMG "+ex.getMessage()); }
    }
    System.out.println("TEXTURE_CANDIDATES "+id+" count="+n);
  }

  static Img rawTexture(Pkg pkg) throws Exception {
    java.util.List<Pkg.Ent> casps=pkg.ofType(0x034AEECB);
    if(casps.isEmpty())throw new Exception("CASP ausente");
    byte[] casp=pkg.read(casps.get(0));
    java.util.List<Pkg.Ent> refs=new java.util.ArrayList<>();
    for(Pkg.Ent e:pkg.ofType(Tex.T_RLE2))if(refs(casp,e))refs.add(e);
    for(Pkg.Ent e:pkg.ofType(Tex.T_IMG))if(refs(casp,e))refs.add(e);
    Exception last=null;
    for(Pkg.Ent e:refs)try{return e.type==Tex.T_RLE2?Tex.rle2(pkg.read(e)):Tex.dds(pkg.read(e));}catch(Exception ex){last=ex;}
    if(last!=null)throw last;
    throw new Exception("Textura base referenciada não encontrada");
  }

  static byte[] trimByAlpha(byte[] cup,Img tex) throws Exception {
    ByteBuffer b=ByteBuffer.wrap(cup).order(ByteOrder.LITTLE_ENDIAN);
    if(b.get()!='C'||b.get()!='U'||b.get()!='P'||b.get()!='1')throw new Exception("CUP1 inválido para recorte alpha");
    int nv=b.getInt(),ni=b.getInt();b.getInt();
    int vertexEnd=16+nv*44;
    if(vertexEnd+(long)ni*2>cup.length)throw new Exception("CUP1 truncado");
    float[] uv=new float[nv*2];
    for(int v=0;v<nv;v++){int q=16+v*44+24;uv[v*2]=b.getFloat(q);uv[v*2+1]=b.getFloat(q+4);}
    int[] kept=new int[ni];int count=0;
    for(int q=0;q<ni;q+=3){
      int a=b.getShort(vertexEnd+q*2)&65535,bb=b.getShort(vertexEnd+(q+1)*2)&65535,cc=b.getShort(vertexEnd+(q+2)*2)&65535;
      int[][] samples={{a,bb,cc},{a,bb,cc},{a,bb,cc},{a,bb,cc}};
      float[][] coords={{(uv[a*2]+uv[bb*2]+uv[cc*2])/3f,(uv[a*2+1]+uv[bb*2+1]+uv[cc*2+1])/3f},
        {uv[a*2],uv[a*2+1]},{uv[bb*2],uv[bb*2+1]},{uv[cc*2],uv[cc*2+1]}};
      int opaque=0,total=0;
      for(float[] xy:coords){
        int x=Math.max(0,Math.min(tex.w-1,(int)(xy[0]*tex.w)));
        int y=Math.max(0,Math.min(tex.h-1,(int)(xy[1]*tex.h)));
        if((tex.argb[y*tex.w+x]>>>24)>=128)opaque++;
        total++;
      }
      if(opaque==4){kept[count++]=a;kept[count++]=bb;kept[count++]=cc;}
    }
    if(count<Math.max(30,ni/20))throw new Exception("Recorte alpha removeu quase toda a roupa: "+count/3+"/"+ni/3+" triângulos");
    ByteBuffer out=ByteBuffer.allocate(vertexEnd+count*2).order(ByteOrder.LITTLE_ENDIAN);
    out.put(cup,0,vertexEnd);out.putInt(8,count);
    for(int i=0;i<count;i++)out.putShort((short)kept[i]);
    System.out.println("ALPHA_TRIM triangles="+ni/3+" -> "+count/3);
    return out.array();
  }
  /** Ajusta a roupa pela superfície real do corpo, sem deslocar vértices por normais isoladas. */
  static void closest(float px,float py,float pz,
                      float ax,float ay,float az,float bx,float by,float bz,float cx,float cy,float cz,
                      float[] q) {
    float abx=bx-ax,aby=by-ay,abz=bz-az,acx=cx-ax,acy=cy-ay,acz=cz-az;
    float apx=px-ax,apy=py-ay,apz=pz-az;
    float d1=abx*apx+aby*apy+abz*apz,d2=acx*apx+acy*apy+acz*apz;
    float u,v,w;
    if(d1<=0&&d2<=0){u=1;v=0;w=0;}
    else {
      float bpx=px-bx,bpy=py-by,bpz=pz-bz;
      float d3=abx*bpx+aby*bpy+abz*bpz,d4=acx*bpx+acy*bpy+acz*bpz;
      if(d3>=0&&d4<=d3){u=0;v=1;w=0;}
      else {
        float vc=d1*d4-d3*d2;
        if(vc<=0&&d1>=0&&d3<=0){float t=d1/(d1-d3);u=1-t;v=t;w=0;}
        else {
          float cpx=px-cx,cpy=py-cy,cpz=pz-cz;
          float d5=abx*cpx+aby*cpy+abz*cpz,d6=acx*cpx+acy*cpy+acz*cpz;
          if(d6>=0&&d5<=d6){u=0;v=0;w=1;}
          else {
            float vb=d5*d2-d1*d6;
            if(vb<=0&&d2>=0&&d6<=0){float t=d2/(d2-d6);u=1-t;v=0;w=t;}
            else {
              float va=d3*d6-d5*d4;
              if(va<=0&&(d4-d3)>=0&&(d5-d6)>=0){float t=(d4-d3)/((d4-d3)+(d5-d6));u=0;v=1-t;w=t;}
              else {float inv=1f/(va+vb+vc);v=vb*inv;w=vc*inv;u=1-v-w;}
            }
          }
        }
      }
    }
    q[0]=u*ax+v*bx+w*cx;q[1]=u*ay+v*by+w*cy;q[2]=u*az+v*bz+w*cz;q[3]=u;q[4]=v;q[5]=w;
  }

  /** Mantém folga pequena e uniforme entre pele e tecido. Não escala nem deforma a peça. */
  static byte[] improveFit(byte[] cup, BodyRef body, boolean jeans) throws Exception {
    ByteBuffer b=ByteBuffer.wrap(cup).order(ByteOrder.LITTLE_ENDIAN);
    if(b.getInt()!=0x31505543) throw new Exception("CUP1 inválido no ajuste de caimento");
    int nv=b.getInt(),ni=b.getInt();b.getInt();
    int vertexEnd=16+nv*44;
    if(vertexEnd+(long)ni*2!=cup.length) throw new Exception("CUP1 inválido no ajuste de caimento");
    float[] bp=body.pos,bn=body.nor,q=new float[6];
    int[] bi=body.idx;
    @SuppressWarnings("unchecked") java.util.ArrayList<Integer>[] incident=new java.util.ArrayList[bp.length/3];
    for(int v=0;v<incident.length;v++) incident[v]=new java.util.ArrayList<>();
    for(int t=0;t<bi.length/3;t++) for(int k=0;k<3;k++) incident[bi[t*3+k]].add(t);
    float target=jeans?0.75f:1.0f;
    int moved=0,skipped=0;float maxMove=0f;
    for(int v=0;v<nv;v++){
      int o=16+v*44;
      float x=b.getFloat(o),y=b.getFloat(o+4),z=b.getFloat(o+8);
      int nearest=-1;float best=Float.MAX_VALUE;
      for(int j=0;j<bp.length/3;j++){
        if(Math.abs(x)>2.5f&&Math.abs(bp[j*3])>1f&&(x>0)!=(bp[j*3]>0))continue;
        float dx=x-bp[j*3],dy=y-bp[j*3+1],dz=z-bp[j*3+2],d=dx*dx+dy*dy+dz*dz;
        if(d<best){best=d;nearest=j;}
      }
      if(nearest<0||best>36f){skipped++;continue;}
      float bestD=Float.MAX_VALUE,bx=0,by=0,bz=0,nx=0,ny=0,nz=0;
      for(int t:incident[nearest]){
        int ia=bi[t*3],ib=bi[t*3+1],ic=bi[t*3+2];
        int a=ia*3,bb=ib*3,c=ic*3;
        closest(x,y,z,bp[a],bp[a+1],bp[a+2],bp[bb],bp[bb+1],bp[bb+2],bp[c],bp[c+1],bp[c+2],q);
        float dx=x-q[0],dy=y-q[1],dz=z-q[2],d=dx*dx+dy*dy+dz*dz;
        if(d>=bestD)continue;
        float tx=bn[a]*q[3]+bn[bb]*q[4]+bn[c]*q[5];
        float ty=bn[a+1]*q[3]+bn[bb+1]*q[4]+bn[c+1]*q[5];
        float tz=bn[a+2]*q[3]+bn[bb+2]*q[4]+bn[c+2]*q[5];
        float nl=(float)Math.sqrt(tx*tx+ty*ty+tz*tz);
        if(nl<1e-7f)continue;
        nx=tx/nl;ny=ty/nl;nz=tz/nl;bestD=d;bx=q[0];by=q[1];bz=q[2];
      }
      if(bestD>16f){skipped++;continue;}
      float signed=(x-bx)*nx+(y-by)*ny+(z-bz)*nz;
      float delta=target-signed;
      if(delta<=0.05f)continue;
      if(delta>2.5f){skipped++;continue;}
      b.putFloat(o,x+nx*delta);b.putFloat(o+4,y+ny*delta);b.putFloat(o+8,z+nz*delta);
      moved++;if(delta>maxMove)maxMove=delta;
    }
    System.out.println("FIT_SURFACE target="+target+"cm moved="+moved+" skipped="+skipped+" maxMove="+maxMove+"cm; proportions and UV preserved");
    return cup;
  }

  public static void main(String[] a) throws Exception {
    if(a.length!=3) throw new Exception("Uso: T3 top.package short.package jeans.package");
    Path root=Paths.get(".").toAbsolutePath();
    BodyRef male=body(root.resolve("app/src/main/assets/cute/p_body_am5.bin"));
    String[] ids={"minimalist_top_am5","minimalist_short_am5","minimalist_jeans_am5"};
    String[] slots={"top","bottom","bottom"};
    String[] names={"Camiseta Minimalist","Short Minimalist","Calça jeans Minimalist"};
    Path out=root.resolve("app/src/main/assets/cute/skate"); Files.createDirectories(out);
    for(int i=0;i<3;i++){
      Path src=root.resolve(a[i]);
      if(!Files.isRegularFile(src)) throw new Exception("Pacote ausente: "+src);
      byte[] packageBytes=Files.readAllBytes(src);
      Importer.Out converted=Importer.convert(packageBytes,src.getFileName().toString(),male);
      if(converted.pieces.size()!=1) throw new Exception(names[i]+": esperado 1 modelo LOD0, recebidos "+converted.pieces.size()+"; "+converted.notes);
      Importer.PieceOut piece=converted.pieces.get(0);
      if(!slots[i].equals(piece.slot)) throw new Exception(names[i]+": slot calculado "+piece.slot+"; esperado "+slots[i]+". Conversão cancelada para não cadastrar no lugar errado.");
      if(piece.fit>30.0) throw new Exception(names[i]+": encaixe reprovado (erro "+piece.fit+").");
      if(!piece.hasTex || piece.png==null) throw new Exception(names[i]+": textura não foi convertida.");
      Pkg pkg=new Pkg(packageBytes);
      dumpTextureCandidates(pkg,ids[i]);
      Img raw=rawTexture(pkg);
      int transparent=0; for(int px:raw.argb) if((px>>>24)<250) transparent++;
      // A textura de roupa usa o alpha do atlas como máscara auxiliar, não como transparência do tecido.
      // Mantém a textura opaca e a malha inteira; o recorte por pixel abria buracos no denim.
      piece.alpha=false; piece.png=raw.opaque().limit(1024).pot().png();
      System.out.println("TEXTURE "+ids[i]+" | "+raw.w+"x"+raw.h+" | source-alpha-transparent="+transparent+" | output=opaque");
      byte[] fitted=improveFit(piece.cup,male,i==2);
      Files.write(out.resolve(ids[i]+".cup"),fitted);
      Files.write(out.resolve(ids[i]+".png"),piece.png);
      System.out.println("OK "+ids[i]+" | "+piece.slot+" | vertices="+piece.verts+" | fit="+piece.fit+" | cup="+piece.cup.length+" | png="+piece.png.length);
      for(String note:converted.notes) System.out.println("INFO "+ids[i]+": "+note);
    }
  }
}
