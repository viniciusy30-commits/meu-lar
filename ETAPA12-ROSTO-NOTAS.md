# Etapa 12 — sobrancelhas e boca com cor (aguardando teste no celular)

Pedido: "As sobrancelhas e a boca estão sem cor".

## Causa
O tile do rosto no atlas `cute/textures.png` não tinha sobrancelhas (só um traço quase invisível) e os lábios tinham praticamente a cor da pele. Não é bug de código: é a textura.

## O que mudou (só pixels do rosto; malha, ossos, animações e código Kotlin não mudaram)
- `assets/cute/textures.png`, `recolor.png`, `recolor_s.png` regerados por `ferramentas/etapa12_rosto.py`.
- **Sobrancelhas**: curva 3D mapeada para o atlas pelos triângulos da frente do rosto (`etapa12_uvmap.py`), traço grosso perto do nariz e afinando para fora. Entram na região 5 (cabeloFrente) com sombra 0,5: ficam com **metade da cor do cabelo escolhido** (acompanham qualquer cor de cabelo; no padrão, castanho-avermelhado).
- **Lábios**: segmentados por cor no tile, pintados de rosa-coral mantendo o sombreado original; ficam na região da pele (id 1) com sombra menor, então acompanham o tom de pele escolhido (sempre mais avermelhados que a pele). A linha da boca vira vinho escuro.
- Correção feita nesta continuação: uma faixa clara diagonal no meio da sobrancelha direita (emenda do mapeamento) foi fechada.
- `novidades.txt`: aviso novo no topo.

## Conferência feita aqui
Prévia renderizada com a mesma fórmula de recoloração do `CuteColor.kt`, em 3 combinações (original, pele clara + cabelo ruivo, pele escura + cabelo preto): sobrancelhas e lábios aparecem e mudam de cor corretamente.

## Observação (não mexido)
Com pele muito clara, a prévia mostra manchas mais rosadas ao redor dos olhos e do nariz. Isso já existia antes desta etapa (vem da máscara de pele da Etapa 2). Se incomodar no celular, vira a próxima etapa.

## Ferramentas
`ferramentas/etapa12_uvmap.py`, `etapa12_rosto.py`, `etapa12_preview.py`. Uso: `python3 etapa12_rosto.py <pasta cute> <pasta saída>`.
