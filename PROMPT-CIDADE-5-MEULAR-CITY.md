# PROMPT MESTRE — CIDADE 5 "MEULAR CITY" (meu-lar)

> Como usar: cole TUDO abaixo (de "MISSÃO" até o fim) numa conversa nova com o Claude Code **dentro do repositório meu-lar**.
> Depois mande, uma de cada vez: "Faça a ETAPA A", "Faça a ETAPA B"… (lista na PARTE 14). Não peça tudo de uma vez: é isso que gera os bugs de conexão e localização.

---

# REVISÃO 2 — PREVALECE SOBRE AS PARTES 2, 3, 5.2, 6, 7 E 8 (feedback do usuário: "quadradona, repetitiva, pequena")

O usuário rejeitou a grade retangular. **A cidade NÃO usa superquadras nem coordenadas de grade fixa.** O que vale agora:

## R2.1 Mundo e geografia (calculados em `tools/gen-cidade5/plan.py` + `geo.py`)
- Mundo **4400 × 3600 m** (heightmap final de 8 m). A cidade ocupa só ~4–6 km² no meio; **o resto é paisagem**: montanhas altas com rocha e neve ao norte, a oeste e a leste (relevo fractal, até ~400 m), colinas arborizadas, fiordes e mar ao sul. O jogador vê montanha em todo o horizonte.
- **Bacia urbana com contorno orgânico** (sem lado reto, nem elipse, nem quadrado): contorno por ruído, enseadas que entram na terra (enseada da Marina a oeste, enseada da Orla Leste a leste), pontas de terra e dois bairros de colina. A máscara urbana é calculada (terra, declive < 34 %, altitude < 150 m, ao menos 0,15 km²).
- **Água:** **mar e praia ao sul** (costa ondulada, baía, praia de areia clara com dunas); **dois estreitos** (fiordes) a oeste e a leste da cidade, com 400–440 m de largura; **um rio** que desce da montanha ao norte, atravessa a cidade (50 → 140 m de largura) e desemboca no mar; **a Lagoa** (190×110 m) numa praça no centro, com **Anel da Lagoa** (avenida em volta), praia de areia, coreto, pier de madeira, bancos e árvores.
- **Colinas dentro da cidade (ruas sobem e acompanham as curvas de nível):** Alto da Colina (120 m, NW), Parque do Mirante (85 m, NE), Colina da Igreja, Colina Leste, morro do centro, Península Real (SE) e as colinas de acesso às pontes.
- **PONTES VERMELHAS (uma em cada lado do mapa), estilo Golden Gate (EUA):** pontes suspensas **vermelho-alaranjado "International Orange"**, **duas torres art déco** de ~80 m com travessas, cabos principais em curva (catenária) e pendurais verticais a cada 12 m, tabuleiro a +34 m sobre a água, vão central ~420 m, 4 faixas + calçadas, iluminação. Uma cruza o estreito **oeste** (Z=1500) e a outra o estreito **leste**. **Cada uma termina em um TÚNEL (boca com arco de concreto) na montanha, na borda do mapa**, de modo que o mapa **nunca termina abruptamente**: o carro entra no túnel, a tela escurece e o jogo devolve o jogador à cidade (ou mostra "fim da estrada"). Névoa leve e montanhas ao fundo.
- **Outras pontes:** 3 sobre o rio (Ponte do Moinho, Ponte Central, Ponte Real e Ponte da Foz), todas com parapeito, postes e calçadas.

## R2.2 Rede viária ORGÂNICA (nada de grade)
- Gerada por **campo de tensores + linhas de fluxo** (Chen et al.): hierarquia **avenida (28 m) → coletora (20 m) → local (15 m)**; cada região tem sua própria direção e densidade: centro com grade inclinada, bairros do oeste e do leste em ângulos diferentes, **ruas circulares em volta da lagoa**, **ruas paralelas à costa/rio/enseadas**, **ruas que acompanham as curvas de nível nas colinas**, becos e cul-de-sacs. Quarteirões de tamanhos e formas variados; sem dois bairros com o mesmo desenho.
- **Av. Beira-Mar** segue a costa a ~60 m da água. **Rotatórias** em 6–9 nós de avenida (R 30–48 m). Perfis de via, faixas, esquinas, semáforos etc. da PARTE 2.3, 2.4 e 4 continuam valendo.
- Toda via termina em outra via, rotatória, **cul-de-sac**, praia/cais ou **portal de túnel**. Grafo único e conexo. Validadores da PARTE 14 (adaptados: conexão, tocos curtos, cruzamentos sem nó, declives, via na água, pontes, rotatórias) e **terraplenagem** (Etapa B) para declives acima do limite.

## R2.3 Onde ficam os bairros, casas e profissões (ZONEAMENTO, não coordenadas fixas)
O gerador calcula o zoneamento a partir da geografia; cada item abaixo vai para a zona indicada, em lotes ao longo das ruas, **tabela final em `HOUSE_LOTS`/`JOB_PLACE`** gerada de forma determinística:
| Zona | Onde | O que vai lá |
|---|---|---|
| **Centro / Praça da Lagoa** | em volta da lagoa e das avenidas centrais, terreno plano | arranha-céus (Atlas 172 m, Nova Tech), Prefeitura, Fórum, Almeida & Prado, Escritório Central, teatro, museu, biblioteca, hotéis, comércio |
| **Distrito Médico** | terra plana ao norte do centro, junto ao rio | Hospital Santa Clara, Clínica Aurora, farmácia 24h |
| **Alto da Colina** | colina noroeste (nobre) | Casas **2** e **3**, mansões decorativas, portão com guarita, mirante |
| **Parque do Mirante** | colina nordeste | trilhas, mirante, reservatório |
| **Vila Esperança** (popular) | oeste, flat, perto do centro | Casas **1** (inicial), **12**, **8**, **13**, **9**; Brilho Limpeza, Lanchonete do Zé, Posto Rota Sul |
| **Parque das Flores** | oeste, junto ao parque grande | Casas **10**, **11**, **14**; Escola Primavera |
| **Jardim Central** | leste, ruas de tijolo, igreja | Casas **5**, **6**, **7**; Igreja Matriz |
| **Recanto do Sul / Praia** | orla sul, lotes entre a Av. Beira-Mar e a areia | Casas **15**, **16**, **4**; píer, quiosques, calçadão |
| **Península Real** | ponta de terra a sudeste | Casa **17**, doca, mansões |
| **Distrito de Serviços** | planície ao longo do rio/oeste | Delegacia, Quartel, Oficina do Toninho, Central de Coleta, Expresso Já, Pilar Construtora |
| **Orla Leste / enseada leste** | enseada leste | Parque de Diversões (roda-gigante, montanha-russa), farol |
| **Marina** | enseada oeste | marina, clube náutico |
| **Parque Aquático** | orla, areia plana | Splash Meular |
| **Estádio / SuperBom / Shopping** | terras planas do leste | Arena, shopping, SuperBom |
Regras de lote, orientação das casas (frente para a rua), interior das 19 profissões (PARTE 9) e das 17 casas, alturas, texturas e orçamento continuam como estão. **Onde as partes 3, 6, 7, 8 citam coordenadas de grade (X/Z de superquadra, "SQ(i,j)", "bloco (bx,bz)"), troque pela zona acima; o gerador entrega as coordenadas reais.**

## R2.4 Etapas (nova ordem)
A **ETAPA A** (geografia + rede viária orgânica + pontes + validadores + prévia) está FEITA em `tools/gen-cidade5/` (rodar: `python3 gen_cidade5.py out`). Seguem B (terreno final 8 m, terraplenagem de ruas, pontes e portais; estradas dos túneis), C (chão), D (lotes + 17 casas), E (centro), F (parques/pontos turísticos), G (19 profissões), H (vida: árvores, trânsito, luz), I (integração no jogo).

---

# MISSÃO

Crie do zero uma cidade americana grande e completa para o jogo Android "Meu Lar" (Kotlin + OpenGL ES próprio, sem Unity). A cidade será o mapa "Cidade 5". Ela tem: centro com arranha-céus, bairros ricos e pobres, subúrbios, condomínios, apartamentos, orla com praia e píer, parque aquático, parque de diversões, praças, parques, marina, estádio, shopping, hospital, escolas, rio com pontes, rodovia elevada com viadutos e rotatórias.

**Só dois tipos de lugar têm interior mobiliado:** (1) as 19 construções de profissão; (2) as 17 casas do jogador (as mesmas da Cidade 2 / Hds). **Todo o resto é decoração**: fachada completa, calçada, entrada falsa, vitrine opaca ou com cartaz atrás do vidro, sem interior navegável, sem móvel dentro. Nada de "meio-interior".

Este documento é a ESPECIFICAÇÃO. Onde ele der número, coordenada ou tabela, **obedeça o número**. Não improvise layout, não "melhore" o mapa, não mude nome de rua. Se algo faltar, escolha a opção mais simples, **escreva a escolha no arquivo `DECISOES.md`** e siga em frente. Se algo for impossível, pare e diga qual regra bate com qual.

---

# PARTE 0 — REGRAS DE OURO (a causa de todos os bugs das tentativas anteriores)

Todas as tentativas anteriores falharam por: peças que não se encaixam, coisas no lugar errado, texturas com defeito. Para impedir isso:

1. **UMA ÚNICA FONTE DA VERDADE.** Crie `tools/gen-cidade5/plan.py` com TODAS as constantes e tabelas deste documento (grade, larguras, coordenadas, lotes, nomes). Nenhum outro arquivo pode ter número de coordenada escrito à mão. Tudo (ruas, calçadas, lotes, árvores, postes, colisão, mapa, GPS) é **calculado** a partir de `plan.py`.
2. **TUDO NA GRADE.** Cada elemento é posicionado por fórmula (índice da superquadra, índice do quarteirão, índice do lote) e não por "olhômetro". Proibido número mágico solto (ex.: `x += 37.3`). Se precisar de um deslocamento, dê nome a ele em `plan.py`.
3. **UMA UNIDADE:** metros. **Eixos:** X = leste (+), Z = sul (+), Y = cima (+). Origem (0,0) no canto noroeste do mundo. Ângulos: 0 = aponta para +X, cresce no sentido horário visto de cima (igual ao `Relevo.kt`/`gen_bairro.py`; **confira no código e copie a convenção**).
4. **UM ELEMENTO, UM DONO.** Cada metro quadrado de chão pertence a exatamente UMA camada: asfalto, calçada, gramado, areia, água, piso de lote, plaza. Antes de gerar a malha, gere um **mapa de ocupação** (raster de 1 m) e **falhe com erro** se duas camadas ocuparem o mesmo metro. Zero sobreposição. Zero buraco.
5. **ANTI-PISCAR (z-fighting).** Dois planos nunca ocupam a mesma altura. Alturas fixas (PARTE 12): asfalto 0,00; faixa de pedestre/linha pintada +0,005 (decal com `polygonOffset` ou, se não houver, +0,008); guia 0,15; calçada 0,15 (topo); gramado de lote 0,10 (abaixo da calçada, com a guia de contenção); areia 0,05 → 0 seguindo a praia. Laje, telhado e paredes não compartilham face coplanar.
6. **CONEXÃO POR CONSTRUÇÃO.** Toda rua termina em outra rua, em rotatória, em cul-de-sac ou na borda do mundo. Nunca "no ar". Todo cruzamento é gerado por UMA função `intersection()` que desenha o piso do cruzamento inteiro, as 4 (ou 3) esquinas de calçada com raio, as rampas e as faixas de pedestre. As ruas são desenhadas **entre** cruzamentos, nunca atravessando-os.
7. **VALIDAR ANTES DE ENTREGAR.** Os validadores da PARTE 14 são parte da entrega. Se um validador falha, o gerador **aborta** e imprime coordenada + nome do elemento. Não entregue com validador vermelho.
8. **DETERMINISMO.** Semente fixa `RNG = 5005`. Rodar o gerador duas vezes dá arquivos idênticos (byte a byte).
9. **NÃO QUEBRE O QUE EXISTE.** Cidades 1, 2, 3 e 4 continuam funcionando. A Cidade 5 é nova, escolhida em Configurações > Mapa. Se faltarem os assets da 5, volta sozinho para a Cidade 4/3.
10. **ENTREGA EM ETAPAS** (PARTE 14). Cada etapa compila, roda e passa nos validadores antes da seguinte. Prévia PNG 2D de cada etapa (como `prev_pop.py`).
11. **ANDROID/MEMÓRIA:** celular médio. Limites na PARTE 13. Não ultrapasse.
12. **NÃO CONFIE NA SUA MEMÓRIA do repositório:** LEIA antes de escrever (PARTE 1). O compilador de mapa (Gradle) não existe aqui; escreva o código com muito cuidado e releia-o. Se algo não compilar quando o usuário testar, ele manda o erro e você corrige só aquilo.

---

# PARTE 1 — LEIA ISTO NO REPOSITÓRIO ANTES DE ESCREVER QUALQUER LINHA

Leia, nesta ordem, e **anote em `DECISOES.md`** o que é fato (formato de arquivo, constantes) e o que é dúvida:

- `PLANO-VIVO.md` (seções Cidade 2 a 4, Etapas 163–187) e `ETAPA177…187-NOTAS.md`.
- `app/src/main/java/com/vinicius/meular/Relevo.kt`: como lê `city3.json`/`relevo.bin`/`sub.json`/`sub.bin`/`sub_mesh.bin`; classes `Road` (campo `c`: 0 e 1 = avenida/rodovia, 2 coletora, 3 local), `Hub` (rotatória), pontes, `curbW`, `groundH`, `roadSurface`, `service`.
- `app/src/main/java/com/vinicius/meular/UserMap.kt` e `MapEditorActivity.kt`: o compilador do editor (cruzamentos, pontes, viadutos, becos, postes). **O formato de saída que o `Relevo.kt` aceita é a interface obrigatória.** Se o formato atual não comporta algo desta especificação (ex.: mundo maior que 1000×800, viaduto contínuo, calçada separada), **estenda o formato de modo compatível** (campos novos opcionais) e descreva a extensão em `DECISOES.md`.
- `tools/gen-bairro/` (`gen_bairro.py`, `house.py`, `fences.py`, `bake.py`): geradores em Python; reutilize `bake.py` (malha assada) e o estilo de `house.py` para as casas de decoração.
- `Hds.kt`, `HdsEstate.kt`, `city2.json` (campo `plots`: caixa de cada uma das 17 casas), `city2walk.bin`: como as 17 casas são colocadas, subir de nível (platô), colisão, andares, escadas, porão, telhado que some.
- `Jobs.kt` (as 19 profissões, nomes e letreiros — **use exatamente esses nomes**), `JobRooms.kt` e `JobFurn.kt` (interiores já feitos, direções 0/1/2/3, `JobSpace`), `CityInt.kt` (interiores de hospital, mercado, banco etc. da Cidade 1), `CitySign.kt` (atlas de letreiros), `Doors.kt`, `Elevado.kt`, `Flora.kt`, `Vehicles.kt`, `TeslaCar.kt`, `Sky.kt`, `Water.kt`, `Shade.kt`.
- `app/src/main/assets/hds/mobilia/mobilia.json`: móveis do catálogo Hds (use **só** ids que existem aqui).

**Fato já conhecido (confirme no código):** o jogo desenha ruas com guia + calçada; carros existem em `Vehicles.kt`; a casa do jogador (Casa 1 do Hds) tem interior real com portas livres; colisão é por retângulos 2D + altura do chão (`groundH`); o editor atual limita o mundo a 1000×800 m — esta cidade usa **2700×2100 m**, então o formato/limites devem ser estendidos.

---

# PARTE 2 — SISTEMA DE COORDENADAS, GRADE MESTRA E PERFIS DE RUA

## 2.1 Mundo
- Retângulo **X 0…2700, Z 0…2100** (metros). Heightmap em células de 8 m (como `relevo.bin`): 338 × 263 amostras. Altura em centímetros (int16), igual ao formato atual.
- Referência vertical: **Y = 0,00 = topo do asfalto** em terreno plano. Nível do mar (superfície da água) = **Y = −0,40**.
- **Direção do trânsito: mão direita (EUA).** Rotatórias: sentido anti-horário. Faixa de pedestre: listras "zebra" brancas (estilo EUA "continental") sobre o asfalto, largura 3,0 m, listras de 0,5 m com vão de 0,5 m.

## 2.2 Grade mestra (NÃO MUDE ESTES NÚMEROS)
- Avenidas **norte–sul** (eixo em X): `XA = [200, 588, 976, 1364, 1752, 2140]` (passo 388 m)
  Nomes: `Av. Oeste (200)`, `Av. das Flores (588)`, `Av. dos Pioneiros (976)`, `Av. da República (1364)`, `Av. do Rio (1752)`, `Av. Leste (2140)`.
- Avenidas **leste–oeste** (eixo em Z): `ZA = [200, 588, 976, 1364, 1752]` (passo 388 m)
  Nomes: `Av. Norte (200)`, `Av. dos Jardins (588)`, `Av. Central (976)`, `Av. do Sul (1364)`, `Av. Beira-Mar (1752)`.
- Largura da avenida = 28 m → **superquadra (SQ)** (i, j) é o retângulo livre entre avenidas: `X ∈ [XA[i]+14, XA[i+1]−14]`, `Z ∈ [ZA[j]+14, ZA[j+1]−14]` → **360 × 360 m**, com i = 0…4 e j = 0…3. Total: 20 SQ.
- Uma SQ do **tipo CENTRO/COMERCIAL** é dividida em 4×4 quarteirões de **75×75 m** separados por ruas coletoras de **20 m**: origem do quarteirão (bx, bz) = `(XA[i]+14+95·bx, ZA[j]+14+95·bz)`, lado 75. (4·75 + 3·20 = 360 ✓)
- Uma SQ do **tipo RESIDENCIAL** é dividida em 5×5 quarteirões de **60×60 m** separados por ruas locais de **15 m**: origem = `(XA[i]+14+75·bx, ZA[j]+14+75·bz)`, lado 60. (5·60 + 4·15 = 360 ✓)
- Uma SQ do **tipo ESPECIAL** (parque, estádio, parque aquático, hospital…) recebe o desenho dado na seção própria, mas **a borda de 360×360 e as 4 avenidas ao redor não mudam**.

## 2.3 Perfis de via (corte transversal — largura total medida de borda de calçada a borda de calçada)
Cada via tem eixo central, e as camadas se repetem simétricas (exceto onde dito).

| Via | Total | Composição (de fora para o eixo) |
|---|---|---|
| **Avenida** (c=1) | 28,0 | calçada 2,5 · faixa de estacionamento 2,5 · 2 faixas de 3,5 · canteiro central 4,0 (com árvores a cada 12 m, ver 11) · 2 faixas de 3,5 · estacionamento 2,5 · calçada 2,5. Guia (meio-fio) 0,20 de largura, altura 0,15 entre asfalto e calçada, incluída na faixa de calçada. |
| **Coletora** (c=2) | 20,0 | calçada 4,0 · estacionamento 2,5 · 2 faixas de 3,5 · estacionamento 2,5 · calçada 4,0 (calçada larga com árvores e bancos no centro) |
| **Local** (c=3) | 15,0 | calçada 2,5 · estacionamento 2,0 · 2 faixas de 3,0 · estacionamento 2,0 · calçada 2,5 |
| **Rodovia (via expressa)** | 36,0 | pista 3 faixas de 3,6 por sentido (21,6) · canteiro/barreira central 3,0 (barreira de concreto "Jersey" 0,81 m) · acostamento 2,6 de cada lado · mureta externa 1,0 |
| **Rua marginal** | 20,0 | = coletora, mão dupla |
| **Beco** | 6,0 | sem calçada, asfalto/concreto, fundos de comércio |
| **Rua Duna / orla** | 15,0 | = local |

- Estacionamento é uma faixa **pintada** (linhas brancas a cada 6 m, "T" perpendicular) ou apenas **marcada por pavimento levemente mais claro**: sem objetos 3D, a não ser carros decorativos parados (PARTE 11).
- Calçada: laje de concreto em quadrados de 1,5 m com juntas finas (textura), +0,15.
- Rebaixo de cadeirante em CADA esquina e CADA faixa de pedestre: rampa de 1,5 m de largura, com piso de bolinhas (textura "tátil" amarelo-queimado) — geometria: rampa inclinada de 0,15 a 0,00 ao longo de 1,2 m.
- Esquina: o canto da calçada é um **arco de raio 6,0 m** (em avenida×avenida 8,0 m), centro no ponto de encontro dos eixos das calçadas. O arco é de meio-fio contínuo, sem emenda.

## 2.4 Faixas e pinturas (todas decals na altura +0,005 sobre o asfalto)
- Avenida: o canteiro central é físico, então não há linha amarela no meio; as bordas internas da pista (junto ao canteiro) têm linha amarela contínua simples e as externas linha branca contínua. Faixas entre pistas de mesmo sentido: tracejada branca (3 m / 9 m). Estacionamento: linha branca contínua separando a faixa.
- Coletora e local: linha dupla amarela contínua no eixo; borda do estacionamento branca.
- Cruzamento sinalizado: **linha de retenção** branca de 0,6 m de largura, 1,5 m antes da faixa de pedestre, ocupando a(s) faixa(s) de entrada; faixa de pedestre em TODOS os 4 braços.
- Rotatória: setas brancas de entrada, linhas tracejadas brancas de cada braço (yield) e faixa de pedestre a 6 m do anel, nos 4 braços; ilha-divisória triangular em cada braço, com 4 m de largura na base.
- Cruzamento de avenida com avenida: **semáforos em braço** (poste de 7 m com braço de 6 m com 2 cabeças) em duas esquinas diagonais + 1 semáforo de pedestre em cada esquina.
- Cruzamento com coletora/local: **placa de PARE** (octogonal vermelha) no braço menor, a 1 m da linha de retenção, e uma placa de nome de rua (blade) no poste da esquina.


---

# PARTE 3 — O MAPA GERAL (onde fica cada coisa)

Visão de cima (norte para cima). Cada célula é uma superquadra SQ(i,j). Tipos: RES = residencial 5×5 · CEN = centro 4×4 · ESP = especial.

```
 X →   0        200       588       976      1364      1752      2140   2260   2360-2430   2470      2700
 Z     |  Serra   |  Av.Oeste |Av.Flores|Av.Pioneir|Av.Repúbl.| Av. Rio  |Av.Leste|ROD.| RIO |  PENÍNSULA REAL
 0     +----------+-----------+---------+---------+---------+----------+-----+----+-----+------------
 60    ======== RODOVIA BELTWAY NORTE (Z=60) ======================================\ (curva R100 → sobe)
 130   -- faixa de serviços: rua de serviço Z=130 (Central de Coleta, Expresso Já, Pilar Construtora) --
 200   ============ AV. NORTE =================================================================
       |SQ(0,0) ESP |SQ(1,0) ESP |SQ(2,0) RES |SQ(3,0) ESP  |SQ(4,0) ESP  |  Rodovia elevada
       |Alto da     |Parque do   |Jardim      |Distrito     |Arena        |  (viaduto contínuo
       |Colina      |Mirante     |Central     |Médico       |Meular       |   Z150→1480)
 588   ============ AV. DOS JARDINS ===============================================  ==> Ponte do Moinho
       |SQ(0,1) RES |SQ(1,1) ESP |SQ(2,1) CEN |SQ(3,1) CEN  |SQ(4,1) CEN  |
       |Parque das  |Parque     |Centro Norte|Centro Leste |Shopping +   |
       |Flores(bairro)|das Flores |(escritórios)|(torres)   |SuperBom     |
 976   ============ AV. CENTRAL ====== [ROTATÓRIA PRAÇA CENTRAL em (1364,976)] =====  ==> Ponte Real → Península
       |SQ(0,2) RES |SQ(1,2) CEN |SQ(2,2) CEN |SQ(3,2) CEN  |SQ(4,2) RES  |
       |Vila        |Distrito de |Centro Oeste|Centro Sul   |Condomínio   |
       |Esperança   |serviços    |(cultura)   |(hotéis)     |Rio Azul     |
 1364  ============ AV. DO SUL ==================================================
       |SQ(0,3) RES |SQ(1,3) ESP |SQ(2,3) ESP |SQ(3,3) ESP  |SQ(4,3) ESP  |
       |Bairro      |Marina e    |Orla Central|Parque       |Parque de    |
       |Recanto Alto|Clube Náutico|+ Píer     |Aquático     |Diversões+Farol|
 1752  ============ AV. BEIRA-MAR ====[ROTATÓRIA DO FAROL (1364,1752)]=========  ==> Ponte da Foz → Península
       Rua Duna (Z=1800, só X 214…1000)   calçadão / praia / MAR (Z>1880)
```

## 3.1 Rodovia (via expressa) — viaduto
- **Beltway Norte:** eixo em Z=60 de X=0 até X=2160, nível do chão (Y=0), 36 m. Entra no mapa pela borda oeste (X=0) e some na borda do mundo (desenhe uma barreira-cenário e uma cortina de árvores de fundo).
- **Curva:** arco de raio 100 m, centro (2160, 160), de (2160,60) até (2260,160), girando para o sul. Ao longo do arco, a altura sobe linearmente de 0 a 7,5 m (declive ≈ 4,8 %).
- **Rodovia Leste:** eixo em **X=2260**, de Z=160 até Z=1480, **elevada: tabuleiro a Y=+7,5** (altura livre sob a viga: 6,0 m; viga com 1,5 m). Em seguida **rampa descendente** de Z=1480 até Z=1620 (140 m, 5,4 %), voltando a Y=0, e termina em T na **Av. Beira-Mar** (semáforo).
- **Estrutura elevada:** pilares de concreto retangulares 2,0 × 3,0 m, pé no chão e topo sob a viga, num único alinhamento sobre o eixo (X=2260), a cada **30 m** (nos pontos em que o eixo cruza avenida, os dois pilares mais próximos ficam a ≥ 17 m do eixo da avenida para não invadir a pista). Viga-caixão com laterais lisas, mureta/guarda-corpo "Jersey" nas bordas, postes de luz de 12 m a cada 40 m no canteiro central, placas verdes de saída em pórtico (letras brancas) a 300 m antes de cada saída.
- **Marginais:** ruas marginais (20 m) com eixos em **X=2222** (oeste) e **X=2298** (leste), mão dupla, ao nível do chão, de Z=190 a Z=1620, passando sob a rodovia. O espaço entre os pilares e as marginais é calçada larga + faixa de árvores. Faixa de 58 m entre Av. Leste (X=2140±14) e a marginal oeste = **"cinturão verde"**: gramado, fileira dupla de árvores e muro-ruído de concreto liso, 3 m de altura, com recorte para as ruas que atravessam.
- **Saídas:** duas alças de acesso (rampas de 6,25 %, faixa de 4,0 m + acostamento 1,8 m) ligando a rodovia às marginais em **Z=588** (alças ao norte do eixo, sobe/desce) e **Z=1364**. Cada alça é uma rampa reta de 120 m mais curva de raio 40 m; o encontro com a marginal é um cruzamento com semáforo.
- **Cruzamentos sob a rodovia:** as avenidas Z=200, 588, 976, 1364 passam SOB o tabuleiro (altura livre 6,0 m). Onde passam, o teto visível é a laje inferior da viga: cor cinza-concreto, sem textura de asfalto.

## 3.2 Rio
- Eixo central do rio: curva suave entre os pontos (X,Z): (2395,0) → (2395,500) → (2380,1000) → (2395,1500) → (2395,1830) → foz no mar (2395,1880). Largura constante **70 m**. Margens inclinadas 1:3. Profundidade máxima 3 m (leito −3,0). Parte da margem tem **muro de contenção** com guarda-corpo (cais) entre Z=900 e Z=1100 (trecho urbano).
- Pontes: **Ponte do Moinho** (eixo Z=588, coletora, 20 m + 2 calçadas de 3 m, vão 90 m, 2 pilares na água), **Ponte Real** (eixo Z=976, avenida 28 m, vão 100 m, arco metálico branco por cima com cabos), **Ponte da Foz** (eixo Z=1752, Av. Beira-Mar continua, 28 m, baixa, balaustrada de concreto e postes clássicos) e a **Ponte Norte** (Beltway não cruza o rio; ignore).
- Todas as pontes têm rampa de acesso suave (máx 5 %); a altura do tabuleiro é a do asfalto +0,6 m; guarda-corpo 1,1 m; poste a cada 25 m; calçada 3,0 m de cada lado com banco a cada 40 m.

## 3.3 Terreno
- Praticamente plano (Y de −0,1 a +0,5) exceto: **Alto da Colina** (SQ(0,0), região X 0…620, Z 0…620): colina com cume Y=+38 m em (300, 330). Ruas desse bairro seguem o morro com declive ≤ 10 % (local) e ≤ 7 % (a Av. das Flores e Av. Norte que o contornam ficam planas via cortes laterais).
- **Parque do Mirante** (SQ(1,0)): colina baixa, cume Y=+22 m em (780, 380); trilhas com declive ≤ 12 %.
- **Praia:** Av. Beira-Mar em Y=0,00; a partir da calçada sul (Z=1766) a areia cai de Y=+1,2 (duna) a 0 em Z=1860, linha d'água (Y=−0,4) em Z≈1880, fundo cai a −6 em Z=2000 e −12 em Z=2100. Costa levemente ondulada: `Zcosta(X) = 1880 + 8·sin(X/140)`.
- **Serra do Pinhal** (X 0…186): faixa de morro arborizado até Y=+25 m, sem acesso, como moldura. Mesma ideia atrás do Beltway Norte (Z<42): talude gramado 1:3 e mata densa até a borda.
- Todo platô de casa/edifício é **nivelado** com borda de talude 1:2 suavizada (como o compilador do editor faz).

## 3.4 Rotatórias (todas com R medido na borda externa do asfalto)
| Nome | Centro (X,Z) | R | Ilha central |
|---|---|---|---|
| **Praça Central** | (1364, 976) | 48 | chafariz em 3 níveis + monumento (ver 8.1), canteiros de flores, 4 faixas de pedestres para a praça ao redor |
| Rotatória do Mirante | (588, 588) | 30 | gramado + árvore grande (carvalho) + placa "Alto da Colina" |
| Rotatória das Flores | (588, 976) | 32 | canteiro de flores coloridas, 3 palmeiras |
| Rotatória Universitária | (976, 588) | 30 | gramado + escultura abstrata de aço |
| Rotatória do Rio | (1752, 976) | 38 | fonte circular + relógio |
| Rotatória do Sul | (976, 1364) | 30 | gramado com ipês/jacarandás |
| **Rotatória do Farol** | (1364, 1752) | 44 | chafariz + miniatura do farol + bandeiras |
Nas rotatórias, os quarteirões de canto são **cortados pelo círculo** de raio R + 6 (calçada de 4 + guia 2): o espaço cortado vira calçada em arco, ligando as calçadas das avenidas sem emenda.

## 3.4b Contorno irregular da cidade (OBRIGATÓRIO — a cidade NÃO é retângulo nem círculo)
A grade mestra (2.2) continua sendo a base, mas **o que existe de cidade é definido por uma MÁSCARA DE CIDADE** (`CITY_MASK`, polígono fechado em `plan.py`, raster de 8 m), e o contorno é **orgânico**:
- **Silhueta:** polígono de ~40 vértices com reentrâncias e saliências, sem lados paralelos longos: baía côncava no sudeste (entra até Z≈1650 entre X 1900…2300), cabo de pedra no sudoeste, vale do rio a leste, serra recortando o noroeste, enseada da marina, e um **bairro anexo** (Península Real) ligado só por ponte. Perímetro/área ≥ 1,25 do de um retângulo equivalente.
- **Superquadras de borda são PARCIAIS:** SQ(0,0), (4,0), (0,3), (4,3) e as que tocam a baía/serra/rio são **cortadas pela máscara**. Quarteirão cortado: só os lotes 100 % dentro da máscara são construídos; o resto vira mata, rocha, duna, margem ou água.
- **Ruas que saem da grade:** além da grade, 6 a 10 ruas **curvas** (raio mínimo 25 m, declive ≤ 8 %): estrada panorâmica da colina, rua da orla acompanhando a costa, estrada ribeirinha, 2 acessos do Beltway. Elas **ligam** nós da grade por arcos/clotoides (nunca por "ponte no ar").
- **Fim de rua:** onde a máscara corta uma rua da grade, ela termina em **cul-de-sac** (raio 12 m), **mirante/píer/praça de margem** ou **portão/estrada de terra**, nunca em vazio, nunca com asfalto "cortado".
- **Fora da máscara:** terreno natural contínuo até a borda do mundo (mata, campo, rocha, água) com talude suave; **sem parede/borda visível**. A cidade inteira é cercada por um anel de 150 m de mata/colina que fecha o horizonte.
- **Validadores:** (a) todo elemento urbano está dentro da máscara; (b) nenhuma via termina na máscara sem o fim de rua previsto; (c) o contorno não tem lado reto > 300 m; (d) conectividade mantida após o recorte.

## 3.5 Zonas com nome (o "bairro" que aparece no mapa/GPS)
Mapa/GPS lista: Alto da Colina · Parque do Mirante · Jardim Central · Distrito Médico · Arena Meular · Parque das Flores (bairro + parque) · Centro (Norte/Leste/Oeste/Sul) · Shopping · Vila Esperança · Distrito de Serviços · Condomínio Rio Azul · Recanto do Sul · Marina · Orla Central · Parque Aquático · Parque de Diversões · Península Real.


---

# PARTE 4 — REFERÊNCIAS VISUAIS (o "jeito" da cidade) E ANATOMIA DA RUA

O usuário enviou fotos de referência. O estilo-alvo é **"cidade americana de verdade"**: não é caixa cinza lisa. Traduza assim:

- **Main Street histórica (Centro Oeste e Jardim Central):** casarões brancos de madeira (clapboard) de 2–3 andares, telhado de duas águas cinza-escuro, janelas com **venezianas pretas**, chaminé de tijolo, frontão triangular com janela em arco, **toldos listrados** (azul/branco, preto/branco, vermelho/creme) sobre as lojas, **bandeira americana** em suporte inclinado na parede, plaquinhas penduradas em ferro (blade signs), floreiras com flores, vasos na porta.
- **Calçada de tijolo** (vermelho-queimado, espinha de peixe) nas coletoras históricas, com **faixa de concreto** junto à guia, **bancos de ferro fundido + madeira**, lixeira azul/verde, canteiro com cerquinha de ferro preto, **postes de luz clássicos** (haste preta curva com lanterna, 4,5 m) com decoração sazonal (espigas de milho/abóboras no outono), **hidrante** vermelho/amarelo e caixa de correio azul.
- **Esquinas de avenida:** **semáforos em braço de mastro** (mast arm) com 2–3 cabeças vermelho/amarelo/verde e placas de nome de rua verdes presas no braço; **placas de PARE/pedestre** amarelo-limão; faixa de pedestre **continental** (barras largas) e linha de retenção; guia pintada de amarelo perto de hidrante e esquina; carros estacionados de ambos os lados (vários modelos/cores).
- **Fios elétricos e postes de madeira** aparecem nas fotos: no jogo, **só nas ruas locais dos subúrbios e Vila Esperança** (poste de madeira 10 m a cada 40 m, 2 cruzetas, 3 fios finos como linhas de 2 triângulos finos, sem sombra, **só até 120 m do jogador**, depois somem). Centro e avenidas novas: fiação subterrânea (sem fios).
- **Árvores de outono** (laranja/vermelho/amarelo) misturadas a verdes e pinheiros: o mapa tem **clima temperado com 3 paletas de folhagem** (verde, âmbar, vinho) sorteadas por quarteirão para dar variedade sem repetir "carimbo". O céu e a luz seguem o `Sky.kt` atual.
- **Praça de pedestres com piso geométrico** (foto do calçadão): losangos/faixas em tons de terracota, bege e cinza, em padrão repetido; usar nas praças e no calçadão da orla (textura de ladrilho em atlas, 4 padrões, escala 1 m = 1 repetição).
- **Arco monumental sobre avenida dividida (foto aérea com palmeiras):** a entrada da cidade pela Av. Central do oeste (X≈215, Z=976) tem um **"Portal da Cidade"**: arco de concreto branco com perfil de catenária, vão de 32 m sobre a avenida inteira (28 m), altura 14 m, pés largos 3 m×2 m nos dois lados, canteiro de gramado + palmeiras-imperiais + 3 postes duplos de 12 m com braço. É **só decoração, sem colisão acima de 5,5 m** (o carro e o jogador passam por baixo).
- **Subúrbio visto do alto (fotos aéreas):** copas de árvores cobrem 50–60 % do bairro; telhados cinza/marrom/vermelho-telha variados; quintais verdes com cerca; ruas retas na grade com ruas curvas só na colina; mata e serra no fundo. Meta do jogo: **olhando do alto, o bairro tem que parecer uma foto dessas** — árvores grandes por lote (1–3), de rua a cada 12 m, jardins diferentes, carros na garagem/na rua.
- **Igreja branca de campanário** (foto): Igreja Matriz no Jardim Central (8.4).
- **Comércio colorido** (foto da avenida comercial): na Vila Esperança e Distrito de Serviços, fachadas coloridas de 1–2 andares com letreiros grandes, toldos, marquises; pequeno prédio de apartamentos ao fundo.

## 4.1 Anatomia completa de um QUARTEIRÃO (aplica-se a todos; descrito do exterior para o interior)
Para o quarteirão de 75×75 (CEN) ou 60×60 (RES), a partir do meio-fio da rua:
1. Guia (meio-fio) 0,20 × 0,15 de altura; 2. **calçada** (largura do perfil, 2.3); 3. **faixa-jardim** de 1,2 m entre calçada e lote (só RES), gramado Y=0,10 com árvore de rua a cada 12 m no eixo da faixa (a 1,0 m da guia no CEN: a árvore fica DENTRO de um canteiro quadrado de 1,2×1,2 vazado na calçada, com grade de ferro); 4. **lote**.
- Poste de luz: a cada 34 m no lado alternado (RES) ou nos dois lados em frente a frente (avenida), recuado 0,6 m da guia, nunca dentro de entrada de garagem nem de faixa de pedestre (distância mínima 3 m).
- Hidrante: a cada ~90 m, 0,8 m da guia, nunca na frente de entrada de garagem.
- Bueiro de pista: a cada 40 m junto à guia (grade de ferro 0,8×0,4 como decal escuro, Y=+0,005).
- Entrada de garagem (RES): rebaixo da guia de 4,5 m de largura + faixa de concreto da calçada ao lote, sem poste/árvore/hidrante nela.
- Esquina do quarteirão: arco de raio 6 m; no canto fica a rampa de cadeirante dupla (cada lado) e um poste de semáforo ou placa de PARE.
- **Beco de serviço** atrás dos quarteirões do CEN (6 m, no meio de cada quarteirão no sentido leste–oeste) com caçambas, escadas de incêndio e portas de serviço. É só cenário.

## 4.2 Mobiliário urbano (catálogo único; cada item tem modelo, altura, e regra de posição)
| Item | Dimensão | Onde |
|---|---|---|
| Banco de parque | 1,8×0,6×0,9 | calçadas de coletoras do CEN a cada 40 m; parques; orla |
| Lixeira | Ø0,5×0,9 | junto a cada banco, ponto de ônibus, esquinas do CEN |
| Ponto de ônibus (abrigo) | 3,0×1,2×2,4 | avenidas, a cada 400 m, 12 m depois da esquina |
| Caixa de correio azul | 0,6×0,6×1,2 | 1 por esquina de coletora no CEN e Jardim Central |
| Telefone/hidrante/bicicletário | — | CEN e orla |
| Banca de jornal | 2,0×1,5×2,4 | esquinas CEN |
| Placa de rua (blade) | 0,8×0,2 no topo de poste | toda esquina |
| Poste de semáforo | altura 7 m | cruzamentos sinalizados |
| Carrinho de hot-dog / food truck | decoração | Orla e praças |
| Cones/barreira | — | só no Distrito de Serviços (obra) |


---

# PARTE 5 — BAIRROS E AS 17 CASAS DO JOGADOR

## 5.1 Regra das 17 casas (NÃO ALTERE)
- São **exatamente as casas da Cidade 2 (Hds)**, mesmos modelos, mesmos interiores, mesmas caixas (`city2.json` → `plots`). **Não redesenhe a casa. Só desenhe o LOTE em volta (cerca/muro, gramado, calçada de entrada, árvores).**
- Dimensões reais das caixas (largura X × profundidade Z, m, de `plots`): Casa1 8,7×8,7 · Casa2 38,6×22,0 · Casa3 29,3×21,1 · Casa4 23,1×19,0 · Casa5 21,5×16,5 · Casa6 16,4×19,9 · Casa7 18,4×19,4 · Casa8 17,6×8,7 · Casa9 16,4×13,1 · Casa10 17,6×14,4 · Casa11 17,6×15,6 · Casa12 11,5×11,3 · Casa13 17,8×11,7 · Casa14 17,5×14,5 · Casa15 18,0×19,5 · Casa16 16,7×21,7 · Casa17 29,0×34,6. **Leia `plots` de novo e use os números do arquivo se diferirem.**
- **Orientação:** o editor atual não gira casas ("frente para o norte"). Verifique em `Hds.kt`/assets qual lado é a frente real e **sempre** posicione de modo que a frente (porta) dê para a rua. Se a frente for norte, cada lote fica no lado **sul** de uma rua leste-oeste. Escreva a tabela real de frentes em `DECISOES.md`.
- Cada casa vai sobre **platô nivelado** (a altura do piso da casa vem de `Hds`/`city2walk.bin`), com a calçada de entrada concordando em rampa de ≤ 5 % com a calçada da rua (sem degrau maior que 15 cm sem rampa).
- Cada lote precisa de **acesso**: caminho da porta até a calçada, e garagem/entrada de carro para a rua (rebaixo da guia).
- Preço/classe seguem `HdsEstate.kt` (Popular <200 m², Médio <400, Alto padrão <700, Nobre ≥700), todas à venda; a Casa 1 é a inicial (sua).

## 5.2 Distribuição (tabela definitiva)

| Bairro | Classe | SQ / local | Casas | Tipo de rua | Caráter |
|---|---|---|---|---|---|
| **Vila Esperança** | Popular | SQ(0,2) (RES) | **1** (inicial), 12, 8, 13, 9 | locais retas, calçada estreita, postes de madeira com fios, muros baixos de bloco, casas pequenas geminadas decorativas | bairro simples e animado, carros velhos, varais, comércio de esquina |
| **Parque das Flores** | Médio | SQ(0,1) (RES) | 10, 11, 14 | locais retas arborizadas | subúrbio clássico: casas 1–2 pavimentos, cercas de estacas brancas, gramados, balanço, basquete na garagem |
| **Jardim Central** | Médio | SQ(2,0) (RES) | 5, 6, 7 | locais com calçada de tijolo e árvores velhas | sobrados vitorianos/coloniais, varandas, perto da Igreja e da Escola |
| **Recanto do Sul** | Médio-alto, praia | faixa sul da Av. Beira-Mar, oeste (Rua Duna), X 214…1000 | 15, 16, 4 | Rua Duna 15 m paralela ao mar | casas de praia: sobre pilotis decorativos (só nas casas de decoração), deques, passarelas de madeira até a areia |
| **Alto da Colina** | Nobre | SQ(0,0) (ESP, colina) | 3, 2 | ruas curvas em encosta, portão com guarita | condomínio fechado de mansões; muros de pedra, jardins de cipreste, piscinas decorativas, vista |
| **Península Real** | Nobre | leste do rio, X 2470…2700 | 17 | rua privada de 15 m e rotatória | **maior casa (1002 m²)**, doca privada, quadra, gramado enorme, cercada de mansões decorativas |

(5 + 3 + 3 + 3 + 2 + 1 = 17 ✓)

### Localização exata dos lotes das 17 casas
Defina em `plan.py` uma tabela `HOUSE_LOTS[k] = (SQ, bloco, lado, índice)` calculada; margens: frente 6 m, fundo 6 m, laterais 3 m (Alto da Colina e Península: 8 m); o **lote = caixa + margens**. A ordem dos lotes dentro de cada quarteirão é fixa:
- **Vila Esperança SQ(0,2)** (origem X=214, Z=990; quarteirões de 60, ruas de 15; bloco (bx,bz) em (214+75bx, 990+75bz)):
  - Casa 1: bloco (2,2) (X 364…424, Z 1140…1200), lote no **meio do quarteirão da face norte**, ao lado direito de uma rua. **Ao norte dela, Rua Esperança 1 é a rua do jogador.** Em frente, uma pracinha (bloco (2,1)) para o jogador ver desde a porta.
  - Casa 12: bloco (1,2) · Casa 8: bloco (3,2) · Casa 13: bloco (1,3) · Casa 9: bloco (3,3), cada uma no lado voltado para a sua rua; o resto do quarteirão e os demais blocos = casas **decorativas** modestas, mercearia, igrejinha evangélica, campo de pelada, pracinha. Rua com carros mais antigos.
- **Parque das Flores SQ(0,1)** (origem X=214, Z=602): Casa 10 bloco (1,1) · Casa 11 bloco (3,1) · Casa 14 bloco (2,3). Resto: casas decorativas suburbanas, Escola de bairro **não** (a escola é em Jardim Central).
- **Jardim Central SQ(2,0)** (origem X=990, Z=214): Casa 5 bloco (1,1) · Casa 6 bloco (3,1) · Casa 7 bloco (2,3). Resto: sobrados, Escola Primavera (bloco (0,3)+(1,3) unidos), Igreja Matriz (bloco (4,2)), praça (bloco (2,2)).
- **Recanto do Sul**: Rua Duna, eixo Z=1800, de X=214 até X=1000 (T com a Av. Beira-Mar em X=250, 500, 750, 1000). Lotes ao SUL da Rua Duna (Z=1807…): Casa 15 em X 300…336, Casa 16 em X 520…560, Casa 4 em X 740…790 (cada lote 60–65 m de frente por 70 m de fundo até a duna). Entre Beira-Mar (calçada Z=1766) e a Rua Duna (calçada Z=1792): faixa de **dunas + passarelas de madeira** e vagas de estacionamento. Os outros lotes da Rua Duna: casas de praia decorativas coloridas.
- **Alto da Colina SQ(0,0)**: portão de entrada em (X=420, Z=214+14), pórtico de pedra com guarita decorativa e cancela animada. 3 ruas curvas em curvas de nível: **Rua do Mirante** (anel, local), **Alameda dos Ipês** (ramal) e cul-de-sac em Y=+28 com **Casa 2** (a de 850 m², patamar em Y=+26) e **Casa 3** em Y=+17. Mansões decorativas (9) com muros de pedra, torres, garagens triplas.
- **Península Real**: ponte da Foz → rotatória R=26 em (2560, 1740) → rua privada em fundo-de-saco ao norte (Z 1500…1740); **Casa 17** no fim, com platô e doca de 20 m sobre o rio; 6 mansões decorativas de frente para a rua.

## 5.3 Outros tipos de moradia (todos DECORAÇÃO, sem interior)
- **Subúrbio** (Parque das Flores, Jardim Central, Vila Esperança): casas térreo/sobrado em 8 modelos de `house.py`/gerador (telhado de duas águas, de quatro águas, "cottage", "colonial", "craftsman", "ranch", "sobrado de tijolo", "geminada"). Cada lote: garagem para 1–2 carros, caminho, cerca da frente variada (nenhuma / estacas brancas / sebe / alambrado / mureta de tijolo), fundos em madeira, 1–3 árvores, caixa de correio, lixeiras rolantes na calçada em dia de coleta (decor), 1 carro por lote. Nunca duas casas vizinhas iguais (cor de parede, telhado, cerca, árvore, carro).
- **Condomínio Rio Azul** (SQ(4,2), RES): **muro perimetral** de 2,4 m (bege, pilares a cada 6 m, grade de ferro), **2 portarias** (norte e sul) com cancela e guarita, rua interna anel de 15 m, **12 prédios de apartamento de 6–10 andares** (decoração) em 3 fileiras, **piscina decorativa** (acesso bloqueado por cerca de vidro e colisão, o jogador não entra), quadra, churrasqueira, playground, estacionamento com carros. Cada prédio: térreo com hall de vidro fosco (sem interior), 6–10 andares com janelas e varandinhas, platibanda e caixa d'água.
- **Prédios de apartamento** nas avenidas (CEN e Orla): 8–20 andares, fachada de 3 materiais (concreto claro, vidro azulado, tijolinho), varandas com guarda-corpo, térreo comercial.
- **Slots reservados para apartamentos jogáveis futuros (Apt1–3 do kit Hds):** deixe 3 prédios marcados com `buyable_future=true` em `plan.py` (Condomínio Rio Azul B3, Orla Torre Sol, Centro Torre Residencial). Não crie interior agora.

---

# PARTE 6 — O CENTRO (DOWNTOWN) — SQ(2,1), SQ(3,1), SQ(2,2), SQ(3,2)

Centro = 4 superquadras CEN ao redor da **Praça Central** (rotatória em (1364,976)). Quarteirões 75×75, ruas coletoras de 20 m. Origem dos quarteirões: SQ(2,1) = (990,602); SQ(3,1) = (1378,602); SQ(2,2) = (990,990); SQ(3,2) = (1378,990). Bloco (bx,bz): origem = SQ + 95·(bx,bz).

## 6.1 Regras de altura (silhueta de cidade grande)
- A altura cai com a distância à Praça Central `d`: d<120 m → 90–180 m (arranha-céus); 120–260 → 40–90 m; 260–420 → 20–45 m; >420 → 10–25 m. Cada prédio tem **recuo** em degraus (pódio 12–18 m + torre recuada 4–6 m) e coroa (antena, heliponto, coroa iluminada ou topo piramidal).
- Fachadas: 5 famílias — **cortina de vidro** (azul, verde-água, cinza-fumê), **concreto + janelas em fita**, **tijolo vermelho + janelas altas (prédio clássico)**, **pedra/calcário com colunas (banco/tribunal)**, **art déco** (escalonado com faixas verticais claras). Cada fachada = textura 512 px com janelas repetindo a cada 3,6 m × 3,6 m (`Mt.FACADE`), **UV em metros** (nunca esticado), cantos com pilastras.
- Térreo comercial: vitrines altas (4,5 m) com toldos, letreiros de loja (atlas `CitySign`), entrada falsa (porta de vidro com **batente + puxador**, opaca/escura atrás: sem navegação).
- **Beirais e relevo:** cornija 0,5 m, marquise 2 m sobre a calçada nos prédios de esquina (poste de apoio a 0,6 m da guia).
- Prédios **nunca invadem calçada** nem avenida; fundo do prédio encosta no **beco**; empenas laterais cegas recebem pintura (anúncio gigante, mural) de 4 modelos.

## 6.2 Mapa do Centro (cada quarteirão com função e altura)
**SQ(3,1) — Centro Leste (torres)**
| Bloco | Conteúdo |
|---|---|
| (0,3) | **Fórum da Comarca** (profissão Juiz) — ver 9.15; canto NE da Praça Central |
| (1,2) | **Grupo Atlas — SEDE** (profissão Empresário) — **a torre mais alta (172 m / 40 andares)** — ver 9.18 |
| (2,1) | **Nova Tech** (Programador) — torre de vidro curva 18 andares/72 m — ver 9.17 |
| (0,0),(1,0),(2,0),(3,0) | hotéis e torres de escritório 14–30 andares; um com letreiro de cobertura "Hotel Meular" |
| (3,1),(3,2),(3,3) | banco (pedra), torre residencial "Centro Torre Residencial" (reservada p/ apartamento futuro), torre de estacionamento |
| (0,1),(0,2),(1,1),(1,3),(2,2),(2,3) | torres variadas 8–24 andares |
**SQ(2,1) — Centro Norte (escritórios)**
| (1,1) | **Escritório Central** (Secretário) — ver 9.8 |
| (2,1) | **Almeida & Prado** (Advogado) — ver 9.14 |
| (3,3) | **Teatro Municipal** (art déco, marquise luminosa) — canto NW da praça |
| demais | escritórios 8–16 andares, café-calçada, banco, agência de viagens |
**SQ(2,2) — Centro Oeste (cultura/main street)**
| (3,0) | **Museu de História** (pedra, escadaria de 15 degraus, colunas dóricas) — canto SW da praça |
| (2,0),(1,0),(0,0) | **Main Street histórica**: casarões brancos/tijolo de 2–4 andares com toldos, floreiras, bandeiras (ver 4); calçada de tijolo; **Rua Principal = coletora Z=1037…** |
| (0..3,2),(0..3,3) | **Biblioteca Pública** (tijolo + torre de relógio) em (1,2); hotel boutique; restaurantes; **garagem-edifício** aberta (rampas visíveis) em (3,3) |
**SQ(3,2) — Centro Sul (hotéis e prefeitura)**
| (0,0) | **Prefeitura** (Prefeito) — canto SE da praça, ver 9.19 |
| (1,0),(2,0) | **Hotel Grand Meular** 22 andares (letreiro) e **Convention Center** (casca de vidro, 90×60 m, 14 m altura) |
| (0,1),(1,1) | **Aquário Municipal** (turístico; fachada onda azul, tubarão gigante de vidro/estátua na entrada) |
| (2,1),(3,1),(0,2..3),(1..3,2..3) | hotéis, restaurantes, cassino-de-fachada (decor: "Meular Palace"), torres residenciais e comerciais |
- **Quarteirões (3,3) das SQ(2,1) e (3,0) das SQ(2,2) etc. nos cantos da Praça Central:** cortados em arco R=52 (3.4).
- Os quarteirões que não têm uso definido acima: sorteie entre `{torre de escritório, torre residencial, hotel, shopping de rua, banco, estacionamento em prédio, loja de departamentos}` com a regra de altura de 6.1; sem repetir o mesmo modelo de fachada em vizinhos.

## 6.3 Praça da Prefeitura e "Quatro Cantos"
Os quatro quarteirões do entorno da Praça Central (Fórum NE, Prefeitura SE, Museu SW, Teatro NW) têm **frente voltada para o círculo**, escadarias e colunas, bandeiras em mastros de 12 m (3 por prédio: EUA, estado e cidade). A calçada em arco (R=52) é ladrilhada com o piso geométrico (4) e tem 12 bancos, 8 postes clássicos e 24 árvores de rua. Pedestres cruzam o anel por 4 faixas ligando as 4 esquinas à ilha central.


---

# PARTE 7 — ORLA, PRAIA, PARQUE AQUÁTICO, DIVERSÕES, MARINA (linha sul)

Praia é toda a faixa Z>1752. **Pare a linha da Av. Beira-Mar (Z=1752).** A calçada sul da avenida é a **calçadão**.

## 7.1 Calçadão e praia (X 214…2140)
- **Calçadão (promenade)**: largura 12 m (Z 1766…1778), piso geométrico (4), **ciclovia vermelha** de 3 m (Z 1778…1781) separada por faixa de pedra, bancos a cada 30 m virados para o mar, postes de luz a cada 20 m, 60 lixeiras, 8 **bebedouros**, **chuveiros de praia** a cada 100 m, **quiosques** (decor; 4×4 m, teto de palha ou colorido; letreiros "Sorvetes", "Açaí", "Surf Shop", "Hot Dogs") a cada 70 m, **food trucks** a cada 200 m. Palmeiras-reais a cada 18 m em canteiros de 2×2 m no lado do mar.
- **Duna e areia:** duna com capim (Y +1,2) ao longo do calçadão, com **passarelas de madeira** (largura 2,4 m, a cada 120 m) e escadinhas (degraus de 15 cm). Areia clara (textura de ruído suave, sem repetição visível: 2 tiles misturados por máscara). **Sem objetos pontiagudos soltos.** Guarda-sóis (decor, 40 por trecho de 100 m, 6 cores, posição por Poisson-disk com raio mínimo 6 m), cadeiras, redes de vôlei com quadra a cada 200 m (rede 9,5 m, postes de 2,4 m; 2 quadras marcadas com linhas na areia), toalhas, uma **torre de salva-vidas** a cada 250 m (casinha branca/vermelha em pernas de 3 m, bandeirinha).
- **Mar:** shader da `Water.kt` (espuma na beira), costa `Zcosta(X)` (3.3), **bloqueio de profundidade**: jogador só entra até Y=−1,1 (ver `Relevo.wet`); mais fundo = barreira invisível + boias com corda (linha de boias a 60 m da costa).
- **Píer da Orla Central**: sai da Praça da Orla (SQ(2,3)) em X=1170, de Z=1780 até Z=1960 (largura 8 m, deck de madeira Y=+1,8 sobre estacas de 0,35 m a cada 4 m, vigas visíveis embaixo, corrimão baixo). No fim, plataforma 24×24 m com **restaurante decorativo** ("Pier 21", telhado de duas águas, varanda, sem interior), **luneta turística**, bancos e pescadores (decor). Escada de acesso ao mar nas laterais.
- **Farol** (no molhe de pedra da foz do rio, centro X=2330, Z=1840, ligado ao calçadão por passarela de 6 m): torre cônica listrada vermelho/branco 34 m, galeria, lanterna que **gira com um feixe de luz** (decoração), casinha do faroleiro, cerca de pedra, trilha de cascalho, **cais de pedra** com **rochas** (cluster de 10 rochas) quebrando ondas.
- **Marina** (SQ(1,3)): 2 molhes de 120 m, 40 vagas, **barcos e veleiros decorativos** (12 modelos), **Clube Náutico** (2 andares, varanda, bandeiras), galpão de reparo, guindaste, boias, postes de cais, restaurante "Dock 5" (decor).
- **Hotéis de orla (SQ(2,3), norte da avenida na face Z=1364…1738)**: 6 hotéis/condomínios de 12–20 andares com piscinas no pódio, letreiros luminosos, lojas de surf no térreo; **Torre Sol** (reserva de apartamento futuro).
- **Praça da Orla**: quarteirão 120×120 em SQ(2,3), com **anfiteatro** (arquibancada de concreto, palco), **fonte seca** (jatos), pista de skate (decor) e **mural** de 20 m.

## 7.2 Parque Aquático "Splash Meular" (SQ(3,3), 360×360)
Tudo é decoração com **água rasa decorativa** (sem nado). Se o motor de piscina (`Pool.kt`) permitir mergulho, **marque como proibido** (cerca/guarda-corpo, colisão): só as 17 casas têm piscina jogável.
- **Entrada**: bilheteria (fachada tropical 20×10 m com letreiro 3D "SPLASH MEULAR", mascote golfinho de 5 m), catracas, portão em arco azul de 8 m, estacionamento em frente 120×80 m (linhas, 180 vagas, 40 carros, árvores em ilhas de 4×4 m a cada 6 vagas, 2 pontos de ônibus).
- **Muro perimetral** de 2,4 m (colorido), cinturão de palmeiras.
- **Layout interno (SQ(3,3) ocupa X 1378…1738, Z 1378…1738; entrada pelo lado sul, voltada para a Av. Beira-Mar, estacionamento ao sul da bilheteria)**:
  - **Piscina de ondas** 70×40 m (profundidade 0,3…1,5 m decor) no centro-sul, praia de areia de 10 m, guarda-sóis, guarda-vidas;
  - **Rio lento** (anel de 4 m de largura, 160 m de perímetro) circulando o parque, com boias redondas;
  - **Torre de toboáguas** (4 torres: 14, 18, 22, 26 m; 8 tubos coloridos; azul, verde, laranja, roxo; tubos em curvas de raio mínimo 3 m, suportes de aço a cada 6 m);
  - **Cachoeira + piscina infantil** com **castelo de jatos** e baldes basculantes gigantes (animação `dyn`);
  - **Área de lanchonete** (cobertura 40×20 m, mesas decor, 6 barracas), **vestiários** (2 blocos 18×10 m), **cabanas** alugáveis (decor) e **hidromassagens**.
- Cores: turquesa `#16C8D8`, laranja `#FF8A1F`, amarelo `#FFD23F`, rosa `#FF5C8A`, verde-lima `#8BD24A`. Água: mesmo shader da piscina (translúcida, 70 % alfa).

## 7.3 Parque de Diversões "Meular Fun Pier" (SQ(4,3): X 1766…2126, Z 1378…1738)
Decorativo; use `CityFun.kt` como base dos brinquedos animados (`dyn`).
- **Portal de entrada** com letreiro luminoso, bilheteria, 120 m de fila em corredores de estacas.
- **Roda-gigante** 48 m (diâmetro 44 m, 20 cabines coloridas, base de aço, **gira 0,5 rpm**), no **eixo X=1960, Z=1540** (centro do parque).
- **Montanha-russa** de aço: trilho em laço duplo, **trem animado de 5 vagões** (`dyn`, percurso fechado de 520 m, altura máx. 32 m, apoio a cada 8 m), estação cobertas, sem passageiro jogável.
- **Carrossel** (Ø 16 m, telhado listrado, 24 cavalos que sobem e descem), **barco pirata** (pêndulo de 10 m), **torre de queda** 38 m, **carrinhos bate-bate** (tenda 24×30 m), **trem-fantasma** (fachada de caveira 12 m), **tiro ao alvo**, barracas de algodão-doce, maçã do amor, pipoca (6), jogos de argola.
- **Chão:** asfalto-claro e calçamento colorido em padrão; canteiros de flores; **lago pequeno com chafariz**; estátuas; fogos de artifício decorativos (partículas, 1 ×/60 s).
- Cercado por muro/grade de 2,4 m com 2 entradas (Av. do Rio, Av. Beira-Mar).


---

# PARTE 8 — PRAÇAS, PARQUES E PONTOS TURÍSTICOS

## 8.1 Praça Central (a rotatória-praça, (1364,976))
- Anel de asfalto de 16 m (2 faixas), R externo 48 → ilha interna R = 32 com **meio-fio duplo**: guia + faixa de calçada de 3 m em volta (R 29…32) piso geométrico; a ilha é um **jardim circular** pisável por 4 caminhos radiais de 3 m (N, S, L, O) com faixa de pedestre em cada acesso.
- Centro: **chafariz de 3 níveis** (bacia Ø14 m, 0,9 m; bacia média Ø8 m; taça Ø3 m com jato de 5 m animado — partículas/`dyn`) e, no meio, uma **estátua de bronze** (soldado/fundador) de 4 m sobre pedestal de granito de 3 m. 4 bancos de pedra, 12 postes clássicos em círculo, 4 canteiros de flores em anel (tulipas, margaridas, lavanda), 8 carvalhos grandes, bandeiras (3 mastros de 10 m).
- À noite: iluminação quente no chafariz e nos postes.

## 8.2 Parque das Flores (SQ(1,1), ESP, 360×360)
Parque central de cidade. **Contorno: calçada contínua de 3 m + grade baixa de ferro com 10 portões**.
- **Lago** (forma irregular, ~120×80 m, borda de pedra e junco), **ilhota** com salgueiro e **ponte de madeira em arco** (Y +1,2; 3 m de largura, guarda-corpo); **cisnes/patos decor**; deck de pesca.
- **Alamedas**: anel de 4 m de largura (cascalho claro), 2 diagonais de 3 m cruzando em um **coreto** hexagonal (Ø 10 m, telhado de cobre verde, 8 colunas, bancos internos); alamedas levam às 10 entradas.
- **Jardim de flores formal** 60×40 m (canteiros em losango com 5 espécies, sebes aparadas 0,6 m, fonte pequena), **estufa de vidro** 20×12 m (decor, só fachada), **playground** com 10 brinquedos (escorregador, balanço, gangorra, trepa-trepa, caixa de areia), **academia ao ar livre**, **quadra de basquete** (marcação, 2 tabelas) e **campo de futebol** (72×46 m, traves, grama listrada), pista de caminhada de 1,6 km, **mesas de piquenique** sob árvores, **food truck**.
- **Bosque**: 160 árvores em 3 espécies + sub-bosque (arbustos) em manchas (ruído de Poisson), nenhuma árvore a < 2 m de alameda ou ponte.

## 8.3 Parque do Mirante (SQ(1,0), colina)
Trilhas serpenteantes em curva de nível, **mirante** circular de pedra e madeira no topo (Y +22 m, Ø 12 m, guarda-corpo, 6 lunetas), **reservatório d'água** (tanque cilíndrico branco 18 m com letreiro "Meular"), **estacionamento** no sopé (60 vagas), grande **gramado de piquenique**, **bosque de pinheiros**.

## 8.4 Jardim Central — Igreja e praça
**Igreja Matriz**: nave branca de madeira/estuque com **campanário de 38 m** e agulha, portal duplo, vitrais coloridos decor, adro com gramado, cemitério pequeno (decor, 40 lápides) atrás; **praça** com coreto pequeno, **bancos** de ferro, fonte e estátua; **calçada de tijolo**; sino que **toca na hora cheia** (som; opcional).

## 8.5 Arena Meular (SQ(4,0), ESP)
**Estádio** oval 190×160 m, 28 m de altura, **arquibancadas** em 3 anéis (cores por setor), **telhado em anel** com treliças, 4 torres de luz (50 m), **gramado de campo** (105×68, listras, linhas, 2 gols), pista de atletismo; entradas por 8 portões com **catracas** (decor). Estacionamento 2 × (160×80 m) com 250 vagas e 70 carros; **tendas** e vendedores; **bilheterias**; letreiro no pórtico.

## 8.6 Distrito Médico
Hospital + Clínica (profissões 9.12, 9.13), **estacionamento coberto**, **heliponto**, **ambulâncias** decor, **farmácia 24h** de fachada, **laboratório**, **lanchonete** e jardim de cura.

## 8.7 Outros pontos turísticos (cartões no mapa, ícone de câmera)
1 Portal da Cidade (arco) · 2 Chafariz da Praça Central · 3 Mirante · 4 Farol · 5 Píer · 6 Roda-gigante · 7 Aquário · 8 Ponte Real (arco branco) · 9 Igreja Matriz · 10 Museu · 11 Estádio · 12 Parque Aquático · 13 Letreiro "Meular" no morro: letras brancas de 12 m em X 380…520, Z 470, na encosta do Alto da Colina (estilo Hollywood, texto "MEULAR").
Cada um aparece no mapa/GPS com nome, e no GPS como destino.

## 8.8 Outros equipamentos
**Escolas** (além da Primavera): colégio municipal em Vila Esperança (decor); **Faculdade** (SQ(1,2), bloco (0,0),(0,1): campus em tijolo, biblioteca, gramado, 4 prédios de 3 andares); **Correios**, **Corpo de Bombeiros** sim (profissão), **Posto** (profissão), **mercearias**, **padaria**, **farmácias**, **academia** (decor), **cinema** (SQ(4,1) Shopping), **bancos**.

## 8.9 Shopping + SuperBom (SQ(4,1), CEN adaptado)
- **Meular Mall**: caixa 160×120×12 m com **fachada em módulos coloridos**, entrada de vidro duplo com pórtico, **letreiros de 40 marcas fictícias** (use `CitySign`), cinema com cartazes, praça de alimentação (decor), **estacionamento** a norte e sul (2×(190×60) m, 600 vagas).
- **SuperBom** (profissão Repositor): ver 9.6, na esquina NE da SQ(4,1), com **estacionamento 70×36 m** e **carrinhos de compras** (decor).


---

# PARTE 9 — OS 19 EDIFÍCIOS DE PROFISSÃO (por fora e por dentro)

Nomes, letreiros e ids vêm de `Jobs.kt` (**não renomeie**). Cada prédio existe **uma vez** no mapa. As posições abaixo usam a fórmula de bloco (2.2). Cada prédio é um objeto `JOB[id]` em `plan.py` com: `footprint (x0,z0,x1,z1)`, `floors`, `door = (x,z,face)`, `station = ponto onde o jogador "trabalha"`, `sign`, `interior_spec`.

## 9.0 Regras comuns a TODOS os prédios de profissão
**Por fora**
- Fachada com **porta principal** (batente + folha, 1,1×2,2 m) no centro da frente, **degrau ou rampa** de ≤ 15 cm conectando à calçada com **rampa de cadeirante**, **capacho**, **luminária de parede**, **letreiro** (estilo/atlas `CitySign`) com o texto exato de `Jobs.sign`, **número da casa** e **vitrine/janelas** reais (vidro translúcido que mostra o interior de fato, por ser navegável).
- Fundos/laterais: saída de emergência (porta cinza + placa EXIT), ar-condicionado no telhado ou na lateral, calha, tubulação, lixeiras, **luz de segurança**, cerca ou muro de separação do vizinho (3 m de recuo mínimo).
- Telhado/teto: **some quando o jogador está dentro** (mecanismo `Hds`/`City.setInside` já existente) e volta quando sai.
- Estacionamento ou vagas na rua, 2–6 carros decor + 1 veículo temático (ver cada prédio).
**Por dentro**
- Piso em `City.FLOOR`; pé-direito 3,0 m (térreo) / 3,4 m em hall; **porta → corredor livre de 1,4 m até o primeiro ambiente**; nada encostado na porta; móveis de parede virados para dentro; **rodapé nas 4 paredes**, faixa de cor do nível (verde 1, azul 2, vermelho 3, dourado 4 — como `JobRooms.finish`), saída de emergência, extintor, capacho, luminárias de teto em grade de 3,4×3,2 m que não cruzam paredes.
- Paredes: **colisão pela geometria real** (grade de 25 cm, retângulos mesclados), com **vãos de porta de 1,0 m livres e arestas arredondadas em 15 cm** (padding `Hds.PAD`).
- **Só use móveis que existem no catálogo `mobilia.json`** (id + categoria) e os de `JobFurn.kt`. Se faltar um móvel específico, use o mais parecido e anote em `DECISOES.md`.
- **Estação de trabalho (`station`)**: marcador de 1,2 m de diâmetro (círculo luminoso suave) no ponto indicado em cada prédio: ali começa o turno.
- Se o prédio já tem interior em `JobRooms.kt`, **mantenha esse interior** (móveis e proporções) e só ajuste paredes/porta/dimensões para encaixar na nova casca; se não encaixar, reescreva o interior como especificado abaixo.
- Prédios altos (≥ 4 andares): **só o térreo e UM andar acima são navegáveis** (escada de 1,2 m de largura, 17 cm por degrau, 18 degraus por 3,4 m, com patamar), elevador só decorativo (porta fechada). Os outros andares são fachada, com janelas e **cortinas/persianas** atrás do vidro para não mostrar o vazio.

## NÍVEL 1 — COMEÇO (6)

### 9.1 DIARISTA — "Brilho Limpeza" — letreiro `LIMPEZA BRILHO`
- **Local:** SQ(0,2) bloco (0,0): **X 214…274, Z 990…1050**, pegando o canto da Av. Oeste × Av. Central, a 6 m das duas calçadas; porta na face leste.
- **Fora:** térreo 14×10 m, 3,2 m, reboco **branco com faixa turquesa**, toldo turquesa-branco, vitrine com cartaz de balde/espuma, **van da empresa** (turquesa, logotipo) parada na vaga lateral, bicicleta com carrinho.
- **Dentro (14×10):** recepção 4×4 com balcão + 2 cadeiras + sofá + planta; sala de treino 5×5 com mesa de demonstração e quadro; depósito 5×4 com **prateleiras de metal com produtos (`Mt.GOODS`)** e **carrinhos de limpeza**; banheiro 2×2. `station` = balcão da recepção (u: centro, v: 1,6 m).

### 9.2 LIXEIRO — "Central de Coleta" — `CENTRAL DE COLETA`
- **Local:** faixa de serviços: **X 300…384, Z 140…184**, frente para a **Rua de Serviço (Z=130)**.
- **Fora:** galpão metálico 30×16 m (verde-escuro, pé-direito 7 m, telhado de duas águas), **portão basculante 6 m** de 2 folhas, escritório anexo 10×8 m, **pátio cercado 40×30 m** (alambrado 2,4 m) com **3 caminhões de lixo** (verde, animados em fila), **caçambas** coloridas (azul=papel, amarelo=metal, verde=vidro, vermelho=plástico), pilha de pallets.
- **Dentro do escritório (10×8):** recepção 4×3 (balcão), sala de escala 4×4 com quadro de rotas, mesa e 4 cadeiras, vestiário 3×2 com **armários**, banheiro 2×2. O galpão 30×16 tem **bancada de triagem**, esteira (decor), prateleira de EPI e balança, para o turno. `station` = quadro de escala.

### 9.3 ATENDENTE — "Lanchonete do Zé" — `LANCHONETE`
- **Local:** SQ(0,2) bloco (3,0): **X 439…499, Z 990…1050**, lado oeste da Av. Central × Rua Esperança (esquina).
- **Fora:** térreo 14×9 m, **tijolo aparente + faixa vermelha e amarela**, toldo vermelho-branco listrado, **letreiro luminoso "LANCHONETE"** + "Zé" em neon, **cardápio em quadro-negro** na porta, mesinhas de calçada (4) com guarda-sol, **placa de promoção** pintada à mão.
- **Dentro (14×9):** balcão em L 6 m com caixa, chapa/fritadeira/geladeira, **8 mesas de 4 lugares**, vitrine de salgados, sorveteria (freezer), banheiro 2×2, depósito 3×3. `station` = atrás do balcão.

### 9.4 ENTREGADOR — "Expresso Já" — `CENTRAL DE ENTREGAS`
- **Local:** faixa de serviços: **X 420…500, Z 140…184**.
- **Fora:** galpão 26×14 m (cinza e **laranja**), 2 portões de carga 3,2×3,5 m, **plataforma de carga** (altura 1,2 m) com 2 baías, **vans e 4 motos** (laranja com baú) paradas, bicicletário, painel LED "Expresso Já".
- **Dentro (26×14):** recepção 5×4, **esteira de triagem** (10 m, decor), **estantes de pacotes** (caixas de papelão), balança, mesa de despacho com 3 computadores, vestiário/armários, banheiro, mapa gigante da cidade na parede. `station` = mesa de despacho.

### 9.5 FRENTISTA — "Posto Rota Sul" — `POSTO`
- **Local:** SQ(0,2) bloco (4,4): **X 514…574, Z 1290…1350** (canto SE da Vila Esperança, cruzamento sinalizado de Av. das Flores × Av. do Sul).
- **Fora:** **cobertura** 24×14 m, 4,8 m de altura, 4 colunas, 2 ilhas com **4 bombas** (2 por ilha, mangueiras, display), **totem de preços** alto (6 m) na esquina, **loja de conveniência** 12×8 m, lava-rápido (decor), calibrador, ar/água, lixeiras, **2 carros** abastecendo. Entradas/saídas de veículos 8 m, rebaixo de guia (sem poste/hidrante).
- **Dentro (12×8):** caixa com balcão e **expositor de cigarro/doces**, **geladeira de bebidas**, 3 gôndolas com produtos (`Mt.GOODS`), **cafeteira**, banheiro, depósito. `station` = caixa. Na ilha: `station2` = bomba 1.

### 9.6 REPOSITOR — "SuperBom" — `SUPERMERCADO`
- **Local:** SQ(4,1) bloco (3,0): **X 2051…2126, Z 602…677**; estacionamento 70×36 m ao sul.
- **Fora:** 56×34 m, 7 m de altura, platibanda com **faixa vermelha e branca**, **letreiro de 10 m**, entrada de **portas automáticas duplas** (6 m) com cobertura, **carrinhos** enfileirados, caixas de gás/pallets, **docas** nos fundos.
- **Dentro (56×34):** **12 gôndolas** de 10 m em 4 fileiras (corredores de 3 m, rótulos de setor pendurados), **6 caixas** (esteiras + caixa registradora + sacolas), **seção de hortifrúti** (caixotes), **açougue/frios** (balcões refrigerados), **padaria**, **freezers** em L, estoque 16×10 com **paletes empilhados** e empilhadeira (decor), banheiros. `station` = ponta de gôndola 3.

## NÍVEL 2 — TÉCNICO (6)

### 9.7 PROFESSOR — "Escola Primavera" — `ESCOLA`
- **Local:** SQ(2,0) blocos (0,3)+(1,3) fundidos: **X 990…1160, Z 499…574**, porta na face sul, voltada para a Av. dos Jardins (Z=588).
- **Fora:** prédio em U, **tijolo claro + telhado verde**, 90×24 m, 2 andares, **torre do relógio** 14 m, **pátio** (quadra poliesportiva marcada, 2 tabelas, 2 traves), **ônibus escolar** (amarelo, 2), **jardim**, 80 árvores jovens, grade de 1,8 m. **Zona escolar:** placa amarela, faixa elevada.
- **Dentro (térreo e 1 andar):** **hall de 10×8** com troféus, secretaria 6×5, **6 salas de aula de 9×7** (cada com 20 carteiras, mesa do professor, **quadro-negro + giz**, mapa e cartazes), **biblioteca** 12×8, **refeitório** 14×9, **ginásio** 22×14 (quadra interna), 2 banheiros. `station` = mesa do professor da sala 1.

### 9.8 SECRETÁRIO — "Escritório Central" — `ESCRITÓRIOS`
- **Local:** SQ(2,1) bloco (1,1): **X 1085…1160, Z 697…772**, torre.
- **Fora:** **torre 12 andares / 48 m**, pódio 36×28, cortina de vidro azul, **hall com porta giratória 3 m** + toldo, **letreiros** no topo ("Escritório Central").
- **Dentro:** térreo = **lobby 18×12** (recepção, 2 sofás, painel de diretório, 4 catracas decor); 1º andar navegável = **open-space 34×24**: **18 estações** (mesa + cadeira + PC), 3 salas de reunião de vidro 6×5, copa 6×4, impressoras, arquivo. `station` = estação 1.

### 9.9 POLICIAL — "Delegacia" — `POLÍCIA`
- **Local:** SQ(1,2) bloco (1,1): **X 697…772, Z 1085…1160**.
- **Fora:** **tijolo cinza + vidro azul**, 2 andares, 40×26 m, **estrelinha dourada** no frontão, **bandeiras** (3), **globos azuis** ao lado da porta, **4 viaturas** (azul/branco) no estacionamento lateral, pórtico de **garagem** 2 vagas, mastro.
- **Dentro:** **recepção 10×6** (balcão alto, ficha), **área de trabalho 16×12** (8 mesas, quadro de procurados), **2 celas de 3×3** com grades, **sala de interrogatório 4×4** com espelho, armeiro (cofre), vestiário, sala do delegado 5×5, copa. `station` = balcão da recepção.

### 9.10 BOMBEIRO — "Quartel dos Bombeiros" — `BOMBEIROS`
- **Local:** SQ(1,2) bloco (3,1): **X 887…962, Z 1085…1160**.
- **Fora:** 48×26 m, tijolo vermelho + **3 portões de garagem** 4,2×4,6 m (vermelhos, abrindo para cima), **torre de treinamento** 18 m, **mangueira** pendurada, **caminhão de bombeiros** (2) estacionado na frente com escada, **sirene** no telhado, **hidrante** vermelho.
- **Dentro:** **garagem 30×16** com os 2 caminhões **dentro**, rack de mangueiras, bancada de equipamento; dormitório 14×8 (8 beliches); cozinha/refeitório 12×7; sala de TV; **mastro de descida** (decor) 3,4 m; vestiário. `station` = painel de comando.

### 9.11 MECÂNICO — "Oficina do Toninho" — `OFICINA`
- **Local:** SQ(1,2) bloco (0,3): **X 602…677, Z 1275…1350**.
- **Fora:** galpão 22×16 m, **portão de enrolar** 5 m (cinza), parede com **letras pintadas "TONINHO"**, **pneus empilhados** (torre de 3 m), **carro velho sobre blocos**, **reboque**, caçamba de óleo, cercado de ferro-velho 20×20 (decor).
- **Dentro:** **2 elevadores de carro** (hidráulicos, com carro erguido), **bancada de ferramentas** (parede com contornos de ferramentas), **compressor**, **estante de peças**, escritório 5×4 com balcão e caixa registradora, banheiro, vestiário. `station` = bancada.

### 9.12 ENFERMEIRO — "Clínica Aurora" — `CLÍNICA`
- **Local:** SQ(3,0) bloco (0,1): **X 1378…1453, Z 309…384**.
- **Fora:** 2 andares, 38×24 m, **fachada lisa branca + faixa verde-água**, **toldo de entrada** com cruz verde, **rampa de ambulância**, **jardim terapêutico**, 20 vagas.
- **Dentro:** **recepção 10×6** com guichê e 20 cadeiras de espera + **TV**, triagem 4×4 (balança e régua), **4 consultórios 5×4** (maca, escrivaninha, pia, armário de remédios), **sala de curativos 5×5**, **sala de vacinas 4×4**, farmácia 5×4, 2 banheiros PCD. `station` = balcão de triagem.

## NÍVEL 3 — FACULDADE (5)

### 9.13 MÉDICO — "Hospital Santa Clara" — `HOSPITAL`
- **Local:** SQ(3,0) blocos (1,1),(2,1),(1,2),(2,2) fundidos (ruas internas fechadas): **X 1473…1643, Z 309…479**.
- **Fora:** **bloco central de 6 andares 90×36 m** (concreto claro, janelas em fita, **cruz vermelha** luminosa de 5 m no topo), **ala de pronto-socorro** 40×20 (1 andar) com **rampa de ambulância coberta**, **heliponto** no teto (H amarelo, luzes), estacionamento 260 vagas, **jardim**, **ambulâncias** (3), geradores, **farmácia 24h**.
- **Dentro (térreo + 2º andar):** **saguão 24×14** (balcão duplo, 24 cadeiras, TV), **PS** com **8 macas** em baias com cortinas, **sala de raio-X**, **centro cirúrgico** 12×10 (mesa, luzes, monitores), **UTI 14×10** (6 leitos), **enfermaria 20×10** (12 leitos), consultórios (6), laboratório, farmácia interna, lanchonete, capela. `station` = balcão do PS; `station2` = sala cirúrgica.

### 9.14 ADVOGADO — "Almeida & Prado" — `ADVOCACIA`
- **Local:** SQ(2,1) bloco (2,1): **X 1180…1255, Z 697…772**.
- **Fora:** 8 andares/34 m, **pedra e vidro bronze**, colunas de entrada, **placa de bronze "ALMEIDA & PRADO — Advogados"**, **balança da justiça** decor.
- **Dentro:** lobby 12×10 com recepção em madeira; 1º andar navegável: **sala de reunião grande** 10×6 (mesa de 12 lugares), **2 salas de sócios** 6×5 (estantes de livros, poltrona), 6 baias, arquivo, copa. `station` = mesa dos sócios.

### 9.15 JUIZ — "Fórum da Comarca" — `FÓRUM`
- **Local:** SQ(3,1) bloco (0,3): **X 1378…1453, Z 887…962** (canto NE da Praça Central).
- **Fora:** **neoclássico**: escadaria de 18 degraus, **6 colunas coríntias** de 9 m, frontão triangular com relevo, cúpula baixa, 3 andares, 60×40 m, **bandeiras** (3), **estátua de Têmis**.
- **Dentro:** **hall 16×12** com piso xadrez, **sala de audiências 16×12** (bancada do juiz elevada 0,6 m, 2 mesas, **galeria com 40 bancos**, box de testemunha, bandeira), gabinete do juiz 6×5, cartório 10×8, arquivo, 2 celas de espera 3×3. `station` = bancada do juiz.

### 9.16 ENGENHEIRO — "Pilar Construtora" — `CONSTRUTORA`
- **Local:** faixa de serviços **X 1100…1180, Z 140…184**.
- **Fora:** **escritório 18×12 m** 2 andares (concreto e **tapume amarelo**) + **canteiro de obra cercado 50×40 m** com **guindaste** (altura 30 m, braço de 28 m, **gira devagar**), **betoneira**, pilha de **vergalhões, blocos e areia**, 2 **caminhões basculantes**, contêineres de escritório.
- **Dentro do escritório:** recepção, **sala de projetos 12×8** (3 pranchetas grandes, maquete 1,5×1 m, plantas na parede), **sala de reunião**, copa, banheiro. `station` = prancheta 1.

## NÍVEL 4 — TOPO (3)

### 9.17 PROGRAMADOR — "Nova Tech" — `TECNOLOGIA`
- **Local:** SQ(3,1) bloco (2,1): **X 1568…1643, Z 697…772**.
- **Fora:** torre curva de **vidro espelhado** 18 andares / 72 m, topo com **painel LED**, jardim vertical, **bicicletário**, **carros elétricos** (Tesla do jogo) em carregadores.
- **Dentro:** lobby 14×12 com **parede de LED** e sofás; 1º andar navegável: **open-space 30×22** com **20 estações com 2 monitores** + sofás, **sala de servidores** de vidro (racks), **sala de reuniões**, **copa com pufes e pebolim**. `station` = estação 1.

### 9.18 EMPRESÁRIO — "Grupo Atlas" — `SEDE`
- **Local:** SQ(3,1) bloco (1,2): **X 1473…1548, Z 792…867**, no cruzamento com a Praça Central.
- **Fora:** **torre mais alta da cidade: 172 m / 40 andares**, pódio de 4 andares, **coroa dourada iluminada** à noite, **chafariz** no jardim da entrada, **esfera** de aço de 3 m na calçada, **limusine** estacionada.
- **Dentro:** **lobby 20×16** com piso de mármore, **recepção em curva**, lustre; 1º andar navegável = **diretoria**: **gabinete do presidente 12×10** (mesa de 3 m, sofá, bar, estante, vista), **sala do conselho 14×8** (mesa de 16 lugares), 4 salas de diretores, assistentes. `station` = mesa do presidente.

### 9.19 PREFEITO — "Prefeitura" — `PREFEITURA`
- **Local:** SQ(3,2) bloco (0,0): **X 1378…1453, Z 990…1065** (canto SE da Praça Central).
- **Fora:** **georgiano/colonial** de tijolo + pedra branca, 3 andares, 64×34 m, **torre central** com **relógio** (22 m) e cúpula, escadaria com corrimão, **bandeiras** (3 mastros de 12 m), **brasão** em relevo, jardim formal com sebe, **placa "Prefeitura de Meular"**.
- **Dentro:** **hall 18×14** com **brasão no piso**, **plenário 20×14** (bancos em semicírculo, mesa do prefeito, tribuna), **gabinete do prefeito 10×8**, sala de reunião 8×6, **protocolo** 10×6 (balcões, senha), arquivo. `station` = gabinete.


---

# PARTE 10 — EDIFÍCIOS DECORATIVOS (TODO O RESTO) — REGRAS DE FACHADA

Decoração = **casca**: 4 fachadas completas + telhado + calçada de entrada. **Nada de interior, nem móvel, nem escada, nem sala.** Vidros: **opacos escuros** (textura de vidro com reflexo falso e cortina/persiana atrás) ou **quadro de cartaz** (lojas). Portas: desenhadas e **bloqueadas por colisão**.
- Toda fachada tem **3 camadas**: base (térreo 4,5 m), corpo (repetição de módulo 3,6 m), coroa (cornija/platibanda).
- Lojas de rua: letreiro luminoso (atlas), toldo, vitrine com cartaz, número, ar-condicionado em cima, **tubulação lateral** e **escada de incêndio** nos fundos (mostra do beco).
- Catálogo de **tipos de fachada decorativa** (todos parametrizados por largura, altura, cor): `loja_vitrine`, `loja_toldo`, `cafe_calcada`, `banco_pedra`, `farmacia_cruz`, `padaria`, `barbearia` (poste listrado), `pizzaria`, `torre_vidro`, `torre_concreto`, `torre_deco`, `predio_tijolo`, `predio_apt_varandas`, `armazem`, `galpao_industrial`, `igreja_pequena`, `casa_colonial`, `casa_craftsman`, `casa_ranch`, `casa_cottage`, `casa_praia`, `mansao_pedra`, `sobrado_geminado`, `hotel_letreiro`, `estacionamento_predio`.
- **Variação obrigatória:** vizinhos nunca repetem o mesmo tipo+cor. Use paleta por bairro (5 cores de parede, 3 de telhado, 4 de porta/veneziana) e um sorteio com semente `hash(lote)`.
- **Empenas (paredes laterais cegas)** visíveis: textura de tijolo com **mural/anúncio pintado** (4 modelos) ou janelas falsas.
- **Telhados**: casas 2 águas/4 águas 30°–38° com beiral 0,5 m, calha e rufo; prédios com platibanda 0,8 m, caixa d'água, ar-condicionado, antena.
- **Limites:** nenhum prédio cruza lote, rua ou calçada; mínimo 3 m de recuo lateral em RES, 0 m (parede colada) no CEN, 6 m de frente em RES, 0 m no CEN.

---

# PARTE 11 — VEGETAÇÃO, VEÍCULOS, PESSOAS, LUZ, SINALIZAÇÃO

## 11.1 Árvores (regras de plantio)
- **Espécies** (use `Flora.kt` e os modelos Hds: `oak_a`, `oak_b`, `cherry_a`, `pine_a`, palmeira de `CityFun`): carvalho, bordo (3 paletas), cerejeira, pinheiro, palmeira-real (orla), jacarandá. Escala 0,8–1,3, rotação aleatória, tom de verde ±8 %.
- **Rua de bairro (RES):** 1 árvore a cada 12 m na faixa-jardim, deslocada 3 m da entrada de garagem, 6 m de esquina e 4 m de poste/hidrante.
- **Avenida:** canteiro central com árvores a cada 12 m, copa 6–8 m, ou **palmeiras-imperiais a cada 10 m** na Av. Beira-Mar e Av. Central; a distância mínima do eixo do poste é 3 m.
- **Lote RES:** 1–3 árvores (frente e fundos) a ≥ 4 m da casa e ≥ 2 m da cerca; **nunca dentro de piscina, garagem, passeio ou cerca**.
- **Parques e colinas:** Poisson-disk com raio mínimo 5 m (bosque), 8 m (parque).
- **Proibido:** árvore sobre asfalto, calçada (fora do canteiro), água, prédio ou rampa (validador).
- **Memória:** só **uma versão leve** de cada árvore (≈1,2 mil triângulos); o modelo Hds completo (~7 mil vértices) só até 120 m do jogador, como `Relevo.service`. Orçamento total: ≤ 9 mil árvores no mapa; ≤ 1,2 mil modelos pesados ao mesmo tempo ≤ 260 m.
- Arbustos, flores, trepadeiras (parede de tijolo da referência), vasos nas portas.

## 11.2 Trânsito e pedestres (decoração animada, leve)
- **Carros** em movimento só nas avenidas e coletoras do **Centro e Beira-Mar** (3–5 por faixa em grupo), **param nos semáforos** (ciclo 28 s: verde 12 / âmbar 3 / vermelho 13 em cada eixo), **dão preferência ao jogador** e **desaparecem a 140 m**. 14 modelos (sedã, SUV, picape, van, táxi amarelo, ônibus, viatura, ambulância, caminhão de lixo, moto), 8 cores. **Estacionados** (decor): 1 a cada 12 m em 40 % das vagas, **alinhados à guia (0,3 m)**, paralelos, sem passar por entrada de garagem nem hidrante.
- **Ônibus** urbano (verde-azul "Meular Bus", 12 m) em loop nas avenidas, paradas nos pontos (decor).
- **Pedestres** (`Mob.kt`): 80 no Centro, 40 no Calçadão, 20 por bairro, andando só em **calçadas e faixas de pedestre**, respeitando semáforo, sumindo a 55 m. Sem pedestre em lugar sem calçada.

## 11.3 Iluminação
- **Postes de luz:** avenida 2 lados a cada 34 m (altura 9 m, 2 braços) / coletora 1 lado alternado a cada 34 m (altura 7 m) / local 1 lado a cada 40 m (poste de madeira + luminária de 7 m) / clássico (Centro histórico, parques, calçadão): haste preta com lanterna, 4,5 m a cada 20 m. Luz acende à noite (o `Sky.kt`/`Shade.kt` já tem ciclo?). Se não houver, deixe **materiais emissivos** ligados por `night` boolean.
- Letreiros iluminados, faróis de carro, semáforos, janelas de prédios acesas (30 % por andar, sorteio estável).

## 11.4 Sinalização e texto (use `CitySign.kt` + atlas)
- Placa de rua: **verde**, texto branco ("Av. Central", "Rua Esperança"), no poste e no braço do semáforo; **nomes** da tabela 2.2 mais: ruas locais nomeadas por plantas/árvores (`Rua dos Ipês`, `Rua das Acácias`, `Rua Maple`), sempre únicas.
- **Placas de trânsito** (retângulo 0,6×0,75 m, refletivo): PARE (octogonal), Dê a Preferência, **Velocidade 25/35/45 mph**, **Proibido virar à esquerda**, **Zona escolar**, **Pedestre**, **Sentido**, **Rotatória à frente**, **Hospital**, **Parque**, **Praia**, **Estacionamento**; **placas de saída** verdes em pórtico sobre a rodovia.
- **Número de lote** em cada casa (placa pequena na caixa de correio).
- **Mapa/GPS:** todos os nomes acima viram marcadores; cada profissão e cada casa tem pino.

---

# PARTE 12 — MATERIAIS, TEXTURAS E ALTURAS (NÃO INVENTE ALTURAS)

## 12.1 Tabela de alturas (Y, em metros, relativas ao asfalto = 0)
| Camada | Y (topo) | Observação |
|---|---|---|
| Asfalto | 0,000 | base |
| Decal de pintura (faixa, linha, seta, bueiro) | +0,005 | `polygonOffset` quando possível; se não, +0,008. **Cada decal só se sobrepõe ao asfalto, nunca à calçada.** |
| Guia (face vertical) | 0…0,15 | espessura 0,20 |
| Calçada | 0,150 | topo |
| Rebaixo/rampa | 0,15 → 0,00 | em 1,2 m |
| Gramado de lote / faixa-jardim | 0,100 | 5 cm abaixo da calçada; fica **dentro** da guia de contenção de 5 cm |
| Piso de lote/entrada | 0,150 | concordando com a calçada |
| Areia | +1,2 (duna) → +0,05 → 0 | ver 3.3 |
| Água | −0,40 | superfície; borda tem espuma |
| Ponte (tabuleiro) | asfalto +0,6 | (3.2) |
| Viga da rodovia | 6,0…7,5 | |
Plano de recorte (near) e profundidade: manter `Renderer3D` do jeito que está (0,3 m fora, 0,25 m dentro).

## 12.2 Texturas e UV (os bugs de textura vêm daqui)
1. **UV sempre em metros** (1 UV = 1 m; `Gfx` converte). Nunca escale UV por "tamanho da face", senão a textura estica.
2. **Atlas:** cada textura tem 4 px de **padding** (extrude) por tile; mipmaps com `Tex.uploadCoverageMips` (já existe) para folhas e letreiros. Não amostre fora do retângulo do tile.
3. **Janelas de prédio:** textura 512 px = 1 módulo de 3,6 m × 3,6 m (janela + parede). Prédio de largura W repete `W/3,6` vezes **inteiras** (arredonde a largura do prédio para múltiplo de 3,6 m ou **adicione pilastra de canto** para absorver o resto: nunca janela cortada ao meio na esquina).
4. **Telhado:** textura de telha com UV alinhada ao beiral, repetição de 0,5 m; cumeeira como faixa separada.
5. **Asfalto:** 2 texturas (limpo, desgastado) misturadas por vértice; **sem emendas em cruzamento**: o cruzamento é UMA malha só.
6. **Calçada:** quadrados de 1,5 m, juntas de 2 cm; tijolo 0,22×0,11 m na espinha; ladrilho geométrico em 4 padrões (escala 1 m).
7. **Normais:** calculadas por face; faces lisas (prédio) sem suavização entre paredes; **winding anti-horário** visto de fora; sem face dupla (back-face culling ligado). Todo quad de parede tem normal apontando para fora.
8. **Cor por vértice** só para variação (±6 %); não substitua textura.
9. **Letreiros/folhas:** recorte (`solid`), sem mistura; cor do texto contrasta (contraste ≥ 4,5:1).
10. **Sem textura "preta" ou "magenta"**: se faltar textura, usar cor sólida cinza-claro e registrar em `DECISOES.md` (não deixar o jogo travar).

## 12.3 Paleta
- Concreto `#C9C6BE`, asfalto `#3A3B3F`, asfalto desgastado `#4A4B50`, guia `#B8B5AD`, linha branca `#F2F2F2`, amarela `#F5C518`, tijolo `#9C4A35`, tijolo-claro `#B56B4A`, clapboard branco `#F1EEE6`, azul-colonial `#5B7FA6`, verde-venez. `#2F4F3E`, telhado cinza `#4F5258`, telha `#B5523B`, areia `#E8D5A8`, água rasa `#25C5C9` → funda `#0F5C8A`, grama `#6FA84A` / `#5B9A3F` / `#7AB75A` (listras de corte), copas verde `#4E8B3A`, âmbar `#D98A2B`, vinho `#8E2C3A`.

---

# PARTE 13 — COLISÃO, CHÃO, DESEMPENHO E MEMÓRIA

## 13.1 Colisão e chão
- `groundH(x,z)` retorna: asfalto 0 / calçada 0,15 / gramado 0,10 / areia seguindo duna / ponte / rampa / piso de casa pelo `Hds.surface`. **Cada transição ≤ 0,15 m sem rampa.**
- Retângulos de colisão (2D, como `City.addSolid`): **todos os prédios de decoração, cercas, muros, postes grossos (Ø 0,3 m), pilares da rodovia, hidrantes, bancos, lixeiras, mesas, quiosques, estátuas, cabines, piscinas decorativas**. **Não** colidem: árvores a menos de 6 m de altura de copa (colisão só no tronco Ø 0,5 m), placas finas, flores, linhas, faixas.
- Água: bloqueio quando `groundH < −1,1`.
- Ruas e calçadas **nunca** têm colisão. Cada porta de **profissão** e de **casa** tem vão livre.
- **Ônibus/carros** animados: caixa de colisão simples.

## 13.2 Orçamento (celular médio; confirme no `Renderer3D`)
- **Triângulos visíveis ≤ 450 mil** a qualquer momento; malha total do mapa ≤ **160 mil** por pedaço de 64 m **assada** (baixa, só fachadas) + detalhes gerados sob demanda a ≤ 95 m, descartados a 140 m (como `City.service`).
- **Memória de assets** do mapa ≤ **120 MB** (texturas 1024 px máx; atlas 2048; use ETC2/compressão se o `Tex` suportar).
- Pedaços de 64 m: cada um com bounding box para **frustum culling**; distância de desenho 235 m (terreno 420 m), carros 140 m, pedestres 55 m, fios 120 m.
- **LOD de 3 níveis** nos prédios: fachada completa < 120 m; caixa texturizada 120–260 m; silhueta/cor lisa > 260 m (nas torres apenas).
- Árvores/postes/hidrantes/bancos: **instanciados** (mesma malha repetida por matriz); nada de gerar 1 malha por árvore.
- Geração do mapa em **thread separada**; GL em fatias de ~10 ms (como `Hds.gl()`).
- Se estourar o orçamento, **reduza primeiro**: densidade de árvore pesada, fios, fiação, letreiros animados, carros animados, nunca a geometria das ruas.

---

# PARTE 14 — ETAPAS DE ENTREGA, VALIDADORES E CRITÉRIOS DE ACEITE

## 14.1 Arquivos que você cria
```
tools/gen-cidade5/plan.py        ← ÚNICA fonte de verdade (tudo desta especificação)
tools/gen-cidade5/roads.py       ← perfis de via, cruzamentos, rotatórias, pontes, rodovia elevada
tools/gen-cidade5/terrain.py     ← heightmap, colina, praia, rio, platôs
tools/gen-cidade5/lots.py        ← quarteirões, lotes, 17 casas, prédios decorativos
tools/gen-cidade5/landmarks.py   ← praça, parques, orla, píer, parque aquático, diversões, marina, estádio, farol
tools/gen-cidade5/jobs.py        ← 19 prédios de profissão (casca + dados do interior)
tools/gen-cidade5/validate.py    ← TODOS os validadores abaixo
tools/gen-cidade5/preview.py     ← PNG 2D por etapa (cores por camada)
tools/gen-cidade5/gen_cidade5.py ← orquestra e escreve os assets
app/src/main/assets/hds/city5.json, relevo5.bin, city5_mesh.bin (+ estenda o formato de modo compatível)
Kotlin: Relevo.kt (ler city5*), Hds.kt (17 casas), CityMap.kt (mapa/GPS), MainActivity.kt (Configurações > Mapa: 1→2→3→4→5), JobRooms.kt (interiores novos)
DECISOES.md                       ← decisões, dúvidas, fatos do repositório, limites
```

## 14.2 Etapas (rode UMA por vez; só passe para a próxima com validadores verdes e prévia aprovada pelo usuário)
- **ETAPA A — Esqueleto:** `plan.py`, grade, avenidas, coletoras, locais, rotatórias, cruzamentos, rodovia, rio, pontes. **Sem prédios.** Prévia 2D com nomes. *Aceite:* grafo de ruas conexo, zero rua solta, zero sobreposição.
- **ETAPA B — Terreno:** heightmap, colina, praia, rio, platôs, rampas das pontes e da rodovia. *Aceite:* declives dentro dos limites; ruas nunca mergulham no terreno (diferença ≤ 0,05 m).
- **ETAPA C — Chão:** asfalto, guias, calçadas, rebaixos, faixas, linhas, gramados, areia, água, bueiros. *Aceite:* mapa de ocupação 1 m sem conflito.
- **ETAPA D — Lotes e 17 casas:** quarteirões, lotes, **posições exatas das 17 casas** (tabela com X,Z,Y, frente, lote), cercas, entradas de garagem. *Aceite:* cada casa dentro do lote, com frente para uma rua e caminho até ela.
- **ETAPA E — Centro e prédios decorativos:** fachadas, alturas, esquinas, becos, quatro cantos da praça.
- **ETAPA F — Parques e pontos turísticos:** Praça Central, Parque das Flores, Mirante, Arena, Orla, Píer, Marina, Parque Aquático, Diversões, Farol, Portal, letreiro "MEULAR".
- **ETAPA G — Profissões:** os 19 prédios (casca + interior), estações de trabalho.
- **ETAPA H — Vida e detalhe:** árvores, postes, hidrantes, mobiliário, placas, carros estacionados, tráfego, pedestres, luz noturna.
- **ETAPA I — Integração:** GPS/mapa, pinos, seleção de mapa, GPS entre qualquer par de pontos, desempenho.

Ao final de cada etapa entregue: (a) arquivos novos/alterados, (b) comandos para rodar, (c) PNG da prévia, (d) saída dos validadores, (e) lista "o que ainda não foi testado no celular". **Nunca diga que testou no aparelho:** não há aparelho aqui. Diga o que foi verificado por script.

## 14.3 Validadores obrigatórios (`validate.py`; cada um imprime PASSOU/FALHOU + coordenadas)
1. **Grafo viário:** todos os nós conectados; toda rua termina em cruzamento, rotatória, cul-de-sac ou borda; **nenhum vértice de via a < 0,05 m de outro sem ser o mesmo nó**.
2. **Cruzamentos:** em cada um existe 1 piso de cruzamento + calçadas de canto com raio + rampas + faixas em todos os braços + linha de retenção + (semáforo ou PARE).
3. **Ocupação 1 m:** nenhuma célula com 2 camadas; nenhuma célula do mundo dentro dos limites urbanos sem camada (buraco) — fora da cidade, o fundo é terreno/mata/água.
4. **Lotes:** todo lote tem frente para rua, está 100 % dentro do quarteirão, não se sobrepõe a outro, e a casa/edifício está 100 % dentro do lote com os recuos de 2.x.
5. **As 17 casas:** tabela completa (nome, X, Z, Y piso, lote, rua da frente) = `HOUSE_LOTS`; a caixa da casa bate com `city2.json`/`plots` (tolerância 5 cm); distância mínima entre caixas de casas vizinhas ≥ 6 m; acesso por calçada; Y do piso concorda com o platô.
6. **Profissões:** os 19 existem uma vez só; porta voltada para rua; `station` dentro do prédio; **teste de ida**: A* do centro da Casa 1 até cada porta usando apenas calçada, faixa de pedestre e entrada: deve achar caminho.
7. **Teste de ida para as 16 casas** e para os 13 pontos turísticos (a pé e de carro).
8. **Z-fighting:** detector (como o `FIGHT=1 ./run.sh` do harness): nenhuma face coplanar (|ΔY|<1 mm e áreas sobrepostas) entre camadas diferentes.
9. **Normais/winding:** nenhum triângulo com área < 1e-6 m²; nenhuma normal apontando para dentro de sólidos; amostra de 500 triângulos checada.
10. **UV:** nenhum UV fora do tile do atlas; escala UV por face dentro de [0,9; 1,1] m/UV (exceto marcado).
11. **Árvores/postes/hidrantes:** nenhum item sobre asfalto, água, prédio ou lote que não seja o seu; distâncias mínimas de 11.1/4.1.
12. **Altura:** declives de via ≤ limites; degrau no caminho a pé ≤ 0,15 m (sem rampa); pontes e rodovia com altura livre ≥ 5,5 m sobre as vias.
13. **Colisão:** nenhum retângulo de colisão sobre porta de casa/profissão; nenhum jogador pode ficar preso: gerar 200 pontos aleatórios de calçada e verificar que cada um alcança a Casa 1 em A*.
14. **Orçamento:** triângulos por pedaço, memória estimada e nº de instâncias ≤ 13.2.
15. **Determinismo:** rodar 2× e comparar hashes dos arquivos.

## 14.4 Critérios de aceite visuais (o usuário confere no celular)
- Andar por **qualquer** rua sem encontrar rua "no ar", buraco, degrau fantasma, piscar de textura ou prédio cruzando outro.
- Olhando do alto, a cidade parece as fotos de referência: copas de árvore, telhados variados, ruas retas, colina verde, mar azul, torres no centro.
- Da Casa 1, a pé: chega à Lanchonete do Zé, Posto, Brilho Limpeza em ≤ 2 minutos; de carro chega a todas as 19 profissões.
- Da Praça Central se enxerga: as 4 construções cívicas, os 3 arranha-céus (Atlas, Nova Tech, Hotel Grand), e a Av. Central até o Portal.
- Nada de interior fora das 19 profissões e das 17 casas.

## 14.5 O que NUNCA fazer
- Nunca edite coordenada à mão no código Kotlin; só leia os arquivos gerados.
- Nunca "conserte" um validador relaxando a tolerância; conserte o plano.
- Nunca troque nomes de rua, de profissão, de casa ou de bairro desta especificação.
- Nunca coloque móvel em prédio decorativo.
- Nunca entregue sem prévia PNG e sem saída dos validadores.
- Nunca diga "ficou perfeito". Diga o que foi gerado, o que foi verificado e o que depende de teste no aparelho.

## 14.6 Primeira resposta esperada (antes de escrever código)
*(Execução direta neste repositório: o usuário autorizou começar sem esperar confirmação. Registre os fatos/dúvidas em `DECISOES.md` e siga para a ETAPA A.)*
Responda apenas com: (1) **fatos do repositório** que você confirmou (formatos, constantes, orientação da frente das 17 casas, limites do mundo 1000×800 e como vai estendê-los), (2) **lista de dúvidas/conflitos** entre esta especificação e o código (com a decisão sugerida para cada), (3) **plano de arquivos** e a confirmação "começo pela ETAPA A?". Só depois de o usuário responder, comece a ETAPA A.
