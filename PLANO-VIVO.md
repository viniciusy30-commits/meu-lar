# PLANO-VIVO — personagem fofinho (meu-lar)

Objetivo (não muda): customização de personagem bonita, fofinha e bem feita; sem polígonos estranhos.
Feedback mais recente do usuário: corpo parecia "boneco de feira" (peças coladas), rosto feio, mãos as piores; quer o mais profissional e natural possível.

## Passos
- [x] 1. Cute.kt/AvatarModel (elipsoides) — primeira versão, agora usada só como reserva (Avatar.buildCute)
- [x] 2. Motor de escultura em Java (pacote sculpt): campos de distância (SDF) com união suave + malha por surface nets
  - Prims (elipsoide, cone arredondado, ruído), Mesher, Layer (malha + tags de material por vértice)
  - Body (corpo contínuo, cabeça com maxilar/bochechas/nariz/lábios, mãos com dedos), Eyes
  - Gear (cabelos 1..8, barbas 1..3, camisa/regata/vestido/saia/shorts/calça, sapatos, óculos), Figure (monta tudo, cores, cache, pedaços indexados)
- [x] 3. Integração no app: SculptAvatar.kt (ponte + AvatarBuilder em segundo plano, com ticket), Gfx.Part com índices curtos, Renderer3D com glDrawElements, Avatar.build com reserva caso dê erro
- [x] 4. Câmera do criador (Creator.kt) para o corpo mais alto (≈1,57 m); pinça aceita zoom mais perto (GameView.kt)
- [x] 5. Testes no PC: 156 combinações (gênero × corpo × cabelo/roupa/calça/óculos/barba) sem erro nem NaN; 150–175 mil triângulos, ~1,4 s a frio / ~0,2 s com cache
- [x] 6. novidades.txt

## Decisões
- Formato salvo do Avatar (encode/decode) não mudou: saves antigos continuam valendo.
- Se o motor novo falhar por qualquer motivo (Throwable), cai no modelo antigo de elipsoides.
- Montagem fora da thread de desenho; a thread GL só troca a malha quando ela fica pronta (o personagem anterior continua na tela enquanto isso).
- Shader/iluminação do app não mudaram; lente dos óculos usa alfa por vértice (sem passada de vidro).

## Pontos a olhar com o APK no celular
- Tempo da primeira montagem e FPS (≈85 mil vértices, 145–175 mil triângulos).
- Rosto: estilizado e fofo, mas pode precisar de ajuste fino (nariz pequeno, cabeça meio oval).
- Moicano (cabelo 6): laterais podem parecer carecas demais.

## Arquivos alterados
app/src/main/java/com/vinicius/meular/{SculptAvatar.kt (novo), sculpt/*.java (novos), Gfx.kt, Renderer3D.kt, Avatar.kt, Creator.kt, GameView.kt}, app/src/main/assets/novidades.txt

## Rodada final (proporções/mãos/rosto)
- [x] Torso mais alto/largo, braços mais finos e curtos, pernas e quadril reajustados; roupas acompanham
- [x] Mãos refeitas (palma, polegar, 4 dedos) e caixa de malha da mão ampliada (pontas dos dedos não são mais cortadas)
- [x] Rosto mais fino estilo Sims (mandíbula, queixo, maçãs do rosto mais altas, lábios mais cheios)
- [x] Teste PC: 324 combinações sem erro/NaN

## PRÓXIMO PASSO
Se o build falhar, corrigir só o erro apontado. Se passar: ver o personagem no celular e ajustar rosto/moicano/desempenho conforme o que aparecer.

## Pack Cute Characters (importação de teste)
- [x] Pack (RAR5, unitypackage armazenado) extraído: 25 personagens (f_1–f_12, m_1–m_13), 7 animações, textura 128–1024, material
- [x] f_1.fbx (binário) convertido por script Python (fora do app) para assets/cute/f_1.bin: malha 6550 vértices / 8986 triângulos, 64 ossos, pesos (4 por vértice), animações Idle e Walk em matrizes por quadro (24 fps), altura normalizada 1,5 m, frente em +Z
- [x] CuteChar.kt: carrega o .bin, pele na CPU por quadro, textura própria (Part.tex); Renderer3D usa no criador (Idle) e na casa (Idle/Walk); se falhar, volta ao personagem antigo
- [ ] Ainda NÃO compilado/testado no celular (sem Gradle no ambiente). Se o build falhar, corrigir só o erro apontado
- [ ] Próximo: peças modulares (cabelo/roupa separáveis) e importar mais personagens; painel antigo de personalização REMOVIDO (Creator.kt só tem o botão Pronto)

## Câmera 3ª pessoa + pulo
- [x] Renderer3D: `third` (padrão ligado), câmera orbitando o personagem (2,7 m, encurta dentro da casa), drawPlayer (Walk/Idle, vira para a direção do movimento), sombra, pulo (py/vy, jumpReq)
- [x] Ui.kt: ícones CAMERA e JUMP; MainActivity: botão de câmera no topo, botão de pular (só no modo andar)
- [ ] Não compilado nem testado no celular. Pular não passa por cima de móveis (colisão é só no plano)

- [x] Animação de pulo: clip Jump = primeiros 17 quadros do "Song Jump" do pack (assado no f_1.bin, 3º clip); drawPlayer usa jumpT (tempo no ar) para sincronizar

## Rodada Mary (BoZo Stylized Modular Characters)
- [x] Extraído o unitypackage do RAR e lidos os FBX (leitor próprio); montada a Mary: corpo, cabeça, olhos, suéter, saia, sandálias, cabelo traseiro (Flare) e franja (LongSweeps) = 14.691 vértices, 24.062 triângulos, 55 ossos (com dedos)
- [x] Textura única 2048x1024 (assada das máscaras do pack com as cores da Mary.asset); mesmo formato CUT1 lido por CuteChar.kt (arquivos cute/f_1.bin e cute/textures.png, nomes mantidos; CuteChar.kt não mudou)
- [x] Animações criadas à mão nos ossos: Idle 3 s (laço), Walk 1 s (laço), Jump 0,71 s (sem agachar; o jogo já começa no ar)
- Limitações: cabelo e olhos presos à cabeça (sem física); mãos com dedos abertos como no modelo original; saia segue as coxas
- Licença: o pack veio de site de redistribuição; para publicar o jogo, ter a licença original do BoZo
## Rodada animação do andar (Mary)
- [x] Walk refeito (2ª versão, após vídeo do usuário: "robô"): curvas de passada com splines periódicas (quadril, joelho, tornozelo: calcanhar→rolagem→impulso), ciclo 0,72 s, braços opostos às pernas com cotovelo atrasado, torção de pelve/coluna/cabeça, dedos relaxados (curvatura via rz nos ossos dos dedos), ground-lock da pelve; velocidade de solo medida ≈1,66 m/s
- [x] Velocidade do jogador 2,6→1,9 m/s e da avatar da casa 2,2→1,9; CuteChar.WALK_RATE=1,14 casa o passo com 1,9 m/s (sem deslizar)
- [x] CuteChar.kt otimizado: os 55 ossos são interpolados uma vez por quadro (antes por vértice, ~4x mais caro) — causa provável das travadinhas
- [x] CuteChar.frame(clip, t, slot): fase do laço reinicia ao trocar de clip e transição suave de ~0,15 s (0,06 s para o pulo); slots 0 = jogador, 1 = avatar da casa, 2 = criador (Renderer3D passa slot nas chamadas 1 e 2)
- [ ] Ainda não compilado nem testado no celular
- Ferramentas de geração (fora do repo): scripts Python em /home/claude (fbx.py, ext.py, asm.py, anim.py, build.py, render.py); a animação é gerada em anim.py (walk/idle/jump) e assada em f_1.bin
## PRÓXIMO PASSO
Ver no APK: se o andar ainda parecer rápido/lento demais, ajustar só o comprimento do ciclo (0,8 s em build.py) e a amplitude S em anim.py; mãos ainda ficam com dedos abertos (possível curvar dedos).

- [x] 3ª versão do walk (feedback "driblando"): curvas de perna simplificadas (joelho máx ~42°, quadril ±22°), ciclo 0,9 s, altura da pelve suavizada por FFT (2 harmônicas; o ground-lock cru dava soluço); velocidade de solo medida 1,18 m/s → jogo 1,4 m/s com CuteChar.WALK_RATE=1,19 (ciclo efetivo ≈0,76 s)

- [x] 4ª versão do walk (feedback "deslizando"): perna guiada por pé (IK de 2 ossos no plano sagital, anim.py: foot_target/_ik): tornozelo anda linear no apoio (60% do ciclo, curso 70 unid) e faz arco no balanço; pelve baixa só o necessário (bob ≈5 unid). Pé de apoio varia ≈2 unid no chão (medido). Ciclo 0,9 s; WALK_RATE=1,2; velocidade do jogo 1,28 m/s (=clip 1,065 m/s × 1,2). Para mudar a velocidade: mudar juntos Renderer3D (1,28) e WALK_RATE

## Personalização modular BoZo — Etapa 1 (infraestrutura com a Mary em pedaços)
- [x] Formato novo em `assets/cute/`: `base.bin` (CUT1: corpo + boca + cabeça + olhos + os 3 clips Idle/Walk/Jump copiados **byte a byte** do f_1.bin aprovado), uma peça por arquivo `p_<slot>_<id>.bin` (CUP1: "CUP1", nv, ni, flags, vértices de 44 bytes iguais ao CUT1, índices locais uint16) e `pieces.txt` (manifesto `slot|id|arquivo|textura` + linha `outfit=` com a roupa padrão; a ordem das linhas é a ordem de desenho).
- [x] Peças geradas (a Mary inteira, igual à de antes): top/Sweater, bottom/Skirt, feet/Sandals, hairBack/Flare (inclui 2 tufos pequenos que usam a textura do cabelo), hairFront/LongSweeps. Além disso foram descartados ~800 vértices órfãos (nenhum triângulo os usava).
- [x] `CuteChar.kt`: mesma interface de antes (`frame`, `clipSeconds`, `ready`, `initGl`, `assets`; Renderer3D NÃO mudou). Os 55 ossos são interpolados uma vez por quadro e as mesmas matrizes vestem o corpo-base e cada peça ativa (lista de peças ativas, uma `Part` por peça, todas com `textures.png`). Novos: `setOutfit(chaves "slot/id")`, `outfit()`, `available()`, `modular`.
- [x] Reserva: se base.bin/pieces.txt/peças falharem, carrega o `f_1.bin` inteiro como antes (mantido nos assets, intocado); se também falhar, `frame` devolve null e o app usa o personagem esculpido.
- [x] Verificado no PC (`ferramentas/etapa1_verify.py`): clips idênticos byte a byte; malha base+peças × f_1.bin com diferença 0,0 (posição e normal) nos 128 quadros dos 3 clips; mesmos UVs e cores; 24.062 triângulos preservados, mesma ordem de desenho.
- [ ] Ainda NÃO compilado nem testado no celular (sem Gradle/Kotlin no ambiente). Se o build falhar, corrigir só o erro apontado.
- Ferramentas (agora no repo): `ferramentas/etapa1_split.py` (divide f_1.bin em base + peças) e `ferramentas/etapa1_verify.py`.
- Para testar: a Mary deve aparecer IGUAL (criador, casa e câmera 3ª pessoa), com Idle, andar e pulo iguais. Detalhe técnico: agora são 6 desenhos por personagem em vez de 1.
- Observação: existe uma pasta antiga `viniciusy30-commits-meu-lar-46a5cc2/` na raiz do repositório (cópia velha, não é usada pelo app).
- PRÓXIMO: Etapa 2 (cores por máscara), só depois do teste.

## Personalização modular BoZo — Etapa 2 (cores)
- [x] Recoloração por máscara do pack, **sem mexer em malha, ossos nem animações** e sem mexer no shader: o atlas `cute/textures.png` continua sendo a base; `CuteColor.kt` gera uma textura recolorida numa thread de fundo e a thread GL só sobe ela (glTexSubImage2D) no começo de `CuteChar.frame`.
- [x] Dados gerados no PC por `ferramentas/etapa2_masks.py` a partir das máscaras do pack (canais R/G/B = cor 1/cor 2/cavidades): `cute/recolor.png` (R=peso do slot 0, G=peso do slot 1, B=id da região), `cute/recolor_s.png` (sombra do pixel) e `cute/recolor.txt` (regiões, slots e cor de referência de cada uma = cor com que a Mary foi assada). Regiões: corpo(pele), blusa(2 cores), saia, cabelo trás/frente (cor + pontas rosa), olhos (só a íris, detectada pela cor assada), sandália (2 cores).
- [x] Modelo por pixel/canal (sRGB): `saida = (base + S*(w0*max(D0,0)+w1*max(D1,0))) * (1 + w0*min(D0/ref0,0)+w1*min(D1/ref1,0))`, D = cor escolhida − referência. Clarear soma, escurecer multiplica (mantém o detalhe). Com as cores originais a saída é idêntica ao textures.png (diferença 0, verificado em `ferramentas/etapa2_sim.py`).
- [x] 9 slots (`CuteColor.SLOT_NAMES`): Pele, Olhos, Cabelo, Pontas, Blusa, Detalhe, Saia, Sandália, Tiras; paletas de 8 a 14 cores; -1 = original. Pontas acompanham o cabelo (25% mais claro), Detalhe acompanha a blusa (25% mais claro) e Tiras acompanham a sandália, enquanto não escolhidos.
- [x] `Avatar.cc` (IntArray de 9) salvo no `encode()` DEPOIS dos 13 números antigos; `decode()` aceita saves antigos (sem cc = tudo original). GameState aplica `CuteColor.setColors(avatar.cc)` ao carregar; se o contexto GL for recriado a textura recolorida sobe de novo.
- [x] `Creator.kt`: fileira de partes + fileira de cores + "Pronto"; a câmera do criador sobe um pouco (alvo 0,7) para o painel não cobrir os pés.
- [ ] Ainda NÃO compilado nem testado no celular (sem Gradle/Kotlin no ambiente). Se o build falhar, corrigir só o erro apontado.
- Limitações conhecidas: cor da peça é a cor MÉDIA da região (as sombras do pack acompanham); cabelo branco/preto mostra um resto leve das pontas rosa; cores só valem para as 5 peças atuais (as próximas peças das Etapas 3–5 entram no mesmo atlas/mesmo esquema com novas regiões).
- PRÓXIMO: Etapa 3 (cabelos), só depois do teste.


## Etapa 3 — Cabelos (entregue, aguardando teste)
- [x] 23 cabelos convertidos do pack (FBX -> CUP1) por `ferramentas/etapa3_hair.py` (+ `fbxr.py`, `fbxmesh.py`): 14 traseiros + 9 franjas, somando Flare e LongSweeps da Mary = 15 + 10.
- Pesos: osso 8 (cabeça) acima de y=150, misturando com o osso 4 (peito) até y=140, para o cabelo longo seguir o peito e não atravessar o corpo.
- Textura: `cute/hair.png` (1024x1024, 20 texturas do pack assadas em castanho) com máscaras `hair_recolor.png`, `hair_recolor_s.png`, `hair_recolor.txt` (região 1 = cabelo, slots Cabelo/Pontas). Flare e LongSweeps seguem em `textures.png`.
- `CuteColor.kt`: agora com 2 camadas (Mary e cabelos); `CuteChar.setHair(trás, frente)` e hair.png subida/recolorida igual ao atlas da Mary.
- `Avatar`: 2 números novos no fim do save (hb, hf = índices em AvaPal.HB_IDS / HF_IDS); saves antigos ficam com o cabelo da Mary.
- `Creator.kt`: partes "Cabelo atrás" e "Franja" (estilos) antes das cores.
- Chapéu escondendo cabelo: fica para a Etapa 5 (chapéus). Cabelo atrás/frente são independentes.


## Etapa 4 — Roupas (entregue, aguardando teste)
- [x] 18 blusas + 15 calças/saias + 3 vestidos convertidos do pack por `ferramentas/etapa4_extra.py` (+ `clothes_lib.py`, `fbxr.py`, `fbxmesh.py`). Pesos de osso vêm dos clusters do FBX: conferido que Sweater e Skirt da Mary saem IDÊNTICOS (diferença 0). Sweater e Skirt continuam em `textures.png`.
- Mapeamento nome do osso -> índice de 55 ossos em `clothes_lib.bone_index` (twists vão para o osso pai).
- Atlas único `cute/extra.png` (2016x1344, tiles 224) com cabelos + roupas, máscaras `extra_recolor.png`/`extra_recolor_s.png`/`extra_recolor.txt`. Regiões: 1 cabelo (Cabelo/Pontas), 2 cima e vestidos (Blusa/Detalhe), 3 baixo (Saia/Detalhe baixo = slot novo nº 9). Cores "originais" das peças novas: cinza-claro (cima) e cinza-azulado (baixo), mudam pela paleta. `hair.png`/`hair_recolor*` viraram placeholders de 1 pixel (podem ser apagados do repositório).
- CUP1 com flags&1: depois dos índices vem `nHide` + ids (uint16) de triângulos do corpo-base cobertos pela peça (distância < 1,5 e mesma orientação). `CuteChar.rebuildActive` monta o corpo sem esses triângulos.
- Roupa de baixo: `top/Underwear` e `bottom/Underwear` (faixa e shorts curtos gerados do próprio corpo, 0,35 acima da pele), aparecem quando não há blusa/calça/vestido.
- `Avatar`: salvos ctop, cbot, cov (índices em CT_IDS, CB_IDS, CO_IDS), cor do slot 9; formato: 13 antigos | 9 cores | hb hf | cor 9 | ctop cbot cov. `wearKeys()` decide as peças. `CuteChar.setWear` substitui `setHair`.
- `Creator.kt`: partes Cabelo atrás, Franja, Blusa, Calça/saia, Vestido (estilos) e depois as cores.
- Limites conhecidos: roupas largas (moletom, calça baggy) podem atravessar braço/perna em poses extremas do Walk; correção seria nos pesos da peça. Sapatos, luvas, chapéus, óculos e barba ficam para a Etapa 5.
- PRÓXIMO PASSO: esperar o teste das Etapas 3 e 4; depois Etapa 5.

## Extra — Biquíni (entregue, aguardando teste)
- `ferramentas/bikini.py`: malha procedural colada ao corpo-base (pesos interpolados do corpo, mesmas animações). Peças `top/Bikini`, `bottom/Bikini`, `overall/Bikini` (conjunto), listadas em AvaPal.CT_IDS/CB_IDS/CO_IDS e em `cute/pieces.txt`.
- Atlas `extra.png`: tiles 52 (região 2, top) e 53 (região 3, calcinha) com bolinhas e debrum recoloríveis (tecido = cor 1; debrum/laços = cor 2).


## Etapa 6 — Tela do criador estilo The Sims (entregue, aguardando teste)
- [x] `Creator.kt` novo (categorias, sub-abas, grade de miniaturas, cores, Girar/Pronto), ícones do pack em `assets/cute/icons/`, câmera com zoom/giro por categoria (`cTargetYaw`, `cShift` em Renderer3D; GameView cancela o giro ao tocar). Detalhes em `ETAPA6-NOTAS.md`.
- [ ] Ainda NÃO compilado nem testado no celular. Se o build falhar, corrigir só o erro apontado.
- PRÓXIMO PASSO: esperar o teste da Etapa 6; depois Etapa 7 (corpo e rosto: sliders e formato da cabeça).

## All Star
- [x] Peça, atlas, ícone, lista de sapatos
- [ ] Testar no celular

## Etapa 7 — Corpo e rosto (entregue, aguardando teste)
- [x] `BodyMorph.kt` (proporções por deformação de repouso em todas as peças), `morph.bin` (13 canais de rosto), `CuteChar.setShape/refit`, `Avatar.bs/fs` (+23 números no save), `Creator.kt` (Corpo > Proporções, Rosto > Formato). Detalhes em `ETAPA7-NOTAS.md`.
- [ ] Ainda NÃO compilado nem testado no celular. Se o build falhar, corrigir só o erro apontado.
- PRÓXIMO PASSO: esperar o teste (Etapas 6 e 7); depois Etapa 8 (expressões, piscar, desempenho, licença).
- Etapa 7, correção: olhos repintados (íris menor, esclera, brilho) — `ferramentas/etapa7_olhos.py`; mexeu em textures.png e recolor*.

## Etapa 8 — piscar e expressões (entregue, aguardando teste)
- [x] morph.bin com 18 canais (5 dinâmicos), CuteChar piscar/expressão/surpresa no pulo, Creator Rosto > Expressão. Detalhes em `ETAPA8-NOTAS.md`.
- [ ] Ainda NÃO compilado nem testado no celular. Se o build falhar, corrigir só o erro apontado.
- Licença: dispensada pelo usuário. Desempenho/atravessamento: não medidos.
- PRÓXIMO PASSO: esperar o teste das Etapas 6, 7 e 8.

## HUD estilo The Sims + botão de pular (entregue, aguardando teste)
- [x] Detalhes em `ETAPA9-HUD-NOTAS.md`. [ ] Não compilado nem testado no celular.

## Etapa 10 — correr (entregue, aguardando teste)
- [x] Clipe RUN no base.bin, analógico: arrasto cheio corre, leve anda; botão verde. Detalhes em `ETAPA10-CORRIDA-NOTAS.md`.
- [ ] Não compilado nem testado no celular.

## Etapa 12 — sobrancelhas e boca com cor (entregue, aguardando teste)
- [x] Textura do rosto repintada (sobrancelhas seguem o cabelo, lábios seguem a pele). Detalhes em `ETAPA12-ROSTO-NOTAS.md`.
- [ ] Não testado no celular. Possível próximo ajuste: manchas rosadas da máscara de pele em tons muito claros (já existiam).

## Etapa 13 — corpo masculino/feminino e busto maior (entregue, aguardando teste)
- [x] Botões Feminino/Masculino em Corpo > Proporções, deformação masculina, busto novo (até +8 cm), normais corrigidas. Detalhes em `ETAPA13-CORPO-NOTAS.md`.
- [ ] Não compilado nem testado no celular. Possível próximo ajuste: cabelo comprido atravessando busto grande.
- ATENÇÃO (aprendido na continuação): em `codigo/` do ZIP de continuação, `Avatar.kt`, `Creator.kt` e `novidades.txt` da raiz eram versões ANTIGAS; a versão atual está em `codigo/viniciusy30-commits-meu-lar-75b834b/`.

## Etapa 38 — Móveis do pack home-set-2020s (entregue, aguardando teste)
- [x] 49 móveis convertidos dos FBX (tamanho/forma/texturas originais) para `assets/mob`; `MobLoader` (Mob.kt); `Type.mob/rug`; loja com miniaturas. Detalhes em `ETAPA38-MOVEIS-NOTAS.md`.
- [ ] Não compilado nem testado no celular. Se o build falhar, corrigir só o erro apontado.

## Etapa 41 — Cabelo Faye (mod Sims 4) (entregue, aguardando teste)
- [x] `ferramentas/etapa41_faye.py` converte o .package: franja/topo (GEOM 805EC934) + trança (8037F206), LOD0, escala uniforme 1,3, textura original (degradê loiro/rosa) em `faye.png`. Peça `hairBack/Faye` (Cabelo > Atrás > "Faye"); em Frente escolha "Sem". Detalhes em `ETAPA41-FAYE-NOTAS.md`.
- [ ] Não compilado nem testado no celular. Se pesar (21,9 mil vértices) usar LOD1 (GEOM 8035B4BE).


## Etapa 42 — cabelo Heartbeat (Sims 3)
- [x] Conversor ferramentas/etapa42_heartbeat.py, p_hairback_heartbeat.bin, heartbeat.png, ícone, pieces.txt, Avatar.kt (HB_IDS/HB_N), CuteChar.kt (isAlphaHair)
- [ ] Testar no celular (build do GitHub). PRÓXIMO PASSO: ajustar encaixe/cor só se o teste mostrar problema.


## Etapa 43 — Julie (personagem pronta, corpo/rosto do Sims 3) (entregue, aguardando teste)
- [x] `ferramentas/etapa43_julie.py` gera `p_body_julie.bin` (corpo + rosto + couro cabeludo + olhos ligados ao esqueleto), `julie.png` (atlas) e `p_hairback_heartbeatjulie.bin` (Heartbeat ajustado a ela). Cartão "Julie" em Personagens prontos; `Avatar.julie` salvo no fim do encode; `CuteChar.MANAGED` inclui "body"; `Creator.kt`: Masculino/Feminino saem da Julie. Detalhes em `ETAPA43-JULIE-NOTAS.md`.
- [ ] Não compilado nem testado no celular. PRÓXIMO PASSO: se o build falhar, corrigir só o erro; depois ajustar encaixe/cor da Julie conforme o teste.


## Etapa 44 — Corpos do Sims 3 no lugar do "Bozo" (entregue, aguardando teste)
- [x] `ferramentas/etapa44_sims.py` gera 21 corpos (bebê, criança, jovem, adulto, idoso × feminino/masculino × magro/normal/gordo; criança e bebê unissex), 8 atlas de pele `sk_*.png`, 6 cabelos Heartbeat ajustados e `simbodies.txt`. Criador: Base e abas Corpo/Rosto mostram Idade, Sexo, Corpo e Cabelo. Postura do Sims: braços para baixo ao lado do corpo (`ARM_EXTRA` no script). Altura relativa por idade em `pieces.txt` (5º campo) aplicada em `CuteChar.setWear`.
- [x] Roupas antigas (feitas para o Bozo) não aparecem nos corpos novos; roupa de baixo pintada na pele. PRÓXIMO PASSO: o usuário manda as roupas do Sims 3 → converter peça a peça (top/bottom/overall/feet) para cada tipo de corpo.
- [ ] Não compilado nem testado no celular. Se o build falhar, corrigir só o erro apontado.

## Etapa 48 — Anatomia do Jovem (entregue, aguardando teste)
- [x] Coluna reta, ombros/clavículas certos, braços junto do corpo (tf/tm × magro/normal/gordo). Causa: juntas da coluna/clavícula na frente do peito + retarget copiando a curvatura do Bozo. Detalhes em `ETAPA48-JOVEM-NOTAS.md`.
- [ ] Não compilado nem testado no celular. Adulto/idoso/criança/bebê têm o mesmo defeito de origem: rodar `etapa48_jovem.py` nesses grupos se o Jovem ficar aprovado.


## Etapa 50 - Sliders de corpo (27) para o corpo do Sims 3
- [x] bodyrig.txt + ferramentas etapa50_*.py
- [x] BodyMorph.warpSim (Kotlin), CuteChar (carga do rig e uso), Avatar (save compativel), Creator (aba Corpo com grupos)
- [ ] Testar no celular (ver ETAPA50-SLIDERS-CORPO-NOTAS.md)

## Etapa 51 - Sem animacoes (corpo do Sims 3 como veio)
- [x] clips_*.bin, base.bin e f_1.bin com 1 clipe parado; ferramentas/etapa51_sem_animacao.py
- [ ] Testar no celular (ver ETAPA51-SEM-ANIMACAO-NOTAS.md)
- [ ] Esqueleto real do Sims 3: precisa do arquivo de esqueleto (nao veio nos RAR)

## Etapa 108 — Roupas masculinas Minimalist corrigidas (entregue, aguardando teste)
- [x] `Ts4Cloth` (LOD0, recorte só de transparentes, escala s0, empurrão suave iterativo, textura recortada), `Cover.markSurface` sem cunhas na borda aberta, assets regenerados, renders antes/depois. Detalhes em `ETAPA108-ROUPAS-TS4-NOTAS.md`.
- [ ] Testar no celular (camiseta, short, jeans e combinações; caminhar/correr). Possível próximo passo: outras cores dos pacotes, pesos originais da EA.

## Etapa 110 — Short/pernas, gola, barra da calça e cores das roupas Minimalist (entregue, aguardando teste)
- [x] Short encolhido e pernas separadas (pesos por perna), tampas da barra removidas, pesos de pé/dedos da calça passados à canela, gola puxada ao pescoço, 41 cores (18/12/11) com seletor em `ModStore.VARS`. Detalhes em `ETAPA110-PERNAS-GOLA-CORES-NOTAS.md`.
- [ ] Testar no celular (parado, andando, correndo; cores). Se algo ainda fugir: ajustar `SHORT_HEM_SCALE` (0,78) ou a faixa da gola (`band` em `collarPull`) e reconverter com `T3`.

## Etapa 112 — Tênis Dunk High masculino + pacote StandStillInCAS preservado
- [x] VHSync Dunk High convertido para o corpo adulto masculino do Sims 4 (`am5`), slot `feet`, 4.244 vértices, 6.232 triângulos e 38 swatches.
- [x] Corrigida a ponta/sola deformada: sapatos não passam pelo `pushOut` de tecido; a geometria original é preservada.
- [x] CUP1 oculta 570 triângulos do pé-base enquanto o tênis está vestido; a canela permanece visível. `Thumb.kt` aplica a mesma máscara nas miniaturas.
- [x] `ModStore` registra o tênis em Sapatos, com seletor das 38 cores.
- [x] Prévia 3D renderizada e inspecionada em 3/4, frente e lateral; miniatura Kotlin também testada. Detalhes em `imagens-dunk-high/`.
- [x] StandStillInCAS original preservado em `mods-sims4/originais/`. É tuning ASM XML do CAS do The Sims 4, sem malha/textura; não é renderizável nem executável pelo Meu Lar.
- [ ] Build Android e teste no aparelho após envio do ZIP para `_incoming` (Gradle/gradlew indisponível neste ambiente).
- Detalhes e validações: `ETAPA112-DUNK-HIGH-STANDSTILL-NOTAS.md`.

## Etapa 113 — braços e mãos dos modelos TS4
- [x] `clips_am5.bin`: os movimentos locais de clavículas, braços, antebraços, mãos e dedos do `af5` foram retargetados para o rig `am5` em todos os 11 clipes; tronco, cabeça e pernas masculinos foram preservados.
- [x] `CuteChar.kt`: pivôs específicos para as mãos masculina e feminina; polegar reposicionado para ficar por cima dos dedos durante a corrida; transição da mão fechada corrigida com slerp para evitar deformação da matriz.
- [x] Renders offline de andar, correr, pulo e das duas mãos dos dois modelos; rotações locais conferidas e comprimentos do rig masculino preservados.
- [ ] Build Android e teste no aparelho após envio do ZIP para `_incoming` (sem `gradlew`/Gradle/Android SDK neste ambiente).
- Detalhes: `ETAPA113-BRACOS-MAOS-NOTAS.md`; prévias em `imagens-etapa113/`.

## Etapa 118/119 — Piscina + sentar na borda (entregue, aguardando build e teste)
- [x] Quintal maior, piscina, clipes Mixamo (mergulho, nado, nadar até a borda, boiar) nos corpos am5/af5, `Pool.kt`, lógica em `Renderer3D.kt`. Detalhes em `ETAPA118-PISCINA-NOTAS.md`.
- [x] Andando até a água: senta na borda (pernas na água) e entra; pular perto da borda mergulha.
- [ ] Build e teste no celular: altura do assento na borda, pernas dentro d'água, entrada na água, câmera, mergulho vindo de perto.

## Etapa 163 — Cidade 2: ruas e casas do Hds (entregue, aguardando build e teste)
- [x] Dados: `app/src/main/assets/hds/city2.glb` (1.837 peças, 95 materiais, 49 texturas, 12 MB) + `city2.json` (2.837 instâncias, 17 casas com caixa, 922 retângulos de colisão feitos da geometria real das paredes — vãos de porta abertos —, ruas e limites). Gerados por `ferramentas/hds/city2_export.py` (leitores do Hds em `ferramentas/hds/`).
- [x] `Hds.kt` (novo): monta pedaços de 64 m, telhado/forro de cada casa em malha separada, colisões e marcadores "Casa 1..17"; GL sobe texturas/malhas em fatias de ~10 ms (`Hds.gl()` chamado por `City.service`).
- [x] `City.kt`: flag `HDS` (+ `hdsBuilt`), desvio em `build()`, chão plano, sem trânsito/pedestres/TownHouses nessa cidade; `Renderer3D.kt`: desenha os telhados (somem com o jogador dentro, vista de cima), sem mar, remonta ao trocar de mapa; `CityMap.kt`: mapa vetorial da cidade 2; `MainActivity.kt`: Configurações > "Mapa: Cidade 1 / Cidade 2" (pref `cidade2`).
- [x] Quarteirão (1,0) reservado e vazio: o lote do jogador fica no centro dele.
- [ ] Build e teste no celular: carregamento (12 MB + texturas), memória, FPS, entrar nas casas pelas portas, telhado sumindo, marcadores no mapa, trocar de mapa nas Configurações.
- [ ] Futuro: compra das casas (o jogador disse que será diferente), apartamentos e escritório do Hds (cenas Apt1-3 já no kit), trânsito e pedestres na cidade 2, móveis nas casas.
- Reconstruir os dados: precisa do `Hdssemarqs.zip` (Hds/assets/bin/Data) em `/home/claude/hds`; ver `ferramentas/hds/LEIA-ME.txt`.

## Etapa 164 — Cidade 2: piscar (parcial)
- [x] `Hds.addPrim` descarta triângulos repetidos no mesmo lugar (hash de posição a 2 cm): ~4.470 duplicatas exatas no city2.glb.
- [x] Colisão das paredes engordada em 15 cm (Hds.PAD); plano próximo da câmera 0,1 dentro das casas (Hds.inside).
- [ ] Ainda falta: camadas coplanares de materiais diferentes (piso sobre piso), colisão de escadas/andares (colisão é 2D, só entre 0,25 e 1,8 m), shaders/iluminação iguais ao outro jogo.
- Não compilado (sem Kotlin aqui). Se o build falhar, corrigir só o erro apontado.
## Etapa 165 — Cidade 2: piso, colisão e profundidade (correções de código; validação visual pendente)
- [x] `Hds.groundH`: pisos internos usam `City.FLOOR` (0,27 m); asfalto e calçadas recebem alturas de superfície próprias com base nas linhas de rua.
- [x] `City.groundH`: encaminha a Cidade 2 ao cálculo de altura do Hds antes da regra do lote.
- [x] `Hds.addPrim`: hash de triângulo combina os três vértices em ordem canônica, reduzindo colisões falsas do hash por soma.
- [x] `Renderer3D`: plano próximo dentro das casas aumentado de 0,10 m para 0,25 m para recuperar precisão do depth buffer.
- [ ] Build Android e teste visual no aparelho: confirmar encaixe dos pés, portas/parede, ausência de piscar e emendas/desníveis das avenidas. Este ambiente não tem emulador Android para renderização real.

## Etapa 165 (continuação em outra conta)
- [x] Cunhas pretas nas paredes: eram a malha RoomAmbientOcclusion (cor preta opaca). Glb.kt agora ignora essas peças.
- [x] Colisão: +57 retângulos de cerca (picket) que faltavam em city2.json.
- [ ] Ruas com bordas diagonais / casas ainda piscando: o vídeo não veio no ZIP; conferir no APK.
- [ ] Escadas e andar de cima: ainda sem altura de caminhada (groundH só tem o térreo).
- [ ] Shaders iguais ao jogo original do Hds: não feito.

## Etapa 166 — Cidade 2: andares, escadas, porão e caixa da Casa 5 (entregue, aguardando build e teste)
- [x] BUG achado: a Casa 5 tinha caixa de 286x100 m (peças soltas a ~243 m de altura entravam no cálculo). Nessa área enorme o chão virava piso de casa (27 cm, "ruas com borda diagonal"), o telhado sumia e a câmera usava plano próximo curto. `city2.json` agora tem a caixa certa (532,6..550,2 x 132,7..148,3).
- [x] Novo `hds/city2walk.bin` (gerado por `ferramentas/hds/walk_export.py`): por casa, grade de 25 cm com alturas reais de piso (térreo, 2º andar, escadas, porão) e máscara de paredes por faixa de 50 cm de altura.
- [x] `Hds.surface` (chão sob os pés, degrau até 55 cm) usado em `Renderer3D.groundH`; `Hds.upper` faz `City.blocked` usar as paredes do andar onde o jogador está (acima de 1,2 m ou no porão); térreo continua com a colisão antiga.
- [ ] Build e teste no celular: subir escadas, andar no 2º andar, paredes lá em cima, porão, casa 5 (rua normal em volta).
- [ ] Ainda pendente: piscar (camadas coplanares), shaders do jogo original, móveis nas casas.

## Etapa 167 — Buraco do porão na grama + papéis de parede (entregue, aguardando build e teste)
- [x] Teste da 166 (relato do usuário): casas não piscam mais; escadas sobem e descem. Problema: nos porões a grama (quadrado de 120 m em y=0) ficava por cima da escada.
- [x] `walk_export.py` grava `holes` em `city2.json` (células com piso abaixo de -0,5 m: porões, escadas, piscina); `Hds.addGrass` recorta a grama nesses buracos (quadriculado pelas bordas dos buracos, UV interpolada).
- [x] Shader do jogo original: papéis de parede usam máscara de cor (fundo + _ColorOnR/G/B). `ferramentas/hds/bake.py` assa isso em textura: 13 materiais (flores, treliças, damasco) agora têm padrão e cor, antes saíam lisos. `city2.glb` regenerado (mesma ordem de peças/instâncias).
- [ ] Ainda não feito: sombra de ambiente (RoomAmbientOcclusion, textura em R, cor preta alfa 0,1) precisa de pintura com transparência; sombras assadas da fachada da casa 17 (_ShadowTex, 2ª UV); azulejos (_LayerR/G/B); brilho (_Glossiness 0–0,5) e normal maps; detalhe de tecido (_DetailTex).

## Etapa 168 — Grama em todas as peças baixas + azulejos (entregue, aguardando build e teste)
- [x] Causa de a grama ainda aparecer sobre piscinas/escadas: além do quadrado grande, há faixas de grama de beira de rua (`road_20_m`, `road_turn_r`, `junction`, material grass_terrain_tile, y=0,2) por cima. `Hds.addClipped` recorta qualquer triângulo rente ao chão (y -0,15..0,4) de peça fora de casa pelos buracos (polígono cortado nas 4 linhas do buraco, UV/normal interpoladas).
- [x] Buracos agora vêm de qualquer superfície abaixo de -0,06 m (antes: só piso ≤ -0,5 m): pega o topo das escadas e a borda rasa da piscina. 33 retângulos.
- [x] Azulejos (ceramic_tile_wall_01/09): máscara escolhe a camada R/G/B, cada uma com sua cor; assado em textura (`bake.py`). `city2.glb` regenerado (mesmas instâncias).
- [ ] Ainda não feito (precisa mexer no renderizador, sem como testar aqui): sombra de ambiente com transparência (RoomAmbientOcclusion), sombras assadas da fachada da casa 17 (_ShadowTex, 2ª UV), brilho (_Glossiness), normal maps, detalhe de tecido.

## Etapa 169 — Sombra de ambiente com transparência (entregue, aguardando build e teste)
- [x] Teste da 168 não relatado ainda; pedido do usuário: corrigir grama restante em piscinas/escadas (feito na 168) e "o que ficou faltando".
- [x] RoomAmbientOcclusionMaterial: antes saía preto opaco (cor preta × textura). Agora `bake.py` assa RGBA: RGB preto, alfa = canal R da textura × 0,28. O renderizador já mistura por alfa da textura, então as chapas viram sombra suave nos cantos dos cômodos. `city2.glb` regenerado (mesmas instâncias/json).
- [ ] Ainda não feito (exige mexer no shader do renderizador e dados extras, sem como testar aqui): sombras assadas da fachada da casa 17 (_ShadowTex, 2ª UV), brilho (_Glossiness), normal maps, detalhe de tecido (_DetailTex).
