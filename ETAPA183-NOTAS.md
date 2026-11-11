# Etapas 182 e 183 (Relevo.kt) — NÃO compiladas: rodar o build e conferir

## 182 — ruas
- Avenida/rodovia (c 0 e 1): guia baixa + faixa de grama + cerca (mourões a cada ~3 m e 2 travessas). Pontes ficam sem cerca (têm parapeito).
- Rua de bairro: guia fina + calçada larga (local 2,4 m, coletora 2,0 m) em piso TILE claro.
- Rodovia que cruza a ilha da Praça Central: sem guia nem cerca sobre a ilha (nearIsland).
- curbW/CWF agora: 0,1 -> 1,4 | 2 -> 2,0 | 3 -> 2,4. city3.json e relevo.bin regenerados (gen_city7.py): casas, rotatórias, terreno e pontes idênticos.

## 183 — gráficos
- Árvores: Flora do HDS (oak_a, oak_b, cherry_a, pine_a; pinheiro cresce com a altitude) no lugar das pirâmides. Pedaço de árvore tem 1 triângulo vazio só para receber a flora (c.pend).
- Água: cor por vértice, turquesa rasa -> azul funda, espuma na margem; leito escurece com a profundidade. Continua plana (sem ondas animadas).
- Pontes: parapeito com duas faces + capa de pedra, postes de luz a cada 4 trechos, pilares duplos com travessa.
- Manchas escuras no asfalto: causa não confirmada (ver conversa).
