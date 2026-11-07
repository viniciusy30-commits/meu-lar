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
      if(opaque>=2){kept[count++]=a;kept[count++]=bb;kept[count++]=cc;}
    }
    if(count<Math.max(30,ni/20))throw new Exception("Recorte alpha removeu quase toda a roupa: "+count/3+"/"+ni/3+" triângulos");
    ByteBuffer out=ByteBuffer.allocate(vertexEnd+count*2).order(ByteOrder.LITTLE_ENDIAN);
    out.put(cup,0,vertexEnd);out.putInt(8,count);
    for(int i=0;i<count;i++)out.putShort((short)kept[i]);
    System.out.println("ALPHA_TRIM triangles="+ni/3+" -> "+count/3);
    return out.array();
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
      Img raw=rawTexture(new Pkg(packageBytes));
      int transparent=0; for(int px:raw.argb) if((px>>>24)<250) transparent++;
      piece.alpha=false; piece.png=raw.opaque().limit(1024).pot().png();
      System.out.println("TEXTURE "+ids[i]+" | "+raw.w+"x"+raw.h+" | alpha-channel-transparent="+transparent+" | transparent="+transparent+"/"+raw.argb.length);
      Files.write(out.resolve(ids[i]+".cup"),trimByAlpha(piece.cup,raw));
      Files.write(out.resolve(ids[i]+".png"),piece.png);
      System.out.println("OK "+ids[i]+" | "+piece.slot+" | vertices="+piece.verts+" | fit="+piece.fit+" | cup="+piece.cup.length+" | png="+piece.png.length);
      for(String note:converted.notes) System.out.println("INFO "+ids[i]+": "+note);
    }
  }
}
