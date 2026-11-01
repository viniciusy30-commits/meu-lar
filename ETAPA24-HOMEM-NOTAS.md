# Etapa 24 — postura e rosto masculinos (aguardando teste no celular)
Junto vai o cabelo colado na cabeça (etapa 23: p_hairfront_repartidovol.bin e p_hairback_mediovol.bin).

## Postura (só masculino)
- `base.bin`: clipes 4 (parado) e 5 (andar) regerados: pés afastados na largura dos ombros e pontas dos pés para fora, pelve sob o tronco (sem a "barriga para frente"), peito aberto, cabeça nivelada, dedos relaxados. Clipes 0-3 e 6 intactos. Script: `ferramentas/etapa24_postura_masculina.py`.
- `CuteChar.kt`: `MALE_CLIPS = true` só para parado/andar; correr e pular seguem os do feminino. Braços para dentro (etapa 17) continuam.
## Rosto (só masculino)
- Olhos menores: `BodyMorph.maleEyes` encolhe globo e pálpebras (80% largura, 68% altura), a sobrancelha desce junto: olhar mais sério. Ajuste: `EYE_SX`, `EYE_SY`.
- Boca mais fina e natural, sobrancelha mais grossa, cantos dos olhos levemente para baixo: `M_FACE_ADD` (Boca fina 0,8). Os sliders do criador somam por cima.
Sem compilador/teste no aparelho: o build é a prova final.
