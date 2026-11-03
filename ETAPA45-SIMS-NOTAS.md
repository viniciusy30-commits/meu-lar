# Etapa 45 — Esqueleto próprio do Sims 3 (aguardando teste)

Corrige pescoço, braços e mãos bugados dos corpos do Sims 3 (Etapa 44).

Causa: os pesos eram copiados do corpo antigo (Bozo) pelo vértice mais próximo e a malha do Sims não coincidia com as juntas do esqueleto do app (corte seco no pescoço, ombros/cotovelos girando no ponto errado, antebraços para dentro, mãos "luva").

O que mudou:
- Nada do Bozo: as juntas (ombro, cotovelo, punho, quadril, joelho, tornozelo, coluna, pescoço, cabeça) são ajustadas direto na malha de cada corpo do Sims 3 (`ferramentas/etapa45_rig.py`).
- Pesos de pele por difusão ao longo dos segmentos dos ossos, com degradê suave no pescoço e no ombro.
- Clipes de animação do app adaptados ao esqueleto do Sims: um conjunto por estágio+sexo (`assets/cute/clips_<af|am|tf|tm|ef|em|cu|pu>.bin`, formato CLP1).
- `CuteChar.kt`: carrega o conjunto de clipes do corpo escolhido (`useSimClips`); a correção de braço do masculino (MALE_FOREARM_IN) não se aplica mais aos corpos do Sims; a altura "lift" mede só o corpo do Sims e os sapatos.
- Corpos (`p_body_*.bin`) e cabelos traseiros (`p_hairback_h??.bin`) regerados.
- Gerador: `python3 ferramentas/etapa45_sims_rig.py <pasta com bodies/ e faces/> app/src/main/assets/cute`.
- Sem compilador local: o build do GitHub é a prova final. Se falhar, corrigir só o erro apontado.
