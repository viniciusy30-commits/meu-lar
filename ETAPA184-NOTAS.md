# Etapa 184 — cidade povoada (NÃO compilada: rodar o build e conferir)

## Como os dados são gerados
1. `python3 gen_city7.py`  -> city3.json + relevo.bin (ruas, terreno, rotatórias; CWF = 1,4 / 1,4 / 2,0 / 2,4)
2. `python3 gen_pop.py city3.json relevo.bin` -> acrescenta ao city3.json: bld, lamp, hyd, tree (determinístico, semente 184)
3. `python3 prev_pop.py cx cz meia_largura px_por_m saida.png` -> prévia 2D (prédios por cor, árvores, postes amarelos, hidrantes vermelhos)

## O que o gerador faz
- Lotes ao longo das ruas locais, coletoras e avenidas (alinhados à rua, recuo, sem cair em rua, água, declive > 2–3,2 m, sobreposição ou perto das 17 casas do HDS).
- Segunda passada: miolo dos quarteirões e vãos do centro, alinhado à rua mais próxima.
- Zona urbana por distância à Praça Central e às demais rotatórias: torres e escritórios no centro, apartamentos e lojas em volta, casas e sobrados na periferia, lotes vazios/pracinhas (~7%).
- Postes a cada ~34 m (avenida: dois lados, 8,5 m e 2 braços; rua: um lado, alternado), fora das bocas de cruzamento e das pontes.
- Hidrantes a cada ~90 m nas ruas locais/coletoras.
- Árvores: de rua (calçada de bairro), jardim da frente, ilhas das rotatórias (menos a Praça Central) e mata/morro SÓ fora da cidade, em manchas.

## Relevo.kt
- Carrega bld/lamp/hyd/tree; cada pedaço de terreno de 64 m emite seus prédios, postes e hidrantes (tudo em caixas girados: obox/quadN).
- Casa/sobrado: telhado de duas águas, porta, chaminé. Loja: laje e toldo colorido. Apartamento: laje + casa de máquinas. Escritório: pódio + corpo. Torre: pódio + corpo + coroa + antena. Fachada = Mt.FACADE (janelas a cada 3 m).
- Árvores: posições vêm do gerador; versão leve sempre, modelo do HDS perto do jogador (Relevo.service, 260 m).
- Pontes: vigas sob o tabuleiro e junta de dilatação (além do parapeito, postes e pilares duplos da 183).

## Limites conhecidos
- Prédios e postes ainda são só visuais (sem colisão): dá para atravessar.
- Memória: estimativa +30–40 MB (3,4 mil prédios, 1,3 mil postes). Se estourar o heap, reduzir `step` dos postes e o preenchimento em gen_pop.py.
