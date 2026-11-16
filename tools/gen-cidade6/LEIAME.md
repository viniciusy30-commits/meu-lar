# Cidade 6 — Meu Lar (GLB)

Cidade nova, desenhada do zero (2,5 × 2 km), gerada por `tools/gen-cidade6/build6.py`.
Saída em `cidade6/` na raiz do repositório.

## Arquivos

| Arquivo | O que é |
|---|---|
| `cidade6/cidade6_completa.glb` | Construções (casas, prédios, comércio, cívicos) num GLB só, **texturas embutidas** (abre direto no Blender). |
| `cidade6/cidade6_vegetacao.glb` | Complemento do GLB único: ruas, calçadas, pontes, cais, terreno, água, orla, parques, árvores, arbustos e flores (mesma origem; importe os dois juntos). Separado para cada arquivo caber em < 100 MB. Carros e mobiliário de rua só nos tiles. |
| `cidade6/tiles/tile_II_JJ.glb` | A cidade em pedaços de 250 × 250 m, **com tudo** (carros, postes, placas...). Cada tile tem um nó por camada (`ruas_…`, `lotes_…`, `vegetacao_…`, `carros_…` etc.). |
| `cidade6/tiles/texturas/*.jpg` | Texturas compartilhadas pelos tiles (uri relativa `texturas/x.jpg`). |
| `cidade6/cidade6.json` | Manifesto: lista de tiles (origem, triângulos), **casas do jogador**, colisões, ponto de nascimento. |

## Eixos e unidades
X = leste, Z = sul, Y = para cima, em metros (mesmo eixo do glTF). Cada nó de tile tem `translation` = canto do tile;
os vértices são relativos a ele.

## Casas do jogador (as 17 da Cidade 5)
Os lotes estão **vazios** (só gramado, cerca de quintal e caixa de correio), no tamanho de cada casa do `city2.glb`
+ recuos. Para cada casa, o manifesto (`casas_jogador`) traz:
- `k`, `casa`, `modelo` (nome do nó no `city2.glb`), `bairro`;
- `centro` [x, y, z]: onde fica o centro da casa;
- `frente` [fx, fz]: direção para onde a frente da casa deve olhar (para a rua);
- `yaw_graus`: o mesmo, como rotação em Y (`atan2(fx, fz)`: 0 = frente para +Z/sul);
- `lote` (4 cantos), `lote_m`, `casa_m`, `recuo_frente_m`.

Os GLB também têm nós vazios `CasaJogador_KK_<modelo>` nesse ponto, já girados (servem de marcador ao importar).

## Materiais / texturas
Um material por textura (JPEG 512 px, repetição). A cor do vértice (COLOR_0) multiplica a textura: o siding, o reboco
e as telhas são claros e recebem a cor de cada casa. Índices de 16 bits (primitivas com < 65 mil vértices).

## O que tem
- **Centro**: grade de quadras de 120 m, prédios colados com loja no térreo (fachadas por andar), quadras de torres de vidro
  sobre praças, Prefeitura com cúpula de frente para o **Parque Central** (lago, fonte, coreto, playground, caminhos),
  Igreja Matriz com praça, hospital.
- **Subúrbios** (oeste, norte, leste): ruas de casas americanas (ranch, colonial, craftsman, cape cod, moderna) com garagem,
  varanda, janelas, chaminé, entrada de carro, caixa de correio, cerca de quintal, cerquinha branca, piscina, depósito;
  árvores na faixa de grama; avenidas com comércio (postos, supermercados, galerias com estacionamento); 3 escolas com campo.
- **Ruas**: asfalto, guias, calçadas com juntas, faixa de grama, canteiro central nas avenidas, faixas pintadas, faixas de
  pedestre, linhas de retenção, semáforos, placas de PARE, postes, hidrantes, carros estacionados.
- **Rio** com cais de pedra, guarda-corpo, calçadão ribeirinho, quadras, pontes (com postes) e passarela em arco.
- **Orla**: Av. Beira-Mar com palmeiras, calçadão, quiosques, praia com guarda-sóis e postos de salva-vidas, píer;
  hotéis de frente para o mar; marina com píeres e barcos na foz do rio.
- **Morros** com mata nas bordas norte, oeste e leste.

## Regerar
```
cd tools/gen-cidade6
pip install shapely mapbox-earcut scipy numpy pillow
python3 build6.py            # SINGLE=leve (padrao) | SINGLE=0 para nao gerar o GLB unico
```
