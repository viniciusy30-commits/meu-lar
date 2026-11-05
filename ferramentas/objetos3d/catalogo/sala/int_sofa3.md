# int_sofa3 — Sofá de 3 lugares

**Categoria:** sala / assentos  ·  **Classe:** interativo  ·  **Versão:** 1

## Descrição visual
Sofá de 3 lugares da mesma família da poltrona (anos 60): estrutura de carvalho com pernas torneadas que sobem até os braços, travessas, dois pés centrais extras (sofá comprido não enverga), encosto com quatro montantes inclinados, travessa e ripas. Três almofadas de assento soltas com vivo duplo e três almofadas de encosto inclinadas com botões, em linho mostarda. Manta de tricô bege dobrada sobre o braço esquerdo, com espessura.

**Variações reais previstas:** Outros tecidos e versão de 2 lugares na mesma família.

## Medidas e escala
- Largura (X) 1.799 m · altura (Y) 0.772 m · profundidade (Z) 0.650 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 53% da altura do personagem.
- Área ocupada no chão (colisores): 1.79 x 0.62 m. Grade do jogo: 2x1 casa(s).
- Altura de uso: assento a 0.342 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Altura de uso: assento a 0.342 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Altura de uso: assento a 0.342 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 7705 · triângulos: 11492 · nós: 16 · arquivo: 554 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_sofa3 | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| estrutura | int_sofa3 | (0.000, 0.000, 0.000) | sim | peça fixa |
| almofada_assento_0 | int_sofa3 | (-0.540, 0.244, 0.060) | sim | peça móvel (escala) |
| almofada_encosto_0 | int_sofa3 | (-0.540, 0.345, -0.150) | sim | peça fixa |
| almofada_assento_1 | int_sofa3 | (0.000, 0.244, 0.060) | sim | peça móvel (escala) |
| almofada_encosto_1 | int_sofa3 | (0.000, 0.345, -0.150) | sim | peça fixa |
| almofada_assento_2 | int_sofa3 | (0.540, 0.244, 0.060) | sim | peça móvel (escala) |
| almofada_encosto_2 | int_sofa3 | (0.540, 0.345, -0.150) | sim | peça fixa |
| manta | int_sofa3 | (0.000, 0.000, 0.000) | sim | peça fixa |
| COL_base | int_sofa3 | (0.000, 0.180, -0.005) | - | colisor |
| COL_braco_E | int_sofa3 | (-0.845, 0.430, 0.005) | - | colisor |
| COL_braco_D | int_sofa3 | (0.845, 0.430, 0.005) | - | colisor |
| COL_encosto | int_sofa3 | (0.000, 0.560, -0.235) | - | colisor |
| IP_sentar_0 | int_sofa3 | (-0.540, 0.000, 0.200) | - | ponto de interação |
| IP_sentar_1 | int_sofa3 | (0.000, 0.000, 0.200) | - | ponto de interação |
| IP_sentar_2 | int_sofa3 | (0.540, 0.000, 0.200) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| tecido_linho | linho.png (256x256) | metal 0.00, rugosidade 0.92 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_base | box | (0.000, 0.180, -0.005) | 1.790 x 0.360 x 0.570 | sim | movel |
| COL_braco_E | box | (-0.845, 0.430, 0.005) | 0.088 x 0.140 x 0.600 | sim | movel |
| COL_braco_D | box | (0.845, 0.430, 0.005) | 0.088 x 0.140 x 0.600 | sim | movel |
| COL_encosto | box | (0.000, 0.560, -0.235) | 1.730 x 0.420 x 0.160 | sim | movel |
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. móvel grande ancorado
- massa: 48.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| almofada_assento_0 | escala | [0, 1, 0] | escala 1.00 a 0.88 | 0.60 s | suave | 1.0 | inverte de onde está |
| almofada_assento_1 | escala | [0, 1, 0] | escala 1.00 a 0.88 | 0.60 s | suave | 1.0 | inverte de onde está |
| almofada_assento_2 | escala | [0, 1, 0] | escala 1.00 a 0.88 | 0.60 s | suave | 1.0 | inverte de onde está |

## Interações
Sentar em qualquer um dos 3 lugares (o mais perto do personagem); só a almofada daquele lugar afunda. Mesma sequência e cancelamento da poltrona.
- IP_sentar_0: ação "sentar"; posição final da raiz do personagem (-0.540, 0.000, 0.200); olha para +Z; aproximação em [-0.54, 0, 0.62].
- IP_sentar_1: ação "sentar"; posição final da raiz do personagem (0.000, 0.000, 0.200); olha para +Z; aproximação em [0.0, 0, 0.62].
- IP_sentar_2: ação "sentar"; posição final da raiz do personagem (0.540, 0.000, 0.200); olha para +Z; aproximação em [0.54, 0, 0.62].
- Cancelamento: Igual à poltrona.

## Estados e persistência
livre / ocupado por lugar. Não grava ocupação.

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
- `app/src/main/assets/obj3d/int_sofa3.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_sofa3.png`
- Fonte: `ferramentas/objetos3d/models.py` (função sofa3), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
