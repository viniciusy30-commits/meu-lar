# Etapa 102 — alça clara estranha no ombro da blusa Bloom (aguardando teste)
- Causa: na etapa 92 as alças do sutiã foram pintadas na textura da blusa com a cor da pele do arquivo sk_s4f.png, opacas. No jogo essa pele pintada não recebe a mesma luz/tom do corpo e aparecia como uma faixa clara e chapada no ombro.
- Correção: essas faixas ficaram transparentes (alfa 0) nas 12 texturas bloom_<cor>_af5.png. Agora aparece a pele real do corpo no lugar. A renda e as mangas não foram tocadas.
- Só as 12 PNGs mudaram; a malha (bloom_af5.cup) e o código são os mesmos.
- Não testado no aparelho; o build do GitHub é a prova final.
