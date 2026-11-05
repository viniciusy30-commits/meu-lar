# int_guarda_roupa — Guarda-roupa

**Categoria:** quarto / armazenamento  ·  **Classe:** funcional  ·  **Versão:** 1

## Descrição visual
Guarda-roupa de 2 portas e 2 gavetas, laca off-white com interior em carvalho: laterais, topo, base, fundo, rodapé recuado, moldura no topo, divisória. Lado esquerdo com 4 prateleiras e roupas dobradas; lado direito com cabideiro (tubo com suportes), 6 cabides com camisas e sapatos no fundo; caixa organizadora. Portas de 2,2 cm com almofadas em relevo, puxadores de latão e 3 dobradiças cada. Gavetas com caixa interna completa e roupas enroladas dentro.

**Variações reais previstas:** Versões de 3 portas e com espelho na mesma família de armários.

## Medidas e escala
- Largura (X) 1.130 m · altura (Y) 1.644 m · profundidade (Z) 0.539 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 113% da altura do personagem.
- Área ocupada no chão (colisores): 1.13 x 0.50 m. Grade do jogo: 2x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 12346 · triângulos: 15304 · nós: 9 · arquivo: 748 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_guarda_roupa | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| corpo | int_guarda_roupa | (0.000, 0.000, 0.000) | sim | peça fixa |
| porta_E | int_guarda_roupa | (-0.546, 0.958, 0.230) | sim | peça móvel (dobradica) |
| porta_D | int_guarda_roupa | (0.546, 0.958, 0.230) | sim | peça móvel (dobradica) |
| gaveta_E | int_guarda_roupa | (-0.272, 0.185, 0.230) | sim | peça móvel (trilho) |
| gaveta_D | int_guarda_roupa | (0.272, 0.185, 0.230) | sim | peça móvel (trilho) |
| COL_corpo | int_guarda_roupa | (0.000, 0.822, 0.000) | - | colisor |
| SURF_topo | int_guarda_roupa | (0.000, 1.644, 0.000) | - | superfície de apoio |
| IP_usar | int_guarda_roupa | (0.000, 0.000, 0.700) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| tecido_linho | linho.png (256x256) | metal 0.00, rugosidade 0.92 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| latao_escovado | escovado.png (128x128) | metal 1.00, rugosidade 0.32 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_corpo | box | (0.000, 0.822, 0.000) | 1.130 x 1.644 x 0.500 | sim | movel |
- Superfície de apoio SURF_topo a 1.644 m: caixas, objetos
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. móvel alto ancorado: não tomba nem desliza
- massa: 85.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| porta_E | dobradica | [0, 1, 0] | 0° a -105° | 0.65 s | suave | 0.0 | inverte de onde está |
| porta_D | dobradica | [0, 1, 0] | 0° a 105° | 0.65 s | suave | 0.0 | inverte de onde está |
| gaveta_E | trilho | [0, 0, 1] | 0.00 a 0.30 m | 0.45 s | suave | 0.0 | inverte de onde está |
| gaveta_D | trilho | [0, 0, 1] | 0.00 a 0.30 m | 0.45 s | suave | 0.0 | inverte de onde está |

## Interações
Abrir/fechar a porta ou gaveta para onde o personagem olha: ele vira para a alça e faz a animação de interagir; a peça começa a se mexer quando a mão chega (0,55 s). Portas 105° na dobradiça, gavetas 30 cm no trilho, limitadas antes de tocar parede ou outro móvel. Porta aberta bloqueia a passagem, mas quem está dentro da área dela sempre consegue sair.
- IP_usar: ação "abrir/fechar"; posição final da raiz do personagem (0.000, 0.000, 0.700); olha para -Z; aproximação em None.
- Cancelamento: Mexer o analógico antes de a mão chegar cancela sem mexer a peça; tocar de novo inverte de onde está.

## Estados e persistência
Cada peça: fechada / abrindo / aberta / fechando. Grava aberta/fechada.

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
- `app/src/main/assets/obj3d/int_guarda_roupa.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_guarda_roupa.png`
- Fonte: `ferramentas/objetos3d/models.py` (função guarda), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
