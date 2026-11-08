# Etapa 112 — VHSync Dunk High + preservação do StandStillInCAS

## Dunk High
- Package original preservado em `mods-sims4/originais/[VHSync] Dunk High Men's Sneakers 1.126.78.package`.
- CASP identifica a peça como `ymShoes`: masculino adulto.
- Conversão para CUP1 usando o corpo `p_body_am5.bin`:
  - slot final: `feet`;
  - 4.244 vértices e 6.232 triângulos;
  - 38 swatches;
  - texturas de 1.024 × 512;
  - deslocamento máximo registrado no encaixe: 2,91 cm.
- Correção no `Ts4Cloth`: a rotina de remoção de tampas horizontais era própria para barras de calças e apagava triângulos da sola. Malhas baixas classificadas como sapatos agora preservam a sola e não recebem a exclusão da barra.
- Cadastro no `ModStore`: item masculino adulto, categoria Sapatos, com seletor das 38 cores. Não altera o formato dos saves.
- Assets: `app/src/main/assets/cute/skate/dunk_high_am5.cup` e 38 PNGs de textura.
- Miniatura embutida: `app/src/main/assets/cute/thumbs/dunk_high_am5.png`.

## StandStillInCAS
- Package original preservado em `mods-sims4/originais/MizoreYukii_StandStillInCAS_All-in-One.package`.
- Inspeção do DBPF: um recurso `0x02D5DF13`, conteúdo XML começando por `<ASM name="CAS">`.
- Não há CASP, GEOM ou textura. É tuning/estado de animação do CAS do The Sims 4, não uma peça 3D renderizável.
- Mantido como arquivo original; não foi convertido para animação do Meu Lar, pois o app não interpreta ASM tuning do The Sims 4.

## Render e validações executadas
- `T4Shoe.java` compilou com `javac` junto aos conversores do projeto.
- Conversão executada a partir do package original; retorno `slot=feet`, 38 swatches.
- `render_dunk_high_fit.py` executado com sucesso (`DUNK_HIGH_RENDER_OK`).
- Prévia gerada com a mesma projeção e rasterização de `Thumb.kt`: 3/4, frente e lateral. As imagens mostram o par, a sola preservada e a entrada do tornozelo no cano.
- Texturas verificadas: 38 PNGs válidos, 1.024 × 512, sem pixels transparentes no atlas convertido.
- Limite do teste: não foi executado um APK Android nem testado em aparelho/emulador neste ambiente. O build Android será acionado pelo workflow após o ZIP ser extraído em `_incoming`.

## Arquivos principais adicionados/alterados
- `app/src/main/java/com/vinicius/meular/ModStore.kt`
- `app/src/main/java/com/vinicius/meular/mods/Ts4Cloth.java`
- `app/src/main/assets/cute/skate/dunk_high_*`
- `app/src/main/assets/cute/thumbs/dunk_high_am5.png`
- `ferramentas/mods_teste/T4Shoe.java`
- `ferramentas/mods_teste/render_dunk_high_fit.py`
- `ferramentas/mods_teste/cores/dunk_high*.txt`
- `mods-sims4/originais/*`
