# Etapa 19 — All Star mais parecido com o Converse Chuck Taylor original (aguardando teste no celular)

Pedido: "o All Star tem que ficar mais parecido com o original" (foto de referência: cano alto de lona, biqueira de borracha, faixa branca com friso preto, cadarço branco chato, língua, patch com estrela).

## O que mudou (só a peça feet/AllStar e a área dela no atlas extra2)
- **Sola/faixa mais finas**: antes parecia plataforma. Fundo da sola -2,0 -> -1,35 (igual aos sapatos sociais); faixa de borracha mais baixa; degrau sola->faixa menor; frisos pretos refeitos nas novas alturas.
- **Biqueira**: mais curta (começa mais perto do bico), borda de trás em arco e mais recuada no alto, ombro arredondado, mais baixa. A borda lona/borracha agora é **recortada exatamente** pela curva do SDF (antes apagava triângulos inteiros e ficava serrilhada).
- **Cadarço chato e largo** (fita, 0,9 x 0,17) no lugar do fio redondo; o 2º cadarço passa por cima no cruzamento; laço deitado sobre a lona.
- **7 pares de ilhós** (eram 6) e **língua** de lona aparecendo acima do último ilhós.
- Ruído da borracha reduzido (listras na biqueira).
- Vértices: 8,9 mil -> 11,1 mil (os dois pés). Recolor continua igual (região 7: cor 1 = lona, cor 2 = borracha/cadarço). Peças, esqueleto e `hide` do corpo recalculados pelo mesmo script.

## Conferência feita aqui
- O gerador antigo reproduzia o arquivo antigo byte a byte (base segura). Antes/depois renderizados de 5 ângulos.
- Pixels do atlas mudados só na caixa do All Star (y 673..894, x 229..888); outras texturas e `extra2_recolor.txt` intactos.
- Parte da frente do pé e a biqueira ficam dentro do sapato (teste com o SDF); só a canela aparece dentro do cano oco, como deve.
- Sem compilador/aparelho aqui: o build do GitHub é a prova final (só mudaram arquivos binários e imagens).

## Para ajustar (topo de ferramentas/allstar.py)
- Sola mais fina/grossa: `BOT`, `FOX_T`, `FOX_H`. Biqueira maior/menor: `zc` em `rubber0` (13,0 = onde começa). Largura do cadarço: `LW_`.
- Regerar: `python3 ferramentas/allstar.py app/src/main/assets/cute/` (precisa de numpy, scipy, scikit-image, Pillow). A versão anterior está em `allstar_v1.py`.
