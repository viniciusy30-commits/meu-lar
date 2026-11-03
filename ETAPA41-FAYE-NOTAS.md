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
