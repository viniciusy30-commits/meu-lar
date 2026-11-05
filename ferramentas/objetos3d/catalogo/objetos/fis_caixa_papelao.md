# fis_caixa_papelao — Caixa de papelão

**Categoria:** objetos / utilidades  ·  **Classe:** fisico  ·  **Versão:** 1

## Descrição visual
Caixa de papelão ondulado 40 x 30 x 32 cm com cantos levemente arredondados, fresta entre as abas no topo coberta por fita adesiva que desce 9 cm nas laterais, e impressão de manuseio (setas "este lado para cima", frágil, manter seco, etiqueta com código de barras) na frente e na lateral. Impressão aplicada como decalque (tinta com recorte por alfa) sobre o papelão.

**Variações reais previstas:** Tamanhos diferentes (P/M/G) e caixa aberta com abas levantadas ficam para o lote de utilidades.

## Medidas e escala
- Largura (X) 0.402 m · altura (Y) 0.301 m · profundidade (Z) 0.321 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 21% da altura do personagem.
- Área ocupada no chão (colisores): 0.40 x 0.32 m. Grade do jogo: 1x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 120 · triângulos: 120 · nós: 4 · arquivo: 61 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| fis_caixa_papelao | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| caixa | fis_caixa_papelao | (0.000, 0.000, 0.000) | sim | peça fixa |
| COL_caixa | fis_caixa_papelao | (0.000, 0.150, 0.000) | - | colisor |
| SURF_tampa | fis_caixa_papelao | (0.000, 0.300, 0.000) | - | superfície de apoio |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| papelao | papelao_liso.png (256x256) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| fita_adesiva | fita.png (256x64) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| papelao_impresso | papelao_impresso.png (256x256) | metal 0.00, rugosidade 0.55 | MASK dupla face | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_caixa | box | (0.000, 0.150, 0.000) | 0.400 x 0.300 x 0.320 | não (é empurrado) | objeto_solto |
- Superfície de apoio SURF_tampa a 0.300 m: objetos pequenos
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **dinamico**. caixa leve: pode ser empurrada, cair de móveis e tombar; repousa sem tremer (dorme parada)
- massa: 1.2
- atrito: 0.62
- restituicao: 0.12
- amortecimento: 0.08
- amortecimento_ang: 0.25
- Simulação: Physics.kt (passos de 1/120 s, impulsos acumulados com atrito, contato por cantos/arestas da caixa ou esfera; piso, paredes, colisores dos móveis, outros objetos e o personagem). Dorme parado (não treme nem gasta CPU).

## Partes animadas
Não se aplica: objeto sem peças móveis (o movimento é todo da física).

## Interações
Empurrar: andando contra ela (pernas) ou com as mãos quando está numa mesa/bancada. Cai de móveis, tomba na borda, empilha.
- Cancelamento: Não se aplica (física contínua; para sozinha).

## Estados e persistência
Sem estados de uso. Posição e rotação do corpo são gravadas quando ela para (dorme).

## Testes
| Teste | Onde | Resultado |
|---|---|---|
| Arquivo GLB válido (cabeçalho, blocos, acessores, índices, normais, faces, materiais, imagens, metadados) | verificador glb_lib.verify, aqui | aprovado |
| Leitura pelo código do jogo (Glb.kt compilado de verdade, rodando na JVM) | aqui | aprovado: nós, colisores, pivôs, animações e pontos de interação lidos |
| Geometria relida do GLB e renderizada (3 ângulos; aberto/fechado nas peças móveis) | aqui | conferido visualmente |
| Física: queda, repouso, sono, tombar na borda da mesa, empilhar, quique, chute, parede (Physics.kt compilado, 9 cenários) | aqui (JVM) | aprovado |
| Escala no jogo | celular | **pendente** (não consigo rodar Android aqui) |
| Posicionamento (colocar, girar, mover) | celular | **pendente** (não consigo rodar Android aqui) |
| Colisão andando em volta | celular | **pendente** (não consigo rodar Android aqui) |
| Partes móveis / interação / interrupção | celular | **pendente** (não consigo rodar Android aqui) |
| Persistência (salvar e reabrir) | celular | **pendente** (não consigo rodar Android aqui) |
| Desempenho no aparelho | celular | **pendente** (não consigo rodar Android aqui) |

## Arquivos
- `app/src/main/assets/obj3d/fis_caixa_papelao.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/fis_caixa_papelao.png`
- Fonte: `ferramentas/objetos3d/models.py` (função caixa), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
