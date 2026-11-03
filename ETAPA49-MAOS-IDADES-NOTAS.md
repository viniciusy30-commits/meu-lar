# Etapa 49 — Mãos naturais e anatomia do Jovem em todas as idades (aguardando teste)

Pedido: mãos esticadas (rígidas) em todos os personagens; andar/correr com anatomia estranha nas outras idades.
Referência: a anatomia do **Jovem** (coluna, ombros, braços), sem mexer na aparência.

## Causa
1. **Mãos:** a malha da mão do Sims 3 é uma "luva" inteira ligada só ao osso `hand`. Os 30 ossos de dedos (25..54) existiam, mas
   nenhum vértice tinha peso neles e os clipes os faziam copiar o punho → mão reta e dura.
2. **Idades:** só `tf`/`tm` (Jovem) tinham passado pela correção da Etapa 48 (coluna reta, clavícula/ombro, braços junto do corpo).
   `af am ef em cu pu` ainda tinham o zigue-zague de coluna e os braços abertos do clipe antigo.

## O que mudou (só assets + ferramenta; Kotlin/shader/texturas NÃO mudaram)
- `ferramentas/etapa49_maos_idades.py` (novo): roda o pipeline da Etapa 48 em `tf tm af am ef em cu pu` e acrescenta:
  - **pesos dos dedos:** vértices da mão ganham peso nos ossos dos 4 dedos + polegar (3 falanges, mistura suave nas juntas);
  - **dedos dobrados nos clipes:** mão relaxada (parado, andar, pulo) e punho frouxo (correr; clipes 3 e 6). Rotação em torno
    das juntas reais da malha, sempre para o lado da palma; polegar fecha em direção ao indicador.
- Assets regerados: `p_body_{af,am,ef,em,cu,pu,tf,tm}*.bin` (só `bi/bw`; posição/UV/índices idênticos) e `clips_{af,am,ef,em,cu,pu,tf,tm}.bin`.
- Verificado: 0 NaN, soma dos pesos = 255, ossos ≤ 54, inclinação do tronco igual entre idades (parado ≈ 0°, andar ≈ 0–1°, correr ≈ 12°).
- Roupas (`p_top_*` etc.) não foram alteradas: as mangas terminam no punho, e o que fica da mão para baixo é pele.

## Ajustes finos (topo de `etapa49_maos_idades.py`)
- `CURL_RELAX` / `CURL_RUN`: graus por falange (proximal, média, distal) de indicador, médio, anelar, mínimo e polegar. Mais aberto = números menores.
- Posição do nó dos dedos: `u_mcp = 0.50 * L` em `hand_model` (fração do comprimento da mão).

## Gerar de novo
`python3 ferramentas/etapa49_maos_idades.py app/src/main/assets/cute` (usa `--out <pasta>` para não sobrescrever; aceita lista de grupos).
Sem compilador/aparelho aqui: o build do GitHub e o teste no celular são a prova final.
