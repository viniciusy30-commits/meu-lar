# Etapa 67 – Quintal (árvores, arbustos, flores, cerca)

- Novo `Flora.kt`: carrega `assets/flora/<id>.bin` (formato FLR1: peças por textura/material/recorte, cor por vértice com sombra de copa assada, UV) e junta várias instâncias (posição, escala, giro, tinta) em poucas peças grandes (`Flora.Batch`), divididas em blocos de até 64000 vértices.
- `Models.yard()` agora usa: oak_a/oak_b (carvalho e bordo), cherry_a, pine_a, bush_a/b/pink/white, hedge, grass_a/b (tufos), fl_* (flores), fence_panel/fence_post. O resto (caminho, varanda, banco, caixa de correio, postes de luz, colinas, céu) continua como antes.
- Folhagem = cartões com textura de folhas (alfa recortado, `Part.cut = 0.4`), normais para fora da copa (sombreamento macio) e brilho assado por vértice (interior mais escuro).
- `Renderer3D`: `Flora.reset()` junto com `MobLoader.reset()`; `MainActivity`: `Flora.assets = assets`.
- Gerador: `ferramentas/ambiente/{flora_lib,textures,trees}.py` (Python, numpy/PIL/scipy). `python3 textures.py && python3 trees.py` recria texturas e .bin em `out/`.
- Contagem aproximada (triângulos): carvalho ~7 mil, cerejeira ~6,7 mil, pinheiro ~0,8 mil, arbusto ~0,3 mil, painel de cerca ~0,2 mil.
- Não testado no aparelho (sem compilador Android aqui). Pontos a olhar: textura de folha sem halo escuro nas bordas (PNG não pré-multiplicado), cerca fechando nos cantos, portão aberto na frente.

# Etapa 68 – Móveis, casa e desempenho

- **Móveis**: `Models.furniture(t)` usa `assets/flora/f_<nome>.bin` (chair, table, bed, sofa, shelf, plant, rug, tv, fridge, stove, lamp, night, coffee, wardrobe) via `Flora.Batch`; se o arquivo faltar, cai no modelo antigo de caixas. Mesmo tamanho em casas (x em [0,largura], z em [0,profundidade], frente em +z). Gerador: `ferramentas/ambiente/furn_items.py` (caixas arredondadas com normais analíticas, almofadas com "puff", torneados, cartões de folha/flor, texturas de madeira/tecido/metal/tapete/tela). Normal zero = sem luz (tela da TV, mostrador do fogão).
- **Casa**: `Models.wall()` agora põe janelas (`win_190/160/125`: batente, travessas, peitoril, verga, vidro com alfa), cortinas (`curt_*`, com dobras e cor pela tinta), porta (`door_110`, folha aberta 105° para FORA, não bloqueia a passagem) e lambri (`wain_1`, módulos de 1 m, menos na porta). O rodapé simples foi removido (o lambri já tem rodapé).
- **Desempenho**: `Part.gpu` + `Part.upload()/release()` (Gfx.kt): peças estáticas vão para VBO/IBO (antes os vértices eram reenviados da memória do app a cada quadro). Ligado em `MB.toMesh(true)` (todas as malhas de `Models`), `MobLoader.load` e `Flora.Batch.build`. Personagem/avatar/cabelo continuam com matriz no cliente (mudam por quadro). `GlGen.gen` sobe em `onSurfaceCreated` (buffers antigos deixam de valer e são reenviados sozinhos). `rebuild()` libera os buffers da casa/quintal antigos.
- Não testado no aparelho. Pontos a olhar: móveis aparecem com as texturas (madeira/tecido), TV com a tela de pôr do sol, porta aberta para fora, cortinas coloridas, nenhum buffer preto/quebrado depois de sair e voltar ao app.
