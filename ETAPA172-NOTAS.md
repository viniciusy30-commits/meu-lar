# Etapa 172 — Catálogo Hds: texturas, cores, girar e loja nova
- Loja > Catálogo Hds: categorias com os ícones do Hds; dentro, botões de subcategoria e o ícone de cada móvel.
- Móvel colocado > botão **Cor** (só nos que têm partes coloríveis): escolha a cor de cada parte. "Voltar às cores originais" desfaz.
- Botões **Girar esq.** e **Girar dir.** na barra de edição.
- Os móveis foram exportados de novo com todas as texturas e as opções de cor do jogo original (`assets/hds/mobilia`, 1.115 modelos).
- Código: `GameState.kt` (cores no item, girar nos dois sentidos), `HdsMob.kt`, `Glb.kt` (malhas com cores trocadas), `Renderer3D.kt`, `MainActivity.kt`.
- Arquivos antigos da Etapa 171 (`assets/hds/mobilia/th/`) deixam de ser usados e podem ser apagados depois.
