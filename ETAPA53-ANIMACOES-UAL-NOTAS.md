# Etapa 53 - Parado / Andar / Correr (aguardando teste)

Pedido: "coloque as animacoes de walk, run e idle o mais parecido possivel com The Sims 3".

Fonte: Universal Animation Library [Standard] (Quaternius, CC0): Idle_Loop, Walk_Loop, Jog_Fwd_Loop, adaptadas aos 55 ossos do app
(mesmo esqueleto/malha do Sims 3 da Etapa 45; malhas e pesos NAO mudaram).

## O que mudou
- `assets/cute/clips_{tf,tm,af,am,ef,em,cu,pu}.bin`: 4 clipes cada: 0 Parado, 1 Andar, 2 Pulo (pose do parado), 3 Correr.
- Ajustes "estilo Sims 3" (calmo): parado sem troca de pes, cabeca erguida; andar relaxado com bracos soltos; correr mais ereto, bracos mais baixos.
  Parametros por clipe em `PARAMS` (ferramentas/etapa53_animacoes_ual.py).
- Pes sem deslizar: pernas por cinematica inversa; velocidade do pe de apoio medida: andar 1,0 m/s, correr 2,45 m/s.
- Kotlin: `WALK_RATE` 0,96 -> 1,0 (CuteChar.kt); velocidade andar 1,28 -> 1,0 m/s e `RUN_SPEED` 2,05 -> 2,45 m/s (Renderer3D.kt) para casar com os passos.
- Ferramentas: `etapa53_animacoes_ual.py`, `etapa53_preview.py`, `ual_glb.py`.
  `python3 etapa53_animacoes_ual.py <assets/cute> UAL1_Standard.glb --out <pasta>`

## Limites
Nao sao as animacoes reais do jogo (o pacote do Sims 3 enviado nao traz animacoes); sao da UAL ajustadas ao estilo. Pulo continua sem animacao.
