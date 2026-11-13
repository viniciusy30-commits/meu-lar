# DECISOES - Cidade 5 (Meular City) v2

## Mudanca de direcao (feedback do usuario)
A grade retangular (superquadras) foi descartada: "quadradona, repetitiva, pequena". Codigo antigo guardado em `old_grid/` (nao usado).

## Fatos do repositorio (confirmados)
- `Relevo.kt` le `roads[]` (c: 0/1 avenida/rodovia, 2 coletora, 3 local; w; p = x,z,y,ponte x4; soma CX=CZ=300), `rounds[]`, `houses[]`, relevo em celulas de 8 m. Conversao para esse formato = Etapa I.
- `UserMap.kt` limita o editor a 1000x800 m; a Cidade 5 tem 4400x3600 (o `Relevo.kt` ja le `world`, `nx`, `nz` do arquivo).

## Decisoes da Etapa A v2
- Mundo 4400x3600 m, campos de trabalho de 16 m (o heightmap final de 8 m sai na Etapa B).
- Relevo: montanhas ao redor (ruido fractal + cumes), 9 colinas, bacia urbana com contorno por ruido + 2 enseadas, mar ao sul, 2 estreitos, rio, lagoa.
- Mascara urbana: terra > 0,55 m, < 150 m, declive < 34 %, afastada 1 celula da agua, componentes >= 900 celulas (0,23 km2).
- Rede: campo de tensores (grades zonais, radial na lagoa, alinhamento a agua, curvas de nivel nas colinas) + linhas de fluxo em 3 niveis (ave 360 m, col 150 m, loc 80 m de separacao), planarizacao, fusao de nos (9 m), poda de tocos < 80 m.
- Pontes vermelhas: SO CENARIO (sem estrada, sem tunel jogavel); mirante com cancela 30 m antes de cada cabeceira. Dados: Z=1500, oeste (290->800) e leste (3640->4100), torres em 330/750 e 3680/4060, tabuleiro +34 m, portais de tunel em (90,1420) e (4310,1440). Estradas de montanha e acessos sao polilinhas provisorias; terraplenagem na Etapa B.
- Anel da Lagoa (ave) com 4 ligacoes; 9 rotatorias; 4 pontes sobre o rio (3 geradas + ligacoes).
- Declive: 1 trecho local a 25 % (limite 16 %): sera resolvido pela terraplenagem/ajuste na Etapa B.

## Pendencias
- O app ainda NAO carrega a Cidade 5. Nada testado em aparelho.
- Zoneamento exato dos bairros/casas/profissoes (Etapa D) e orla/parques (Etapa F).

## Etapa B (feita)
- Heightmap final `out/relevo5.bin` (551x451, passo 8 m, formato do Relevo.kt) com terraplenagem: altura de cada no relaxada ate declives <= 6,5 % (ave), 7,5 % (col), 9,5 % (loc); corte/aterro com talude 1:2,2 (7..34 m) em volta da pista.
- `city5_roads.json` agora traz o Y de cada ponto da rua.
- Fins de rua: 9 bolsoes, 3 cais, 2 mirantes (todos justificados); conectores novos nao podem correr a menos de 22 m de outra rua.
- Nada testado em aparelho; o app ainda nao carrega a Cidade 5.

## Etapa C (feita): chao, calcadas, protecoes, pontes
- `ground.py` gera a malha assada (formato SUB1 do `Relevo.kt`, 64 m por celula) em `out/city5_ground.bin` (~24 MB, 225 mil triangulos sem compressao; Etapa I pode quantizar). `frontages.json` leva as linhas de frente de lote (calcada externa, por zona) e as covas de arvore para as Etapas D/H.
- Alturas (motor nao tem polygonOffset): asfalto = Y da rua + 0,12; guia/calcada +0,15 sobre o asfalto; canteiro/verge 5 cm abaixo da calcada; faixas e decals +0,02 (o prompt dizia +0,005; mudado por causa do z-fighting).
- Cruzamentos: UM piso por no (leque), cantos com guia arredondada (raio 5/6/8 m), calcada em arco, esquina viva nos cantos convexos, bulbo de retorno nos bolsoes e no mirante, faixas de pedestre (barras de 0,5 m), linha de retencao e rampas tateis. Plato plano de ~15-45 m junto a cada cruzamento (terraplenagem e chao usam o mesmo perfil).
- Rede: removidas 20 ruas colidindo a menos de 52 graus de outra num no (nao desenham bem) e 15 trechos < 40 m foram fundidos.
- Calcada por zona: centro = tijolo + faixa de concreto junto a guia + covas de arvore a cada 12 m; bairro = faixa-jardim 1,2 m + calcada de concreto; colina = concreto escuro; orla = calcadao em listras de areia.
- Protecoes: avenida com canteiro central; guard-rail (trilho W + postes de 4 m) onde a pista esta >1 m acima do terreno; cerca de alambrado de 1,5 m em avenidas; muro de arrimo de pedra onde o terreno sobe >1,6 m; pontes sobre o rio com parapeito, postes de luz a cada 24 m, vigas e pilares.
- Pontes vermelhas (so cenario): 2 torres de 58 m, cabos em catenaria com pendurais, trelica, ancoragens, portal de tunel escuro cravado na montanha e mirante com cancela e bloco de concreto. Deck = nivel do mirante (37 m / 39 m).
- Nao feito aqui (de proposito): viadutos (o novo mapa organico nao tem pista elevada; diga se quer um), pier/calcadao com textura final e plaza da lagoa (Etapa F), lotes e entradas de garagem (Etapa D; o chao sera regerado com os lotes).

## Correcoes da Etapa C apos feedback do usuario (faixas repetidas, faixa sobre canteiro, grama/calcada cobrindo a pista)
- Faixas de pedestre: 1 por braco, so em cruzamentos com pelo menos uma via coletora/avenida (cruzamento so de locais = so PARE), so em trechos com >= 45 m livres e nunca a menos de 60 m de outra (146 no mapa todo). O canteiro central e as linhas de faixa terminam ANTES da faixa (5,6 m), que fica 100% sobre asfalto (zebra continua de lado a lado).
- Rotatorias de verdade (9): anel de 9,5 m, ilha central de grama com guia, calcada em arco interrompida onde as ruas entram, linha tracejada, faixas nos bracos; terreno plano em disco.
- Causas do "grama/calcada cortando a pista": (1) bulbos de retorno em cima de outra rua; (2) cantos agudos (< 72 graus) entre bracos; (3) curvas fechadas e grampos nas polilinhas; (4) pares de ruas paralelas coladas. Corrigido com: bulbo so se livre, remocao de bracos agudos (medidos a 12 e 26 m), fusao de nos de grau 2, simplificacao + arredondamento das curvas (raio >= 1,4 x meia-largura), remocao de ruas paralelas coladas e laco de reparo que mede a sobreposicao asfalto x calcada/ilha/canteiro e remove a rua de menor hierarquia ali.
- Validadores novos: sobreposicao (asfalto x calcada/canteiro/verge), buracos no eixo, faixas fora do asfalto, faixas a < 60 m, calcada dos dois lados.
- `out/fotos/` traz 39 fotos de TODAS as ruas (ladrilhos de 400 x 400 m) + `00_mapa_indice.png`.
