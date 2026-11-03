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
