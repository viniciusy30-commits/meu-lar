# int_aparador — Aparador de carvalho

**Categoria:** sala / armazenamento  ·  **Classe:** interativo  ·  **Versão:** 1

## Descrição visual
Aparador de carvalho de 1,10 m: tampo de 2,5 cm com borda chanfrada, laterais, base, fundo, divisórias, trave entre gavetas e portas, prateleira interna, quatro pés palito inclinados com ponteiras de latão. Duas gavetas com caixa interna completa (laterais, fundo, traseira) e duas portas com almofada em relevo, dobradiças de latão e puxadores redondos de latão. Dentro: livros deitados, tigela de cerâmica e toalhas dobradas (aparecem ao abrir). Folgas de 3 mm entre as frentes.

**Variações reais previstas:** Rack de TV, cômoda e criado-mudo saem desta mesma família (carcaça + trilhos + dobradiças).

## Medidas e escala
- Largura (X) 1.100 m · altura (Y) 0.660 m · profundidade (Z) 0.438 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 46% da altura do personagem.
- Área ocupada no chão (colisores): 1.10 x 0.40 m. Grade do jogo: 2x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 4533 · triângulos: 5616 · nós: 10 · arquivo: 425 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_aparador | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| corpo | int_aparador | (0.000, 0.000, 0.000) | sim | peça fixa |
| gaveta_E | int_aparador | (-0.265, 0.566, 0.188) | sim | peça móvel (trilho) |
| gaveta_D | int_aparador | (0.265, 0.566, 0.188) | sim | peça móvel (trilho) |
| porta_E | int_aparador | (-0.538, 0.332, 0.188) | sim | peça móvel (dobradica) |
| porta_D | int_aparador | (0.538, 0.332, 0.188) | sim | peça móvel (dobradica) |
| COL_corpo | int_aparador | (0.000, 0.405, 0.000) | - | colisor |
| COL_pes | int_aparador | (0.000, 0.075, 0.000) | - | colisor |
| SURF_tampo | int_aparador | (0.000, 0.660, 0.000) | - | superfície de apoio |
| IP_usar | int_aparador | (0.000, 0.000, 0.650) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| latao_escovado | escovado.png (128x128) | metal 1.00, rugosidade 0.32 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| tecido_linho | linho.png (256x256) | metal 0.00, rugosidade 0.92 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| ceramica_esmaltada | esmalte.png (256x256) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_corpo | box | (0.000, 0.405, 0.000) | 1.100 x 0.510 x 0.400 | sim | movel |
| COL_pes | box | (0.000, 0.075, 0.000) | 1.000 x 0.150 x 0.300 | sim | movel |
- Superfície de apoio SURF_tampo a 0.660 m: objetos
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. móvel grande ancorado; só portas e gavetas se mexem (dobradiça e trilho com limite)
- massa: 38.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| gaveta_E | trilho | [0, 0, 1] | 0.00 a 0.26 m | 0.42 s | suave | 0.0 | inverte de onde está |
| gaveta_D | trilho | [0, 0, 1] | 0.00 a 0.26 m | 0.42 s | suave | 0.0 | inverte de onde está |
| porta_E | dobradica | [0, 1, 0] | 0° a -100° | 0.55 s | suave | 0.0 | inverte de onde está |
| porta_D | dobradica | [0, 1, 0] | 0° a 100° | 0.55 s | suave | 0.0 | inverte de onde está |

## Interações
Abrir/fechar a peça para onde o personagem olha (alça a até 1,25 m e à frente dele): gaveta desliza 26 cm no trilho; porta gira 100° na dobradiça. Antes de abrir, o jogo testa o caminho da peça: se bater na parede ou em outro móvel, abre só até onde dá.
- IP_usar: ação "abrir/fechar"; posição final da raiz do personagem (0.000, 0.000, 0.650); olha para -Z; aproximação em [0, 0, 0.65].
- Cancelamento: Tocar de novo durante o movimento inverte a partir de onde está (sem salto).

## Estados e persistência
Cada peça: fechada / abrindo / aberta / fechando (progresso 0..1). Grava aberta/fechada de cada peça.

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
- `app/src/main/assets/obj3d/int_aparador.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_aparador.png`
- Fonte: `ferramentas/objetos3d/models.py` (função aparador), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
