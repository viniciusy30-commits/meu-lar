# Etapa 36 — HUD em vidro translúcido (glassmorphism), só ícones

Pedido: sem botões chapados/coloridos sólidos; visual transparente, bonito e atual.

- `Ui.frost(...)`: vidro translúcido (degradê com transparência, reflexo no topo, borda fina de luz).
- `IconView.fancy()`: ícones com degradê claro e brilho (glow) suave por trás.
- Barra inferior direita: dock de vidro escuro com 3 botões de vidro colorido translúcido
  (azul = Trabalhar/maleta, roxo = Loja/carrinho, verde = "..." Configurações). Sem texto.
- Barra de trabalho: trilho de vidro + enchimento em degradê menta→ciano, logo abaixo do dock.
- Topo esquerdo: cápsula de vidro com moeda, dinheiro e "+" verde (abre a Loja).
- Topo direito: botões redondos de vidro (vista e personagem).
- Botão de pular: vidro azul acima do dock. Botões de editar móvel e mensagens também em vidro.
- Arquivos: Ui.kt, MainActivity.kt. Lógica do jogo não mudou. Menus (Loja/Config/Criador) seguem no estilo antigo.
- Observação técnica: o Android não borra o fundo atrás do vidro em Views comuns; a transparência é real
  (dá para ver o jogo através), mas sem desfoque do fundo.
- Sem compilador local: o build do GitHub é a prova final.
