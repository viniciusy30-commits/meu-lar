# int_geladeira — Geladeira duplex

**Categoria:** cozinha / eletrodomesticos  ·  **Classe:** funcional  ·  **Versão:** 1

## Descrição visual
Geladeira duplex branca: carcaça com espessura, interior branco-gelo, freezer em cima com gaveta de gelo e potes, divisória, três prateleiras com borda, jarra, potes, frutas, queijo, gaveta de legumes transparente com legumes, porta com vedação, prateleiras de porta com garrafas, caixa de leite e ovos, puxadores verticais de alumínio, grade do rodapé.

**Variações reais previstas:** Inox, frost free de 2 portas lado a lado e frigobar no próximo lote de cozinha.

## Medidas e escala
- Largura (X) 0.620 m · altura (Y) 1.475 m · profundidade (Z) 0.636 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 102% da altura do personagem.
- Área ocupada no chão (colisores): 0.62 x 0.59 m. Grade do jogo: 1x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 8475 · triângulos: 10924 · nós: 9 · arquivo: 387 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_geladeira | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| corpo | int_geladeira | (0.000, 0.000, 0.000) | sim | peça fixa |
| luz | int_geladeira | (0.000, 0.970, -0.050) | sim | peça fixa |
| gaveta_legumes | int_geladeira | (0.000, 0.220, 0.220) | sim | peça móvel (trilho) |
| porta_freezer | int_geladeira | (0.305, 1.260, 0.240) | sim | peça móvel (dobradica) |
| porta_geladeira | int_geladeira | (0.305, 0.555, 0.240) | sim | peça móvel (dobradica) |
| COL_corpo | int_geladeira | (0.000, 0.740, -0.005) | - | colisor |
| SURF_topo | int_geladeira | (0.000, 1.480, -0.030) | - | superfície de apoio |
| IP_usar | int_geladeira | (0.000, 0.000, 0.850) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| ceramica_esmaltada | esmalte.png (256x256) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE dupla face | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| latao_escovado | escovado.png (128x128) | metal 1.00, rugosidade 0.32 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_corpo | box | (0.000, 0.740, -0.005) | 0.620 x 1.480 x 0.590 | sim | movel |
- Superfície de apoio SURF_topo a 1.480 m: objetos
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. eletrodoméstico pesado ancorado
- massa: 60.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| gaveta_legumes | trilho | [0, 0, 1] | 0.00 a 0.22 m | 0.40 s | suave | 0.0 | inverte de onde está |
| porta_freezer | dobradica | [0, 1, 0] | 0° a 110° | 0.60 s | suave | 0.0 | inverte de onde está |
| porta_geladeira | dobradica | [0, 1, 0] | 0° a 110° | 0.60 s | suave | 0.0 | inverte de onde está |

## Interações
Abrir/fechar freezer e geladeira (dobradiça à direita, 110°, limitada se houver parede/móvel). A gaveta de legumes só pode ser aberta com a porta de baixo aberta. A luz interna acende com a porta de baixo aberta.
- IP_usar: ação "abrir/fechar"; posição final da raiz do personagem (0.000, 0.000, 0.850); olha para -Z; aproximação em None.
- Cancelamento: Tocar de novo inverte do ponto em que está.

## Estados e persistência
Cada porta/gaveta: fechada/abrindo/aberta/fechando. Grava aberta/fechada.

## Testes
| Teste | Onde | Resultado |
|---|---|---|
| Arquivo GLB válido (cabeçalho, blocos, acessores, índices, normais, faces, materiais, imagens, metadados) | verificador glb_lib.verify, aqui | aprovado |
| Leitura pelo código do jogo (Glb.kt compilado de verdade, rodando na JVM) | aqui | aprovado: nós, colisores, pivôs, animações e pontos de interação lidos |
| Geometria relida do GLB e renderizada (3 ângulos; aberto/fechado nas peças móveis) | aqui | conferido visualmente |
| Escala no jogo | celular | **pendente** (não consigo rodar Android aqui) |
| Posicionamento (colocar, girar, mover) | celular | **pendente** (não consigo rodar Android aqui) |
| Colisão andando em volta | celular | **pendente** (não consigo rodar Android aqui) |
| Partes móveis / interação / interrupção | celular | **pendente** (não consigo rodar Android aqui) |
| Persistência (salvar e reabrir) | celular | **pendente** (não consigo rodar Android aqui) |
| Desempenho no aparelho | celular | **pendente** (não consigo rodar Android aqui) |

## Arquivos
- `app/src/main/assets/obj3d/int_geladeira.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_geladeira.png`
- Fonte: `ferramentas/objetos3d/models.py` (função geladeira), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
