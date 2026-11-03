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
