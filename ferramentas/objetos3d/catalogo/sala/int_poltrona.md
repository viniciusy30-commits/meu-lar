# int_poltrona — Poltrona de linho

**Categoria:** sala / assentos  ·  **Classe:** interativo  ·  **Versão:** 1

## Descrição visual
Poltrona estilo anos 60: estrutura de carvalho com pernas torneadas inclinadas que sobem até os braços (tábuas com ponta arredondada, mais largas na frente), travessas do assento, encosto com dois montantes inclinados 9°, travessa de cima e duas ripas. Almofada de assento solta com vivo em cima e embaixo e almofada de encosto inclinada com seis botões de capitonê, em linho azul-acinzentado. Cinta de tecido escuro sob a almofada. Frente, lados e traseira acabados.

**Variações reais previstas:** Outros tecidos (mostarda, terracota, bouclé) e versão de couro no próximo lote; mesma família de construção para o sofá de 3 lugares.

## Medidas e escala
- Largura (X) 0.744 m · altura (Y) 0.793 m · profundidade (Z) 0.650 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 55% da altura do personagem.
- Área ocupada no chão (colisores): 0.74 x 0.62 m. Grade do jogo: 1x1 casa(s).
- Altura de uso: assento a 0.342 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 3952 · triângulos: 5452 · nós: 11 · arquivo: 382 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_poltrona | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| estrutura | int_poltrona | (0.000, 0.000, 0.000) | sim | peça fixa |
| almofada_assento | int_poltrona | (0.000, 0.244, 0.060) | sim | peça móvel (escala) |
| almofada_encosto | int_poltrona | (0.000, 0.345, -0.150) | sim | peça fixa |
| COL_base | int_poltrona | (0.000, 0.180, -0.005) | - | colisor |
| COL_braco_E | int_poltrona | (-0.330, 0.430, 0.005) | - | colisor |
| SURF_braco_E | int_poltrona | (-0.330, 0.506, 0.005) | - | superfície de apoio |
| COL_braco_D | int_poltrona | (0.330, 0.430, 0.005) | - | colisor |
| SURF_braco_D | int_poltrona | (0.330, 0.506, 0.005) | - | superfície de apoio |
| COL_encosto | int_poltrona | (0.000, 0.560, -0.235) | - | colisor |
| IP_sentar | int_poltrona | (0.000, 0.000, 0.200) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| tecido_linho | linho.png (256x256) | metal 0.00, rugosidade 0.92 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_base | box | (0.000, 0.180, -0.005) | 0.720 x 0.360 x 0.570 | sim | movel |
| COL_braco_E | box | (-0.330, 0.430, 0.005) | 0.085 x 0.140 x 0.600 | sim | movel |
| COL_braco_D | box | (0.330, 0.430, 0.005) | 0.085 x 0.140 x 0.600 | sim | movel |
| COL_encosto | box | (0.000, 0.560, -0.235) | 0.640 x 0.420 x 0.160 | sim | movel |
- Superfície de apoio SURF_braco_E a 0.506 m: copo, livro, controle
- Superfície de apoio SURF_braco_D a 0.506 m: copo, livro, controle
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. móvel grande ancorado: não tomba nem desliza com o personagem
- massa: 24.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| almofada_assento | escala | [0, 1, 0] | escala 1.00 a 0.88 | 0.60 s | suave | 1.0 | inverte de onde está |

## Interações
Sentar: o personagem anda até a frente (caminho calculado), entra na folga do assento, vira de costas, senta (1,3 s), fica sentado (laço) e levanta (1,0 s). A almofada afunda 12% enquanto ele está sentado. Assento ocupado não aceita outro.
- IP_sentar: ação "sentar"; posição final da raiz do personagem (0.000, 0.000, 0.200); olha para +Z; aproximação em [0, 0, 0.62].
  Sequência: andar até a aproximação → virar de costas → sentar (1,3 s) → sentado (laço) → levantar (1,0 s).
- Cancelamento: Mexer o analógico ou tocar em Levantar: indo, para na hora; sentando (antes de 35%), volta a ficar em pé; depois disso, levanta com a animação inteira.

## Estados e persistência
livre -> andando -> virando -> sentando -> sentado -> levantando -> livre. Não grava "sentado" (ao abrir o jogo, ninguém está sentado).

## Testes
| Teste | Onde | Resultado |
|---|---|---|
| Arquivo GLB válido (cabeçalho, blocos, acessores, índices, normais, faces, materiais, imagens, metadados) | verificador glb_lib.verify, aqui | aprovado |
| Leitura pelo código do jogo (Glb.kt compilado de verdade, rodando na JVM) | aqui | aprovado: nós, colisores, pivôs, animações e pontos de interação lidos |
| Geometria relida do GLB e renderizada (3 ângulos; aberto/fechado nas peças móveis) | aqui | conferido visualmente |
| Personagem real (corpo am1) na pose sentada sobre o GLB, lado e 3/4 | aqui | sem atravessar assento/encosto; pés no chão |
| Escala no jogo | celular | **pendente** (não consigo rodar Android aqui) |
| Posicionamento (colocar, girar, mover) | celular | **pendente** (não consigo rodar Android aqui) |
| Colisão andando em volta | celular | **pendente** (não consigo rodar Android aqui) |
| Partes móveis / interação / interrupção | celular | **pendente** (não consigo rodar Android aqui) |
| Persistência (salvar e reabrir) | celular | **pendente** (não consigo rodar Android aqui) |
| Desempenho no aparelho | celular | **pendente** (não consigo rodar Android aqui) |

## Arquivos
- `app/src/main/assets/obj3d/int_poltrona.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_poltrona.png`
- Fonte: `ferramentas/objetos3d/models.py` (função poltrona), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
