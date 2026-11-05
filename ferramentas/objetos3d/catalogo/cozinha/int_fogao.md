# int_fogao — Fogão 4 bocas com forno

**Categoria:** cozinha / eletrodomesticos  ·  **Classe:** funcional  ·  **Versão:** 1

## Descrição visual
Fogão 4 bocas de inox: gabinete em chapas, mesa preta, queimadores com espalhador e tampa, grades de ferro com espessura (aro, braços e pés), painel com 5 botões (com marca), porta do forno com visor escuro e puxador, cavidade do forno com grade, pés. Panela com tampa numa boca.

**Variações reais previstas:** Cooktop separado e fogão de 5 bocas na família de eletrodomésticos.

## Medidas e escala
- Largura (X) 0.570 m · altura (Y) 0.910 m · profundidade (Z) 0.594 m
- Escala do jogo: adulto ~1.45 m; o objeto tem 63% da altura do personagem.
- Área ocupada no chão (colisores): 0.56 x 0.50 m. Grade do jogo: 1x1 casa(s).
- Eixos: Y para cima, frente = +Z, origem no centro do piso do objeto, metros.

## Malha, hierarquia e pivôs
Vértices: 5420 · triângulos: 6224 · nós: 12 · arquivo: 242 KB

| Nó | Pai | Pivô (m, no objeto) | Malha | Papel |
|---|---|---|---|---|
| int_fogao | - | (0.000, 0.000, 0.000) | - | raiz (metadados) |
| corpo | int_fogao | (0.000, 0.000, 0.000) | sim | peça fixa |
| botao_0 | int_fogao | (-0.200, 0.660, 0.252) | sim | peça móvel (dobradica) |
| botao_1 | int_fogao | (-0.100, 0.660, 0.252) | sim | peça móvel (dobradica) |
| botao_2 | int_fogao | (0.000, 0.660, 0.252) | sim | peça móvel (dobradica) |
| botao_3 | int_fogao | (0.100, 0.660, 0.252) | sim | peça móvel (dobradica) |
| botao_4 | int_fogao | (0.200, 0.660, 0.252) | sim | peça móvel (dobradica) |
| chamas | int_fogao | (0.000, 0.740, 0.000) | sim | peça fixa |
| porta_forno | int_fogao | (0.000, 0.080, 0.250) | sim | peça móvel (dobradica) |
| COL_corpo | int_fogao | (0.000, 0.360, -0.010) | - | colisor |
| SURF_mesa | int_fogao | (0.000, 0.760, -0.010) | - | superfície de apoio |
| IP_usar | int_fogao | (0.000, 0.000, 0.680) | - | ponto de interação |

## Materiais e texturas
| Material | Textura | PBR (visualizadores) | Transparência | Observação |
|---|---|---|---|---|
| latao_escovado | escovado.png (128x128) | metal 1.00, rugosidade 0.32 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |
| plastico_fosco | liso.png (8x8) | metal 0.00, rugosidade 0.55 | OPAQUE dupla face | cor do vértice x textura; sombra de contato (AO) assada na cor do vértice |

UVs: projeção planar em metros nas peças de madeira/tecido (textura repete), mapeamento próprio nas folhas, impressão e bola. No jogo o shader é simples (sem PBR completo): metal e rugosidade servem para outros visualizadores; no jogo vale o código de material (brilho).

## Colisores
| Nome | Forma | Centro (m) | Tamanho (m) | Bloqueia personagem | Camada |
|---|---|---|---|---|---|
| COL_corpo | box | (0.000, 0.360, -0.010) | 0.560 x 0.720 x 0.500 | sim | movel |
- Superfície de apoio SURF_mesa a 0.760 m: panelas (sobre as grades)
- Zonas sem colisão: puxadores, dobradiças, botões, folhas e costuras (só decoração).

## Física
- Tipo: **estatico**. eletrodoméstico ancorado
- massa: 35.0
- Ancorado: nunca tomba, desliza ou é empurrado. Só as peças móveis animam.

## Partes animadas
| Peça | Tipo | Eixo | Intervalo | Duração | Curva | Inicial | Ao cancelar |
|---|---|---|---|---|---|---|---|
| botao_0 | dobradica | [0, 0, 1] | 0° a -110° | 0.35 s | suave | 0.0 | inverte de onde está |
| botao_1 | dobradica | [0, 0, 1] | 0° a -110° | 0.35 s | suave | 0.0 | inverte de onde está |
| botao_2 | dobradica | [0, 0, 1] | 0° a -110° | 0.35 s | suave | 0.0 | inverte de onde está |
| botao_3 | dobradica | [0, 0, 1] | 0° a -110° | 0.35 s | suave | 0.0 | inverte de onde está |
| botao_4 | dobradica | [0, 0, 1] | 0° a -110° | 0.35 s | suave | 0.0 | inverte de onde está |
| porta_forno | dobradica | [1, 0, 0] | 0° a 85° | 0.55 s | suave | 0.0 | inverte de onde está |

## Interações
Ligar/desligar de frente para o fogão: os botões giram e aparecem as chamas azuis (animadas) nas 4 bocas. Abrir/fechar a porta do forno (dobradiça embaixo, 85°).
- IP_usar: ação "ligar"; posição final da raiz do personagem (0.000, 0.000, 0.680); olha para -Z; aproximação em None.
- Cancelamento: Desligar a qualquer momento apaga as chamas e volta os botões.

## Estados e persistência
desligado / ligado (gravado). Porta do forno: fechada/aberta (gravada).

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
- `app/src/main/assets/obj3d/int_fogao.glb` (texturas embutidas) e `app/src/main/assets/obj3d/thumb/int_fogao.png`
- Fonte: `ferramentas/objetos3d/models.py` (função fogao), texturas: `ferramentas/objetos3d/textures.py`
- Importação: automática; o tipo `G_*` em GameState.kt aponta para o arquivo pelo nome.
