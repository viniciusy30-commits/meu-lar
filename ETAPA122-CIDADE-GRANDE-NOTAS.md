# Etapa 122 — Cidade grande, interiores, praia, parque, veículos, mapa e GPS

## Arquivos
- `City.kt` — grade 7×7 (casa no meio), tabela `T` de bairros, colisão (`blocked`), chão (`groundH`), trânsito, pedestres, carregamento sob demanda (`requestNear`/`service`), malha única de longe (`farAll`).
- `CityGeo.kt` — ruas (uma malha só), casas (5 estilos + mansão), terrenos à venda, prédios (`tower`), lojas (`shopRow`), interiores (`interior`), móveis, praça, parque, igreja, escola, polícia, hospital, posto, supermercado, shopping.
- `Vehicles.kt` — carroceria por perfil extrudado, rodas com aro, faróis etc.; motos com piloto.
- `CityFun.kt` — praia (calçadão, areia, quiosques, píer) e parque de diversões com brinquedos animados (`dyn`).
- `CityMap.kt` — `Gps` (rota pela grade de ruas), `MapOverlay` (mapa em tela cheia), `GpsHud`, `MiniMap`.
- `Water.kt` — `drawSea` (mesmo shader da piscina com ondas maiores, espuma na beira e névoa).

## Entrar nas construções
Cada construção grava a geometria em dois construtores: A (piso, móveis, base das paredes até 0,9 m) e H (o resto).
Os vértices de H ficam numa faixa contínua por material; quando o jogador entra, `Part.skipA/skipB` pula essa faixa (sem malha extra).

## Desempenho
- Montagem da cidade em thread separada; detalhe de cada quarteirão gerado de novo (mesma semente) quando o jogador chega a ~95 m e descartado a ~140 m.
- Longe: todos os quarteirões numa malha só, pulando (`Part.skips`) os que estão em detalhe.
- `draw()` só manda ao GL os uniformes que mudaram.
- Nada foi testado em aparelho aqui: o build do GitHub é a primeira verificação.

## Para a compra de casas (próxima etapa)
`City.Bld.forSale` e `price` já existem; terrenos à venda aparecem no mapa como "Terreno à venda".
