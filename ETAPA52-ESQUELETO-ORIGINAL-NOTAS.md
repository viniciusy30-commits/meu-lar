# Etapa 52 - Esqueleto original do The Sims 3 (aguardando teste)

Fonte: `auRig`, `cuRig`, `puRig.grannyrig` do pacote Blender GEOM Tools (SmugTomato). Sao os esqueletos do proprio jogo (257 ossos, nomes `b__Pelvis__`, `b__L_UpperArm__`...), na mesma escala em metros das malhas OBJ do Sims 3 (conferido: cabeca em 1,674 m, braco em A como a malha).

## O que mudou (so dados + ferramentas; Kotlin NAO mudou)
- `assets/cute/skel_au.txt`, `skel_cu.txt`, `skel_pu.txt`: esqueleto original completo (adulto/jovem/idoso, crianca, bebe).
- `assets/cute/bodyrig.txt`: as juntas dos sliders de corpo (ombro, cotovelo, mao, quadril, joelho, tornozelo, alturas do peito/pescoco/cabeca) agora vem do esqueleto original, antes eram ajustadas a olho na malha (3 a 7 cm de diferenca; quadril e joelho eram os que mais erravam).
- Jovem/adulto/idoso usam o `auRig`; crianca `cuRig`; bebe `puRig`. Masculino: mesmo rig, escalado pela altura da malha.
- Verificado: 27 sliders x 21 corpos x (+100/-100) sem NaN, deslocamentos maximos na mesma faixa de antes (ate ~8 cm em Postura do bebe).
- Ferramentas: `ferramentas/etapa52_esqueleto_original.py` e `sims3_rig_tools.py` (leitor de .grannyrig).

## Limites
- Sem animacao (Etapa 51), o esqueleto so aparece nos pontos de pivo dos sliders; o corpo continua parado na pose original.
- Os 55 ossos do app (`clips_*.bin`, pesos de pele `bi/bw` dos corpos) continuam os da Etapa 45. Para pesos de pele com os 257 ossos reais seria preciso o GEOM de cada corpo do jogo (os OBJ nao trazem pesos) e mudar o formato do app.
