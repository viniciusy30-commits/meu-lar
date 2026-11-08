# Etapa 116 — manchas do queixo + cores de pele, sobrancelhas, olhos e lábios (Sims 4)

## 1) Manchas embaixo do queixo (homem Sims 4)
Triângulos da parte de baixo do queixo usavam a área clara do pescoço/peito do atlas. `p_body_am5.bin`: cor por vértice (274 vértices) igualada à pele do rosto. Malha/ossos/UV iguais. af5 não alterado.

## 2) Cores no corpo do Sims 4 (antes só valiam para o corpo do Sims 3)
- Novo `S4Skin.kt`: recolore o atlas `sk_s4m.png` / `sk_s4f.png` numa thread de fundo e sobe com glTexSubImage2D (mesmo esquema do `CuteColor`). Mantém o sombreado da textura; só muda a cor.
- Máscaras novas (assets/cute): `sk_s4{m,f}_mask.png` (R pele, G sobrancelha, B lábios) e `sk_s4{m,f}_iris.png`. Geradas por `ferramentas/etapa116_mascaras_s4.py`.
- Slot novo 13 = Sobrancelhas (paleta de cabelo). Salvo no FIM do save (saves antigos continuam válidos, ficam no original). Aba "Sobrancelhas" em Rosto.
- Pele: Corpo > Pele. Olhos / Sobrancelhas / Lábios: Rosto.
- Ligações: `CuteColor.setColors/start` chamam `S4Skin`; `CuteChar.frame` chama `S4Skin.upload`.

Limites: Kotlin NÃO foi compilado aqui (sem Gradle); testado só o algoritmo em Python, renderizado offline. A aba Sobrancelhas aparece também com corpo do Sims 3, onde não faz efeito. Máscara dos lábios é aproximada (pega a pele escura ao redor do lábio inferior em alguns tons).

## 3) Boca "comida" (atualização)
Na textura (`sk_s4m.png` / `sk_s4f.png`) havia um contorno claro em volta dos lábios e uma emenda vertical no lábio de cima; no jogo, com a luz, isso lê como boca "mordida". Limpei os dois (pele suave no lugar do contorno; brilho da emenda igualado). Ferramenta: `ferramentas/etapa116_limpar_boca_s4.py` (rodar UMA vez sobre o atlas original). As máscaras de cor foram regeneradas em cima das texturas novas.
Não resolvido: uma fresta fina na malha entre o lábio de cima e o de baixo (linha escura). Depende da malha e não mexi.
