# Etapa 6 — tela do criador estilo The Sims (aguardando teste no celular)

## O que entrou
- `Creator.kt` reescrito: categorias (Corpo, Cabelo, Rosto, Roupa, Sapatos, Acessórios) -> sub-abas -> grade 4 colunas de miniaturas -> cores da parte (Original + paleta). Barra de cima com "Girar" (frente/costas) e "Pronto".
- Miniaturas: 98 ícones do próprio pack (OutfitIcons, 128 px) em `assets/cute/icons/<slot>_<id>.png` (minúsculas); os 3 do biquíni foram desenhados em código. Sem ícone = tile "Sem".
- Câmera por categoria/sub-aba (distância, altura e ângulo): cabelo "Atrás" gira para as costas; rosto em close; sapatos nos pés; roupa no tronco/quadril.
- `Renderer3D.kt`: novos `cTargetYaw` (giro suave até um ângulo; o toque do jogador cancela, tratado em `GameView.kt`) e `cShift` (desloca a imagem para cima para o personagem ficar no meio da área livre acima do painel; calculado pela altura do painel). O alvo da câmera agora é o próprio `cTargetY` (antes era 0,14*dist abaixo) e sem o +0,1 na altura do olho.
- Cores salvam a cada toque (antes só no "Pronto"). Formato do save (`Avatar.encode`) NÃO mudou.
- Mapa de cores usado: Pele(0); Olhos(1); Cabelo/Pontas(2,3) também na barba; Blusa/Detalhe(4,5); Saia(6) e Detalhe baixo(9); Sandália/Tiras(7,8); Acessório 1/2(10,11) em óculos, chapéu, chifres/antenas e luvas.

## Base usada
`Avatar.kt`, `CuteChar.kt`, `CuteColor.kt` e `pieces.txt` da Etapa 5 (sem alteração nesta etapa).

## O que testar
1. Cada categoria dá o zoom certo e o personagem aparece inteiro acima do painel (inclusive em tela pequena).
2. Cabelo > Atrás mostra as costas; Frente volta para a frente; "Girar" alterna; arrastar/pinçar funciona e cancela o giro automático.
3. Miniaturas batem com a peça aplicada; selecionada fica com borda branca; a rolagem não pula ao escolher.
4. Cores aparecem abaixo de cada grade e mudam a peça certa.
5. Sem compilador aqui: se o build falhar, corrigir só o erro apontado.

## Revisão 2 (feedback do teste): paisagem, visual e zoom
- App inteiro agora em paisagem (`sensorLandscape` no AndroidManifest). Outras telas (HUD, menus) podem precisar de ajuste de layout: testar.
- Criador em paisagem: personagem à esquerda, painel à direita (46% da largura) com trilho de categorias (emoji), sub-abas, grade 3 colunas com miniaturas maiores, marca de selecionado, cores em grade e botão Pronto. Botões redondos giram o personagem; insets de recorte/barras tratados em `setInsets(l,t,r,b)`.
- Zoom refeito para paisagem (altura visível = 0,61 x distância): sem deslocamento vertical, assim a cabeça não corta; deslocamento horizontal `cShiftX` coloca o personagem no centro da área livre.
- Revisão 3: o personagem tem ~1,55 m (olhos ~1,45), não 1,3; câmeras recalculadas com essas alturas (cabeça não corta mais).

## All Star
- Peça feet/AllStar gerada por ferramentas/allstar.py (região 7 do atlas extra2: cor 1 = lona/faixa, cor 2 = borracha/cadarço). Índice novo no fim de FT_IDS (saves intactos).
- Testar: forma nos pés, animação de andar/pular, recolor, desempenho (~8,9 mil vértices).
