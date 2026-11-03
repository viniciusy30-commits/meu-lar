# Etapa 41 — Cabelo Faye (mod Sims 4) — aguardando teste

- Cabelo > Atrás > "Faye (franja + trança)"; em Frente escolha "Sem" (a franja já vem na peça).
- Malha original LOD0 sem alterações (franja/topo + trança), só escala uniforme 1,4 e posição na cabeça. 21.857 vértices / 33.514 triângulos.
- Preso à cabeça (osso 8); abaixo do pescoço segue o peito (osso 4), como os outros cabelos longos.
- Textura original do mod (`faye.png`, 1024x1024, degradê loiro→rosa). Não muda com a paleta de cores do cabelo.
- `CuteChar.kt`: peças com `faye.png` descartam alfa < 0,4 (mechas). `Avatar.kt`: "Faye" no fim de HB_IDS/HB_N (saves antigos intactos).
- Se ficar pesado no celular: gerar com a malha LOD1 (GEOM 8035B4BE).
- Sem compilador local: o build do GitHub é a prova final.
- Ajuste 2 (após o 1º teste): escala 1,4 e posição que cobre o topo da cabeça; mipmaps na textura; raízes escuras clareadas (só nas mechas).
- Ajuste 3: `faye.png` decodificado com inPremultiplied=false (corrige franja preta/riscos: o fundo transparente virava preto e escurecia as bordas das mechas).
- Ajuste 4: ladrilhos de mechas (franja/topo) com brilho de baixa frequência achatado: cor loira uniforme + detalhe das mechas (a rampa de cor do Sims não existe no app). A trança não mudou.
- Ajuste 5 (causa real): o mod tem cada carta de cabelo duplicada (frente/costas no mesmo lugar) e o app nao tinha culling: as duas faces brigavam por profundidade com iluminacao oposta (chiado no topo/franja). Agora a peca Faye usa GL_CULL_FACE (winding confere com as normais em 99,5%), recorte opaco (alfa 0,45, sem mistura) e a textura voltou a ser a ORIGINAL do mod (sem clarear raizes nem achatar cor; a trança nao muda).
- Ajuste 6 (topo deformado + flutuando): (1) o cabelo e encaixado na cabeca real do app: o gerador (`ferramentas/etapa41_faye.py`) le `base.bin`, mede a folga entre a calota e a pele por direcao e puxa o cabelo ao longo do raio (campo suave, some abaixo de y=140; as mechas nao sao deformadas) - folga mediana no alto caiu de ~3,0 para ~1,7 cm. (2) o Sims pinta o couro cabeludo da cabeca da cor do cabelo e a malha do mod nao tem calota; sem isso o topo eram so mechas finas franzidas com furos mostrando a pele. Agora o arquivo inclui um couro cabeludo liso (pedaco da malha da cabeca, inflado 1,2, osso da cabeca) com o ladrilho denso da textura original (UV espelhada, sem emenda). Orelhas/laterais baixas e a testa ficam de fora (cartas e franja cobrem). Mesmo `faye.png` original; so o .bin mudou.
