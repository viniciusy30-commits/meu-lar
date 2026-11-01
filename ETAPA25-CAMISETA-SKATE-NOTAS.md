# Etapa 25 — camiseta larga estilo skatista (aguardando teste no celular)

Nova roupa: **Roupa > Blusa > "Camiseta larga (skatista)"** (id `SkateTee`), preta, caimento largo (ombro caído, corpo comprido e solto, manga larga até o cotovelo) e estampa de cruz ornamentada cor creme nas costas, como na referência.
- Malha `p_top_skatetee.bin`: deformação suave da camiseta original (mesmo esqueleto/pesos, então anima e acompanha o corpo; conferida contra jeans/bermuda/cargo: o tecido fica sempre por fora). Textura própria `skatetee.png` (1024x1536) com a estampa só nas costas, UV planar.
- Cor fixa (preta com estampa creme): o seletor de cor da blusa não recolore esta peça.
- Entrada nova no fim das listas de `Avatar.kt` (saves antigos não mudam), em `pieces.txt` e ícone `icons/top_skatetee.png`.
- A estampa é um desenho original inspirado na referência (não é a arte da marca).
- Ajustes possíveis: tamanho/posição da cruz, comprimento da manga e do corpo, cor.

## Junto neste ZIP (ainda não aplicados)
- Cabelo colado na cabeça (etapa 23).
- Postura masculina (etapa 24c): clipes novos parado/andar no `base.bin`, braços soltos, dedos sem curvatura, rosto masculino como era.
Ferramentas: `ferramentas/etapa24_postura_masculina.py`, `ferramentas/etapa25_camiseta_skate.py`.
Sem compilador/teste no aparelho aqui: o build é a prova final.

## Ajuste 26
- Mangas: os vértices da manga tinham peso parcial no tronco e rasgavam quando o braço mexia; agora a manga inteira segue só o osso do braço.
- Barra: mais comprida (desce até ~14 cm abaixo da cintura, cobre o quadril) e bem mais larga em baixo (caimento solto, conferido contra jeans/bermuda/cargo).
