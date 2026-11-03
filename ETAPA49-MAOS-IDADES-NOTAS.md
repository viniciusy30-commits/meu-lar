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

## Revisão 2 — braços "enormes" e axila estranha (principalmente correndo)
- **Axila:** a difusão de pesos da Etapa 45 prendia a lateral inteira do tronco (até 14 cm abaixo do ombro) na clavícula (~50% do peso).
  Ao mexer o ombro, a costela lateral virava uma "aba" esticada. Agora (`fix_clavicle`) a clavícula só influencia o topo do ombro;
  abaixo dele o peso vai para a coluna (tronco) ou para o braço, e `smooth_armpit` suaviza a transição numa esfera de ~13 cm em cada axila.
- **Braço "longo" correndo:** o balanço vinha do clipe antigo, exagerado para trás (−58° a +14°) com cotovelo muito fechado (103–117°).
  Agora (`natural_arms`, `SWING`, `ABD`, `ELBOW2`): correr −38° a +12°, cotovelo 93–105°; andar com balanço lateral mais contido.
  Comprimento dos ossos não mudou (braço 31 cm + antebraço 25 cm no adulto): era o balanço.
- Verificado em tf, af, ef, am, em, cu, pu (renderização sombreada de frente/lado/3-4, andar e correr): sem "aba" na axila, 0 NaN, soma dos pesos = 255.

## Revisão 3 — cabeça olhando para cima / pescoço "enorme" na corrida
- Causa: no clipe de correr o tronco inclina ~16° para a frente e o pescoço acompanha (12–21°), mas a cabeça era jogada 10–21° para TRÁS
  (olhar para o alto + dobra no pescoço). Todas as idades herdavam isso.
- Agora (`fix_head`, `HEAD`): na corrida (clipes 3 e 6) tronco 16° → pescoço ~6–10° → pescoço alto ~4° → cabeça ~−1° (olhando para a frente),
  mantendo uma fração do balanço original para não ficar rígido. Parado, andar e pulo não mudaram.

## Ajustes finos (topo de `etapa49_maos_idades.py`)
- `CURL_RELAX` / `CURL_RUN`: graus por falange (proximal, média, distal) de indicador, médio, anelar, mínimo e polegar. Mais aberto = números menores.
- `SWING` / `ABD` / `ELBOW2`: (centro atual, escala, novo centro) em graus do balanço; escala maior = braço balança mais (1.0 = como o clipe original).
- `HEAD`: (ângulo-alvo médio, fração do balanço original mantida) de neck_01, neck_02 e cabeça na corrida; cabeça mais para cima = número maior que −1, mais para baixo = menor.
- `rad` em `smooth_armpit` e `fix_clavicle`: tamanho da zona suave da axila / altura onde a clavícula deixa de agir.
- Posição do nó dos dedos: `u_mcp = 0.50 * L` em `hand_model` (fração do comprimento da mão).

## Gerar de novo
`python3 ferramentas/etapa49_maos_idades.py app/src/main/assets/cute` (usa `--out <pasta>` para não sobrescrever; aceita lista de grupos).
Sem compilador/aparelho aqui: o build do GitHub e o teste no celular são a prova final.
