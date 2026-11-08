# Etapa 110 — Short sem cara de saia, pernas separadas, gola colada, barra da calça e cores

Pedido: "o short parece uma saia, as 2 pernas coladas (parado e andando), a gola ainda flutua, a calça faz pontas em cima do pé ao andar/correr, e quero as cores".

## Causas medidas e correções
| Problema | Causa | Correção |
|---|---|---|
| Short parecendo saia | barra com ~2x a largura da coxa (21 cm de meia-largura contra ~6 cm da coxa) | `Ts4Cloth.shrinkLegs`: cada perna é encolhida em torno do próprio eixo (barra x0,78, voltando a 1,0 na virilha) |
| Pernas coladas parado | os dois tubos se sobrepunham ~3 cm no centro | com o encolhimento sobra vão de ~4 cm entre as pernas |
| Pernas coladas andando | peso da perna decidido só pela posição x (±1,5 cm): vértices do centro seguiam as duas pernas ao mesmo tempo | `Ts4Cloth.legLabels`: acha as duas pernas como componentes conexos abaixo da virilha; `Fit.cleanWeights(..., legT)` põe cada perna 100% no próprio osso |
| Aletas pretas na barra | "tampas" horizontais no fundo do tubo, empurradas para fora (até 6 cm) | tampas removidas (36 triângulos no short e 36 na calça) |
| Pontas da calça sobre o pé | pesos de dedos/pé na barra; ao dobrar o pé a barra rasgava | para calça/short, pesos dos dedos e do pé vão para a canela (ossos 20→19→18 e 24→23→22) |
| Gola flutuando | pescoço do tecido largo, vazio entre gola e pele (dava para ver o forro escuro atrás) | `Ts4Cloth.collarPull`: faixa de 6,5 cm da gola é puxada até a pele (folga 0,35 cm) com deslocamento suavizado na malha (sem serrilhado) |
| Cores | só a 1ª de cada pacote existia | `T3` gera uma textura por cor (mesma malha e mesmo recorte): camiseta 18, short 12, calça 11; `ModStore` ganhou `MIN_TOP/MIN_SHORT/MIN_JEANS` e 3 entradas em `VARS` (cores no seletor, como a Autumn/Bloom) |

## Arquivos
- `mods/Ts4Cloth.java`, `mods/Fit.java`, `ferramentas/mods_teste/T3.java` (+ `ferramentas/mods_teste/cores/*.txt`: cor média de cada swatch, base dos nomes em `ModStore.kt`).
- `ModStore.kt`: listas de cores e `VARS` das três peças (`c01` = textura principal; as outras `minimalist_<parte>_cNN_am5.png`).
- Assets regenerados: `minimalist_{top,short,jeans}_am5.cup` e `.png` + 38 texturas de cor (`assets/cute/skate`).
- Textura limitada a 1024 px (APK: 24 MB de assets Minimalist em vez de 15 MB por causa das 38 cores).
- Renders: `imagens-roupas-ts4/etapa110/` (estático, zoom da gola, poses de passada, amostra de cores). `ferramentas/render_roupas/pose_teste.py` faz a pose sintética.

## NÃO validado
- Sem Gradle/Android aqui: o Kotlin (`ModStore.kt`) segue o mesmo molde de `AUTUMN`/`HOOD`, mas não foi compilado. Java do conversor compilado e rodado com JDK 21.
- A pose de teste usa pivôs estimados e ângulos exagerados (a pele aparece na coxa porque falta a máscara do jogo e o esqueleto real); serve para ver pernas independentes e a barra sem pontas, não o resultado final.
- Nomes das cores vêm da cor média (ex.: "Azul 2"); se quiser nomes melhores, é só trocar em `ModStore.kt`.
- Testar no celular: parado, andando, correndo, trocar as cores das três peças.
