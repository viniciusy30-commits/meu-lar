# Etapa 171 — Catálogo Hds na loja
Nova aba **Catálogo Hds** na loja do Meu Lar: escolha a categoria (Portas e janelas, Sofás e poltronas, Quarto, Cozinha, Banheiro...) e compre o móvel para colocar na casa.
- 1.129 móveis, 13 categorias, 43 MB de assets (`app/src/main/assets/hds/mobilia`).
- Código: `GameState.kt` (Type agora é classe), `HdsMob.kt` (novo), `Glb.kt`, `MainActivity.kt`.
- Limitações conhecidas: portas/janelas não encaixam na parede ainda; variações de cor por máscara não foram extraídas; um modelo (OutdoorArbor2) foi descartado por tamanho absurdo.
