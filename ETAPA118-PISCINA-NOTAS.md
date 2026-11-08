# Etapa 118 — Piscina no quintal (mergulho, nado, sentar na borda)

## O que tem
- **Quintal maior** nos fundos e **piscina** atrás da casa (5 × 6,4 m, 2 m de fundo): deck de pedra, borda branca, azulejo azul e água translúcida (`Models.kt`, medidas em `Pool.kt`).
- **4 animações do Mixamo** convertidas para o esqueleto do Sims 4 (`ferramentas/etapa118_piscina_clipes.py`), clipes 11 a 14 em `clips_am5.bin` e `clips_af5.bin` (os 11 antigos não mudam): `RUN_DIVE`, `SWIM`, `SWIM_EDGE`, `TREAD`.
- **Correndo** em direção à água (a menos de ~3 m): mergulha sozinho. Na água: parado boia, movendo nada. Empurrando contra a borda: nada até ela e sai para o deck.
- **Novo (Etapa 119) — andando normal até a borda:** empurrando o analógico contra a água por 0,25 s (andando, sem correr), o personagem se vira para a água, **senta na borda branca com as pernas dentro d'água** (clipe de sentar) e, depois de ~1,3 s, **escorrega para dentro** e passa a boiar.
  - Sentado na borda: empurrar o analógico **para a água** ou apertar **pular** entra na hora; empurrar para **trás/lado** levanta e volta para onde estava.
  - **Pular** olhando para a piscina, perto da borda (até ~3 m): mergulha (Run_To_Dive), mesmo parado.
- Só os corpos do Sims 4 (am5 e af5) têm os clipes de piscina.

## Arquivos
`Pool.kt` (novo), `Models.kt`, `Renderer3D.kt`, `CuteChar.kt`, `clips_am5.bin`, `clips_af5.bin`, `ferramentas/etapa118_piscina_clipes.py`.

## Ajustes finos (se precisar)
- Altura/posição do assento na borda: `Pool.SIT_SEAT_Y` (0,06) e a origem do corpo na borda da água (`trySitEdge`, `swToX/swToZ`). Se as pernas ficarem muito dentro ou fora, mude o ponto `swToX/swToZ` (hoje exatamente na borda da água; o quadril fica ~0,23 m para trás).
- Tempo até entrar sozinho: `Pool.SIT_WAIT`; duração do escorregar: `Pool.ENTER_T`; quanto ele entra: `Pool.ENTER_DIST`.
- Nada foi compilado neste ambiente (sem Kotlin/Gradle): o build do GitHub é o primeiro teste.
