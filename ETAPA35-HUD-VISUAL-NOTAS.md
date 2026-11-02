# Etapa 35 — HUD e menus com cara de jogo (estilo The Sims, mas próprio)

Pedido: "o HUD do jogo e os menus estão muito feios; quero pegada profissional estilo The Sims, bonitinho, com cara de jogo".

## O que mudou
- Paleta nova (roxo-ameixa + creme + dourado) em `Pal`; novos tons de botão em `Tn` (SKY, MINT, SUN, CORAL, LAV, ROSE, GHOST, CARD, PANEL).
- `Ui.chunky(...)`: botão "gordinho" (degrau escuro embaixo + degradê + brilho no topo). `Ui.panel(...)` e `Ui.sheetBg(...)` para painéis e menus.
- Ícones novos no `IconView`: BASE, BODY, HAIR, FACE, SHIRT, SHOE, HAT, CHEV, SPARK. O `IconView` agora respeita padding.
- `PillBar` (barra de trabalho) mais grossa, com trilho escuro, contorno e enchimento verde com degradê.
- `MainActivity`: topo (moeda + 3 botões de 44dp), mensagens, painel de baixo (Trabalhar/Loja grandes), botões de editar móvel, botão de pular 66dp, Loja (cartões, abas, chip de dinheiro), Configurações (linhas com ícone colorido e seta), Novidades. Menus ganharam alça, ícone no título e botão fechar em relevo.
- `Creator.kt`: trilho de categorias com ícones vetoriais (sem emoji), abas em relevo, cartões com selo verde, botão Pronto verde em relevo, título e botões de girar em painel. Lógica NÃO mudou.
- Joystick/mira/dica em `Overlay` com as cores novas.

## Cuidado importante (arquivos-base)
Na pasta `codigo/` do pacote de continuação, `Creator.kt`, `Avatar.kt` e `novidades.txt` estavam sobrescritos por versões antigas (da primeira tarefa). Esta entrega usa o `Creator.kt` da etapa 14 e o `novidades.txt` da etapa 14 (últimos entregues) como base. `Avatar.kt` não foi tocado.

## Sem compilador local
O build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.

## Correção: vista aérea não saía da casa
O planejador de caminho (`Renderer3D.planPath`/`blockedAt`) só cobria a casa e tratava o quintal como bloqueado. Agora a grade cobre a casa + quintal (mesmos limites do andar em 1ª pessoa) e o personagem sai pela porta até onde você tocar.
