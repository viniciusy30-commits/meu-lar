# Etapa 8 — piscar e expressões (aguardando teste no celular)

## O que entrou
- `morph.bin` agora tem 18 canais: os 13 de formato do rosto (Etapa 7, iguais) + 5 dinâmicos: Piscar, Feliz, Triste, Brava, Surpresa (gerados por `ferramentas/etapa7_morph_gerar.py` a partir dos blendshapes do `BSMC_Head.fbx`).
- `CuteChar`: piscar automático (a cada 2,5–5,5 s, ~0,17 s; não pisca em surpresa) e transição suave de expressão (~0,18 s). No pulo o rosto faz cara de surpresa (automático, só no personagem do jogo). Só o rosto do corpo-base é recalculado, e só quando o valor muda. Animações, ossos e proporções não foram tocados.
- Criador: **Rosto > Expressão** (Automático, Neutra, Feliz, Triste, Brava, Surpresa) para visualizar. É só visualização, não é salvo; ao tocar Pronto volta ao automático. Save do avatar NÃO mudou.
- Se `morph.bin` for o antigo (13 canais), as expressões simplesmente não aparecem.

## Não feito
- Licença: dispensada (jogo de uso único, pedido do usuário).
- Medição de desempenho e checagem de atravessamento por clip: não foram feitas (sem compilador/aparelho aqui). Piscar custa só um recálculo do rosto (8787 vértices) por alguns quadros.
- Sem compilador: o build do GitHub é a prova final.

## O que testar
1. Parado: o personagem pisca sozinho de tempos em tempos.
2. Rosto > Expressão: cada botão muda sobrancelha/boca/olhos; Automático volta ao normal.
3. Pular: cara de surpresa no ar, volta ao pousar.
4. Com óculos, cabelo e chapéu: nada estranho nos olhos ao piscar.
5. Formato do rosto (sliders) continua funcionando junto com as expressões.
