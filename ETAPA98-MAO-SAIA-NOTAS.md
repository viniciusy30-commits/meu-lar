# Etapa 98 — correção da mão (corrida/pulo) e da colisão da saia (aguardando teste)

Consertos sobre a etapa 97 (a mão tinha ficado pior e o jogo travava/perdia FPS).

## Mão (corpo Sims 4)
- FIST_J_TS4 da etapa 97 estava na escala do esqueleto original do TS4; a malha do corpo é reescalada para 182 cm. Os pivôs dos dedos ficaram fora da mão e os dedos rasgavam.
- Agora os pivôs são trazidos para a escala da malha (punho do skel_s4.txt -> punho do bodyrig af5, escala 0,969). Valores novos em FIST_J_TS4.
- Os ângulos de fechamento (FIST_ANG) não mudaram.

## Saia (colisão perna x saia)
- A colisão empurrava a saia até 10 cm (mais de 3 cm em ~600 vértices ao pular/sentar), esticando o tecido. Agora o empurrão de cada vértice nunca passa da folga que ele já tem até a coxa na pose parada (legRef, calculado uma vez e refeito só se o formato do corpo mudar). Parada: empurrão máx 0,2 cm.
- Desempenho: a colisão percorre só os vértices abaixo do quadril (lista legIdx), não a malha inteira.

## Mantido
- Cabeça/pescoço na corrida (clips_af5/am5 da etapa 97) não mudaram.

Sem compilador local: o build do GitHub é a prova final. Se a mão ainda ficar estranha, mande um print de perto (próximo suspeito: FIST_ANG).
