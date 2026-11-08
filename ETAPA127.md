# Etapa 127

- **Céu** (`Sky.kt`): cúpula com degradê por vértice (28×56), sol em camadas, nuvens procedurais (ruído fractal num plano alto, iluminação do lado do sol) numa textura 1024×256 calculada fora da thread do GL; a cúpula das nuvens gira devagar. Névoa ajustada para a cor do horizonte e mais longe.
- **Sombras** (`Shade.kt`): sol fixo → sombras projetadas calculadas na montagem (fecho convexo da base + base deslocada). Recortadas nas faixas de asfalto (rente ao asfalto) e no resto (rente à calçada). Uma malha só, desenhada no passe de vidro com escrita de profundidade (sem escurecer em dobro).
- **Água natural** (`Water.FSN`): mar (modo 1), lago (modo 2) e tanque de chafariz (modo 3, raio negativo em `City.lakes`). Harness: `WaterSim.kt` espelha o shader.
- **Lago** (`CityGeo.lake`): terreno em grade com margem irregular, gramado com buraco (`lawnHole`), ponte em arco com altura em `City.bridges` (groundH).
- **Letreiros** (`CitySign.kt`): atlas 2048×2048 com marcas (64 base + 32 variantes + 16 bandeiras), estilos BOX/LETTERS/NEON/BOARD/AWNING/PLATE, `Signs.mount/blade/awning/doorDetails/aframe/planter`.
- **Folhas/letreiros**: recorte sem mistura (`solid`) + mipmaps que preservam a cobertura (`Tex.uploadCoverageMips`).
- **Praça** refeita; **móveis** (sofá, poltrona, cadeira, escritório, mesa, mesa de centro, planta com folhas, luminária) refeitos; palmeiras com folíolos.
- **Bugs**: torres frente/fundo se sobrepondo, árvores/piscina invadindo casas do lote de trás, postes da praça no asfalto, paredes de lojas vizinhas se cruzando.
