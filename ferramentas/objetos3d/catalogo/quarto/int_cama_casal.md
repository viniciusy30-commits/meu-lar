# int_cama_casal — Cama de casal

**Categoria:** quarto / camas  ·  **Classe:** interativo  ·  **Versão:** 1

## Descrição visual
Cama de casal: base de carvalho com saia, pés torneados, cabeceira estofada cinza-azulada com capitonê em losango e moldura de madeira, colchão volumétrico com vivo, edredom azul com caimento nas laterais e no pé (com espessura, avesso modelado), dobra do lençol branco, dois travesseiros deitados e duas almofadas apoiadas na cabeceira.

**Variações reais previstas:** Cama de solteiro e beliche reaproveitam a família (estrutura + colchão + roupa de cama).

## Medidas e escala
- Largura (X) 1.320 m · altura (Y) 0.990 m · profundidade (Z) 1.765 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 68% da altura do personagem.
- Área ocupada no chão (colisores): 1.32 x 1.77 m. Grade do jogo: 2x2 casa(s).
- Altura de uso: assento a 0.360 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Altura de uso: assento a 0.360 m (afundado); traseiro do personagem adulto sentado a 0,33–0,36 m (medido na animação).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 8134 · triângulos: 12840 · nós: 7 · arquivo: 570 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_cama_casal | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| estrutura | int_cama_casal | (0.000, 0.000, 0.000) | sim | peça fixa |
| COL_base | int_cama_casal | (0.000, 0.190, 0.020) | - | colisor |
| COL_cabeceira | int_cama_casal | (0.000, 0.500, -0.860) | - | colisor |
| SURF_colchao | int_cama_casal | (0.000, 0.370, 0.100) | - | superfície de apoio |
| IP_deitar_E | int_cama_casal | (-0.770, 0.000, 0.120) | - | ponto de interação |
| IP_deitar_D | int_cama_casal | (0.770, 0.000, 0.120) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| tecido_linho | linho.png (256x256) | metal 0.00, rugosidade 0.92 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_base | box | (0.000, 0.190, 0.020) | 1.240 x 0.380 x 1.680 | sim | movel |
| COL_cabeceira | box | (0.000, 0.500, -0.860) | 1.320 x 1.000 x 0.090 | sim | movel |
- Superfície de apoio SURF_colchao a 0.370 m: objetos leves
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. estrutura ancorada; colchão e roupa de cama não têm física
- massa: 70.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
Não se aplica: objeto sem peças móveis (decorativo).

## Interações
Deitar pelos dois lados: anda até o lado, vira de costas, senta na borda (animação de sentar), deita de costas com a cabeça no travesseiro (transição de 1,1 s, sem teletransporte) e fica deitado. Levantar faz o caminho inverso (deitado -> sentado -> em pé).
- IP_deitar_E: ação "deitar"; posição final da raiz do personagem (-0.770, 0.000, 0.120); olha para -X; aproximação em [-1.22, 0, 0.12].
  Sequência: andar até o lado → virar de costas → sentar na borda → deitar (1 s) → deitado → sentar → levantar.
- IP_deitar_D: ação "deitar"; posição final da raiz do personagem (0.770, 0.000, 0.120); olha para +X; aproximação em [1.22, 0, 0.12].
  Sequência: andar até o lado → virar de costas → sentar na borda → deitar (1 s) → deitado → sentar → levantar.
- Cancelamento: Analógico ou Levantar em qualquer fase: indo, para; deitando/deitado, volta a sentar e levanta.

## Estados e persistência
livre -> sentando -> deitando -> deitado -> sentando -> levantando -> livre. Não grava "deitado".

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
- `app/src/main/assets/obj3d/int_cama_casal.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_cama_casal.png`
- Fonte: `ferramentas/objetos3d/models.py` (função cama), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
