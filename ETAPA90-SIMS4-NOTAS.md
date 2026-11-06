# Etapa 90 — Sims 4 (teste)
- Corpos am5/af5 convertidos dos OBJ enviados (ferramentas/etapa90_sims4.py), escalados para o esqueleto Sims 3 e pesos transferidos de am1/af1.
- Cabeça usa o atlas do Sims 4; olhos gerados (esferas). Corpo: o OBJ veio com o canal de UV errado, então a pele do corpo foi assada a partir da pele Sims 3.
- Sem cabelo/cílios ainda. Não testado no aparelho.

## 90b — textura certa do corpo
- O OBJ do corpo trazia só o UV1. O UV0 (atlas do TS4) foi tirado das roupas de baixo padrão do pacote "Softe" (akalukery): mesmo corpo da EA, então a posição igual dá o UV0 exato; o homem usa o corpo da mulher para tronco/braços.
- Ferramentas: ferramentas/sims4/dbpf.py (lê .package do TS4), geom.py (lê GEOM), uvfix.py.
- Pés: o pacote não tem pés (vêm dos sapatos) -> cor lisa de pele.
- A pele Mercuria (.package) não foi usada: o atlas enviado já tem a pele.

## 90c — acabamento (pescoço, nuca, ombros, pés)
- Pescoço/nuca: o corpo é cortado exatamente na volta de vértices onde a cabeça detalhada encaixa (antes sobravam triângulos sobrepostos: anel escuro e fresta na nuca). Pesos suavizados só na cabeça/pescoço.
- Ombros: atlas sem a linha escura das bordas das ilhas; triângulos entre duas ilhas recebem cor lisa (sem faixa esticada). Normais soldadas nas costuras.
- Pés: ganham o tamanho/posição do pé do Sims 3 (não atravessam mais os sapatos), cor lisa com degradê no tornozelo.

## 90d — ossos e pesos originais do TS4
- Os GEOM das roupas de baixo trazem a lista de ossos (hash FNV-32 do nome em minúsculas) e os pesos de cada vértice. Os 58 hashes foram identificados (b__Pelvis__, b__Spine0..2__, b__L_UpperArm__, b__L_ShoulderTwist__, dedos 0..2, etc.).
- O corpo do TS4 agora usa esses pesos originais da EA (mulher: exatos; homem: cueca exata + tronco/braços pela mulher), ligados por nome aos 55 ossos do app. Pés e cabeça continuam com os pesos transferidos.
- Ainda falta o RIG do TS4 (posições/orientação dos ossos): nenhum dos downloads do celular funcionou. Sem ele não dá para tocar animações próprias do TS4.

## 90e — esqueleto ORIGINAL do TS4
- Achado no pacote "necrodog Wings MOD" (MediaFire): recurso RIG 0x8EAF13DE com os 178 ossos do adulto do TS4 (165 da EA + 13 das asas), versão 3.1.
- ferramentas/sims4/rig.py lê o RIG (posição/quaternion locais, pai, nome, hash); assets/cute/skel_s4.txt guarda tudo (mundo + local).
- Conferido: as juntas caem exatamente no corpo do TS4 (mesmo referencial em metros; L = +x). O pacote também traz 4 CLIPs (animações das asas) para testar a leitura do formato de animação do TS4.
- Ainda não usado pelo jogo: próximo passo é o corpo do TS4 deformar neste esqueleto e as animações serem passadas para ele.

## 90f — animações girando nas juntas do TS4
- ferramentas/etapa90f_clipes_s4.py: clips_am5.bin / clips_af5.bin = os 11 clipes do app refeitos com as juntas do esqueleto original do TS4 (mesma rotação por osso, posições por cinemática direta com os comprimentos do TS4).
- CuteChar: corpo "body/S_<g>5" carrega clips_<g>5.bin. bodyrig am5/af5 = juntas do TS4.
- Próximo: andar/correr novos (captura de movimento Bandai Namco, uso não comercial).

## 90g — andar e correr de captura de movimento (corpo do TS4)
- ferramentas/etapa90g_bandai.py: BVH do Bandai Namco -> 55 ossos com as juntas do TS4 (direção de cada osso copiada, giro a partir de um quadro de calibração, tronco/cabeça mantêm a postura do TS4, um passo completo esq+dir detectado pelo cruzamento dos pés, no lugar, pé no chão, laço costurado).
- Homem: walk_normal + run_masculinity. Mulher: walk_feminine + run_feminine. Substituem os clipes 1 (andar) e 3 (correr) de clips_am5/af5.
- Licença: CC BY-NC-ND (não comercial).

## 90h — andar, correr, pulos e agachar novos (LAFAN1)
- Andar/correr do Bandai trocados (estilo exagerado) por capturas naturais da LAFAN1 (Ubisoft), iguais para homem e mulher.
- Pulo parado, pulo correndo e agachado parado vindos da LAFAN1; andar agachado montado com IK (sem captura limpa disponível).
- Retarget genérico com calibração na T-pose (ferramentas/etapa90h_lafan.py). Licença não comercial. Ver ferramentas/sims4/bvh_lafan/LEIA.txt.

## 90j — caminhadas escolhidas pelo usuário
- Homem: Bandai dataset-2 walk_normal_001 (quadros 73-106). Mulher: walk_normal_004 (65-98). Escolhidas em vídeo (opções A e B).
- Retarget com pernas por IK (tornozelo relativo ao centro da pelve, pés nunca cruzam a linha do meio).
- Regra nova: animação só entra no jogo depois de aprovada em vídeo.

## 90k — correr e pulo correndo escolhidos
- Correr: homem Bandai run_normal_001 (11-34), mulher run_normal_004 (30-53).
- Pulo correndo: CMU 127_21 (homem e mulher). Pulo parado: mantido o atual (escolha do usuário).

## 90l — postura do tronco
- Correr tinha o tronco inclinado para o lado (média de ~9° no homem e ~8° na mulher), herdado do quadro de calibração da captura. Corrigido girando tronco+braços para inclinação lateral média zero (andar, correr e pulo correndo). Andar também deixou de inclinar para trás (de -4° para +1° à frente).

## 90m — braços da corrida
- A corrida era calibrada num quadro com os cotovelos dobrados (giro do antebraço errado -> braço torto). Agora calibra num quadro em pé, braços soltos (dataset-2 walk_normal_001, quadro 0; mesmo esqueleto normalizado), e o tronco segue sem inclinação lateral. Aprovado pelo usuário em vídeo.

## 90m — braços da corrida
- Calibração da corrida passou a usar um quadro em pé com braços soltos (walk_normal_001, quadro 0; mesmo esqueleto normalizado do Bandai) em vez do 1º quadro da corrida (cotovelo dobrado torcia o antebraço). Tronco com inclinação lateral média zero. Aprovado em vídeo.
