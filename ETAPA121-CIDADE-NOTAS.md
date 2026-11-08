# Etapa 121 — Cidade + FPS da água

## FPS
- `Water.kt`: altura e normal das ondas calculadas numa passada só (antes 3×, com 8 ondinhas cada), malha 30×38, fragment em precisão média sem `pow`, e a água só é desenhada quando está na tela.

## Cidade (`City.kt`, novo)
- Grade 5×5 quarteirões de 48 m com ruas de 16 m (3,5 m de calçada de cada lado). O quarteirão do meio é o da casa; sai-se pelo portão da frente.
- Tipos por quarteirão na tabela `type` em `City.build` (praça em frente de casa, lojas, supermercado, posto, hospital, centro, hotel, escola, polícia/bombeiros, parque, prédios, casas).
- Materiais novos em `Gfx.kt`: `ASPHALT`, `FACADE` (janela a cada 3 m), `SIGN` (atlas de letreiros desenhado em `City.signBitmap`).
- Trânsito: 2-3 carros por faixa, semáforo em ciclo de 24 s (`lightPhase`), fila, param para o jogador. Pedestres dão volta nos quarteirões.
- Desempenho: cada quarteirão/rua é um pedaço separado com corte por câmera e distância (235 m); carros até 140 m, pedestres até 55 m. Névoa leve depois de 70 m.
- Colisão: `City.blocked` (prédios, muros, carros), chão `City.groundH` (calçada 15 cm). Regras do quintal em `Renderer3D.yardOk`.
- Sala de testes: sem cidade (como antes).
