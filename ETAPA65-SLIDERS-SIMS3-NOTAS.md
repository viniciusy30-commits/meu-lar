# Etapa 65 — Sliders reais do The Sims 3 (corpo e rosto)

## O que mudou
- Os sliders antigos do corpo (adaptados ao Bozo, funções procedurais do BodyMorph) **não são mais usados nos corpos do Sims 3**.
  No lugar entram os sliders do Slider_Master_Files: cada slider é um BlendUnit (FBLN) → FACE → VPXY → **BOND** (ajustes de osso:
  deslocamento, escala, rotação por osso do esqueleto do Sims 3). Aplicados como o jogo faz (repouso + ajuste; M = W'·W⁻¹ por osso).
- **124 sliders** com dados de osso: 53 de corpo e 71 de rosto (nariz, olhos, sobrancelhas, bochechas, boca, mandíbula, orelhas, cabeça).
  Direção positiva/negativa e máscara de idade/sexo escolhidas por grupo (af/am/tf/tm/ef/em/cu/pu), como no jogo.
- Tela do criador (aba de proporções): "Geral" (Altura, controle do app) + "Corpo" e "Rosto" com categorias recolhíveis, nomes em português, -100..100, zerar tudo.
- "Peso" e os outros sliders antigos de corpo saíram da tela para corpos do Sims 3 (o Bozo/corpos antigos continuam com a tela antiga).
- Save: os 163 valores (`ss`) vão no fim da linha do Avatar; saves antigos abrem com tudo em 0 (sem quebrar).

## Arquivos
- `SimSliders.kt` (novo): leitor dos dados, deformação e pesos de pele por proximidade. Conferido contra a referência Python (diferença máx. 0,002 cm).
- `assets/cute/simsliders.txt` (novo, 114 KB): rigs au/cu/pu, cápsulas de influência e os 124 sliders.
- `Avatar.kt` (campo `ss`, save/load), `CuteChar.kt` (setShape(..., ss), refit usa SimSliders), `Creator.kt` (tela), `GameState.kt`.

## Limites (sem enrolação)
- **Nada foi testado no aparelho**; só a matemática (Kotlin x Python) e renders de conferência. Não consegui compilar o app inteiro aqui (sem SDK do Android).
- **Pesos de pele aproximados**: o jogo usa os pesos do GEOM do corpo; aqui são por proximidade dos ossos. Os movimentos são os do jogo, mas
  regiões de transição (axila, virilha, pescoço) podem diferir um pouco.
- **39 sliders de rosto não entram**: são morphs de malha (BGEO) presos aos vértices do GEOM do Sims 3 (ex.: Cheek Bone Width, Iris Size, Pupil*, Ears Point*,
  Chin Slope, Septum*, Lip Thickness, Asian Eyes, Cleft, Jaw Scale...). Para fazê-los certo preciso do GEOM de cabeça/corpo do Sims 3 (arquivo de malha) ou da lista de opções.
- Nomes em português são tradução dos rótulos do jogo; alguns sliders de rosto podem ter pouco efeito visível por serem sutis (também são no jogo).
- Primeira vez que um slider é mexido numa peça nova, os pesos dela são calculados (uma vez por malha); pode dar um pequeno atraso em roupas pesadas.
- CmarNYC_Edit.Package foi ignorado de propósito (não é do Slider Master original).
