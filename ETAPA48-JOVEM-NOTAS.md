# Etapa 48 — Anatomia do Jovem (coluna, ombros, braços) (aguardando teste)

Prints do criador (Jovem masculino/feminino, magro/normal/gordo): coluna encurvada, cabeça para a frente, ombros estranhos, braços afastados do corpo.

## Causa
1. `etapa45_rig.fit_joints` achava o z (profundidade) da coluna/clavícula com `zmid`, que usa fatias esparsas da malha. No tronco do Sims essas fatias só tinham vértices da FRENTE do peito: `spine_05` e `clavicle` ficavam em z ≈ +11,6 cm, enquanto o eixo real do tronco/pescoço está em z ≈ -2 cm. A coluna fazia um zigue-zague (pescoço "voltava" 14 cm) e a clavícula apontava 36° para trás.
2. `retarget_clips` girava cada osso da coluna para igualar a direção do boneco antigo (Bozo) mesmo em repouso, então esse zigue-zague virava curvatura/corcunda em TODAS as animações.
3. Os braços saíam do clipe antigo ~12-25° abertos (o Sims 3 repousa em A de ~40°).

## O que mudou
- `ferramentas/etapa45_rig.py`: coluna/clavícula em reta do quadril ao pescoço (`zline`); `KEEP_REST`: pelve, coluna e pescoço usam só a rotação do clipe (sem alinhar à curvatura do Bozo).
- `ferramentas/etapa48_jovem.py` (novo): refaz pesos e clipes direto dos `.bin` já gerados (NÃO precisa dos OBJ/RAR). Recupera as juntas de repouso por mínimos quadrados dos clipes, reaplica `fit_joints` corrigido, recalcula pesos de pele e os clipes e fecha os braços até ~6° (parado/andar) e ~5° (correr) da vertical.
- Assets regerados: `p_body_tf{0,1,3}.bin`, `p_body_tm{0,1,3}.bin` (só `bi/bw`; posição, UV e índices idênticos) e `clips_tf.bin`, `clips_tm.bin`.
- Verificado no PC: 0 NaN, pés exatamente no chão em todos os 7 clipes, soma dos pesos = 255.
- Kotlin, shader, texturas, cabelos e roupas NÃO mudaram.

## Gerar de novo
`python3 ferramentas/etapa48_jovem.py app/src/main/assets/cute tf tm`
(uso `--out <pasta>` para não sobrescrever; `--check` mostra as juntas antigas → novas). Os grupos `af am ef em cu pu` têm o mesmo defeito de origem e podem receber o mesmo tratamento (não foram alterados nesta etapa).

## Ajustes finos
- Cotovelos: `ELBOW` em `etapa48_jovem.py` (flexão final em graus; parado ~8° = braço relaxado, andar mantém 55% do balanço, correr/pulo como o clipe).
- Braços mais perto/longe: `TARGET_DEG` em `etapa48_jovem.py` (graus da vertical; menor = mais colado).
- Sem compilador local: o build do GitHub é a prova final.
- Mãos: `align_hands` faz a mão repetir a rotação do antebraço (pivô no punho); antes herdava a do clipe antigo e o punho ficava torto.
