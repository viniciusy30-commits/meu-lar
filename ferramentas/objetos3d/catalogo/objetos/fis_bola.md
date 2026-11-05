# fis_bola — Bola de borracha

**Categoria:** objetos / brinquedos  ·  **Classe:** fisico  ·  **Versão:** 1

## Descrição visual
Bola de borracha oca de 22 cm com seis gomos (vermelho, azul, amarelo intercalados com branco), costuras escurecidas e tampas brancas nos polos.

**Variações reais previstas:** Bola de futebol e de basquete (com textura e quique próprios) no lote de brinquedos.

## Medidas e escala
- Largura (X) 0.220 m · altura (Y) 0.220 m · profundidade (Z) 0.220 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 15% da altura do personagem.
- Área ocupada no chão (colisores): 0.22 x 0.22 m. Grade do jogo: 1x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 701 · triângulos: 1224 · nós: 3 · arquivo: 68 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| fis_bola | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| bola | fis_bola | (0.000, 0.110, 0.000) | sim | peça fixa |
| COL_bola | fis_bola | (0.000, 0.110, 0.000) | - | colisor |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| borracha_bola | bola.png (512x256) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_bola | sphere | (0.000, 0.110, 0.000) | 0.220 x 0.220 x 0.220 | não (é empurrado) | objeto_solto |
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **dinamico**. bola oca de borracha: quica, rola e é chutada quando o personagem corre contra ela
- massa: 0.35
- atrito: 0.55
- restituicao: 0.62
- amortecimento: 0.03
- amortecimento_ang: 0.06
- rolamento: 0.012
- Simulação: Physics.kt (passos de 1/120 s, impulsos acumulados com atrito, contato por cantos/arestas da caixa ou esfera; piso, paredes, colisores dos móveis, outros objetos e o personagem). Dorme parado (não treme nem gasta CPU).

## Partes animadas
Não se aplica: objeto sem peças móveis (o movimento é todo da física).

## Interações
Chutar/empurrar: correndo contra ela, ela é chutada (sobe um pouco); andando, rola. Quica no piso, nas paredes e nos móveis.
- Cancelamento: Não se aplica.

## Estados e persistência
Sem estados de uso. Posição e rotação gravadas quando ela para.

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
- `app/src/main/assets/obj3d/fis_bola.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/fis_bola.png`
- Fonte: `ferramentas/objetos3d/models.py` (função bola), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
