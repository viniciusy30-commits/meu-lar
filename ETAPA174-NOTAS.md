# Etapa 174 — Casas nos lotes certos, sem sobrar só gramado
- Lotes com profundidade medida em cada ponto da rua (`TownHouses.plan`): antes a rua inteira usava uma profundidade só, e se um ponto
  (triângulo, esquina, rua curva) não coubesse, o lado inteiro da rua ficava sem casa. Agora cada lote mede o que cabe ali:
  a 1ª fileira leva metade do quarteirão, a do outro lado leva o que sobrou (fundos encostados), e cunhas/triângulos recebem lotes mais rasos.
- Ao medir, os lotes param no parque, na casa do jogador e em outros lotes (nada se sobrepõe).
- Sobras dos quarteirões residenciais (`TownSmall`): em vez de "sobrados colados" e pátio pavimentado no meio da grama (a calçada sem sentido),
  vira jardim com árvores e arbustos.
- Mansões (nível 4) continuam com a lógica antiga.
- Arquivos: `TownHouses.kt`, `TownSmall.kt` (pasta `app/src/main/java/com/vinicius/meular`).
