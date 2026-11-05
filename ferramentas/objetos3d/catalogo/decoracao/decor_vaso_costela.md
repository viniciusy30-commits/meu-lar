# decor_vaso_costela — Vaso com costela-de-adão

**Categoria:** decoracao / plantas  ·  **Classe:** decorativo  ·  **Versão:** 1

## Descrição visual
Vaso cônico de cerâmica com pé em anel, borda enrolada e esmalte verde-sálvia que escorre irregular até 5 cm do pé (o barro terracota aparece embaixo). A parede interna é modelada até a terra. Terra com relevo e 9 pedrinhas. Costela-de-adão com 9 folhas: cada folha é uma lâmina curva (dobra em V raso e caída para a ponta) com recortes e furos de verdade na textura (recorte por alfa), presa a um pecíolo cilíndrico que sai da terra em arco. Folhas com tons levemente diferentes.

**Variações reais previstas:** Outros esmaltes (terracota, branco, azul) e outras plantas no mesmo vaso entram como variações reais no próximo lote, não só recoloração.

## Medidas e escala
- Largura (X) 1.338 m · altura (Y) 0.784 m · profundidade (Z) 1.344 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 54% da altura do personagem.
- Área ocupada no chão (colisores): 0.36 x 0.36 m. Grade do jogo: 1x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 3377 · triângulos: 5340 · nós: 4 · arquivo: 330 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| decor_vaso_costela | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| vaso | decor_vaso_costela | (0.000, 0.000, 0.000) | sim | peça fixa |
| planta | decor_vaso_costela | (0.000, 0.310, 0.000) | sim | peça fixa |
| COL_vaso | decor_vaso_costela | (0.000, 0.186, 0.000) | - | colisor |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| ceramica_esmaltada | esmalte.png (256x256) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| terra_vaso | terra.png (256x256) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| folha_planta | folha_costela.png (512x512) | metal 0.00, rugosidade 0.80 | MASK dupla face | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_vaso | cyl | (0.000, 0.186, 0.000) | 0.360 x 0.372 x 0.360 | sim | movel |
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. vaso cheio de terra: pesado, não deve tombar nem deslizar ao encostar
- massa: 14.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
Não se aplica: objeto sem peças móveis (decorativo).

## Interações
Nenhuma (decorativo). Colisão só no vaso: as folhas não bloqueiam o personagem.
- Cancelamento: Não se aplica (sem ação).

## Estados e persistência
Sem estados. Nada a salvar além de posição e giro (já gravados pelo jogo).

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
- `app/src/main/assets/obj3d/decor_vaso_costela.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/decor_vaso_costela.png`
- Fonte: `ferramentas/objetos3d/models.py` (função vaso), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
