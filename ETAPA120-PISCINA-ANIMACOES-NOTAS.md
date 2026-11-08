# Etapa 120 — Piscina mais bonita e animações conectadas

## Água (`Water.kt`, novo)
- Programa de shader próprio: malha 40 × 50 com ondas no vertex shader, fresnel, reflexo do céu/sol, cáusticas no fundo, cor por profundidade, espuma na borda.
- `Water.ripple(x, z, força)`: ondinhas em anel (até 8 ao mesmo tempo). Chamado no mergulho, ao nadar, boiando, nadando até a borda e ao escorregar da borda.
- Se o shader não compilar no aparelho, volta sozinho ao plano de vidro da Etapa 118.

## Visual da piscina (`Models.kt`)
- Faixa de azulejo escuro na linha d'água, escada de inox (lado da casa), 2 luzes no fundo.

## Animações (`CuteChar.kt`) — vale para o jogo inteiro
- **Mistura viva:** na troca de clipe o clipe anterior continua tocando enquanto some (antes a última pose ficava congelada → parecia travado).
- **Entrada no mesmo passo:** WALK, RUN, CROUCH_WALK, SWIM, TREAD e CROUCH começam no quadro cujas pernas mais combinam com a pose atual (`bestPhase`).
- **Tempos por par de clipes:** `blendDur(pc, c)` (andar↔parar 0,32 s, andar↔correr 0,35 s, freada 0,40 s, aterrissar 0,22 s, nadar↔boiar 0,6 s...).

## Nado (`Renderer3D.kt`)
- Velocidade com aceleração/freio (`swVX/swVZ`), giro mais lento na água, boia subindo e descendo, histerese nadar/boiar (`swimAnimMove`), subida para a borda em 1,2 s.

Nada foi compilado aqui (sem Gradle): o build do GitHub é o primeiro teste.
