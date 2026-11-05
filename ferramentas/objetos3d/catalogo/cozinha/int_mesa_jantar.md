# int_mesa_jantar — Mesa de jantar

**Categoria:** cozinha / mesas  ·  **Classe:** apoio  ·  **Versão:** 1

## Descrição visual
Mesa de jantar de nogueira para 4 cadeiras: tampo de 3,5 cm com borda arredondada e chanfro embaixo, saia recuada 6 cm (joelhos livres abaixo de 0,505 m), pernas de seção quadrada arredondada afunilando com sapatas e cantoneiras de reforço.

**Variações reais previstas:** Versões de 2, 6 e 8 lugares (mesma construção, comprimentos 0,8 / 1,6 / 2,0 m).

## Medidas e escala
- Largura (X) 1.200 m · altura (Y) 0.600 m · profundidade (Z) 0.740 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 41% da altura do personagem.
- Área ocupada no chão (colisores): 1.20 x 0.74 m. Grade do jogo: 2x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 1790 · triângulos: 2284 · nós: 8 · arquivo: 225 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_mesa_jantar | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| mesa | int_mesa_jantar | (0.000, 0.000, 0.000) | sim | peça fixa |
| COL_tampo | int_mesa_jantar | (0.000, 0.547, 0.000) | - | colisor |
| COL_perna_ET | int_mesa_jantar | (-0.540, 0.282, -0.310) | - | colisor |
| COL_perna_EF | int_mesa_jantar | (-0.540, 0.282, 0.310) | - | colisor |
| COL_perna_DT | int_mesa_jantar | (0.540, 0.282, -0.310) | - | colisor |
| COL_perna_DF | int_mesa_jantar | (0.540, 0.282, 0.310) | - | colisor |
| SURF_tampo | int_mesa_jantar | (0.000, 0.600, 0.000) | - | superfície de apoio |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| madeira_carvalho | carvalho.png (512x512) | metal 0.00, rugosidade 0.62 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_tampo | box | (0.000, 0.547, 0.000) | 1.200 x 0.105 x 0.740 | não (é empurrado) | superficie |
| COL_perna_ET | box | (-0.540, 0.282, -0.310) | 0.060 x 0.565 x 0.060 | sim | movel |
| COL_perna_EF | box | (-0.540, 0.282, 0.310) | 0.060 x 0.565 x 0.060 | sim | movel |
| COL_perna_DT | box | (0.540, 0.282, -0.310) | 0.060 x 0.565 x 0.060 | sim | movel |
| COL_perna_DF | box | (0.540, 0.282, 0.310) | 0.060 x 0.565 x 0.060 | sim | movel |
- Superfície de apoio SURF_tampo a 0.600 m: pratos, copos, objetos
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. móvel de apoio ancorado; só serve de superfície
- massa: 32.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
Não se aplica: objeto sem peças móveis (decorativo).

## Interações
Nenhuma direta (o PDF pede os pontos de sentar nas cadeiras, não no tampo). Superfície para pratos e copos. O tampo não bloqueia o encaixe: a cadeira pode entrar embaixo sem atravessar as pernas; quatro vagas registradas nos metadados.
- Cancelamento: Não se aplica.

## Estados e persistência
Sem estados.

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
- `app/src/main/assets/obj3d/int_mesa_jantar.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_mesa_jantar.png`
- Fonte: `ferramentas/objetos3d/models.py` (função mesa), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
