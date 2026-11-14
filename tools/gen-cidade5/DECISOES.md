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

## Etapa C2 (feita): transito, sinalizacao, lombadas; ruas "cortadas"
- Ruas cortadas das fotos 11/26/31/39 eram de dois tipos: (1) beco sem saida com bolsao BLOQUEADO por outra rua (ficava com ponta reta no meio do mato) -> agora liga na rua vizinha em T, ou encurta ate o bolsao caber, ou apaga o toco; (2) fim de rua na beira do rio/mar (a agua nao aparecia nas fotos) -> as fotos agora mostram relevo e agua e o fim da rua tem pracinha, meio-fio, balizas e placa "fim da via".
- Rede refeita: nos de grau 2 fundidos, curvas arredondadas (raio >= 1,4 x meia-largura), 4 ruas apertadas refeitas em Bezier.
- Modelo de transito (`traffic.py`): mao direita, faixas por sentido, 1.933 movimentos (reto/direita/esquerda/retorno/rotatoria) com caminho de Bezier, 40 semaforos, 265 PARE, 29 dê-a-preferencia, 141 lombadas.
- `furniture.py`: semaforo (poste + braco de mastro + cabecas), placas (PARE, preferencial, velocidade, pedestre, lombada, rotatoria, fim da via), linhas de retencao, setas, dentes de tubarao, lombadas listradas.
- Validadores novos em `validate_traffic.py`. Detalhes visuais em `out/transito/`.
- Nao feito: faixas de pedestre com semaforo de pedestres, setas de conversao, ciclo luminoso animado (o jogo anima pelas fases de `traffic.json`), textos nas placas (atlas na Etapa I).

## Etapa C3 — Orla das praias, sinalização completa
- Praia nunca recebe rua direto: rua -> Av. Beira-Mar (protegida) -> calçadão (YP 2.4, faixas em onda + ciclovia vermelha) -> mureta com vãos -> escadas (≤140 m entre elas) -> areia. 2 píeres (~188 m) com estacas, guarda-corpos, postes e mirante. Palmeiras, bancos, quiosques, torres de salva-vidas, chuveiros, redes de vôlei, guarda-sóis.
- Ruído de detalhe do terreno zerado na zona de praia (calçadão não some sob o relevo).
- Atlas de placas (signs_atlas.png, Mt.SIGN): PARE, PREFERENCIAL, velocidades, pedestre, lombada, rotatória, fim de via, placas de nome de rua. Setas de conversão no asfalto, semáforos de pedestre, quebra-molas.
- Cantos de calçada arredondados (ilhas) em ângulos agudos.
- Pendente: textos das placas só aparecem no app na Etapa I (integração do atlas).

## Integração provisória no app (para ver a cidade no jogo)
- gen_cidade5.py agora exporta (app_export.py) para app/src/main/assets/hds: c5.bin (relevo), c5.json (mundo, Casa 1 provisória no terreno mais plano da zona urbana, ~16 mil árvores fora de ruas/zona urbana), c5_mesh.bin (malha assada: ruas, calçadas, orla, píeres, placas, semáforos, pontes), c5_signs.png (atlas de placas).
- App: City.C5 + Configurações > Mapa cicla 1→2→3→4→5. Relevo.load(c5) reutiliza o caminho "sub" da Cidade 3. Tex.refreshSign troca o atlas de placas ao mudar de mapa.
- Ainda não há prédios, lotes nem as 17 casas (Etapa D em diante): só terreno, água, ruas, orla, pontes e árvores.
- O APK é gerado pelo workflow Build APK na branch main.

## Revisão pós-teste no jogo (ruas levantadas, quadrados verdes, orla João Pessoa)
- Terraplenagem refeita: cada vértice do terreno recebe a altura da rua MAIS PRÓXIMA no ponto projetado (antes pegava a do último ponto amostrado, até 14 m adiante -> degraus de 0,7-1 m). Plano até a borda da calçada + 4 m; taludes 3,6x o desnível (10-70 m).
- Bug antigo: o índice do nó das rotatórias ficava desatualizado após renumerar os nós (3 rotatórias no cruzamento errado). Agora reassocia pela posição.
- Dedupe só remove arestas com o mesmo traçado (antes apagava meio anel da lagoa); anel e ligações da lagoa protegidos.
- "Quadrados verdes": células de 8 m inteiras pintadas de rocha. App agora mistura rocha por vértice (inclinação) e usa máscara de areia (c5_sand.bin): só a praia é areia; margens de rio/lagoa ficam de grama.
- ORLA estilo João Pessoa: costa longa e suave (~2,7 km, sem enseadas), planície costeira de ~300 m, areia de 60 m, calçadão 14 m com ciclovia, jardim de palmeiras, VAGAS a 60° ao longo da Av. Beira-Mar, patamar de pedestre em cada travessia, mureta com escadas a cada ~92 m, 3 píeres, quiosques/salva-vidas/chuveiros/vôlei/guarda-sóis. Tudo construído a partir do eixo da avenida (orla.py chains()).
- Bairro da orla: ruas paralelas à praia a +110 e +220 m e travessas a cada ~110 m chegando na avenida (network.orla_grid). Ponte da Orla na foz do rio. Fins da avenida = retornos (bolsão).
- Avenidas (lvl 0) SEM calçada: guia + canteiro de grama (só carros). Exceção: Av. Beira-Mar do lado da cidade (prédios de frente pro mar). Esquinas continuam com calçada (espera de pedestre).
- Sinalização: uma seta reta por faixa (sem combinações de conversão) e SEM linha de retenção. Postes do lado do mar vão para o jardim; validador agora acusa poste no meio da calçada.
- Ferramentas de QA: qa/qa3d.py + qa/shots.js (three.js no Chromium sem tela, igual ao jogo), qa/tour.py (fotos 3D de todos os ladrilhos), qa/overview.py, qa/trace_build.py, qa/mismatch.py.

## Revisão 2 pós-jogo (frestas, avenidas, orla, píer, pontes)
- Frestas verdes nas bocas dos cruzamentos: as tiras de pista/calçada/guia agora entram 0,3 m no cruzamento (antes terminavam exatamente na linha de corte e a malha de 2 peças deixava uma fresta de ~0,01-0,4 m por onde o terreno aparecia).
- Avenidas: pesquisa em guias de ruas urbanas (NACTO/Raleigh/Seattle): avenida real tem guia + faixa de plantio (~1,6 m, árvores) + calçada (~2 m). Voltou a ter calçada (lado de dentro da faixa de plantio) em vez de grama pura; meia-largura da avenida 14 -> 15,8 m. Nas pontas (faixas de pedestre) a calçada encosta na guia (sem grama entre a faixa e a calçada).
- Orla: pouso das faixas alinhado com a projeção da travessia na AVENIDA (antes pelo ponto mais próximo no calçadão, deslocado); vagas 2,8 x 6,4 m a 60° (guias: ~2,7 x 6,2 m) com piso de concreto claro e linhas de 16 cm; piso das vagas 2 cm abaixo do asfalto e entrando 0,35 m sob a pista (sem fresta). Pontas do calçadão fechadas com muro baixo + poste + banco.
- Píer: deck com 0,42 m de espessura (fachada), 3 tábuas longitudinais sem xadrez + juntas, travessas e pares de estacas a cada 3 m, guarda-corpo com poste/corrimão duplo, plataforma do fim espessa com gazebo, rampa com fachada.
- Pontes vermelhas: blocos de ancoragem agora ficam AO LADO do tabuleiro (z ±11..18) e não em cima da pista; tabuleiro começa na borda do retorno do mirante (14,4 m do centro), cabos a ±12,5 m.
- QA: qa/cracks.py (vista de cima sem terreno, fundo magenta = fresta), qa/crackscan.py (varre todos os nós), validador "borda de asfalto sem guia" (informativo).

## Revisão 3 (ponte conectada, pouso das faixas, pontas da orla)
- Ponte vermelha: sem retorno redondo. A rua termina reta no nó do mirante (corte 0) e o tabuleiro começa ali, com a MESMA seção da rua coletora (pista ±6, guia, calçada até ±10); cancela listrada + barreiras de concreto 4 m à frente (acesso continua fechado: cenário).
- Orla: passagem elevada com a mesma largura da faixa de pedestre (3,5 m; antes 6,8 m).
- Pontas do calçadão: praça-mirante circular (R até 13 m, reduz se faltar terra) com fonte central, piso em setores claro/escuro, anel vermelho (continua a ciclovia), bancos virados ao centro, postes e palmeiras em canteiros redondos, muro baixo e escada de 4,6 m até a areia. Se não cabe (rio/mar), só um muro de fechamento.

## Revisão 4 (vídeos do jogo: bandas verdes e degraus nos cruzamentos)
- CAUSA RAIZ: terrain_final.profile_pts só calculava a altura nos vértices ORIGINAIS da polilinha da rua; o platô plano dos cruzamentos (s <= corte) e a rampa viravam uma reta entre vértices que podem estar a dezenas de metros. Resultado: a rua começava no cruzamento até 1,5 m acima/abaixo da altura do cruzamento (563 de 676 braços com degrau > 3 cm, 389 > 20 cm). O degrau deixava uma abertura por onde o terreno aparecia (banda verde atravessando a rua) e criava "ruas levantadas que não se conectam". Agora o perfil insere vértices exatos em s = corte (cada ponta) e a altura no corte é igual à do cruzamento (0 braços com degrau > 3 cm).
- Plátôs que se tocam (rotatórias vizinhas) -> nós com quase a mesma altura (degrau <= 10 cm).
- Avenidas: canteiro de grama dentro da calçada parecia buraco; agora calçada larga até o fim (faixa de concreto junto à guia + calçada) com covas de árvore.
- Escadas da orla (e da praça-mirante): muros laterais inclinados cobrem a quina do calçadão e o talude de terreno (antes aparecia uma cunha gigante de areia/grama ao lado dos degraus).
- Tiras de asfalto do canteiro central das avenidas também entram 0,3 m no cruzamento.
