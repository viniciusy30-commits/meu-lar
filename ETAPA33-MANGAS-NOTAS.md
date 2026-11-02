# Etapa 33 — boca das mangas da camiseta larga
- Problema: a boca da manga (friso dobrado para dentro na camisa original) virava dente de serra depois da deformação, com pele aparecendo.
- Correção: `ferramentas/etapa27_camiseta_skate.py` junta o friso num anel reto e leva a dobra interna ao raio externo antes de deformar.
- Muda só `p_top_skatetee.bin` (mesmos 1214 vértices / 1910 triângulos). Textura e máscaras iguais.
- Ainda pendente: lascas de pele na gola. Falta testar com o braço em movimento no aparelho.
