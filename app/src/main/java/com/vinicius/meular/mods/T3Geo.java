package com.vinicius.meular.mods;
/** Ponto mais próximo em triângulo (coordenadas baricêntricas em q[3..5]). */
final class T3Geo {
    private T3Geo() {}
    static void closest(float px,float py,float pz,float ax,float ay,float az,float bx,float by,float bz,float cx,float cy,float cz,float[] q){
        float abx=bx-ax,aby=by-ay,abz=bz-az,acx=cx-ax,acy=cy-ay,acz=cz-az,apx=px-ax,apy=py-ay,apz=pz-az;
        float d1=abx*apx+aby*apy+abz*apz,d2=acx*apx+acy*apy+acz*apz,u,v,w;
        if(d1<=0&&d2<=0){u=1;v=0;w=0;}
        else{float bpx=px-bx,bpy=py-by,bpz=pz-bz,d3=abx*bpx+aby*bpy+abz*bpz,d4=acx*bpx+acy*bpy+acz*bpz;
          if(d3>=0&&d4<=d3){u=0;v=1;w=0;}
          else{float vc=d1*d4-d3*d2;
            if(vc<=0&&d1>=0&&d3<=0){float t=d1/(d1-d3);u=1-t;v=t;w=0;}
            else{float cpx=px-cx,cpy=py-cy,cpz=pz-cz,d5=abx*cpx+aby*cpy+abz*cpz,d6=acx*cpx+acy*cpy+acz*cpz;
              if(d6>=0&&d5<=d6){u=0;v=0;w=1;}
              else{float vb=d5*d2-d1*d6;
                if(vb<=0&&d2>=0&&d6<=0){float t=d2/(d2-d6);u=1-t;v=0;w=t;}
                else{float va=d3*d6-d5*d4;
                  if(va<=0&&(d4-d3)>=0&&(d5-d6)>=0){float t=(d4-d3)/((d4-d3)+(d5-d6));u=0;v=1-t;w=t;}
                  else{float inv=1f/(va+vb+vc);v=vb*inv;w=vc*inv;u=1-v-w;}}}}}}
        q[0]=u*ax+v*bx+w*cx;q[1]=u*ay+v*by+w*cy;q[2]=u*az+v*bz+w*cz;q[3]=u;q[4]=v;q[5]=w;}
}
