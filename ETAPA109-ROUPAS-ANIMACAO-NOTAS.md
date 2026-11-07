# Etapa 109 — Roupas masculinas na animação (camiseta, short, jeans)
- Pontas em mangas/calça/short e gola voando: pesos de osso errados em alguns vértices. `Fit.cleanWeights` (outliers pela média dos vizinhos + suavização) chamada em `Ts4Cloth`; nas calças cada perna segue só o próprio osso (corta a coxa atravessando o short).
- Joelhos/coxas "apagados" abaixo da barra: `Cover.markSurface` só esconde pele que tem tecido logo abaixo (`clothBelow`); triângulo que cruza a barra fica visível.
- Assets `minimalist_{top,short,jeans}_am5.{cup,png}` regenerados (geometria igual, pesos novos).
- Renders em `imagens-roupas-ts4/etapa109/` (pose do jogo: parado, andando, correndo).
- Não testado no celular/Gradle; só o Java do importador compilou aqui.
