# Etapa 186 — Cidade 3: bairro americano (NÃO compilada: rodar o build e conferir)
- Configurações > Mapa agora alterna Cidade 1 → 2 → 3. A Cidade 3 é o padrão; as Cidades 1 e 2 não foram apagadas.
- Assets novos em hds/: sub.json (ruas, Casa 1, postes, hidrantes, árvores, colisões), sub.bin (relevo, 8 m) e sub_mesh.bin (33 lotes: casas, garagens, cercas, carros, caixas de correio, placas — malha pronta por pedaço de 64 m).
- Relevo.kt: load(am, wantSub) lê sub.*; build() desenha a malha assada junto de cada pedaço; subSolids() entrega as colisões.
- Hds.kt: na Cidade 3 só a Casa 1 do Hds (com interior) é colocada; as outras 16 não entram.
- Gerador em tools/gen-bairro (python3 gen_bairro.py <pasta de saída>). Corrigido conflito de nome (HS) que travava o gerador.
- Se faltar sub.*, volta sozinho para a Cidade 2.
- Próximo: ver no celular o tamanho/cores das casas, FPS e colisões; depois ampliar o bairro aos poucos.

## Cercas e gramados (pedido seguinte)
- Cada lote tem gramado próprio (tom de verde e listras de corte diferentes).
- Cerca da frente variada: nenhuma (mais comum, como nos EUA), estacas brancas/creme/azul-claro, sebe, trilhos rústicos, mureta de tijolo/pedra ou alambrado; sempre com vão para a entrada de carros e para o caminho da porta. Nunca igual à da vizinha.
- Lados e fundos: madeira fechada (vários tons), alambrado ou estacas; às vezes a cerca fecha o lote inteiro. Sem cerca dupla entre vizinhos.
- Extras de quintal: casinha de ferramentas, trampolim, piscina de lona, mesa de piquenique, balanço.
- Colisão em todas as cercas (1.821 colisões no total). Malha subiu para ~111 mil triângulos (arquivo sub_mesh.bin ~11 MB): se o FPS cair, reduzir o fio do alambrado em fences.py.
- Gerador: tools/gen-bairro/fences.py (chamado por gen_bairro.py).
