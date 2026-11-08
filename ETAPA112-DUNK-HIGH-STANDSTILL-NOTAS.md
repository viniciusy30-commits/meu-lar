# Etapa 112 — VHSync Dunk High + StandStillInCAS preservado

## Dunk High — estado corrigido
- Package original preservado em `mods-sims4/originais/[VHSync] Dunk High Men's Sneakers 1.126.78.package`.
- CASP identifica a peça como `ymShoes`: masculino adulto.
- Conversão para CUP1 usando o corpo `p_body_am5.bin`:
  - slot final: `feet`;
  - 4.244 vértices e 6.232 triângulos;
  - 38 swatches;
  - texturas de 1.024 × 512.
- Assets: `app/src/main/assets/cute/skate/dunk_high_am5.cup` e 38 PNGs de textura.
- Miniatura embutida: `app/src/main/assets/cute/thumbs/dunk_high_am5.png`.

## Correção dos defeitos vistos no avatar
A primeira prévia mostrava duas falhas: a ponta/sola ficava com polígonos pretos pontudos e partes do pé atravessavam o calçado. A causa foi identificada no encaixe:
- `pushOut` é uma rotina de afastamento feita para tecido. Ao aplicá-la à malha rígida do tênis, ela deslocava vértices da biqueira e da sola em direções diferentes, deformando o contorno.
- O CUP1 também não tinha a lista de triângulos do pé-base que devem ser ocultados enquanto o tênis está vestido.

Correções aplicadas:
- `Ts4Cloth` agora preserva a geometria original de peças classificadas como sapatos e não aplica o `pushOut` de tecido.
- `T4Shoe` grava no CUP1 a máscara de 570 triângulos do pé-base, usando os ossos 18, 19, 20, 22, 23 e 24. A canela (ossos 17 e 21) permanece visível acima do cano.
- `Thumb.kt` e `ModStore.kt` aplicam a mesma máscara na miniatura 3D, evitando que a prévia do catálogo mostre o pé atravessando o tênis.
- A sola continua preservada; a rotina de remoção de tampas de calça não é aplicada a sapatos.

## StandStillInCAS
- Package original preservado em `mods-sims4/originais/MizoreYukii_StandStillInCAS_All-in-One.package`.
- Inspeção DBPF: um recurso `0x02D5DF13`, conteúdo XML começando por `<ASM name="CAS">`.
- Não há CASP, GEOM ou textura. É tuning/estado de animação do CAS do The Sims 4, não uma peça 3D nem uma animação que o Meu Lar consiga executar.
- Mantido como arquivo original, sem conversão indevida.

## Render e validações executadas após a correção
- `T4Shoe.java` compilou com `javac` junto aos conversores do projeto.
- Conversão executada novamente a partir do package original: `slot=feet`, 38 swatches, 570 triângulos de pé-base ocultados, `pushed_vertices_total=0` e `max_push_cm=0`.
- `dunk_high_am5.cup` validado: CUP1 com `flags=1`, máscara com 570 índices e tamanho de arquivo consistente; todos os índices da máscara estão dentro dos 9.414 triângulos do corpo.
- As 38 texturas foram regeneradas e verificadas como PNGs válidos de 1.024 × 512.
- Prévia renderizada e inspecionada em 3/4, frente e lateral. A ponta preta deformada desapareceu; o preto restante é a borracha/textura normal da sola.
- Miniatura também renderizada com `Thumb.kt` compilado isoladamente; a máscara de ocultação foi lida corretamente (`hide=570`) e a imagem ficou sem vazamento do pé.
- Limite do teste: não foi possível executar o build Android neste ambiente porque o projeto não contém `gradlew` e não há instalação local do Gradle. O workflow Android deverá fazer o build depois que o ZIP for enviado a `_incoming`; ainda falta testar no aparelho.

## Arquivos principais alterados
- `app/src/main/java/com/vinicius/meular/mods/Ts4Cloth.java`
- `app/src/main/java/com/vinicius/meular/Thumb.kt`
- `app/src/main/java/com/vinicius/meular/ModStore.kt`
- `app/src/main/assets/cute/skate/dunk_high_*`
- `app/src/main/assets/cute/thumbs/dunk_high_am5.png`
- `ferramentas/mods_teste/T4Shoe.java`
- `ferramentas/mods_teste/render_dunk_high_fit.py`
- `ferramentas/mods_teste/cores/dunk_high*.txt`
- `imagens-dunk-high/`
- `mods-sims4/originais/*`
