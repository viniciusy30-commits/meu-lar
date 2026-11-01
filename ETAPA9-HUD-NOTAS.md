# HUD estilo The Sims + botão de pular (aguardando teste no celular)

- Painéis de vidro azul-marinho com borda azul-clara e "plumbob" verde (Pal.SIMS*, Ic.PLUMB). Tudo bem menor que antes.
- Topo esquerdo: painel pequeno com o plumbob e o dinheiro (13sp). Topo direito: 3 botões quadrados de 34dp (vista, personagem, ajustes).
- Base: painel compacto centralizado (não ocupa mais a largura toda) com Trabalhar e Loja (34dp de altura) e a barra de trabalho fina embaixo.
- Botão de editar móvel (Pegar/Girar/Vender): 38dp, rótulos de 10sp, acima do painel.
- **Botão de pular**: círculo azul de 56dp no canto inferior direito (Ic.JUMP), só na primeira pessoa; some na vista aérea e no criador. Chama o mesmo `jumpReq` que o jogo já tinha (animação de pulo existente, sem mudança de física).
- Joystick levemente menor (46dp) e mais para o canto; mira, nome do móvel e dica de controles com texto menor.
- Mensagens (toast) menores, no estilo do painel. Respeita as bordas/entalhe da tela (insets).
- Arquivos: MainActivity.kt, Ui.kt, GameView.kt.
- Sem compilador aqui: o build do GitHub é a prova final.
