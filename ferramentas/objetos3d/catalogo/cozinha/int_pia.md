# int_pia — Pia de cozinha com gabinete

**Categoria:** cozinha / bancadas  ·  **Classe:** funcional  ·  **Versão:** 1

## Descrição visual
Pia de cozinha: gabinete branco com rodapé recuado e divisória, tampo de granito escuro com rodabanca, cuba de inox rebaixada com paredes, fundo e ralo, torneira cromada de bica alta com alavanca, sifão visível dentro, produtos de limpeza. Duas portas com puxadores de barra.

**Variações reais previstas:** Bancada lateral e pia dupla na mesma família.

## Medidas e escala
- Largura (X) 0.920 m · altura (Y) 1.162 m · profundidade (Z) 0.506 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 80% da altura do personagem.
- Área ocupada no chão (colisores): 0.92 x 0.48 m. Grade do jogo: 1x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 3273 · triângulos: 4010 · nós: 9 · arquivo: 151 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_pia | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| corpo | int_pia | (0.000, 0.000, 0.000) | sim | peça fixa |
| alavanca | int_pia | (0.030, 0.840, -0.200) | sim | peça móvel (dobradica) |
| agua | int_pia | (0.000, 1.063, -0.021) | sim | peça fixa |
| porta_E | int_pia | (-0.446, 0.400, 0.220) | sim | peça móvel (dobradica) |
| porta_D | int_pia | (0.446, 0.400, 0.220) | sim | peça móvel (dobradica) |
| COL_corpo | int_pia | (0.000, 0.385, 0.000) | - | colisor |
| SURF_bancada | int_pia | (0.000, 0.770, 0.000) | - | superfície de apoio |
| IP_usar | int_pia | (0.000, 0.000, 0.640) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| latao_escovado | escovado.png (128x128) | metal 1.00, rugosidade 0.32 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE dupla face | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_corpo | box | (0.000, 0.385, 0.000) | 0.920 x 0.770 x 0.480 | sim | movel |
- Superfície de apoio SURF_bancada a 0.770 m: objetos (fora da cuba)
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. bancada ancorada
- massa: 45.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| alavanca | dobradica | [0, 0, 1] | 0° a -55° | 0.30 s | suave | 0.0 | inverte de onde está |
| porta_E | dobradica | [0, 1, 0] | 0° a -100° | 0.50 s | suave | 0.0 | inverte de onde está |
| porta_D | dobradica | [0, 1, 0] | 0° a 100° | 0.50 s | suave | 0.0 | inverte de onde está |

## Interações
Abrir/fechar a torneira de frente para a pia: a alavanca gira e a água cai da bica até o ralo, com respingo, só enquanto aberta. Portas do gabinete com dobradiça e limite.
- IP_usar: ação "ligar"; posição final da raiz do personagem (0.000, 0.000, 0.640); olha para -Z; aproximação em None.
- Cancelamento: Fechar a torneira a qualquer momento.

## Estados e persistência
torneira fechada / aberta (gravado); portas abertas/fechadas (gravadas).

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
- `app/src/main/assets/obj3d/int_pia.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_pia.png`
- Fonte: `ferramentas/objetos3d/models.py` (função pia), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
