# int_cadeira_jantar — Cadeira de jantar

**Categoria:** cozinha / cadeiras  ·  **Classe:** interativo  ·  **Versão:** 1

## Descrição visual
Cadeira de jantar de nogueira: assento de tábua de 3 cm com borda arredondada e almofada fina de linho cru, pernas dianteiras afuniladas (3,4 a 2,8 cm, nada fino demais), pernas traseiras que sobem e viram os montantes do encosto inclinados para trás, encosto com travessa curva e duas ripas curvas (perfil retangular com espessura), travessas laterais baixas, travessa central em H e travessas sob o assento. Acabada de todos os lados.

**Variações reais previstas:** Versão estofada e banqueta alta na família de cadeiras/banquetas.

## Medidas e escala
- Largura (X) 0.420 m · altura (Y) 0.780 m · profundidade (Z) 0.454 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 54% da altura do personagem.
- Área ocupada no chão (colisores): 0.42 x 0.46 m. Grade do jogo: 1x1 casa(s).
- Altura de uso: assento a 0.348 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 862 · triângulos: 1148 · nós: 5 · arquivo: 246 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_cadeira_jantar | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| cadeira | int_cadeira_jantar | (0.000, 0.000, 0.000) | sim | peça móvel (trilho) |
| COL_assento | cadeira | (0.000, 0.178, 0.020) | - | colisor |
| COL_encosto | cadeira | (0.000, 0.575, -0.200) | - | colisor |
| IP_sentar | int_cadeira_jantar | (0.000, 0.000, 0.160) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| tecido_linho | linho.png (256x256) | metal 0.00, rugosidade 0.92 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_assento | box | (0.000, 0.178, 0.020) | 0.420 x 0.365 x 0.400 | sim | movel |
| COL_encosto | box | (0.000, 0.575, -0.200) | 0.400 x 0.460 x 0.070 | sim | movel |
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. estática no uso; arrastável só no modo de edição
- massa: 5.5
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| cadeira | trilho | [0, 0, -1] | 0.00 a 0.35 m | 0.55 s | suave | 0.0 | inverte de onde está |

## Interações
Sentar (ponto central, olhando para a frente = para a mesa): a cadeira desliza 35 cm para trás (puxar, 0,55 s, sem salto), o personagem chega pela lateral livre, entra entre a cadeira e a mesa, vira de costas e senta; sentado, a cadeira volta 25 cm para a mesa levando o personagem junto (fica 10 cm fora do encaixe, joelhos sob o tampo). Para levantar: a cadeira afasta com ele, ele levanta e a cadeira volta ao encaixe. Arrastável no modo de edição.
- IP_sentar: ação "sentar"; posição final da raiz do personagem (0.000, 0.000, 0.160); olha para +Z; aproximação em [-0.62, 0, 0.27999999999999997].
  Sequência: puxar a cadeira (0,55 s) → andar até a lateral → entrar entre a cadeira e a mesa → virar de costas → sentar → empurrar para a mesa junto com o personagem → sentado → afastar → levantar → empurrar a cadeira de volta.
- Cancelamento: Analógico ou Levantar: indo, para e a cadeira volta; sentando (antes de 35%), fica em pé; depois, afasta e levanta.

## Estados e persistência
livre -> puxada -> ocupada -> puxada -> livre. Não grava ocupação.

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
- `app/src/main/assets/obj3d/int_cadeira_jantar.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_cadeira_jantar.png`
- Fonte: `ferramentas/objetos3d/models.py` (função cadeira), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
