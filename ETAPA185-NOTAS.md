# Etapa 185 — cidade redesenhada (NÃO compilada: rodar o build e conferir)
- Mundo 2600x2400 m, centro (1300,1100), praia ao sul, rio a leste, anel interno e externo, 8 avenidas radiais, 17 rotatórias, 541 ruas.
- Formato dos assets igual ao da 184 (Relevo.kt não mudou): hds/city3.json + hds/relevo.bin. 17 casas do HDS reposicionadas.
- 3.395 prédios, ~1.034 postes, ~234 hidrantes, ~4.655 árvores (árvores só fora da cidade e em ruas/jardins).
- Limite conhecido: quarteirões do núcleo são estreitos (~54x20 m livres), então há poucas torres (4) no centro; para mais torres, alargar quadras do núcleo em plan8.py.
- Se estourar memória: reduzir passo dos postes em gen_pop8.py.
