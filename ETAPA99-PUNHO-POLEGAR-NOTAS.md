# Etapa 99 — punho fechado de verdade na corrida (polegar) (aguardando teste)

## Causa
Simulei o `fistHands` na malha do corpo Sims 4 (p_body_af5.bin). Os 4 dedos fechavam, mas o POLEGAR ficava esticado para fora:
ele só girava em Z (18°/28°/18°) como os outros dedos, só que o polegar fica na frente da mão (z ≈ +2..+7 cm),
então girar em Z não o trazia para cima dos outros dedos. Era ele o "dedo apontando" no print.

## Correção (só CuteChar.kt, `fistHands`)
- Corpo Sims 4: o polegar primeiro "entra" girando 35° em X em torno da base dele (THUMB_TUCK_DEG / THUMB_TUCK_P),
  depois dobra as 3 juntas com THUMB_ANG_TS4 = -18 / 5 / 25. Resultado: polegar cruza por cima dos dedos fechados.
- Mão direita espelha o pivô em x (mesma rotação em X). Os 4 dedos e o corpo Sims 3 não mudaram.

## Ajuste fino
- Polegar ainda sai para fora: aumente THUMB_TUCK_DEG (35 -> 45).
- Polegar atravessando os dedos: diminua THUMB_TUCK_DEG ou aumente o 1º valor de THUMB_ANG_TS4 (mais negativo = mais para fora).

Sem compilador/aparelho aqui: validei só numa simulação em Python da mesma matemática sobre a malha. O build do GitHub é a prova final.
