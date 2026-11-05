# Etapa 54 - Importar mods (.package) direto pelo jogo (aguardando teste)

Criador > aba **Mods** (ícone +) > "Importar .package": abre o seletor de arquivos do Android (pode marcar vários). A conversão roda no próprio celular.

## O que lê
- **The Sims 2** (DBPF 1.x): malha GMDC + textura TXTR. Testado com os 3 MESH_*CBOY e as 3 texturas do projeto.
- **The Sims 3** (DBPF 2.0) e **The Sims 4** (DBPF 2.1): malha GEOM + textura DDS/DST/RLE2. Só testado com pacotes sintéticos que montei (não havia package real do Sims 3/4 aqui); DST (textura embaralhada do Sims 3) é palpite do formato.
- Compressão: zlib, RefPack/QFS, DIR do Sims 2.

## Como encaixa (mods/Fit.java)
- Eixos e escala automáticos: busca (escala, altura, profundidade) que minimiza a distância entre a roupa e o corpo atual. Sims 3 = quase só ajuste fino; Sims 2 e 4 = busca maior.
- Sims 2: braços vêm em T; giram em volta do ombro para a pose A do corpo (ângulo vem de bodyrig.txt).
- Pesos de osso: copiados dos vértices do corpo mais próximos (mesmo lado). Cabelo/chapéu seguem a cabeça (osso 8, peito 4). Os pesos do arquivo original são ignorados.
- Tipo da peça (blusa, calça/saia, roupa inteira, sapato, cabelo, chapéu) é deduzido pela altura que a malha cobre.
- Sims 2: triângulos que caem em área preta/lisa da textura (antebraço, mão, pescoço, canela - o jogo original pinta a pele ali) são removidos para aparecer a pele do corpo.
- Corpo por baixo do tecido: `Cover.mark` esconde os triângulos do corpo cobertos (calculado em CuteChar.rebuildActive).

## Fluxo
1. Importar a malha (MESH_...package). Entra cinza se não tiver textura.
2. Importar o package de cor (recolor): é aplicado na última peça sem textura. Ou botão "Textura" na peça escolhe qual.
3. "Vestir"/"Tirar" (um por tipo; roupa inteira troca blusa+calça). "Excluir" apaga.
- Arquivos em filesDir/mods (index.txt, worn.txt, <id>.cup, <id>.png). Peça é do grupo idade+sexo do corpo no momento da importação (só aparece/veste nesse grupo).

## Limites conhecidos
- Encaixada no corpo "normal"; em Magro/Gordo a roupa não acompanha (pode furar ou afundar).
- Sims 2: transparência (cabelo com recorte) não suportada; textura de recolor deve vir em package separado ou junto.
- Várias malhas no mesmo package: escolhe a de melhor encaixe (LOD mais detalhado).
- Sem compilador Android aqui: Java compilado e testado no PC; Kotlin (ModStore) checado com kotlinc + stubs; CuteChar/Creator/MainActivity só revisados. O build do GitHub é a prova final.

Arquivos: mods/*.java (novos), ModStore.kt (novo), CuteChar.kt, Creator.kt, MainActivity.kt, Avatar.kt.

## Ajuste 2
- Criador: saíram as abas antigas (Cabelo, Roupa, Sapatos, Acessórios e Óculos/Barba do Rosto), que não faziam nada nos corpos do Sims. Agora: Base, Corpo, Rosto e **Roupas** (importar, vestir, tirar, excluir).
- Textura preta: texturas quase todas pretas são ignoradas (a peça entra cinza); toda textura importada vira potência de 2 e carrega com CLAMP (no OpenGL ES 2 textura de tamanho "quebrado" com repetição aparece preta).

## Ajuste 3 (boneco todo preto e careca depois de importar)
Causa: o seletor de arquivos pausa o app; ao voltar o OpenGL recria o contexto e as texturas de pele do Sims (sk_*.png) ficavam com o número antigo (morto) -> corpo preto. `CuteChar.initGl` agora zera essas peças e sobem de novo no próximo quadro. (Bug antigo: acontecia também ao sair e voltar ao app no criador.)

## Ajuste 4: .zip e .rar
Importar mods aceita .package, .zip e .rar (extrai os .package de dentro). RAR usa a biblioteca junrar (app/build.gradle.kts); só RAR4 (o RAR5 mais novo mostra aviso para extrair no celular). Zip é nativo.

## Ajuste 5
Quando o package não tem malha legível, a mensagem mostra a causa (GEOM achados/erros e tipos de recurso do arquivo).

## Ajuste 6
Package de recolor do Sims 3 (só CASP + texturas máscara, ex.: "Layered Shirt ..." do newone08, que usa o modelo da EA "amTopTshirtTightUntuck") não traz malha: o jogo agora explica isso na mensagem. Para importar, o package precisa ter GEOM dentro.

## Etapa 55 - Roupas prontas (estilo da referência): camiseta oversized CHAOS, calça cargo baggy preta, tênis preto e branco
Aba Roupas > aparecem sozinhas (adulto/jovem/idoso, masculino e feminino). Geradas direto em cima do corpo do Sims 3 de cada grupo (ferramentas/skate/, `python3 run2.py <grupo>`):
- Camiseta: manga até o cotovelo, caimento largo, gola canelada, barra e punhos com costura dupla, estampa CHAOS (desenho original) na frente.
- Calça cargo: perna reta e larga, bolsos cargo laterais com volume + aba + botão de pressão, bolsos de trás com aba, cós com passadores e botão, braguilha, alça com fivela na lateral, barra empilhada sobre o tênis, lavagem desbotada, costuras cinza.
- Tênis: baixo, couro branco com detalhes pretos (calcanhar, gola, lateral, cadarço), feito a partir do All Star recortado.
- Vêm como "peças embutidas" do ModStore (assets/cute/skate/*.cup/png); só sobem para a memória quando vestidas.
Limites: só corpo "Normal" (magro/gordo não acompanham); sem jaqueta jeans, moletom, mochila e corrente da foto; pesos de osso copiados do corpo (a barra da camiseta e a calça balançam junto das pernas).

## Etapa 55, ajuste 2 (bugs vistos no vídeo)
- Calça colava as pernas e esticava ao andar: agora cada perna tem pesos próprios (os vértices seguem o eixo da perna do lado certo, mistura só no meio das pernas); pernas mais finas (raio 10,4-12,6 cm).
- Calça cobria o tênis: a barra para na altura do cano do tênis (y=9), tubo mais curto.
- Camiseta "cortada em duas partes" na cintura: a barra longa (parte de baixo) copiava pesos das pernas e abria uma fresta ao andar; agora segue o tronco/quadril (só 50% perna na ponta da barra).
- Teste: ferramentas/skate/skin_test.py aplica um quadro das animações do jogo nas peças (andar/correr) e desenha.
- Não é bug da roupa: o anel branco que aparece no peito nos vídeos é o marcador de destino do toque na tela (Renderer3D "walk" ring).

## Etapa 55, ajuste 3
- Pescoço sumia (via o fundo azul entre o pescoço e a gola): a pele escondida sob a roupa (Cover) pegava também a base do pescoço. Agora, sob blusa/roupa inteira, nada acima de (altura do pescoço - 7 cm) é escondido (Cover.mark com ymax).
- Divisão na cintura da camiseta: a barra era uma peça separada com borda própria (costura tracejada + beirada). Agora a barra continua os MESMOS vértices da borda de baixo do tronco (sem emenda, sem beirada); camiseta é uma peça contínua.
- Calça: barra longa, desce quase até o chão atrás e nos lados e sobe na frente (o tênis aparece e nada atravessa); acabamento sem babados; bolsos cargo mais marcados; tirei a alça/fivela e as listras que deixavam os lados feios; textura lavada mais uniforme.

## Etapa 56 — Cabelo preto ondulado (da referência)
- Novo item embutido "Cabelo ondulado preto" (slot hairBack) para os 6 grupos: assets/cute/skate/hair_<g>.cup/.png.
- Gerado por ferramentas/skate/sk_hair.py: capacete de cabelo (casca sobre a cabeça, ondulada) + ~65 mechas em cartões com alfa (franja na testa, laterais cobrindo as orelhas, nuca, cachos no topo). Pesos: osso 8 (cabeça), misturando com o osso 4 perto do pescoço.
- CuteChar.runModJobs: peças de cabelo (chave "hairBack/") agora são desenhadas sem backface culling (cartões dupla-face).
- Ao vestir, o cabelo padrão (hairBack/H_xx) é ocultado automaticamente (Avatar.wearKeys).
- Onde: Customização > Roupas > Importar mods > Cabelo ondulado preto > Vestir.

## Etapa 57 — Calça contínua + cabelo wolf cut
- Calça cargo refeita (ferramentas/skate/sk_cargo2.py): a perna é uma peça única até a barra (sem o tubo duro separado). A barra assenta sobre o tênis (altura calculada pela superfície do tênis), cai quase até o chão atrás e nos lados, com dobras leves; suavizada para não ter degrau.
- Removidas as listras claras das costuras laterais/internas da textura (sk_paint2.py).
- Cabelo trocado: "Cabelo wolf cut preto" (sk_hair2.py): médio, repartido ao meio, franja em cortina, camadas (curtas em cima, compridas na nuca). Substitui o cabelo ondulado da etapa 56 (mesmos nomes de arquivo hair_<g>).

## Etapa 58 — Customização refeita (estilo The Sims) + correção do T-pose
**T-pose ao abrir o jogo (corrigido):** o corpo salvo era aplicado (CuteChar.setWear) antes do initGl carregar os clipes/alturas; os clipes falhavam, `simFail` ficava ligado e frame() nunca tentava de novo, então o boneco ficava parado na pose original até escolher um corpo no criador. Agora:
- `applySimState()` (novo) aplica altura/clipes/tabela do esqueleto; é chamado em setWear e de novo no fim do initGl.
- `useSimClips` não conta "ainda não carregou" como falha; frame() tenta de novo a cada 1,5 s se falhou.

**Tela de customização (Creator.kt) refeita:**
- Categorias (arco): Base, Corpo, Cabelo, Rosto, Roupas (Blusas / Calças / Inteiras), Sapatos, Acessórios.
- Roupas, cabelos, sapatos e acessórios aparecem numa grade de fotos de prévia (miniaturas) com nome, "Nenhum"/"Careca" e o botão tracejado "Importar .package" no fim da grade. Peças importadas ganham miniatura gerada na hora (Thumb.kt) e botão ✕ para excluir; sem textura mostra "sem textura +".
- Base só tem Idade/Sexo/Corpo; cabelo agora é a categoria Cabelo (Careca / Liso longo / Wolf cut preto / importados). Sumiram "Personagens prontos" e o seletor repetido nas Proporções.
- Itens antigos do Bozo removidos do manifesto (assets/cute/pieces.txt) e os .bin deles apagados (~8 MB). Ficam só os corpos do Sims 3, o cabelo padrão (Heartbeat) e as peças novas.
- Miniaturas embutidas: assets/cute/thumbs/<id>.png (tee_/cargo_/shoe_/hair_/hairdef_ + grupo), geradas por ferramentas/thumbs/GeraMiniaturas.kt usando o mesmo Thumb.kt do jogo.
- Camera: cada categoria enquadra a parte (cabelo/rosto de perto, calças nas pernas, sapatos nos pés).

## Etapa 59 — Cabelo estilo Sims 4, calça reta, Jordan e jaqueta
- **Cabelo (sk_hair3.py):** médio, repartido ao meio, franja em cortina, camadas. Agora é uma "saia" contínua de cabelo + mechas grossas de seção arredondada, opacas (sem recorte por alfa, sem o pontilhado), com textura preta e brilho azulado suave. Substitui o wolf cut antigo (mesmos arquivos hair_<g>).
- **Calça (sk_cargo2.py):** sem o "balão" nos quadris/coxas: perna reta e larga (raio quase constante), bolsos de coxa achatados. Barra continua assentando sobre o tênis.
- **Tênis:** Jordan 1 Low preto e branco modelado do zero (sk_jordan.py): sola com friso e costura, bico preto perfurado, painel branco com faixa lateral preta, calcanhar e colarinho pretos, língua, cadarços. Sem logos/marcas. Arquivos shoe_<g> (nome na lista: "Jordan preto e branco").
- **Jaqueta jeans preta lavada (sk_jacket.py):** nova peça no tipo "jacket" (Roupas > Jaquetas), veste POR CIMA da blusa: gola virada, botões, bolsos do peito com aba, pences, carcela/pences nas costas, punhos com botão, cós. Ao vestir a jaqueta, a manga da blusa por baixo some (CuteChar.rebuildActive) para não atravessar. "jacket" entrou em MANAGED e nas listas de cobertura do corpo.
- Miniaturas regeneradas (inclui jaqueta); Thumb.kt enquadra "jacket" de frente.

## Etapa 60 — Regata baggy (Baggy Singlet Set, ArthurGoring / Mod The Sims) embutida
- Pacote Sims 3 (GEOM + 3 estampas) convertido para os corpos masculinos jovem/adulto/idoso (am, tm, em) com o próprio importador (Fit), depois refinado offline em ferramentas/skate/sk_singlet.py: a parte de cima ficava 1-2 cm DENTRO do corpo (sumia atrás da pele) -> empurrada para fora com margem (decollide); malha subdividida 1x; recorte da regata feito por ALFA na textura (bordas limpas) e não por triângulo.
- 4 itens em Roupas > Blusas: branca, preta, "I'll love you when you're dead" (preta) e "Haters be hatin" (preta). Arquivos assets/cute/skate/singlet_<variante>_<grupo>.cup/.png.
- CuteChar: peças com alfa agora são desenhadas sem culling (p.cull=false) — vale para cabelos e roupas recortadas. Peças com alfa não escondem triângulos do corpo (a pele aparece pelos recortes).
- Ferramentas de diagnóstico do importador em ferramentas/importador (listar GEOMs, dump de texturas, ajuste por grupo).
- Achado para o importador: pacotes Sims 3 de roupa justa podem afundar no corpo do app; vale aplicar o "decollide" ao importar (ainda não feito no app).

## Etapa 61 — Cabelo, Jordan e calça mais bonitos
- Cabelo (sk_hair4.py): mechas 3D (tubos achatados e afilados) em camadas: base longa, camada do meio wolf cut com pontas para fora, volume bagunçado no topo, franja bagunçada até as sobrancelhas e mechas laterais emoldurando o rosto. Capacete colado no couro cabeludo (sem "disco" liso no topo). Textura com brilho ao longo da mecha.
- Jordan (sk_jordan.py): perfil mais baixo; cada parte (cabedal, sola, língua, cadarço, gola) com atlas próprio (antes a projeção sobreposta borrava a pintura); biqueira, gola, calcanhar e painel dos cadarços pretos, faixa lateral em arco, cadarços brancos, sola branca com borracha escura.
- Calça (sk_cargo2.py): eixo da perna reto (sem dobra no joelho), raio mais uniforme na coxa; atrás e nos lados a barra passa POR FORA do tênis e cai até ~2 cm do chão; na frente assenta no peito do pé.

## Etapa 62 — Correção do cabelo (prints do jogo)
- Buraco/redemoinho no topo: a cúpula do cabelo agora é mais grossa no topo (colada no couro cabeludo + até 2 cm), com UV planar e textura isotrópica (sem o redemoinho do mapeamento por azimute), e foram adicionadas mechas que sobem dos lados até a coroa e mechas de raiz alta cobrindo a cúpula.
- Franja: pontas acima dos olhos (centro ~176,8; laterais ~173,5); antes cobria os olhos.
- Camadas do meio e da base saem acima da cúpula (offsets maiores). Gerador: ferramentas/skate/sk_hair4.py.

## Etapa 63 - animações novas (Mixamo enviadas pelo usuário)
- Parado (Idle.fbx), Correr (Running_1.fbx), Pulo (Jump_1.fbx) e Pulo correndo (Running_Jump.fbx, clipe novo nº 4) substituem os anteriores; Andar continua o da UAL (não foi enviado).
- `ferramentas/anim_fbx/*.fbx` + `mixamo_src.py` (MixClip, air_window) + `etapa53_animacoes_ual.py` regeneram `assets/cute/clips_*.bin` (5 clipes: 0 parado, 1 andar, 2 pulo, 3 correr, 4 pulo correndo).
- Pulos: a subida do quadril é retirada do clipe (quem sobe é a física do jogo); o trecho no ar é esticado para 0,71 s (tempo do pulo do app).
- Renderer3D: pulo parado tem agachada de 0,14 s antes de sair do chão; pulo correndo se estava correndo; a recuperação do pouso toca até o fim (ou corta se o jogador andar). RUN_SPEED 2,1 -> 3,2 m/s (passo do clipe novo). CuteChar: RUNJUMP=4 (sem corpo do Sims cai em JUMP).
- Não testado no aparelho; o app não foi compilado por inteiro aqui.
- O cabelo da Etapa 62 foi mantido como estava (o pedido de "esquecer" o zip foi lido como "não é o foco agora").
- Andar também trocado: male_Walking_3.fbx (corpos masculinos tm/am/em) e f_male_Walking_2.fbx (os demais, incl. criança/bebê). O masculino tinha deslocamento de raiz (1,8 m/s), retirado. Velocidade de andar do jogo 1,0 -> 1,7 m/s (WALK_SPEED, Renderer3D); duração de cada clipe ajustada a essa velocidade.

## Etapa 64 — Cabelo Bernard (Sims 4, JohnnySims)
- Mesh original (14 216 vértices, 2 UV) lido do .package V1 (GEOM v14, LOD0), textura preta recortada (metade esquerda do atlas, u*2), alpha-cut 0.45.
- Ajustado por corpo (af, am, tf, tm, ef, em): escala não uniforme + inclinação (Nelder-Mead), elevação suave do topo e empurrão radial só onde o fio entra no crânio. Mesh não é refeita, só deformada suavemente.
- Itens embutidos `bern1_<grupo>` (assets/cute/skate/*.cup/.png + thumbs). Registrados no ModStore.
- Crianças (cu) e bebês (pu) também: o ajuste roda com a cabeça do corpo reduzida ao tamanho adulto e o cabelo volta à escala real. Tampa de couro cabeludo (0,4 cm acima do crânio, textura preta) tapa as falhas da nuca e do topo. V2 não incluído. Não testado no aparelho.
- Viseira: as mechas que saíam 12 cm à frente da testa são comprimidas e caem sobre a testa (drape).

## Etapa 66 — Short preto e Chinelo estilo Kenner (peças do jogo)
- `short_<grupo>` ("Short preto", categoria Calça/Bermuda): short baggy preto logo acima do joelho, cós elástico com cordão e costuras. Feito sobre cada corpo (af, am, tf, tm, ef, em).
- `kenner_<grupo>` ("Chinelo estilo Kenner", categoria Sapato): chinelo de dedo com solado grosso, tudo preto: palmilha com textura de pontinhos e tira acolchoada em Y (modelo Kenner Red/Pro); marcado como "alpha" no ModStore para NÃO esconder a pele do pé (senão o pé some por baixo do solado). Sem logotipo da marca (só o estilo).
- Arquivos: assets/cute/skate/{short,kenner}_<g>.cup/.png e assets/cute/thumbs/{short,kenner}_<g>.png; itens registrados no ModStore.kt.
- Não testado no aparelho. Crianças (cu/pu) não têm essas peças (igual à cargo/jordan).
