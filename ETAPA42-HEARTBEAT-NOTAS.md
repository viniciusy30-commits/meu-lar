# Etapa 42 — Cabelo Heartbeat (mod Sims 3, Alesso) — aguardando teste

- Cabelo > Atrás > "Heartbeat (liso + franja)"; em Frente escolha "Sem" (a franja já vem na peça).
- Malha original LOD0 do pacote (cabelo longo liso com franja, 17.780 vértices / 22.804 triângulos) sem alterar a forma: só escala uniforme 0,896 e posição (ajuste rígido medido contra a cabeça do app) + campo radial suave (como o Faye) + empurrão para fora onde o cabelo entrava no corpo (ombros/peito/nuca). Total no app: 18.193 vértices / 23.456 triângulos (inclui o couro cabeludo).
- Preso à cabeça (osso 8); abaixo do pescoço segue o peito (osso 4), como os outros cabelos longos. Lados esquerda/frente do Sims 3 coincidem com o app: sem espelhar; winding confere 100% com as normais (culling certo).
- Cor: o Sims 3 pinta o cabelo com um mapa de controle (R raiz, G mecha clara, B pontas). As cores do preset (ombré castanho→loiro) foram "assadas" em `heartbeat.png` (1024x1024, bordas sem halo cinza). Não muda com a paleta de cores do criador (como o Faye).
- Couro cabeludo: pedaço da cabeça do app (inflado 1,0) com UV num bloco de cor sólida (raiz) da textura, sem furos nem emendas.
- `CuteChar.kt`: função `isAlphaHair` (faye.png e heartbeat.png): recorte de alfa 0,45, culling, sem pré-multiplicar e com mipmaps. `Avatar.kt`: "Heartbeat" no fim de HB_IDS/HB_N (saves antigos intactos). `pieces.txt`: nova linha. Ícone: `icons/hairback_heartbeat.png`.
- Gerador: `ferramentas/etapa42_heartbeat.py <pacote.sims3pack> app/src/main/assets/cute` (usa dbpf.py, geom.py, refpack.py).
- Se ficar pesado no celular: usar a malha LOD1 (GEOM 66D1FF0D750DAFFE). Se a cor ficar escura/clara demais: ajustar GAIN no script.
- Sem compilador local: o build do GitHub é a prova final.
