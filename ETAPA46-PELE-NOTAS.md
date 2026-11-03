# Etapa 46 — Tom de pele (aguardando teste)

Problema visto no vídeo: ombros, pescoço e peito do corpo do Sims apareciam como uma faixa branca, parecendo uma peça de roupa.
Causa: a pele original (~240,213,204) é muito clara e o shader do app soma até ~1,16x de luz nas superfícies voltadas para cima, estourando para branco.
Correção: pele de corpo e rosto escurecida (x0,80) e levemente mais saturada (x1,12) nos 8 atlas `sk_*.png`; olhos, cabelo e shorts/top pintados não mudam.
Ferramenta: `ferramentas/etapa46_tom_pele.py` (rodar UMA vez sobre atlas novos; rodar de novo escurece de novo).
Se ainda parecer claro ou escuro demais, é só ajustar K no script.
